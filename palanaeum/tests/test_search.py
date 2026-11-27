import unittest
from datetime import date, timedelta

from django.core.cache import caches
from django.http import QueryDict
from django.test import RequestFactory, TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from palanaeum.models import EntrySearchVector
from palanaeum.search import (
    AntiTagSearchFilter,
    DateSearchFilter,
    SearchFilter,
    SpeakerSearchFilter,
    TagSearchFilter,
    TextSearchFilter,
    execute_filters,
    get_search_results,
    init_filters,
    paginate_search_results,
)
from palanaeum.tests.base import make_LocMem_caches_setting, set_current_request
from palanaeum.tests.factories import (
    EntryFactory,
    EntryLineFactory,
    EntryVersionFactory,
    EventFactory,
    StaffUserFactory,
    TagFactory,
    UserFactory,
    UserSettingsFactory,
)


def _build_index(entry):
    esv, _ = EntrySearchVector.objects.get_or_create(entry=entry)
    esv.update()
    return esv


class SearchFilterBaseTests(TestCase):
    def test_search_filter_abc_cannot_instantiate_and_super_defaults(self):
        with self.assertRaises(TypeError):
            SearchFilter()

        class DummyFilter(SearchFilter):
            def _get_cache_key(self):
                return super()._get_cache_key()

            def init_from_get_params(self, get_params):
                return False

            def to_tr(self):
                return ""

            def __bool__(self):
                return super().__bool__()

            def as_url_param(self):
                return super().as_url_param()

        df = DummyFilter()
        self.assertIsNone(df._get_cache_key())
        self.assertFalse(bool(df))
        self.assertEqual(df.as_url_param(), "")
        with self.assertRaises(NotImplementedError):
            df.get_entry_ids()


class SearchFiltersTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory()
        UserSettingsFactory(user=self.user, page_length=10)
        self.staff = StaffUserFactory()
        self.event = EventFactory(date=date(2023, 5, 1))

        self.tag_cosmere = TagFactory(name="cosmere")
        self.tag_spren = TagFactory(name="spren")
        self.tag_archived = TagFactory(name="legacy")

        # Entry 1: approved, searchable, older date
        self.e1 = EntryFactory(event=self.event, is_visible=True, is_approved=True, searchable=True)
        v1 = EntryVersionFactory(entry=self.e1, entry_date=date(2020, 1, 10), is_approved=True)
        v1.tags.add(self.tag_cosmere)
        EntryLineFactory(entry_version=v1, speaker="Brandon Sanderson", text="Honor is dead in the sky")
        _build_index(self.e1)

        # Entry 2: approved, searchable, newer date, exact phrase + archived tag
        self.e2 = EntryFactory(event=self.event, is_visible=True, is_approved=True, searchable=True)
        v2_old = EntryVersionFactory(
            entry=self.e2,
            entry_date=date(2021, 6, 1),
            date=timezone.now() - timedelta(minutes=10),
            is_approved=True,
        )
        v2_old.tags.add(self.tag_archived)
        EntryLineFactory(entry_version=v2_old, speaker="Fan", text="Old text")

        v2_new = EntryVersionFactory(
            entry=self.e2,
            entry_date=date(2022, 6, 1),
            date=timezone.now(),
            is_approved=True,
        )
        v2_new.tags.add(self.tag_cosmere, self.tag_spren)
        EntryLineFactory(
            entry_version=v2_new,
            speaker="Hoid",
            text="The golden sun shines on Roshar",
        )
        _build_index(self.e2)

        # Entry 3: not searchable, approved
        self.e3_unsearchable = EntryFactory(
            event=self.event, is_visible=True, is_approved=True, searchable=False
        )
        v3 = EntryVersionFactory(entry=self.e3_unsearchable, entry_date=date(2023, 1, 1), is_approved=True)
        v3.tags.add(self.tag_spren)
        EntryLineFactory(entry_version=v3, speaker="Brandon Sanderson", text="Hidden from text search golden sun")
        _build_index(self.e3_unsearchable)

        # Entry 4: unapproved suggestion
        self.e4_unapproved = EntryFactory(
            event=self.event, is_visible=True, is_approved=False, searchable=True
        )
        v4 = EntryVersionFactory(entry=self.e4_unapproved, entry_date=date(2024, 1, 1), is_approved=False)
        v4.tags.add(self.tag_spren)
        EntryLineFactory(entry_version=v4, speaker="Kelsier", text="Survive in Scadrial")
        _build_index(self.e4_unapproved)

    def tearDown(self):
        caches["search"].clear()
        super().tearDown()

    def test_text_search_filter_parsing_and_matching(self):
        f_empty = TextSearchFilter()
        self.assertFalse(f_empty.init_from_get_params(QueryDict("")))
        self.assertFalse(bool(f_empty))

        # + (%2B) is converted to & for tsquery; searchable=False excluded
        f = TextSearchFilter()
        self.assertTrue(f.init_from_get_params(QueryDict("query=honor%2Bdead")))
        self.assertTrue(bool(f))
        self.assertEqual(f.search_phrase, "honor&dead")
        self.assertEqual(f.search_tokens, ["honor&dead"])
        self.assertIn("query=honor", f.as_url_param())
        self.assertTrue(f._get_cache_key().startswith("text_search_"))
        self.assertIn("name=\"query\"", f.to_tr())

        ids = dict(f.get_entry_ids())
        self.assertIn(self.e1.id, ids)
        self.assertNotIn(self.e3_unsearchable.id, ids)

        # Quoted phrase + plain word, double and single quotes
        f_quote = TextSearchFilter()
        self.assertTrue(f_quote.init_from_get_params(QueryDict('query="golden sun" \'shines\' roshar')))
        self.assertEqual(f_quote.exact_search_tokens, ["golden sun", "shines"])
        self.assertIn("roshar", f_quote.search_tokens)
        q_ids = dict(f_quote.get_entry_ids())
        self.assertIn(self.e2.id, q_ids)
        self.assertGreater(q_ids[self.e2.id], 20)
        self.assertNotIn(self.e3_unsearchable.id, q_ids)

        # _get_results_for_token phrase branch ("<->")
        phrase_hits = f._get_results_for_token("golden sun")
        self.assertIn(self.e2.id, phrase_hits)

    @override_settings(CACHES=make_LocMem_caches_setting("search-text-cache"))
    def test_text_search_filter_uses_search_cache(self):
        caches["search"].clear()
        f = TextSearchFilter()
        f.init_from_get_params(QueryDict("query=honor"))
        first = f.get_entry_ids()
        self.assertTrue(first)
        with self.assertNumQueries(0):
            second = f.get_entry_ids()
        self.assertEqual(first, second)

    def test_date_search_filter(self):
        # Empty DB fallback for min date
        empty_min = date.today()
        EntryVersionFactory._meta.model.objects.all().delete()
        f_no_data = DateSearchFilter()
        self.assertEqual(f_no_data.min, empty_min)

    def test_date_search_filter_queries_and_validation(self):
        f = DateSearchFilter()
        self.assertEqual(f.min, date(2020, 1, 10))
        self.assertFalse(f.init_from_get_params(QueryDict("date_from=2021-01-01")))
        self.assertFalse(f.init_from_get_params(QueryDict("date_from=bad&date_to=2023-01-01")))
        self.assertFalse(bool(f))

        self.assertTrue(
            f.init_from_get_params(QueryDict("date_from=2022-01-01&date_to=2023-06-01"))
        )
        self.assertTrue(bool(f))
        self.assertIn("date_from=2022-01-01", f.as_url_param())
        self.assertTrue(f._get_cache_key().startswith("date_search_"))
        self.assertIn("date-range-filter", f.to_tr())

        # Date search intentionally includes searchable=False
        ids = {eid for eid, _ in f.get_entry_ids()}
        self.assertIn(self.e2.id, ids)
        self.assertIn(self.e3_unsearchable.id, ids)
        self.assertNotIn(self.e1.id, ids)

    def test_speaker_search_filter(self):
        f = SpeakerSearchFilter()
        self.assertTrue(f.init_from_get_params(QueryDict("speaker=brandon")))
        ids = dict(f.get_entry_ids())
        self.assertIn(self.e1.id, ids)
        self.assertNotIn(self.e3_unsearchable.id, ids)
        self.assertNotIn(self.e2.id, ids)

    def test_tag_search_filter_behavior(self):
        f = TagSearchFilter()
        self.assertFalse(f.init_from_get_params(QueryDict("")))
        self.assertIsNone(f._get_cache_key())

        self.assertTrue(f.init_from_get_params(QueryDict("tags=COSMERE&tags=spren")))
        self.assertTrue(bool(f))
        self.assertIn("tags=cosmere", f.as_url_param())
        self.assertIn("selected='selected'", f.to_tr())

        ids = dict(f.get_entry_ids())
        self.assertEqual(ids[self.e1.id], 1)
        self.assertEqual(ids[self.e2.id], 2)
        self.assertEqual(ids[self.e3_unsearchable.id], 1)  # ignores searchable=False

        # Archived tag no longer on newest version must not match
        f_arch = TagSearchFilter()
        f_arch.init_from_get_params(QueryDict("tags=legacy"))
        self.assertEqual(f_arch.get_entry_ids(), frozenset())

    @unittest.expectedFailure
    @override_settings(CACHES=make_LocMem_caches_setting("search-tag-leak"))
    def test_tag_search_cache_isolated_between_contributor_and_anonymous(self):
        """
        Bug in palanaeum/search.py:281-299 — TagSearchFilter caches `search_tag_{tag}`
        without scoping by user/contributor/staff visibility, so contributor queries
        poison the cache for anonymous users with unapproved entry IDs.
        """
        caches["search"].clear()
        with set_current_request(self.user):
            f_user = TagSearchFilter()
            f_user.init_from_get_params(QueryDict("tags=spren"))
            user_ids = {eid for eid, _ in f_user.get_entry_ids()}
            self.assertIn(self.e4_unapproved.id, user_ids)

        with set_current_request(None):
            f_anon = TagSearchFilter()
            f_anon.init_from_get_params(QueryDict("tags=spren"))
            anon_ids = {eid for eid, _ in f_anon.get_entry_ids()}
            self.assertNotIn(self.e4_unapproved.id, anon_ids)

    def test_antitag_search_filter(self):
        f = AntiTagSearchFilter()
        f.init_from_get_params(QueryDict("antitag=spren"))
        ids = {eid for eid, _ in f.get_entry_ids()}
        self.assertIn(self.e1.id, ids)
        self.assertNotIn(self.e2.id, ids)
        self.assertNotIn(self.e3_unsearchable.id, ids)

    def test_pipeline_init_execute_visibility_ordering_and_pagination(self):
        req = self.factory.get("/adv_search/?query=roshar&tags=cosmere")
        filters = init_filters(req)
        self.assertEqual(len(filters), 5)
        scores = execute_filters(filters)
        self.assertEqual(set(scores.keys()), {self.e2.id})

        # Short-circuit when one active filter returns no matches
        req_empty = self.factory.get("/adv_search/?query=nonexistenttermxyz&tags=cosmere")
        self.assertEqual(execute_filters(init_filters(req_empty)), {})

        # Visibility filtering & ordering in get_search_results
        with set_current_request(None):
            res_anon = get_search_results(
                {self.e1.id: 5.0, self.e2.id: 10.0, self.e4_unapproved.id: 20.0},
                ordering="rank",
            )
            self.assertEqual([eid for eid, _ in res_anon], [self.e2.id, self.e1.id])

        with set_current_request(self.user):
            res_desc = get_search_results(
                {self.e1.id: 1.0, self.e2.id: 1.0, self.e4_unapproved.id: 1.0},
                ordering="-date",
            )
            self.assertEqual([eid for eid, _ in res_desc], [self.e4_unapproved.id, self.e2.id, self.e1.id])

            res_asc = get_search_results(
                {self.e1.id: 1.0, self.e2.id: 1.0, self.e4_unapproved.id: 1.0},
                ordering="+date",
            )
            self.assertEqual([eid for eid, _ in res_asc], [self.e1.id, self.e2.id, self.e4_unapproved.id])

        # Pagination: create 15 extra entries to test page 1, page 2, bad page, empty page, orphans
        many_scores = {}
        for idx in range(15):
            e = EntryFactory(event=self.event, is_approved=True)
            v = EntryVersionFactory(entry=e, is_approved=True)
            EntryLineFactory(entry_version=v, text=f"Item {idx}")
            many_scores[e.id] = float(idx)

        ordered = get_search_results(many_scores, ordering="rank")

        def make_req(qs):
            r = self.factory.get(f"/adv_search/?{qs}")
            r.user = self.user
            r.session = {"page_length": 10}
            return r

        # With page_length=10 and orphans=1, 15 items = 2 pages (10 + 5)
        entries_p1, paginator, page1 = paginate_search_results(make_req("page=1"), ordered)
        self.assertEqual(paginator.num_pages, 2)
        self.assertEqual(len(entries_p1), 10)
        self.assertEqual(page1.number, 1)

        entries_p2, _, page2 = paginate_search_results(make_req("page=2"), ordered)
        self.assertEqual(len(entries_p2), 5)
        self.assertEqual(page2.number, 2)

        _, _, page_bad = paginate_search_results(make_req("page=notanint"), ordered)
        self.assertEqual(page_bad.number, 1)

        _, _, page_oob = paginate_search_results(make_req("page=999"), ordered)
        self.assertEqual(page_oob.number, 2)

    @unittest.expectedFailure
    def test_get_search_results_date_ordering_entry_without_version(self):
        """
        Bug in palanaeum/search.py:403-408 — get_search_results looks up
        `entry_dates[entry[0]]` from EntryVersion.newest without handling entries
        that have no EntryVersion (such as empty entries returned by AntiTagSearchFilter),
        raising KeyError.
        """
        empty_entry = EntryFactory(event=self.event, is_visible=True, is_approved=True)
        with set_current_request(self.staff):
            f = AntiTagSearchFilter()
            f.init_from_get_params(QueryDict("antitag=cosmere"))
            scores = execute_filters([f])
            self.assertIn(empty_entry.id, scores)
            results = get_search_results(scores, ordering="-date")
            self.assertIn(empty_entry.id, [eid for eid, _ in results])


class TextSearchSyntaxErrorTransactionTests(TransactionTestCase):
    def test_invalid_tsquery_syntax_returns_empty_frozenset(self):
        # Running invalid SQL to_tsquery('&') aborts the current transaction in Postgres;
        # TransactionTestCase avoids breaking subsequent queries in a shared TestCase atomic block.
        f_bad = TextSearchFilter()
        f_bad.init_from_get_params(QueryDict("query=%26"))
        self.assertEqual(f_bad.get_entry_ids(), frozenset())
