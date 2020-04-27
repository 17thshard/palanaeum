import os
import pathlib
import re
import subprocess
import time
from collections import defaultdict
from datetime import date
from functools import total_ordering
from urllib.parse import urlencode

import bleach
import django.contrib.postgres.search as pg_search
import pytz
from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.db.models import Max, Count, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.cache import caches
from django.utils.html import strip_tags, escape
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from palanaeum.configuration import get_config
from palanaeum.middleware import get_request
from palanaeum.utils import is_contributor


def get_default_page_length():
    return get_config(('default_page_length'))


class UserSettings(models.Model):
    """
    Objects of this class contain settings for different users, like their e-mail preferences, timezone etc.
    """
    class Meta:
        verbose_name = _('user_settings')
        verbose_name_plural = _('user_settings')

    user = models.OneToOneField(User, related_name='settings', on_delete=models.CASCADE)
    timezone = models.CharField(max_length=32,
                                choices=zip(pytz.common_timezones,
                                            map(lambda tz: tz.replace('_', ' '), pytz.common_timezones)),
                                default='UTC')
    page_length = models.IntegerField(default=get_default_page_length,
                                      verbose_name=_("Preferred page length"))
    website = models.URLField(verbose_name=_('Your website'), blank=True)

    @staticmethod
    def get_page_length(request):
        """
        Returns a preferred page length from session, database or default config.
        """
        session_page_length = request.session.get('page_length', None)
        if session_page_length is not None:
            return int(session_page_length)

        if request.user.is_authenticated:
            db_page_length = UserSettings.objects.get(user=request.user).page_length
        else:
            db_page_length = get_config('default_page_length')
        request.session['page_length'] = db_page_length
        return db_page_length


class VisibleManager(models.Manager):
    def generate_queryset(self, approved_only):
        request = get_request()
        if not (request and hasattr(request, 'user')):
            user = AnonymousUser()
        else:
            user = request.user

        queryset = super(VisibleManager, self).get_queryset()

        if user.is_staff:
            return queryset

        queryset = queryset.filter(is_visible=True)

        if user.is_anonymous:
            queryset = queryset.filter(is_approved=True)
        elif approved_only:
            queryset = queryset.filter(Q(is_approved=True) | Q(created_by=user))

        return queryset

    def get_queryset(self):
        return self.generate_queryset(approved_only=False)


class ApprovedVisibleManager(VisibleManager):
    def get_queryset(self):
        return self.generate_queryset(approved_only=True)


def get_current_user():
    return getattr(get_request(), 'user', None)


class Content(models.Model):
    """
    Subclasses of this class can be hidden from regular users and may require
    approval before being visible.
    """
    class Meta:
        abstract = True

    is_visible = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   default=get_current_user(), related_name='+')
    created_date = models.DateTimeField(null=True, auto_now_add=True)
    is_approved = models.BooleanField(default=True, db_index=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='+')
    approved_date = models.DateTimeField(null=True)
    modified_date = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    objects = models.Manager()
    all_visible = VisibleManager()

    def hide(self):
        self.is_visible = False

    def show(self):
        self.is_visible = True

    def visible_for(self, user: User) -> bool:
        if user.is_staff:
            return True

        if self.is_visible and self.is_approved:
            return True

        if not self.is_approved:
            return self.created_by == user

        return False

    def visible(self) -> bool:
        request = get_request()
        if hasattr(request, 'user'):
            return self.visible_for(request.user)
        else:
            return self.is_visible and self.is_approved

    def approve(self):
        request = get_request()
        if not request.user.is_staff:
            raise PermissionDenied()
        self.is_approved = True
        self.approved_date = timezone.now()
        self.approved_by = request.user
        self.save()

    def check_access(self, user):
        """
        Raises PermissionDenied exception if user isn't allow to edit this
        object.
        """
        if user.is_staff:
            return
        if (not self.is_approved) and user == self.created_by:
            return
        raise PermissionDenied()

    @mark_safe
    def created_by_html(self):
        """
        Print author of this object in HTML.
        """
        author = self.created_by
        if author is None:
            return ""
        author_settings = UserSettings.objects.get(user=author)

        if author_settings.website:
            return "<span class='username'><a href='{}'>{}</a></span>".format(author_settings.website, author.username)
        return "<span class='username'>{}</span>".format(author.username)

    def save(self, *args, **kwargs):
        self.modified_date = timezone.now()
        request = get_request()
        if request and hasattr(request, 'user') and isinstance(request.user, User):
            self.modified_by = request.user
        super(Content, self).save(*args, **kwargs)


class Tag(models.Model):
    """
    A single tag consists of a series of letters, without any space between them.
    Tags are case insensitive.
    """
    class Meta:
        ordering = ['name']
        verbose_name = _('tag')
        verbose_name_plural = _('tags')

    NAME_LENGTH = 64
    name = models.CharField(max_length=NAME_LENGTH, db_index=True, unique=True, blank=False)

    def __str__(self):
        return self.name

    def __bool__(self):
        return bool(self.name)

    @property
    def entries_count(self):
        return self.versions.count('entry_id', distinct=True)

    @property
    def events_count(self):
        return self.events.count()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.name = self.name.strip()[:self.NAME_LENGTH].lower()
        if self.name:
            self.name = bleach.clean(self.name, tags=[], strip=True)
            super().save(force_insert, force_update, using, update_fields)
        else:
            if self.pk:
                self.delete()

    def as_link(self):
        from palanaeum.search import TagSearchFilter
        url = reverse('advanced_search') + '?' + urlencode({
            TagSearchFilter.GET_TAG_SEARCH: self.name
        })
        return "<a href='{}'>#{}</a>".format(url, self.name)

    def as_selected_option(self):
        return "<option value='{0}' selected='selected'>{0} ({1})</option>".format(escape(self.name), self.get_usage_count())

    TAG_SANITIZER = re.compile(r"[^A-Za-z0-9'\-_\s]")

    @staticmethod
    def get_tag(name: str):
        if not name:
            return None
        name = name.strip().lower()
        name = Tag.TAG_SANITIZER.sub("", name)
        name = " ".join(name.split())
        name = name[:Tag.NAME_LENGTH]
        try:
            return Tag.objects.get(name__iexact=name)
        except Tag.DoesNotExist:
            return Tag.objects.create(name=name)

    @staticmethod
    def clean_unused():
        return Tag.objects.filter(events=None).filter(versions=None).delete()

    def get_usage_count(self):
        cache = caches['default']
        cached_stats = cache.get('tag_usage_stats')
        if cached_stats and self.pk in cached_stats:
            return cached_stats[self.pk]
        stats = Tag.objects.annotate(events_count=Count('events'), entries_count=Count('versions__entry_id', distinct=True))\
            .values_list('id', 'events_count', 'entries_count')
        stats = {s[0]: s[1] + s[2] for s in stats}
        cache.set('tag_usage_stats', stats)
        return stats.get(self.id, 0)


class Taggable(models.Model):
    class Meta:
        abstract = True

    tags = models.ManyToManyField(Tag)

    def tags_to_edit_string(self):
        """
        Transform objects tags into a single string containing the tags separated with a single space.
        """
        if not self.pk:
            return ""
        tags = self.tags.all()
        return ", ".join(tag.name for tag in tags)

    def update_tags(self, tags):
        """
        Update the list of associated tags.
        The tags argument can be a list of comma separated tags.
        """
        if isinstance(tags, str):
            tags = tags.split(',')
        tags = set(map(Tag.get_tag, tags))
        self.tags.clear()
        for tag in filter(lambda t: t, tags):
            self.tags.add(tag)
        self.save()
        Tag.clean_unused()

    def add_tag(self, tag):
        """
        Add a tag to the set. If the tag is already there, do nothing.
        """
        tag_obj = Tag.get_tag(tag)
        if self.tags.filter(pk=tag_obj.id).exists():
            return
        self.tags.add(tag_obj)
        self.save()
        Tag.clean_unused()

    def remove_tag(self, tag):
        """
        Remove a tag from the set. If the tag is not part of the set, do nothing.
        """
        tag_obj = Tag.get_tag(tag)
        if not self.tags.filter(pk=tag_obj.id).exists():
            return
        self.tags.remove(tag_obj)
        self.save()
        Tag.clean_unused()


@total_ordering
class Event(Taggable, Content):
    """
    A subclass of PublicEntryCollection that represents real-world events.
    It stores information about such events like place, date etc.
    """
    REVIEW_NA = 'N/A'
    REVIEW_PENDING = 'PENDING'
    REVIEW_APPROVED = 'APPROVED'
    REVIEW_STATES = (
        ('N/A', _('not applicable')),
        ('PENDING', _('pending')),
        ('APPROVED', _('approved'))
    )

    class Meta:
        default_related_name = 'events'
        verbose_name = _('event')
        verbose_name_plural = _('events')
        ordering = ('-date', 'name')

    name = models.CharField(max_length=256)
    location = models.CharField(max_length=500, blank=True)
    date = models.DateField(blank=True, null=True)

    tour = models.CharField(max_length=500, blank=True)
    bookstore = models.CharField(max_length=500, blank=True)
    meta = models.TextField(blank=True)
    review_state = models.CharField(max_length=8, choices=REVIEW_STATES, default=REVIEW_NA)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if type(other) != type(self):
            return NotImplemented
        return self.id == other.id

    def __lt__(self, other):
        if type(other) != type(self):
            return NotImplemented
        if self.date > other.date:
            return True
        return self.name < other.name

    def __hash__(self):
        return hash("event_" + str(self.id))

    def get_absolute_url(self):
        return reverse('view_event', args=(self.id, slugify(self.name)))

    def get_next_url(self):
        next_event = Event.all_visible.filter(date__lte=self.date)\
            .exclude(pk=self.pk).values_list("id", "name").first()

        if next_event:
            return reverse('view_event', args=(next_event[0], slugify(next_event[1])))

    def get_prev_url(self):
        prev_event = Event.all_visible.filter(date__gte=self.date)\
            .exclude(pk=self.pk).values_list("id", "name").last()

        if prev_event:
            return reverse('view_event', args=(prev_event[0], slugify(prev_event[1])))

    def sources_iterator(self):
        yield from AudioSource.all_visible.filter(event=self)
        yield from ImageSource.all_visible.filter(event=self)
        yield from URLSource.all_visible.filter(entry_versions__entry__event=self).distinct()

    def all_url_sources(self):
        yield from URLSource.all_visible.filter(entry_versions__entry__event=self).distinct()

    def all_speakers(self):
        lines = EntryLine.objects.filter(entry_version__entry__event=self)
        speakers = defaultdict(int)
        for line in lines:
            speakers[line.speaker] += 1
        speakers = [(count, speaker) for speaker, count in speakers.items()]
        speakers.sort(reverse=True)
        yield from (speaker[1] for speaker in speakers)

    def editable(self):
        request = get_request()
        if hasattr(request, 'user') and request.user.is_staff:
            return True
        return False

    def entries_count(self):
        return Entry.all_visible.filter(event=self).count()


class Entry(TimeStampedModel, Content):
    """
    A single Entry represents more or less one question and one answer given by fan and answered by author.
    """
    class Meta:
        default_related_name = 'entries'
        ordering = ('order',)
        verbose_name = _('entry')
        verbose_name_plural = _('entries')

    CONTENT_TYPE = 'entry'
    order = models.PositiveIntegerField(default=0)
    event = models.ForeignKey(Event, null=True, related_name='entries',
                              on_delete=models.PROTECT)

    def __init__(self, *args, **kwargs):
        super(Entry, self).__init__(*args, **kwargs)
        self.prefetched_lines = []
        self.prefetched_url_sources = []
        self.prefetched = False
        self.prefetched_last_version = None

    def get_absolute_url(self):
        return reverse('view_entry', args=(self.id,))

    @property
    def last_version(self):
        if self.prefetched and self.prefetched_last_version is not None:
            return self.prefetched_last_version
        return self.versions.last()

    def _get_opt_version_value(self, value_name):
        if self.prefetched and self.prefetched_last_version is not None:
            return getattr(self.prefetched_last_version, value_name)
        version = self.versions.last()
        if version is None:
            return ''
        return getattr(version, value_name)

    def all_url_sources(self):
        if self.prefetched and self.prefetched_url_sources:
            return self.prefetched_url_sources
        return (self._get_opt_version_value('url_sources') or URLSource.objects.none()).distinct()

    @property
    def is_suggestion(self):
        return not self._get_opt_version_value('is_approved')

    @property
    def lines(self):
        if self.prefetched and self.prefetched_lines:
            return self.prefetched_lines
        return EntryLine.objects.filter(entry_version=self.versions.last())

    @property
    def note(self):
        return self._get_opt_version_value('note')

    @property
    def date(self):
        return self._get_opt_version_value('entry_date')

    @property
    def paraphrased(self):
        return self._get_opt_version_value('paraphrased')

    @property
    def direct_entry(self):
        # FIXME: This is ugly, I know but I have to make it work for now
        is_direct = str(self._get_opt_version_value('direct_entry')) == 'True'
        is_direct &= not Snippet.objects.filter(entry=self).exists()
        is_direct &= not ImageSource.objects.filter(entry=self).exists()
        is_direct &= not URLSource.objects.filter(entry_versions__entry=self).exists()
        return is_direct

    @property
    def reported_by(self):
        return self._get_opt_version_value('reported_by')

    @property
    def tags(self):
        return self._get_opt_version_value('tags') or Tag.objects.none()

    def __str__(self):
        lines = self.lines
        if not self.lines:
            return '-- empty entry --'
        if type(lines) is list:
            first_line = self.lines[0]
        else:
            first_line = self.lines.first()
        return str(first_line)

    def editable(self):
        return is_contributor(get_request())

    def set_order_last(self):
        if Entry.objects.filter(event=self.event).exists():
            self.order = Entry.objects.filter(event=self.event).aggregate(Max('order'))[
                'order__max'] + 1
        else:
            self.order = 0

    @staticmethod
    def prefetch_entries(entries_ids, show_unapproved=False) -> dict:
        """
        Loads a bunch of Entries in a possibly fastest way, putting data in prefetched fileds.
        Returns a map: entry_id -> entry
        """
        entries = Entry.all_visible.filter(id__in=entries_ids).prefetch_related('event', 'snippets', 'versions',
                                                                                'image_sources')

        # Get newest versions
        version_map = {}
        entry_version_map = {}
        entries_map = {e.id: e for e in entries}

        for entry in entries_map.values():
            entry.prefetched = True

        if show_unapproved:
            versions = EntryVersion.objects.filter(entry__in=entries)
        else:
            versions = EntryVersion.objects.filter(entry__in=entries, is_approved=True)

        for version in versions.order_by('-date', 'id'):
            if version.entry_id in entry_version_map:
                continue
            version_map[version.id] = version.entry_id
            entry_version_map[version.entry_id] = version.id
            entries_map[version.entry_id].prefetched_last_version = version

        # Get lines
        for line in EntryLine.objects.filter(entry_version__in=version_map.keys()).order_by('order'):
            entries_map[version_map[line.entry_version_id]].prefetched_lines.append(line)

        # Get URL sources
        for source in URLSource.all_visible.filter(entry_versions__id__in=version_map.keys()).distinct():
            for version in source.entry_versions.only('id'):
                if version.id in version_map:
                    entries_map[version_map[version.id]].prefetched_url_sources.append(source)

        return entries_map


class EntrySearchVector(models.Model):
    """
    A special class storing search vector for looking up entries.
    """
    entry = models.OneToOneField(Entry, on_delete=models.CASCADE)
    text_vector = pg_search.SearchVectorField()
    speaker_vector = pg_search.SearchVectorField()

    class Meta:
        indexes = [GinIndex(fields=['text_vector']), GinIndex(fields=['speaker_vector'])]

    def update(self):
        lines = self.entry.lines.all()
        text_vector = pg_search.SearchVector(models.Value(strip_tags(self.entry.note), output_field=models.TextField()),
                                             weight='C', config='english')

        for tag in self.entry.tags.all():
            text_vector += pg_search.SearchVector(models.Value(tag.name, output_field=models.TextField()), weight='A',
                                                  config='english')

        for tag in self.entry.event.tags.all():
            text_vector += pg_search.SearchVector(models.Value(tag.name, output_field=models.TextField()), weight='C',
                                                  config='english')

        if lines.exists():
            speaker_vectors = []

            for line in lines:
                text_vector += pg_search.SearchVector(
                    models.Value(strip_tags(line.text), output_field=models.TextField()),
                    weight='B', config='english')
                speaker_vectors.append(pg_search.SearchVector(
                    models.Value(strip_tags(line.speaker), output_field=models.TextField()),
                    weight='A', config='english'))
                text_vector += pg_search.SearchVector(
                    models.Value(strip_tags(line.speaker), output_field=models.TextField()),
                    weight='D', config='english')

            speaker_vector = speaker_vectors[0]
            for sv in speaker_vectors[1:]:
                speaker_vector += sv

            self.speaker_vector = speaker_vector

        self.text_vector = text_vector
        self.save()


class NewestEntryVersionManager(models.Manager):
    def get_queryset(self):
        request = get_request()
        if not (request and hasattr(request, 'user')):
            user = AnonymousUser()
        else:
            user = request.user
        queryset = super(NewestEntryVersionManager, self).get_queryset()
        if not user.is_staff:
            if user.is_authenticated:
                queryset = queryset.filter(entry__is_visible=True)
            else:
                queryset = queryset.filter(entry__is_visible=True, is_approved=True)
        return queryset.order_by('entry_id', '-date', 'id').distinct('entry_id')


class EntryVersion(Taggable):
    """
    This is one of the version an Entry can have. Versions are collections of EntryLines and represent history of
    changes made on given Entry.
    """

    class Meta:
        ordering = ('date', '-id')
        default_related_name = 'versions'
        verbose_name = _('entry version')
        verbose_name_plural = _('entries versions')

    entry = models.ForeignKey(Entry, related_name='versions', on_delete=models.CASCADE)
    entry_date = models.DateField(default=date.today, db_index=True, help_text="The date when the entry happened")
    date = models.DateTimeField(default=timezone.now, db_index=True, help_text="When this version was created.")
    note = models.TextField(blank=True, verbose_name=_('footnote'))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    is_approved = models.BooleanField(default=False, db_index=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    approved_date = models.DateTimeField(null=True)
    paraphrased = models.BooleanField(default=False)
    direct_entry = models.BooleanField(default=False)
    reported_by = models.CharField(max_length=64, blank=True, default='')

    objects = models.Manager()
    newest = NewestEntryVersionManager()

    def save(self, *args, **kwargs):
        if self.pk is None and self.date is None:
            self.date = timezone.now()
        self.note = bleach.clean(self.note, strip=True, strip_comments=True)
        super().save(*args, **kwargs)

    def archive_version(self):
        """
        This function saves a copy of the current version as a separate object
        in the database, leaving this instance free for modifications.
        """
        if not self.lines.exists():
            # No need to archive empty versions
            return self

        archived_version = EntryVersion()
        archived_version.entry = self.entry
        archived_version.date = self.date
        archived_version.note = self.note
        archived_version.user = self.user
        archived_version.is_approved = self.is_approved
        archived_version.approved_by = self.approved_by
        archived_version.approved_date = self.approved_date
        archived_version.entry_date = self.entry_date
        archived_version.paraphrased = self.paraphrased
        archived_version.direct_entry = self.direct_entry
        archived_version.reported_by = self.reported_by
        self.date = timezone.now()
        archived_version.save()

        for url in self.url_sources.all():
            archived_version.url_sources.add(url)

        for tag in self.tags.all():
            archived_version.tags.add(tag)

        lines = []
        for line in self.lines.all():
            nl = EntryLine()
            nl.entry_version = archived_version
            nl.order = line.order
            nl.speaker = line.speaker
            nl.text = line.text
            lines.append(nl)

        EntryLine.objects.bulk_create(lines)
        return archived_version

    @property
    def is_newest(self):
        return not EntryVersion.objects.filter(entry=self.entry, date__gt=self.date).exists()

    def approve(self, approve_by: User):
        EntryVersion.objects.filter(entry=self.entry, is_approved=False, date__lte=self.date).update(
            is_approved=True, approved_by=approve_by, approved_date=timezone.now()
        )
        esv = EntrySearchVector.objects.get_or_create(entry=self.entry)[0]
        esv.update()

        if not self.entry.is_approved:
            self.entry.is_approved = True
            self.entry.approved_by = approve_by
            self.entry.approved_date = timezone.now()
            self.entry.save()

    def reject(self):
        EntryVersion.objects.filter(entry=self.entry, is_approved=False).delete()


class EntryLine(models.Model):
    class Meta:
        ordering = ('entry_version', 'order')
        verbose_name = _('line')
        verbose_name_plural = _('lines')

    entry_version = models.ForeignKey(EntryVersion, db_index=True, related_name='lines', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    speaker = models.CharField(max_length=512, db_index=True)
    text = models.TextField()

    def __str__(self):
        text = strip_tags(self.text)
        if len(text) > 50:
            text = text[:47] + '...'
        return "{}: {}".format(self.speaker, text)

    def save(self, *args, **kwargs):
        self.text = bleach.clean(self.text, strip=True, strip_comments=True,
                                 tags=bleach.ALLOWED_TAGS + ['p'])
        self.speaker = bleach.clean(self.speaker, strip=True, strip_comments=True)
        super(EntryLine, self).save(*args, **kwargs)

    @property
    def entry(self):
        return self.entry_version.entry

    @property
    def entry_id(self):
        return self.entry_version.entry_id


class UsersEntryCollection(TimeStampedModel):
    """
    Users are allowed to create and manage their private collections. They may share them with others, too!
    """
    MAX_NAME_LENGTH = 250

    class Meta:
        verbose_name = _('user_entry_collection')
        verbose_name_plural = _('user_entry_collections')
        ordering = ('name',)

    user = models.ForeignKey(User, related_name='collections', on_delete=models.CASCADE)
    name = models.CharField(max_length=MAX_NAME_LENGTH)
    description = models.TextField(default='', blank=True)
    public = models.BooleanField(default=False)
    entries = models.ManyToManyField(Entry, related_name='collections')

    def save(self, **kwargs):
        self.description = bleach.clean(self.description, strip=True, strip_comments=True)
        super().save(**kwargs)


class Source:
    """
    Common base class for different sources.
    """

    def in_preparation(self):
        """
        If true, it means that the source is processed by the system in some way and is not ready to be worked on yet.
        """
        return False

    def get_url(self):
        raise NotImplementedError

    @property
    def title(self):
        return ''


class ImageSource(Content, Source):
    """
    An image that is a source for an entry.
    """
    class Meta:
        verbose_name = _('image_source')
        verbose_name_plural = _('image_sources')
        ordering = ('event', 'name', 'pk')

    all_visible = ApprovedVisibleManager()

    CONTENT_TYPE = 'image'
    event = models.ForeignKey(Event, related_name='image_sources', on_delete=models.PROTECT)
    entry = models.ForeignKey(Entry, null=True, related_name='image_sources', on_delete=models.SET_NULL)
    file = models.ImageField(max_length=200)
    name = models.CharField(max_length=250)

    def __str__(self):
        return "<ImageSource({}/{}): {} ({})>".format(self.event_id, self.id, str(self.file), self.name)

    def get_url(self):
        return self.file.url

    @property
    def title(self):
        return self.name

    def save_uploaded_file(self, uploaded_file: UploadedFile):
        save_path = pathlib.Path(settings.MEDIA_ROOT, 'sources', str(self.event_id), uploaded_file.name)
        if save_path.exists():
            save_path = save_path.with_name("{}_{}{}".format(save_path.name, time.time(), save_path.suffix))

        save_path.parent.mkdir(parents=True, exist_ok=True, mode=0o775)
        with open(str(save_path), mode='wb') as save_file:
            for chunk in uploaded_file.chunks():
                save_file.write(chunk)

        self.file = str(save_path.relative_to(settings.MEDIA_ROOT))
        return

    def delete(self, using=None, keep_parents=False):
        os.unlink(self.file.path)
        super(ImageSource, self).delete(using, keep_parents)


class URLSource(Content, Source):
    """
    Outside resource pointed by URL.
    """
    class Meta:
        verbose_name = _('url_source')
        verbose_name_plural = _('url_sources')

    CONTENT_TYPE = 'url'
    entry_versions = models.ManyToManyField(EntryVersion, related_name='url_sources')
    url = models.URLField(unique=True)
    text = models.CharField(max_length=160, blank=True)

    def __str__(self):
        return "<URLSource: {}>".format(self.text or self.url)

    def html(self):
        return "<a href='{}' target='_blank'><span>{}</span></a>".format(self.url, self.text or self.url)

    def save(self, *args, **kwargs):
        self.text = bleach.clean(self.text, tags=[], strip=True)
        super(URLSource, self).save(*args, **kwargs)

    def get_url(self):
        return self.url

    @property
    def title(self):
        return self.text or self.url

    @classmethod
    def get_or_create(cls, url: str, text: str):
        try:
            return cls.objects.get(url=url)
        except cls.DoesNotExist:
            new_obj = cls()
            new_obj.text = text
            new_obj.url = url
            new_obj.save()
            return new_obj

    @classmethod
    def remove_unused(cls):
        cls.objects.filter(entry_versions=None).delete()


class AudioSource(Source, Content):
    """
    Specialized class for audio source files.
    """

    class Meta:
        verbose_name = _('audio_source')
        verbose_name_plural = _('audio_sources')

    all_visible = ApprovedVisibleManager()

    WAITING = 0
    PROCESSING = 1
    READY = 2
    FAILED = 3
    STORED_IN_CLOUD = 4

    STATUSES = (
        (WAITING, _('waiting')),
        (PROCESSING, _('processing')),
        (READY, _('ready')),
        (FAILED, _('failed')),
        (STORED_IN_CLOUD, _('stored_in_cloud')),
    )

    CONTENT_TYPE = 'audio'
    raw_file = models.FileField(null=True, max_length=200)
    transcoded_file = models.FileField(null=True, max_length=200)
    event = models.ForeignKey(Event, related_name='audio_sources', on_delete=models.PROTECT)
    length = models.PositiveIntegerField(verbose_name=_('file_length'))  # In seconds
    original_filename = models.CharField(max_length=100, blank=True)
    file_title = models.CharField(max_length=500, default='Default title')
    status = models.SmallIntegerField(choices=STATUSES, default=WAITING)
    cloud_status = JSONField(default=dict)

    def __str__(self):
        return "<Audio source {}: {}>".format(self.pk, self.title)

    def in_preparation(self):
        return self.status in (self.WAITING, self.PROCESSING)

    @property
    def title(self):
        return self.file_title

    @property
    def file(self):
        if self.transcoded_file:
            return self.transcoded_file
        return self.raw_file

    def get_url(self):
        if not self.file:
            return False
        return self.file.url

    def snippets_count(self) -> int:
        return Snippet.all_visible.filter(source=self).count()

    def reset_length(self):
        if self.file:
            proc = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                   "default=noprint_wrappers=1:nokey=1", str(self.file.path)], stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, check=True)
            self.length = int(float(proc.stdout.decode()))

    def save(self, *args, **kwargs):
        if self.file and self.length == 0:
            self.reset_length()
        super(AudioSource, self).save(*args, **kwargs)

    def editable(self):
        request = get_request()
        return request.user.is_authenticated

    def delete(self, using=None, keep_parents=False):
        if self.transcoded_file:
            try:
                os.unlink(self.transcoded_file.path)
                self.transcoded_file = None
            except FileNotFoundError:
                pass
        if self.raw_file:
            try:
                os.unlink(self.raw_file.path)
                self.raw_file = None
            except FileNotFoundError:
                pass
        for snippet in self.snippets.all():
            snippet.delete()
        super().delete(using=using, keep_parents=keep_parents)


def get_snippet_path():
    return os.path.join(settings.MEDIA_ROOT, 'snippets')


class Snippet(Content):
    """
    A snippet is a small piece of an audio recording. Usually containing one question and an answer for this question.
    Snippets are created from AudioSources uploaded by fans.
    """
    class Meta:
        ordering = ('source', 'beginning')
        verbose_name = _('snippet')
        verbose_name_plural = _('snippets')

    source = models.ForeignKey(AudioSource, related_name='snippets', on_delete=models.CASCADE, db_index=True)
    beginning = models.PositiveIntegerField(default=0)  # In seconds
    length = models.PositiveIntegerField(default=0)  # In seconds
    file = models.FilePathField(path=get_snippet_path, recursive=True, match='*.mp3',
                                blank=True, null=True)
    entry = models.ForeignKey(Entry, related_name='snippets', null=True, blank=True, on_delete=models.SET_NULL)
    comment = models.CharField(max_length=500, blank=True)
    muted = models.BooleanField(default=False, help_text=_("Is given part of the audio muted?"))
    optional = models.BooleanField(default=False, help_text=_("This snippet shouldn't be transcribed."))

    def __str__(self):
        return "<Snippet({}/{}): {}-{}>".format(self.source_id, self.id, self.beginning, self.ending)

    def get_ending(self):
        return self.ending

    @property
    def ending(self):
        return int(self.beginning) + self.length

    @ending.setter
    def ending(self, value):
        new_length = int(value) - int(self.beginning)
        if new_length <= 0:
            raise ValueError("Snippet ending cannot be before beginning.")
        self.length = new_length

    def delete(self, *args, **kwargs):
        try:
            os.unlink(str(self.file))
        except FileNotFoundError:
            pass
        super(Snippet, self).delete(*args, **kwargs)

    def editable(self):
        request = get_request()
        if request.user.is_staff or request.user == self.created_by:
            return True
        return False

    @property
    def position_percent(self):
        return self.beginning / self.source.length * 100

    def start_time(self) -> str:
        """
        Returns starting time formatted like this: 00:00:00.
        """
        seconds = int(self.beginning) % 60
        minutes = (int(self.beginning) // 60) % 60
        hours = int(self.beginning) // 60 // 60

        if hours:
            return "{:0>#2d}:{:0>#2d}:{:0>#2d}".format(hours, minutes, seconds)
        else:
            return "{:0>#2d}:{:0>#2d}".format(minutes, seconds)

    def update_file(self):
        from palanaeum import tasks
        if not self.muted:
            tasks.create_snippet.delay(self.id)

    def get_file_url(self):
        if not self.file:
            return False
        return '/' + self.file.replace('\\', '/')


class ConfigEntry(models.Model):
    """
    Stores configuration entries.
    Each key can be associated with serialized value.
    """
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField()


class RelatedSite(models.Model):
    """
    This models represents link to other sites that are showed on the index page.
    """
    class Meta:
        ordering = ('order', 'name')
        verbose_name = _('related site')
        verbose_name_plural = _('related sites')

    name = models.CharField(max_length=128, verbose_name=_('Site name'))
    url = models.URLField(verbose_name=_('Site URL address'))
    image = models.ImageField(verbose_name=_('Site logo'), help_text=_('Site logo should be 34x34 pixels big.'),
                              upload_to='related_sites')
    order = models.IntegerField(default=0)

    def __repr__(self):
        return "{} ({})".format(self.name, self.url)

    def delete(self, *args, **kwargs):
        try:
            os.unlink(self.image.path)
        except FileNotFoundError:
            pass
        super().delete(*args, **kwargs)

    def render(self):
        return mark_safe(
            '<a href="{url}" class="related-site"><img src="{image_url}" class="tinyPhoto"/> {name}</a>'.format(
                url=self.url, image_url=self.image.url, name=self.name
            ))
