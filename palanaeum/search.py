import abc
import re
from collections import defaultdict
from datetime import datetime, date
from urllib.parse import urlencode

from django.core.cache import caches
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import ProgrammingError
from django.db.models.functions import Lower
from django.http.request import QueryDict
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from palanaeum.models import Entry, Tag, EntrySearchVector, UserSettings, EntryVersion

SEARCH_CACHE = caches['search']
SEARCH_CACHE_TTL = 60


class SearchFilter(abc.ABC):
    """
    That's an abstract class defining an interface for Search Filters.
    The filters operate on EntryLines.
    """
    @abc.abstractmethod
    def _get_cache_key(self):
        return None

    def get_entry_ids(self) -> frozenset:
        """
        Return a set of pairs (entry_id, rank) that fulfill the search query.
        Rank should be a non-negative float number.

        Can return entries that shouldn't be visible to regular users!
        """
        raise NotImplementedError

    @abc.abstractmethod
    def init_from_get_params(self, get_params: QueryDict) -> bool:
        """
        Initialize this filter using data passed in GET request.
        Return bool indicating if this search filter is used.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def to_tr(self) -> str:
        """
        Get the HTML code of this filter.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __bool__(self):
        """
        Return true, if this filter is active - it has proper settings.
        """
        return False

    @abc.abstractmethod
    def as_url_param(self) -> str:
        """
        Return a string that can be added to URL, that will later be understood by this filter.
        For example: query=rafo
        """
        return ""


class TextSearchFilter(SearchFilter):
    """
    Search for entries that match given text sample.
    """
    QUOTE_REGEXP = re.compile(r'''(?P<quote>['"])(.+?)(?P=quote)''')
    SQL_QUERY = """\
        SELECT id, entry_id, ts_rank(text_vector, to_tsquery(%s), 32) + 1 as rank
        FROM palanaeum_entrysearchvector esv
        WHERE text_vector @@ to_tsquery(%s)
        """
    GET_PARAM_NAME = 'query'
    LABEL = _('Search for text:')

    def __init__(self):
        self.search_phrase = ''
        self.search_tokens = []
        self.exact_search_tokens = []

    def as_url_param(self) -> str:
        return urlencode({self.GET_PARAM_NAME: self.search_phrase})

    def _get_cache_key(self):
        return "text_search_" + str(hash(" ".join(sorted(self.search_tokens))))

    def _get_results_for_token(self, token):
        token_results = {}
        if ' ' in token:
            # Currently, this should never happen
            query = " <-> ".join(token.split(' '))
        else:
            query = token

        try:
            for esv in EntrySearchVector.objects.raw(self.SQL_QUERY, [query, query]):
                token_results[esv.entry_id] = esv.rank
        except ProgrammingError:
            token_results = {}

        return token_results

    def _get_normal_search_results(self) -> defaultdict:
        results = defaultdict(float)

        for token in self.search_tokens:
            cache_key = "search_text_" + str(hash(token))
            token_results = SEARCH_CACHE.get(cache_key)

            if not token_results:
                token_results = self._get_results_for_token(token)
                SEARCH_CACHE.set(cache_key, token_results, SEARCH_CACHE_TTL)

            for entry_id, rank in token_results.items():
                results[entry_id] += rank

        return results

    def _get_exact_search_results(self) -> defaultdict:
        results = defaultdict(float)

        for token in self.exact_search_tokens:
            cache_key = "exact_search_text_" + str(hash(token))
            token_results = SEARCH_CACHE.get(cache_key)

            if not token_results:
                token_results = {}
                entries_with_token = EntryVersion.newest.filter(lines__text__icontains=token).values_list('entry_id', flat=True)
                # Need to accept only the newest versions of entries! I need to make that newest flag happen!
                for entry_id in entries_with_token:
                    token_results[entry_id] = 10  # Exact match is much more valuable
                SEARCH_CACHE.set(cache_key, token_results, SEARCH_CACHE_TTL)

            for entry_id, rank in token_results.items():
                results[entry_id] += rank
        return results

    def get_entry_ids(self) -> frozenset:
        results = self._get_normal_search_results()
        for key, value in self._get_exact_search_results().items():
            results[key] += value
        return frozenset((entry_id, rank) for entry_id, rank in results.items())

    def init_from_get_params(self, get_params: QueryDict):
        self.search_phrase = get_params.get(self.GET_PARAM_NAME, '').strip()

        if not self.search_phrase:
            return False

        for quoted_text in self.QUOTE_REGEXP.findall(self.search_phrase):
            self.exact_search_tokens.append(quoted_text[1])

        for word in self.QUOTE_REGEXP.sub('', self.search_phrase).split(' '):
            self.search_tokens.append(word)

        return True

    def __bool__(self):
        return bool(self.search_phrase)

    def to_tr(self) -> str:
        return render_to_string(
            'palanaeum/search/filters/text_filter.html',
            {'field_name': self.GET_PARAM_NAME, 'value': self.search_phrase, 'label_text': self.LABEL}
        )


class DateSearchFilter(SearchFilter):
    """
    Limit the search results to EntryLines from events with date fulfilling a condition.
    """
    GET_DATE_FROM = 'date_from'
    GET_DATE_TO = 'date_to'

    def __init__(self):
        try:
            self.min = EntryVersion.objects.order_by('entry_date').only('entry_date').first().entry_date
        except AttributeError:
            self.min = date.today()
        self.date_from = self.min
        self.max = date.today()
        self.date_to = self.max
        self._active = False

    def as_url_param(self) -> str:
        return urlencode({
            self.GET_DATE_FROM: self.date_from.strftime('%Y-%m-%d'),
            self.GET_DATE_TO: self.date_to.strftime('%Y-%m-%d')
        })

    def _get_cache_key(self):
        return "date_search_{}_{}".format(self.date_from, self.date_to)

    def get_entry_ids(self) -> frozenset:
        # Search through the newest versions
        entries = EntryVersion.objects.filter(
            entry_date__range=(self.date_from, self.date_to)).distinct('entry_id')
        entries = entries & EntryVersion.newest.all()

        return frozenset((eid, 0) for eid in entries.values_list('entry_id', flat=True))

    def init_from_get_params(self, get_params: QueryDict):
        try:
            date_from_str = get_params.get(self.GET_DATE_FROM, None)
            date_to_str = get_params.get(self.GET_DATE_TO, None)
            self.date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            self.date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            return False
        else:
            self._active = True

        return True

    def __bool__(self):
        return self._active

    def to_tr(self) -> str:
        return render_to_string(
            'palanaeum/search/filters/date_range_filter.html',
            {
                'from_value': self.date_from.strftime('%Y-%m-%d'),
                'to_value': self.date_to.strftime('%Y-%m-%d'),
                'min_value': self.min.strftime('%Y-%m-%d'),
                'max_value': self.max.strftime('%Y-%m-%d'),
                'from_field_name': self.GET_DATE_FROM,
                'to_field_name': self.GET_DATE_TO,
            }
        )


class SpeakerSearchFilter(TextSearchFilter):
    GET_PARAM_NAME = 'speaker'
    SQL_QUERY = """\
        SELECT id, entry_id, ts_rank(speaker_vector, to_tsquery(%s), 32) + 1 as rank
        FROM palanaeum_entrysearchvector esv
        WHERE speaker_vector @@ to_tsquery(%s)
        """
    LABEL = _('Search for speaker:')

    def __init__(self):
        super(SpeakerSearchFilter, self).__init__()


class TagSearchFilter(SearchFilter):
    GET_TAG_SEARCH = 'tags'
    LABEL = 'Search for tags:'

    def __init__(self):
        self.tags = []

    def __bool__(self):
        return bool(self.tags)

    def as_url_param(self) -> str:
        return "&".join(urlencode({self.GET_TAG_SEARCH: tag.name}) for tag in self.tags)

    def init_from_get_params(self, get_params: QueryDict) -> bool:
        tags = {tag.lower() for tag in get_params.getlist(self.GET_TAG_SEARCH)}
        self.tags = Tag.objects.annotate(name_lower=Lower('name')).filter(name_lower__in=tags)
        return bool(self.tags)

    def get_entry_ids(self) -> frozenset:
        """
        Find entries that have at least one tag that we're looking for.
        Every tag gives +1 search rank. Tags are powerful!
        """
        results = defaultdict(int)
        cache_key = "search_tag_{}"
        for tag in self.tags:
            entries_with_tag = SEARCH_CACHE.get(cache_key.format(tag))

            if not entries_with_tag:
                entries_with_tag = EntryVersion.newest.filter(tags=tag).values_list('entry_id', flat=True)
                SEARCH_CACHE.set(cache_key.format(tag), entries_with_tag, SEARCH_CACHE_TTL)

            for entry_id in entries_with_tag:
                results[entry_id] += 1

        return frozenset(results.items())

    def _get_cache_key(self):
        """
        No general cache for this filter.
        """
        return None

    def to_tr(self) -> str:
        return render_to_string(
            'palanaeum/search/filters/tag_filter.html',
            {
                'field_name': self.GET_TAG_SEARCH,
                'selected_tags': self.tags,
                'label_text': self.LABEL
             }
        )


class AntiTagSearchFilter(TagSearchFilter):
    """
    Search for Entries that don't have given tags.
    Any of them.
    """
    GET_TAG_SEARCH = 'antitag'
    LABEL = _('Exclude those tags:')

    def get_entry_ids(self) -> frozenset:
        """
        Return only those Entries that don't have any required tags.
        """
        entries_that_have_tags = {i[0] for i in super(AntiTagSearchFilter, self).get_entry_ids()}
        entries = Entry.objects.exclude(id__in=entries_that_have_tags).values_list('id', flat=True)

        return frozenset((entry_id, 0) for entry_id in entries)


SEARCH_FILTERS = [
    TextSearchFilter,
    DateSearchFilter,
    SpeakerSearchFilter,
    TagSearchFilter,
    AntiTagSearchFilter
]


def init_filters(request) -> list:
    """
    Read request params and load them into SearchFilter objects.
    """
    filters = [search_filter() for search_filter in SEARCH_FILTERS]

    for search_filter in filters:
        search_filter.init_from_get_params(request.GET)

    return filters


def execute_filters(filters: list) -> dict:
    """
    Execute provided filters, returning a map of entry_it -> score.
    """
    entries_scores = defaultdict(float)
    entries_by_filter = defaultdict(set)

    for search_filter in filters:
        if not search_filter:
            continue

        search_filter_entry_ids = search_filter.get_entry_ids()
        if not search_filter_entry_ids:
            entries_by_filter.clear()
            break

        for entry_id, score in search_filter_entry_ids:
            entries_by_filter[search_filter].add(entry_id)
            entries_scores[entry_id] += score

    if entries_by_filter:
        good_ids = set.intersection(*entries_by_filter.values())
    else:
        good_ids = set()
    entries_scores = {entry_id: score for entry_id, score in entries_scores.items() if entry_id in good_ids}

    return entries_scores


def get_search_results(entries_scores: dict, ordering: str) -> list:
    """
    Convert a map of {entry_id -> score} to an ordered list of (entry_id, score) pairs.
    """
    search_results = list(entries_scores.items())

    # Show only visible entries
    visible_entries_ids = set(Entry.all_visible.filter(pk__in=entries_scores.keys()).values_list('id', flat=True))
    search_results = [sr for sr in search_results if sr[0] in visible_entries_ids]

    if ordering == 'rank':
        search_results.sort(key=lambda i: i[1], reverse=True)
    elif ordering in ('-date', '+date'):
        entry_dates = {eid: edate for eid, edate in
                       EntryVersion.newest.filter(entry_id__in=entries_scores.keys()).
                       values_list('entry_id', 'entry_date')
                       }
        search_results.sort(key=lambda entry: entry_dates[entry[0]], reverse=ordering == '-date')

    return search_results


def paginate_search_results(request, search_results: list) -> tuple:
    """
    Preload a page of search results. Return loaded entries, paginator object and page object.
    """
    page_length = UserSettings.get_page_length(request)
    paginator = Paginator(search_results, page_length, orphans=page_length // 10)

    page_num = request.GET.get('page', '1')

    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    entries_ids = [entry[0] for entry in page]
    entries_map = Entry.prefetch_entries(entries_ids)

    entries = [(entries_map[entry_id], rank) for entry_id, rank in page]

    return entries, paginator, page
