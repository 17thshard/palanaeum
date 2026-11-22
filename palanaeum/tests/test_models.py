import os
import subprocess
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.postgres.search import SearchQuery
from django.core.cache import caches
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from palanaeum.models import (
    AudioSource,
    Entry,
    EntryLine,
    EntrySearchVector,
    EntryVersion,
    Event,
    FAQEntry,
    HelpPage,
    ImageSource,
    NavbarItem,
    RelatedSite,
    Snippet,
    Tag,
    URLSource,
    UserSettings,
    UsersEntryCollection,
)
from palanaeum.tests.base import (
    make_LocMem_caches_setting,
    make_uploaded_image,
    set_current_request,
)
from palanaeum.tests.factories import (
    AudioSourceFactory,
    EntryFactory,
    EntryLineFactory,
    EntryVersionFactory,
    EventFactory,
    FAQEntryFactory,
    HelpPageFactory,
    ImageSourceFactory,
    LinkFactory,
    NavbarItemFactory,
    RelatedSiteFactory,
    SnippetFactory,
    StaffUserFactory,
    TagFactory,
    URLSourceFactory,
    UserFactory,
    UserSettingsFactory,
    UsersEntryCollectionFactory,
)


class UserSettingsModelTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_page_length_session_auth_anon_and_missing(self):
        # 1. Session hit takes precedence without DB lookup
        req = self.factory.get("/")
        req.session = {"page_length": "33"}
        req.user = UserFactory()
        with self.assertNumQueries(0):
            self.assertEqual(UserSettings.get_page_length(req), 33)

        # 2. Authenticated user loads from DB and populates session
        user = UserFactory()
        UserSettingsFactory(user=user, page_length=45)
        req_auth = self.factory.get("/")
        req_auth.session = {}
        req_auth.user = user
        self.assertEqual(UserSettings.get_page_length(req_auth), 45)
        self.assertEqual(req_auth.session["page_length"], 45)

        # 3. Anonymous user reads default_page_length config and caches in session
        from django.contrib.auth.models import AnonymousUser

        req_anon = self.factory.get("/")
        req_anon.session = {}
        req_anon.user = AnonymousUser()
        self.assertEqual(UserSettings.get_page_length(req_anon), 20)
        self.assertEqual(req_anon.session["page_length"], 20)

        # 4. Authenticated user without UserSettings raises DoesNotExist
        user_no_settings = UserFactory()
        req_missing = self.factory.get("/")
        req_missing.session = {}
        req_missing.user = user_no_settings
        with self.assertRaises(UserSettings.DoesNotExist):
            UserSettings.get_page_length(req_missing)


class VisibleManagersAndContentTests(TestCase):
    def setUp(self):
        self.creator = UserFactory(username="creator")
        self.other_user = UserFactory(username="other")
        self.staff = StaffUserFactory(username="staff")
        self.event = EventFactory()

        # Entry uses VisibleManager (approved_only=False)
        self.e_vis_app = EntryFactory(event=self.event, created_by=self.creator, is_visible=True, is_approved=True)
        self.e_vis_unapp = EntryFactory(event=self.event, created_by=self.creator, is_visible=True, is_approved=False)
        self.e_hid_app = EntryFactory(event=self.event, created_by=self.creator, is_visible=False, is_approved=True)
        self.e_hid_unapp = EntryFactory(event=self.event, created_by=self.creator, is_visible=False, is_approved=False)

        # AudioSource uses ApprovedVisibleManager (approved_only=True)
        self.a_vis_app = AudioSourceFactory(event=self.event, created_by=self.creator, is_visible=True, is_approved=True)
        self.a_vis_unapp = AudioSourceFactory(event=self.event, created_by=self.creator, is_visible=True, is_approved=False)
        self.a_hid_app = AudioSourceFactory(event=self.event, created_by=self.creator, is_visible=False, is_approved=True)
        self.a_hid_unapp = AudioSourceFactory(event=self.event, created_by=self.creator, is_visible=False, is_approved=False)

        # ImageSource also uses ApprovedVisibleManager
        self.i_vis_app = ImageSourceFactory(event=self.event, created_by=self.creator, is_visible=True, is_approved=True)
        self.i_vis_unapp = ImageSourceFactory(event=self.event, created_by=self.creator, is_visible=True, is_approved=False)
        self.i_hid_app = ImageSourceFactory(event=self.event, created_by=self.creator, is_visible=False, is_approved=True)
        self.i_hid_unapp = ImageSourceFactory(event=self.event, created_by=self.creator, is_visible=False, is_approved=False)

    def test_visible_manager_matrix(self):
        # No request -> AnonymousUser
        self.assertEqual(set(Entry.all_visible.all()), {self.e_vis_app})
        with set_current_request(None):
            self.assertEqual(set(Entry.all_visible.all()), {self.e_vis_app})
        with set_current_request(self.other_user):
            self.assertEqual(set(Entry.all_visible.all()), {self.e_vis_app, self.e_vis_unapp})
        with set_current_request(self.creator):
            self.assertEqual(set(Entry.all_visible.all()), {self.e_vis_app, self.e_vis_unapp})
        with set_current_request(self.staff):
            self.assertEqual(
                set(Entry.all_visible.all()),
                {self.e_vis_app, self.e_vis_unapp, self.e_hid_app, self.e_hid_unapp},
            )

    def test_approved_visible_manager_matrix(self):
        for model, items in (
            (AudioSource, (self.a_vis_app, self.a_vis_unapp, self.a_hid_app, self.a_hid_unapp)),
            (ImageSource, (self.i_vis_app, self.i_vis_unapp, self.i_hid_app, self.i_hid_unapp)),
        ):
            vis_app, vis_unapp, hid_app, hid_unapp = items
            with set_current_request(None):
                self.assertEqual(set(model.all_visible.all()), {vis_app})
            with set_current_request(self.other_user):
                self.assertEqual(set(model.all_visible.all()), {vis_app})
            with set_current_request(self.creator):
                self.assertEqual(set(model.all_visible.all()), {vis_app, vis_unapp})
            with set_current_request(self.staff):
                self.assertEqual(set(model.all_visible.all()), {vis_app, vis_unapp, hid_app, hid_unapp})

    def test_content_hide_show_visible_approve_check_access_and_save(self):
        self.e_vis_app.hide()
        self.e_vis_app.refresh_from_db()
        self.assertFalse(self.e_vis_app.is_visible)
        self.e_vis_app.show()
        self.e_vis_app.refresh_from_db()
        self.assertTrue(self.e_vis_app.is_visible)

        # visible() without request
        self.assertTrue(self.e_vis_app.visible())
        self.assertFalse(self.e_vis_unapp.visible())
        with set_current_request(self.creator):
            self.assertTrue(self.e_vis_unapp.visible())
            self.assertFalse(self.e_hid_app.visible())

        # approve() requires staff
        with set_current_request(self.creator):
            with self.assertRaises(PermissionDenied):
                self.e_vis_unapp.approve()
        with set_current_request(self.staff):
            self.e_vis_unapp.approve()
            self.assertTrue(self.e_vis_unapp.is_approved)
            self.assertEqual(self.e_vis_unapp.approved_by, self.staff)
            self.assertIsNotNone(self.e_vis_unapp.approved_date)

        # check_access()
        unapproved = EntryFactory(event=self.event, created_by=self.creator, is_approved=False)
        unapproved.check_access(self.staff)
        unapproved.check_access(self.creator)
        with self.assertRaises(PermissionDenied):
            unapproved.check_access(self.other_user)
        with self.assertRaises(PermissionDenied):
            self.e_vis_app.check_access(self.creator)

        # save() sets modified_by from request user
        with set_current_request(self.other_user):
            self.e_vis_app.save()
        self.assertEqual(self.e_vis_app.modified_by, self.other_user)

    @unittest.expectedFailure
    def test_content_visible_for_hidden_unapproved_entry_respects_is_visible(self):
        """
        Bug in palanaeum/models.py:137-147 — Content.visible_for checks
        `if not self.is_approved: return self.created_by == user` before
        checking `self.is_visible`, returning True for hidden items created by `user`.
        """
        self.assertFalse(self.e_hid_unapp.visible_for(self.creator))

    def test_created_by_html_variants(self):
        no_author = EntryFactory(event=self.event, created_by=None)
        self.assertEqual(no_author.created_by_html(), "")

        UserSettingsFactory(user=self.creator, website="")
        self.assertEqual(
            self.e_vis_app.created_by_html(),
            "<span class='username'>creator</span>",
        )

        self.creator.settings.website = "https://example.org"
        self.creator.settings.save()
        self.assertEqual(
            self.e_vis_app.created_by_html(),
            "<span class='username'><a href='https://example.org'>creator</a></span>",
        )

    @unittest.expectedFailure
    def test_created_by_html_missing_user_settings_fallback(self):
        """
        Bug in palanaeum/models.py:184 — Content.created_by_html calls
        UserSettings.objects.get(user=author) unconditionally, raising
        UserSettings.DoesNotExist if the author has no UserSettings row.
        """
        self.assertEqual(
            self.e_vis_app.created_by_html(),
            "<span class='username'>creator</span>",
        )


@override_settings(CACHES=make_LocMem_caches_setting("tag-tests"))
class TagAndTaggableTests(TestCase):
    def setUp(self):
        self.staff = StaffUserFactory()
        self.user = UserFactory()

    def tearDown(self):
        caches["default"].clear()
        super().tearDown()

    def test_tag_save_normalization_truncation_and_empty_deletion(self):
        # save() slices [:NAME_LENGTH] before stripping HTML tags
        tag = Tag.objects.create(name="  <b>Cosmere</b> " + ("x" * 70))
        self.assertEqual(tag.name, "cosmere " + ("x" * 49))
        self.assertTrue(bool(tag))
        self.assertEqual(str(tag), tag.name)

        long_plain = Tag.objects.create(name="y" * 80)
        self.assertEqual(len(long_plain.name), Tag.NAME_LENGTH)
        long_plain.delete()

        # Updating saved tag to blank deletes it
        tag.name = "   "
        tag.save()
        self.assertFalse(Tag.objects.filter(pk=tag.pk).exists())

        # Empty unsaved tag stays unsaved
        empty_tag = Tag(name="   ")
        empty_tag.save()
        self.assertIsNone(empty_tag.pk)
        self.assertFalse(bool(empty_tag))

    def test_get_tag_sanitization_and_permissions(self):
        self.assertIsNone(Tag.get_tag(""))
        existing = TagFactory(name="stormlight archive")

        with set_current_request(self.user):
            found = Tag.get_tag("  Stormlight!!   Archive  ")
            self.assertEqual(found, existing)
            with self.assertRaises(PermissionDenied):
                Tag.get_tag("brand new tag")

        with set_current_request(self.staff):
            created = Tag.get_tag("<b>Brand</b>   New-Tag_1's??")
            self.assertEqual(created.name, "bbrandb new-tag_1's")

    def test_tag_counts_links_clean_unused_and_cached_usage_stats(self):
        tag = TagFactory(name="hoid")
        single_tag = TagFactory(name="jasnah")
        unused = TagFactory(name="unused-tag")
        event = EventFactory()
        event.tags.add(tag, single_tag)

        entry = EntryFactory(event=event)
        v1 = EntryVersionFactory(entry=entry)
        v2 = EntryVersionFactory(entry=entry)
        v1.tags.add(tag, single_tag)
        v2.tags.add(tag)

        # Distinct entry count (1 entry across 2 versions) + 1 event = 2
        self.assertEqual(tag.entries_count, 1)
        self.assertEqual(tag.events_count, 1)
        self.assertIn("tags=hoid", tag.as_link())
        self.assertIn("#hoid</a>", tag.as_link())
        self.assertEqual(
            single_tag.as_selected_option(),
            "<option value='jasnah' selected='selected'>jasnah (2)</option>",
        )

        # Cached usage stats (no cross-join inflation on single-version tag)
        caches["default"].clear()
        self.assertEqual(single_tag.get_usage_count(), 2)
        with self.assertNumQueries(0):
            self.assertEqual(single_tag.get_usage_count(), 2)

        Tag.clean_unused()
        self.assertTrue(Tag.objects.filter(pk=tag.pk).exists())
        self.assertFalse(Tag.objects.filter(pk=unused.pk).exists())

    @unittest.expectedFailure
    def test_tag_get_usage_count_with_multiple_entry_versions_on_same_entry(self):
        """
        Bug in palanaeum/models.py:272-274 — Tag.get_usage_count annotates
        `Count('events')` without `distinct=True` alongside `Count('versions__entry_id', distinct=True)`,
        multiplying `events_count` by the number of matching EntryVersions.
        """
        tag = TagFactory(name="hoid-multi")
        event = EventFactory()
        event.tags.add(tag)
        entry = EntryFactory(event=event)
        EntryVersionFactory(entry=entry).tags.add(tag)
        EntryVersionFactory(entry=entry).tags.add(tag)
        caches["default"].clear()
        self.assertEqual(tag.get_usage_count(), 2)

    def test_taggable_methods(self):
        event = EventFactory()
        unsaved_event = Event(name="Unsaved")
        self.assertEqual(unsaved_event.tags_to_edit_string(), "")

        with set_current_request(self.staff):
            event.add_tag("alpha")
            event.add_tag("alpha")  # idempotent
            event.add_tag("beta")
            self.assertEqual(event.tags_to_edit_string(), "alpha, beta")

            event.remove_tag("alpha")
            self.assertEqual(event.tags_to_edit_string(), "beta")
            self.assertFalse(Tag.objects.filter(name="alpha").exists())

            event.update_tags("gamma, delta")
            self.assertEqual(event.tags_to_edit_string(), "delta, gamma")
            self.assertFalse(Tag.objects.filter(name="beta").exists())

    @unittest.expectedFailure
    def test_taggable_remove_tag_noop_does_not_create_orphan_tag(self):
        """
        Bug in palanaeum/models.py:319-328 — Taggable.remove_tag calls
        Tag.get_tag(tag) before checking membership, which creates a brand new
        unused Tag row when called by staff for a non-attached tag name.
        """
        event = EventFactory()
        with set_current_request(self.staff):
            event.remove_tag("nonexistent-orphan")
        self.assertFalse(Tag.objects.filter(name="nonexistent-orphan").exists())


class EventModelTests(TestCase):
    def setUp(self):
        self.staff = StaffUserFactory()
        self.user = UserFactory()
        self.e_old = EventFactory(name="Alpha", date=date(2020, 1, 1))
        self.e_mid_1 = EventFactory(name="Beta", date=date(2021, 5, 1))
        self.e_mid_2 = EventFactory(name="Gamma", date=date(2021, 5, 1))
        self.e_new = EventFactory(name="Omega", date=date(2022, 1, 1))
        self.e_hidden = EventFactory(name="Hidden", date=date(2021, 6, 1), is_visible=False)

    def test_str_eq_hash_url_and_editable(self):
        self.assertEqual(str(self.e_old), "Alpha")
        self.assertEqual(self.e_old, self.e_old)
        self.assertNotEqual(self.e_old, self.e_new)
        self.assertNotEqual(self.e_old, "Alpha")
        self.assertEqual(hash(self.e_old), hash(f"event_{self.e_old.id}"))
        self.assertEqual(self.e_old.get_absolute_url(), f"/events/{self.e_old.id}-alpha/")

        self.assertFalse(self.e_old.editable())
        with set_current_request(self.user):
            self.assertFalse(self.e_old.editable())
        with set_current_request(self.staff):
            self.assertTrue(self.e_old.editable())

    def test_lt_newer_and_equal_dates(self):
        self.assertTrue(self.e_new < self.e_old)
        self.assertTrue(self.e_mid_1 < self.e_mid_2)
        self.assertFalse(self.e_mid_2 < self.e_mid_1)

    @unittest.expectedFailure
    def test_lt_older_date_returns_false(self):
        """
        Bug in palanaeum/models.py:369-374 — Event.__lt__ falls through to
        `return self.name < other.name` even when `self.date < other.date`,
        making `e_old < e_new` and `e_new < e_old` both True.
        """
        self.assertFalse(self.e_old < self.e_new)

    @unittest.expectedFailure
    def test_lt_handles_none_date(self):
        """
        Bug in palanaeum/models.py:372 — Event.__lt__ compares `self.date > other.date`
        directly without handling nullable `date=None`, raising TypeError.
        """
        e_none = EventFactory(name="Undated", date=None)
        _ = e_none < self.e_old

    def test_prev_and_next_urls_including_same_date_tiebreak_and_visibility(self):
        self.assertIsNone(self.e_old.get_prev_url())
        self.assertEqual(self.e_old.get_next_url(), self.e_mid_1.get_absolute_url())
        self.assertEqual(self.e_mid_1.get_next_url(), self.e_mid_2.get_absolute_url())
        self.assertEqual(self.e_mid_2.get_prev_url(), self.e_mid_1.get_absolute_url())
        # Hidden event skipped for anonymous
        self.assertEqual(self.e_mid_2.get_next_url(), self.e_new.get_absolute_url())
        self.assertIsNone(self.e_new.get_next_url())

        with set_current_request(self.staff):
            self.assertEqual(self.e_mid_2.get_next_url(), self.e_hidden.get_absolute_url())

    def test_sources_speakers_and_entries_count(self):
        audio = AudioSourceFactory(event=self.e_old, is_approved=True)
        AudioSourceFactory(event=self.e_old, is_approved=False)
        img = ImageSourceFactory(event=self.e_old, is_approved=True)
        entry = EntryFactory(event=self.e_old, is_visible=True, is_approved=True)
        EntryFactory(event=self.e_old, is_visible=False)
        v1 = EntryVersionFactory(entry=entry, is_approved=True)
        url_src = URLSourceFactory()
        v1.url_sources.add(url_src)

        EntryLineFactory(entry_version=v1, speaker="Brandon", text="A")
        EntryLineFactory(entry_version=v1, speaker="Brandon", text="B")
        EntryLineFactory(entry_version=v1, speaker="Fan", text="Q")

        self.assertEqual(list(self.e_old.sources_iterator()), [audio, img, url_src])
        self.assertEqual(list(self.e_old.all_url_sources()), [url_src])
        self.assertEqual(list(self.e_old.all_speakers()), ["Brandon", "Fan"])
        self.assertEqual(self.e_old.entries_count(), 1)


class EntrySearchVectorVersionLineTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.staff = StaffUserFactory()
        self.event = EventFactory(date=date(2023, 3, 15))

    def test_entry_unsaved_and_empty_defaults(self):
        unsaved = Entry(event=self.event)
        self.assertEqual(unsaved.lines, [])
        self.assertEqual(unsaved.note, "")
        self.assertEqual(unsaved.date, "")
        self.assertEqual(unsaved.paraphrased, "")
        self.assertFalse(unsaved.direct_entry)
        self.assertEqual(unsaved.reported_by, "")
        self.assertEqual(list(unsaved.tags), [])
        self.assertTrue(unsaved.is_suggestion)
        self.assertEqual(str(unsaved), "-- empty entry --")
        self.assertEqual(repr(unsaved), "<EmptyEntry>")

        saved_empty = EntryFactory(event=self.event)
        self.assertIsNone(saved_empty.last_version)
        self.assertEqual(saved_empty.get_absolute_url(), f"/entry/{saved_empty.id}/")
        self.assertEqual(repr(saved_empty), f"<Entry:{saved_empty.id}>")
        self.assertEqual(saved_empty.order, 0)
        second = Entry(event=self.event)
        second.set_order_last()
        self.assertEqual(second.order, 1)

    @unittest.expectedFailure
    def test_unsaved_entry_last_version_returns_none(self):
        """
        Bug in palanaeum/models.py:454-457 — Entry.last_version accesses
        `self.versions.last()` without guarding `if self.id is None:`, raising
        ValueError on unsaved Entry instances.
        """
        unsaved = Entry(event=self.event)
        self.assertIsNone(unsaved.last_version)

    def test_entry_direct_entry_and_editable(self):
        entry = EntryFactory(event=self.event)
        ver = EntryVersionFactory(
            entry=entry,
            direct_entry=True,
            reported_by="ShardMember",
            paraphrased=True,
            note="<i>Footnote</i>",
            is_approved=True,
        )
        EntryLineFactory(entry_version=ver, speaker="Brandon", text="<p>Words</p>")
        self.assertTrue(entry.direct_entry)
        self.assertFalse(entry.is_suggestion)
        self.assertEqual(entry.reported_by, "ShardMember")
        self.assertTrue(entry.paraphrased)
        self.assertIn("Brandon:", str(entry))

        # Attaching any source invalidates direct_entry
        url_src = URLSourceFactory()
        ver.url_sources.add(url_src)
        self.assertFalse(entry.direct_entry)
        ver.url_sources.clear()
        self.assertTrue(entry.direct_entry)

        img = ImageSourceFactory(event=self.event, entry=entry)
        self.assertFalse(entry.direct_entry)
        img.entry = None
        img.save()
        self.assertTrue(entry.direct_entry)

        SnippetFactory(entry=entry)
        self.assertFalse(entry.direct_entry)

        self.assertFalse(entry.editable())
        with set_current_request(self.user):
            self.assertTrue(entry.editable())

    def test_prefetch_entries_approved_vs_unapproved(self):
        entry = EntryFactory(event=self.event, is_approved=True)
        t0 = timezone.now() - timedelta(minutes=5)
        v_app = EntryVersionFactory(entry=entry, is_approved=True, date=t0, note="Approved note")
        EntryLineFactory(entry_version=v_app, order=1, speaker="S1", text="Second")
        EntryLineFactory(entry_version=v_app, order=0, speaker="S0", text="First")
        url_src = URLSourceFactory()
        v_app.url_sources.add(url_src)

        v_unapp = EntryVersionFactory(entry=entry, is_approved=False, date=timezone.now(), note="Draft note")
        EntryLineFactory(entry_version=v_unapp, order=0, speaker="S2", text="Draft")

        pref_approved = Entry.prefetch_entries([entry.id], show_unapproved=False)
        e_app = pref_approved[entry.id]
        self.assertTrue(e_app.prefetched)
        self.assertEqual(e_app.prefetched_last_version, v_app)
        with self.assertNumQueries(0):
            self.assertEqual(e_app.note, "Approved note")
            self.assertEqual([l.text for l in e_app.lines], ["First", "Second"])
            self.assertEqual(e_app.all_url_sources(), [url_src])

        pref_unapp = Entry.prefetch_entries([entry.id], show_unapproved=True)
        e_unapp = pref_unapp[entry.id]
        self.assertEqual(e_unapp.prefetched_last_version, v_unapp)
        self.assertEqual(e_unapp.note, "Draft note")
        self.assertEqual([l.text for l in e_unapp.lines], ["Draft"])

    def test_newest_entry_version_manager_and_version_lifecycle(self):
        vis_entry = EntryFactory(event=self.event, is_visible=True, is_approved=True)
        hid_entry = EntryFactory(event=self.event, is_visible=False, is_approved=True)
        t_old = timezone.now() - timedelta(minutes=10)
        t_new = timezone.now() - timedelta(minutes=1)

        v_old = EntryVersionFactory(entry=vis_entry, is_approved=True, date=t_old, note="<script>x</script><b>Note</b>")
        self.assertEqual(v_old.note, "<b>Note</b>")
        line = EntryLineFactory(entry_version=v_old, speaker="<b>Brandon</b><script>evil()</script>", text="<p>Hi</p><script>bad()</script>")
        self.assertEqual(line.speaker, "<b>Brandon</b>")
        self.assertEqual(line.text, "<p>Hi</p>")
        self.assertEqual(line.entry, vis_entry)
        self.assertEqual(line.entry_id, vis_entry.id)

        tag = TagFactory(name="cosmere")
        url_src = URLSourceFactory()
        v_old.tags.add(tag)
        v_old.url_sources.add(url_src)

        # archive_version copies lines, tags, url_sources and updates date on self
        archived = v_old.archive_version()
        v_old.save()
        self.assertNotEqual(archived.pk, v_old.pk)
        self.assertEqual(list(archived.tags.all()), [tag])
        self.assertEqual(list(archived.url_sources.all()), [url_src])
        self.assertEqual(archived.lines.count(), 1)
        self.assertFalse(archived.is_newest)
        self.assertTrue(v_old.is_newest)

        # Unsaved / empty version archive_version is a no-op
        unsaved_v = EntryVersion(entry=vis_entry)
        self.assertIs(unsaved_v.archive_version(), unsaved_v)

        # Newer unapproved version + hidden entry visibility in EntryVersion.newest
        v_unapp = EntryVersionFactory(entry=vis_entry, is_approved=False, date=timezone.now())
        v_hid = EntryVersionFactory(entry=hid_entry, is_approved=True, date=t_new)

        with set_current_request(None):
            self.assertEqual(set(EntryVersion.newest.all()), {v_old})
        with set_current_request(self.user):
            self.assertEqual(set(EntryVersion.newest.all()), {v_unapp})
        with set_current_request(self.staff):
            self.assertEqual(set(EntryVersion.newest.all()), {v_unapp, v_hid})

        # Reject deletes unapproved versions
        v_unapp.reject()
        self.assertFalse(EntryVersion.objects.filter(pk=v_unapp.pk).exists())
        self.assertTrue(EntryVersion.objects.filter(pk=v_old.pk).exists())

        # Approve updates Entry, EntryVersion, and EntrySearchVector
        new_entry = EntryFactory(event=self.event, is_approved=False)
        v_pending = EntryVersionFactory(entry=new_entry, is_approved=False)
        EntryLineFactory(entry_version=v_pending, speaker="Kelsier", text="Survive!")
        v_pending.approve(self.staff)
        v_pending.refresh_from_db()
        new_entry.refresh_from_db()
        self.assertTrue(v_pending.is_approved)
        self.assertEqual(v_pending.approved_by, self.staff)
        self.assertTrue(new_entry.is_approved)
        self.assertTrue(
            EntrySearchVector.objects.filter(
                entry=new_entry,
                text_vector=SearchQuery("survive", config="english"),
                speaker_vector=SearchQuery("kelsier", config="english"),
            ).exists()
        )

    def test_entry_search_vector_update_weights(self):
        tag_entry = TagFactory(name="allomancy")
        tag_event = TagFactory(name="dragonsteel")
        self.event.tags.add(tag_event)

        entry = EntryFactory(event=self.event)
        ver = EntryVersionFactory(entry=entry, note="<p>Secret footnote</p>")
        ver.tags.add(tag_entry)
        EntryLineFactory(entry_version=ver, speaker="Hoid", text="Investiture is key")

        esv = EntrySearchVector(entry=entry)
        esv.update()

        for term in ("allomancy", "dragonsteel", "footnote", "investiture", "hoid"):
            self.assertTrue(
                EntrySearchVector.objects.filter(
                    pk=esv.pk, text_vector=SearchQuery(term, config="english")
                ).exists(),
                f"Expected text_vector to match {term!r}",
            )
        self.assertTrue(
            EntrySearchVector.objects.filter(
                pk=esv.pk, speaker_vector=SearchQuery("hoid", config="english")
            ).exists()
        )

    def test_entry_search_vector_update_empty_entry_no_lines(self):
        entry = EntryFactory(event=self.event)
        EntryVersionFactory(entry=entry, note="Footnote without lines")
        esv = EntrySearchVector(entry=entry)
        esv.update()
        self.assertIsNotNone(esv.pk)
        self.assertTrue(
            EntrySearchVector.objects.filter(
                pk=esv.pk, text_vector=SearchQuery("footnote", config="english")
            ).exists()
        )
        self.assertFalse(
            EntrySearchVector.objects.filter(
                pk=esv.pk, speaker_vector=SearchQuery("hoid", config="english")
            ).exists()
        )

    def test_entry_line_str_truncation(self):
        long_line = EntryLineFactory(speaker="Sp", text="x" * 60)
        self.assertEqual(str(long_line), f"Sp: {'x' * 47}...")


class SourceCollectionAndMiscModelTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.staff = StaffUserFactory()
        self.event = EventFactory()

    def test_users_entry_collection_cleans_description(self):
        coll = UsersEntryCollectionFactory(
            user=self.user,
            description="<p>Allowed?</p><b>Keep</b><script>alert(1)</script>",
        )
        self.assertEqual(coll.description, "Allowed?<b>Keep</b>")

    def test_image_source_upload_collision_and_delete(self):
        img = ImageSource(event=self.event, name="Photo")
        img.save_uploaded_file(make_uploaded_image(name="photo.png"))
        img.save()
        first_path = Path(img.file.path)
        self.assertTrue(first_path.is_file())
        self.assertEqual(img.get_url(), img.file.url)
        self.assertEqual(img.title, "Photo")
        self.assertIn("Photo", str(img))

        # Same filename does not overwrite first file
        img2 = ImageSource(event=self.event, name="Photo 2")
        img2.save_uploaded_file(make_uploaded_image(name="photo.png"))
        img2.save()
        self.assertNotEqual(img2.file.name, img.file.name)
        self.assertTrue(Path(img2.file.path).is_file())

        img.delete()
        self.assertFalse(first_path.exists())
        img2.delete()

    def test_url_source_get_or_create_clean_and_remove_unused(self):
        u1 = URLSource.get_or_create("https://example.com/1", "<b>Label</b><script>x</script>")
        self.assertEqual(u1.text, "Label")
        self.assertEqual(u1.get_url(), "https://example.com/1")
        self.assertEqual(u1.title, "Label")
        self.assertIn("Label", str(u1))
        self.assertIn("target='_blank'", u1.html())

        # Existing URL returns same object
        u1_again = URLSource.get_or_create("https://example.com/1", "Other")
        self.assertEqual(u1_again.pk, u1.pk)

        ver = EntryVersionFactory(entry__event=self.event)
        u_used = URLSourceFactory(text="")
        self.assertEqual(u_used.title, u_used.url)
        ver.url_sources.add(u_used)

        URLSource.remove_unused()
        self.assertFalse(URLSource.objects.filter(pk=u1.pk).exists())
        self.assertTrue(URLSource.objects.filter(pk=u_used.pk).exists())

    def test_audio_source_properties_reset_length_editable_and_delete(self):
        raw_path = Path(settings.MEDIA_ROOT) / "sources" / "raw.wav"
        trans_path = Path(settings.MEDIA_ROOT) / "sources" / "trans.mp3"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(b"raw")
        trans_path.write_bytes(b"mp3")

        with mock.patch("palanaeum.models.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["ffprobe"], returncode=0, stdout=b"123.7\n"
            )
            audio = AudioSource(
                event=self.event,
                raw_file="sources/raw.wav",
                transcoded_file="sources/trans.mp3",
                length=0,
                status=AudioSource.PROCESSING,
                file_title="Rec",
            )
            audio.save()

        mock_run.assert_called_once()
        self.assertEqual(audio.length, 123)
        self.assertTrue(audio.in_preparation())
        self.assertEqual(audio.file, audio.transcoded_file)
        self.assertEqual(audio.get_url(), audio.transcoded_file.url)
        self.assertEqual(audio.title, "Rec")
        self.assertIn("Rec", str(audio))

        audio.status = AudioSource.READY
        audio.save()
        self.assertFalse(audio.in_preparation())

        # Empty file -> get_url() returns False
        empty_audio = AudioSourceFactory(event=self.event, raw_file="", transcoded_file="")
        self.assertFalse(empty_audio.get_url())

        # snippets_count respects visibility
        snip_vis = SnippetFactory(source=audio, is_visible=True, is_approved=True)
        SnippetFactory(source=audio, is_visible=False, is_approved=True)
        self.assertEqual(audio.snippets_count(), 1)

        with set_current_request(None):
            self.assertFalse(audio.editable())
        with set_current_request(self.user):
            self.assertTrue(audio.editable())

        # delete() unlinks files and deletes child snippets
        snip_file = Path(settings.MEDIA_ROOT) / "snippets" / "s.mp3"
        snip_file.parent.mkdir(parents=True, exist_ok=True)
        snip_file.write_bytes(b"snip")
        snip_vis.file = str(snip_file)
        snip_vis.save()

        audio.delete()
        self.assertFalse(raw_path.exists())
        self.assertFalse(trans_path.exists())
        self.assertFalse(snip_file.exists())
        self.assertFalse(Snippet.objects.filter(source_id=audio.pk).exists())

    @unittest.expectedFailure
    def test_audio_source_editable_without_request_returns_false(self):
        """
        Bug in palanaeum/models.py:986-988 — AudioSource.editable calls
        `request.user.is_authenticated` without checking `if request is None`,
        raising AttributeError outside an HTTP request.
        """
        audio = AudioSourceFactory(event=self.event)
        self.assertFalse(audio.editable())

    def test_snippet_methods_and_delete(self):
        audio = AudioSourceFactory(event=self.event, length=200)
        snip = SnippetFactory(
            source=audio,
            beginning=65,
            length=15,
            created_by=self.user,
            file="media/snippets/1/65_15.mp3",
        )
        self.assertEqual(snip.ending, 80)
        self.assertEqual(snip.get_ending(), 80)
        snip.ending = 95
        self.assertEqual(snip.length, 30)
        with self.assertRaises(ValueError):
            snip.ending = 65

        self.assertEqual(snip.start_time(), "01:05")
        snip.beginning = 3661
        self.assertEqual(snip.start_time(), "01:01:01")
        snip.beginning = 50
        self.assertAlmostEqual(snip.position_percent, 25.0)
        self.assertEqual(snip.get_file_url(), "/media/snippets/1/65_15.mp3")

        with set_current_request(self.user):
            self.assertTrue(snip.editable())
        with set_current_request(UserFactory()):
            self.assertFalse(snip.editable())
        with set_current_request(self.staff):
            self.assertTrue(snip.editable())

        with mock.patch("palanaeum.tasks.create_snippet.delay") as mock_delay:
            snip.update_file()
            mock_delay.assert_called_once_with(snip.id)
            mock_delay.reset_mock()
            snip.muted = True
            snip.update_file()
            mock_delay.assert_not_called()

        snip.file = ""
        self.assertFalse(snip.get_file_url())
        snip.delete()  # tolerates FileNotFoundError

    def test_related_site_help_faq_link_and_navbar(self):
        site = RelatedSiteFactory(name="Coppermind", url="https://coppermind.net/")
        img_path = Path(site.image.path)
        self.assertTrue(img_path.is_file())
        self.assertEqual(repr(site), "Coppermind (https://coppermind.net/)")
        self.assertIn("https://coppermind.net/", site.render())
        site.delete()
        self.assertFalse(img_path.exists())

        h1 = HelpPageFactory(path="about", title="About 1")
        h2 = HelpPageFactory(path="about", title="About 2")
        self.assertEqual(list(HelpPage.objects.filter(path="about")), [h2, h1])

        f2 = FAQEntryFactory(ordering=2)
        f1 = FAQEntryFactory(ordering=1, new_version=f2)
        self.assertEqual(list(FAQEntry.objects.all()), [f1, f2])
        self.assertEqual(list(f2.prev_versions.all()), [f1])

        link = LinkFactory()
        nav = NavbarItemFactory(single_link=False, url="")
        nav.links.add(link)
        self.assertEqual(list(nav.links.all()), [link])
