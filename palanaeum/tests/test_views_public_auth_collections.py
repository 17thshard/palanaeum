import json
import re
import unittest
from datetime import date, timedelta
from xml.etree import ElementTree

from django.contrib import messages
from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import caches
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from palanaeum.models import (
    Entry,
    EntrySearchVector,
    UserSettings,
    UsersEntryCollection,
)
from palanaeum.tests.base import make_LocMem_caches_setting
from palanaeum.tests.factories import (
    AudioSourceFactory,
    EntryFactory,
    EntryLineFactory,
    EntryVersionFactory,
    EventFactory,
    HelpPageFactory,
    ImageSourceFactory,
    RelatedSiteFactory,
    SnippetFactory,
    StaffUserFactory,
    SuperUserFactory,
    TagFactory,
    URLSourceFactory,
    UserFactory,
    UserSettingsFactory,
    UsersEntryCollectionFactory,
)


class IndexHelpAndEventViewsTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username="reader")
        UserSettingsFactory(user=self.user, page_length=15)
        self.staff = StaffUserFactory(username="staff")
        UserSettingsFactory(user=self.staff)

    def tearDown(self):
        caches["default"].clear()
        super().tearDown()

    def test_index_stats_new_sources_and_related_sites(self):
        event_empty = EventFactory(name="Empty Event")
        event_pop = EventFactory(name="Populated Event")
        EntryFactory(event=event_pop, is_visible=True, is_approved=True)
        site = RelatedSiteFactory(name="17th Shard", url="https://www.17thshard.com/")

        # Create 6 sources across audio & image; index shows latest 5
        sources = []
        for idx in range(3):
            a = AudioSourceFactory(event=event_pop, file_title=f"AudioSrc-{idx}", is_approved=True)
            im = ImageSourceFactory(event=event_pop, name=f"ImageSrc-{idx}", is_approved=True)
            sources.extend([a, im])
        # Unapproved source excluded for anon
        AudioSourceFactory(event=event_pop, file_title="UnapprovedAudio", is_approved=False)

        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        self.assertIn("Populated Event", body)
        self.assertNotIn("Empty Event", body)
        self.assertIn("17th Shard", body)
        self.assertNotIn("UnapprovedAudio", body)
        # Oldest of 6 sources dropped from top 5
        self.assertNotIn("AudioSrc-0", body)
        self.assertIn("ImageSrc-2", body)
        site.delete()

    def test_about_redirect_and_help_pages(self):
        resp_about = self.client.get("/about/")
        self.assertEqual(resp_about.status_code, 301)
        self.assertEqual(resp_about["Location"], "/help/about")

        self.assertEqual(self.client.get("/help/missing").status_code, 404)

        HelpPageFactory(path="about", title="About v1", text="<p>Old text</p>")
        HelpPageFactory(path="about", title="About v2", text="<p>Latest text</p>")
        resp_help = self.client.get("/help/about")
        self.assertEqual(resp_help.status_code, 200)
        self.assertIn("About v2", resp_help.content.decode())
        self.assertIn("Latest text", resp_help.content.decode())

    def test_view_event_visibility_and_anonymous_cache_hit(self):
        event = EventFactory(name="Skyward Launch")
        entry = EntryFactory(event=event, is_approved=True)
        v_app = EntryVersionFactory(
            entry=entry, is_approved=True, date=timezone.now() - timedelta(minutes=5)
        )
        EntryLineFactory(entry_version=v_app, text="Approved answer")
        v_unapp = EntryVersionFactory(
            entry=entry, is_approved=False, date=timezone.now()
        )
        EntryLineFactory(entry_version=v_unapp, text="Pending suggestion")

        url = f"/events/{event.id}-{slugify(event.name)}/"
        anon_body = self.client.get(url).content.decode()
        self.assertIn("Approved answer", anon_body)
        self.assertNotIn("Pending suggestion", anon_body)

        self.client.force_login(self.user)
        user_body = self.client.get(url).content.decode()
        self.assertIn("Pending suggestion", user_body)
        self.assertNotIn("Approved answer", user_body)
        self.client.logout()

        # Hidden event -> 403 for anon/user, 200 for staff
        event.is_visible = False
        event.save()
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 200)

    @unittest.expectedFailure
    @override_settings(CACHES=make_LocMem_caches_setting("view-event-cache"))
    def test_view_event_anonymous_cache_invalidates_after_event_update(self):
        """
        Bug in palanaeum/views.py:163 — view_event checks
        `if cache_timestamp <= event.modified_date:` (inverted comparison),
        causing stale cached anonymous HTML to be returned forever once cached.
        """
        caches["default"].clear()
        event = EventFactory(name="Cached Event", review_state="APPROVED")
        EntryFactory(event=event, is_approved=True)
        url = f"/events/{event.id}-{slugify(event.name)}/"

        resp1 = self.client.get(url)
        self.assertEqual(resp1.status_code, 200)
        self.assertIn("This event has been reviewed", resp1.content.decode())

        event.review_state = "PENDING"
        event.save()
        resp2 = self.client.get(url)
        self.assertIn("This event is waiting for review", resp2.content.decode())


class RecentSearchTagsAndTodoViewsTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username="searcher")
        UserSettingsFactory(user=self.user, page_length=10)
        self.event = EventFactory(name="Q&A Event", date=date(2023, 8, 1))
        self.tag_magic = TagFactory(name="magic systems")
        self.tag_world = TagFactory(name="roshar")
        self.event.tags.add(self.tag_world)

        self.entries = []
        for idx in range(12):
            e = EntryFactory(event=self.event, is_approved=True)
            v = EntryVersionFactory(
                entry=e,
                entry_date=date(2023, 1, idx + 1),
                is_approved=True,
            )
            v.tags.add(self.tag_magic)
            EntryLineFactory(entry_version=v, speaker="Brandon", text=f"Stormlight lore item {idx}")
            esv = EntrySearchVector(entry=e)
            esv.update()
            self.entries.append(e)

    def test_recent_entries_modes_and_pagination(self):
        for mode in ("created", "modified", "recorded", "unknown"):
            resp = self.client.get("/recent/", {"mode": mode})
            self.assertEqual(resp.status_code, 200)

        self.assertEqual(self.client.get("/recent/", {"page": "bad"}).context["page"].number, 1)
        self.assertEqual(self.client.get("/recent/", {"page": "99"}).context["page"].number, 1)
        self.assertEqual(len(self.client.get("/recent/", {"page": "1"}).context["entries"]), 12)

        # Authenticated user with fresh session (page_length=10) paginates to 2 pages
        auth_client = self.client_class()
        auth_client.force_login(self.user)
        p2 = auth_client.get("/recent/", {"page": "2"})
        self.assertEqual(p2.context["page"].number, 2)
        self.assertEqual(len(p2.context["entries"]), 2)

    def test_adv_search_view_results_ordering_pagination_and_404_empty(self):
        # No query params -> 404
        resp_empty = self.client.get("/adv_search/")
        self.assertEqual(resp_empty.status_code, 404)

        # Non-matching query -> 404
        resp_miss = self.client.get("/adv_search/", {"query": "zyxwvutsrq"})
        self.assertEqual(resp_miss.status_code, 404)

        # Matching query -> 200 with ordering & pagination
        for ordering in ("rank", "-date", "+date"):
            resp = self.client.get("/adv_search/", {"query": "stormlight", "ordering": ordering})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.context["entries_found"], 12)

    def test_get_tags_json_and_tags_list(self):
        resp_all = self.client.get("/get_tags/", {"q": ""})
        self.assertEqual(resp_all.status_code, 200)
        data_all = json.loads(resp_all.content)
        self.assertTrue(data_all["success"])
        names = [item["id"] for item in data_all["results"]]
        self.assertIn("magic systems", names)
        self.assertIn("roshar", names)

        # Substring after space matches (' systems')
        resp_space = self.client.get("/get_tags/", {"q": "sys"})
        names_space = [item["id"] for item in json.loads(resp_space.content)["results"]]
        self.assertEqual(names_space, ["magic systems"])

        resp_list = self.client.get("/tags/")
        self.assertEqual(resp_list.status_code, 200)
        self.assertIn("magic systems", resp_list.content.decode())
        self.assertIn("roshar", resp_list.content.decode())

    def test_untranscribed_snippets_todo_view(self):
        src_vis = AudioSourceFactory(event=self.event, file_title="VisibleRecording", is_approved=True)
        src_unapp = AudioSourceFactory(event=self.event, file_title="UnapprovedRecording", is_approved=False)
        hidden_event = EventFactory(name="HiddenEvent", is_visible=False)
        src_hid_ev = AudioSourceFactory(event=hidden_event, file_title="HiddenEvRec", is_approved=True)

        SnippetFactory(source=src_vis, entry=None, optional=False, is_visible=True, is_approved=True)
        SnippetFactory(source=src_vis, entry=None, optional=True, is_visible=True, is_approved=True)
        SnippetFactory(source=src_vis, entry=self.entries[0], optional=False, is_visible=True, is_approved=True)
        SnippetFactory(source=src_vis, entry=None, optional=False, is_visible=False, is_approved=True)
        SnippetFactory(source=src_unapp, entry=None, optional=False, is_visible=True, is_approved=True)
        SnippetFactory(source=src_hid_ev, entry=None, optional=False, is_visible=True, is_approved=True)

        resp = self.client.get("/todo/")
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        self.assertIn("VisibleRecording", body)
        self.assertIn("1 snippet remaining", body)
        self.assertNotIn("UnapprovedRecording", body)
        self.assertNotIn("HiddenEvRec", body)

    @unittest.expectedFailure
    def test_untranscribed_snippets_handles_event_with_none_date(self):
        """
        Bug in palanaeum/views.py:557 — untranscribed_snippets sorts sources by
        `source_count[0].event.date`, raising TypeError if an event has `date=None`
        alongside another event with a date.
        """
        undated_event = EventFactory(name="Undated", date=None)
        s1 = AudioSourceFactory(event=self.event, is_approved=True)
        s2 = AudioSourceFactory(event=undated_event, is_approved=True)
        SnippetFactory(source=s1, entry=None, optional=False)
        SnippetFactory(source=s2, entry=None, optional=False)
        resp = self.client.get("/todo/")
        self.assertEqual(resp.status_code, 200)


class FeedsAndSitemapTests(TestCase):
    def setUp(self):
        self.event = EventFactory(name="Feed Event", date=date.today() - timedelta(days=10))
        self.old_event = EventFactory(name="Old Feed Event", date=date.today() - timedelta(days=120))
        self.hidden_event = EventFactory(name="Hidden Feed Event", is_visible=False)

        self.entry = EntryFactory(event=self.event, is_approved=True, order=0)
        ver = EntryVersionFactory(entry=self.entry, is_approved=True, paraphrased=True)
        EntryLineFactory(entry_version=ver, speaker="Brandon", text="Feed entry body")
        SnippetFactory(source=AudioSourceFactory(event=self.event), entry=self.entry, is_visible=True)
        url_src = URLSourceFactory(text="YouTube")
        ver.url_sources.add(url_src)

        self.entry_hidden_self = EntryFactory(event=self.event, is_visible=False, is_approved=True)
        EntryLineFactory(
            entry_version=EntryVersionFactory(entry=self.entry_hidden_self, is_approved=True),
            text="HiddenSelfEntry",
        )

        self.entry_hid = EntryFactory(event=self.hidden_event, is_approved=True)
        EntryLineFactory(entry_version=EntryVersionFactory(entry=self.entry_hid, is_approved=True), text="Secret")

    def test_recent_entries_feed_and_event_entries_feed(self):
        recent_resp = self.client.get("/recent/feed/")
        self.assertEqual(recent_resp.status_code, 200)
        xml_text = recent_resp.content.decode()
        self.assertIn("Feed entry body", xml_text)
        self.assertIn("paraphrased", xml_text)
        self.assertIn("contains snippet", xml_text)
        self.assertNotIn("HiddenSelfEntry", xml_text)

        # Feed without slug redirects to slugged feed
        no_slug = self.client.get(f"/events/{self.event.id}/feed/")
        self.assertEqual(no_slug.status_code, 302)

        ev_feed = self.client.get(f"/events/{self.event.id}-{slugify(self.event.name)}/feed/")
        self.assertEqual(ev_feed.status_code, 200)
        self.assertIn("Feed entry body", ev_feed.content.decode())

        # Hidden event feed -> 403
        hid_feed = self.client.get(f"/events/{self.hidden_event.id}-hidden/feed/")
        self.assertEqual(hid_feed.status_code, 403)

    @unittest.expectedFailure
    def test_recent_entries_feed_excludes_entries_from_hidden_events(self):
        """
        Bug in palanaeum/feeds.py:41 & palanaeum/models.py:85 — VisibleManager
        only checks Entry.is_visible without filtering `event__is_visible=True`,
        so RecentEntriesFeed exposes entries from hidden events.
        """
        recent_resp = self.client.get("/recent/feed/")
        self.assertNotIn("Secret", recent_resp.content.decode())

    def test_sitemap_xml(self):
        EventFactory(name="Mid Event", date=date.today() - timedelta(days=45))
        resp = self.client.get("/sitemap.xml")
        self.assertEqual(resp.status_code, 200)
        root = ElementTree.fromstring(resp.content)
        locs = [el.text for el in root.iter() if el.tag.endswith("loc")]
        self.assertTrue(any(self.event.get_absolute_url() in loc for loc in locs))
        self.assertTrue(all(loc.startswith("https://") for loc in locs))
        self.assertFalse(any(self.hidden_event.get_absolute_url() in loc for loc in locs))

    @unittest.expectedFailure
    def test_sitemap_handles_event_with_none_date(self):
        """
        Bug in palanaeum/sitemaps.py:32,45 — EventSitemap.changefreq and priority
        subtract/compare `obj.date` without guarding against nullable `date=None`.
        """
        EventFactory(name="Undated Sitemap Event", date=None)
        resp = self.client.get("/sitemap.xml")
        self.assertEqual(resp.status_code, 200)


class AuthAndProfileViewsTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username="member", email="member@example.com")
        self.user.set_password("OldPass123!")
        self.user.save()
        UserSettingsFactory(user=self.user, timezone="UTC", page_length=20)

    def test_register_user_get_post_and_duplicate_email(self):
        self.assertEqual(self.client.get("/auth/register/").status_code, 200)

        resp = self.client.post(
            "/auth/register/",
            {
                "username": "brandnew",
                "email": "brandnew@example.com",
                "password1": "Str0ng!Pass#22",
                "password2": "Str0ng!Pass#22",
            },
        )
        self.assertRedirects(resp, reverse("auth_login"))
        created = User.objects.get(username="brandnew")
        self.assertEqual(UserSettings.objects.get(user=created).page_length, 20)

        dup = self.client.post(
            "/auth/register/",
            {
                "username": "brandnew2",
                "email": "brandnew@example.com",
                "password1": "Str0ng!Pass#22",
                "password2": "Str0ng!Pass#22",
            },
        )
        self.assertEqual(dup.status_code, 200)
        self.assertIn("already exists", dup.content.decode())

    def test_login_logout_and_password_change(self):
        resp_login = self.client.post(
            "/auth/login/",
            {"username": "member", "password": "OldPass123!"},
        )
        self.assertRedirects(resp_login, "/")

        # Django 6 LogoutView requires POST; GET returns 405
        self.assertEqual(self.client.get("/auth/logout/").status_code, 405)

        resp_pw = self.client.post(
            "/auth/password_change/",
            {
                "old_password": "OldPass123!",
                "new_password1": "NewPass456!",
                "new_password2": "NewPass456!",
            },
            follow=True,
        )
        self.assertRedirects(resp_pw, reverse("auth_settings"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass456!"))

        resp_logout = self.client.post("/auth/logout/")
        self.assertRedirects(resp_logout, "/")

    def test_password_reset_full_flow(self):
        reset_get = self.client.get("/auth/password_reset/")
        self.assertEqual(reset_get.status_code, 200)
        self.assertEqual(reset_get.context["site_name"], "Palanaeum")

        resp = self.client.post("/auth/password_reset/", {"email": "member@example.com"})
        self.assertRedirects(resp, reverse("auth_password_reset_done"))
        self.assertEqual(self.client.get("/auth/password_reset/done/").status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        match = re.search(r"(/auth/reset/[^\s]+)", mail.outbox[0].body)
        self.assertIsNotNone(match)
        reset_path = match.group(1)

        # Follow token validation redirect to set-password URL
        confirm_get = self.client.get(reset_path, follow=True)
        self.assertEqual(confirm_get.status_code, 200)
        set_pw_url = confirm_get.request["PATH_INFO"]

        confirm_post = self.client.post(
            set_pw_url,
            {
                "new_password1": "ResetPass789!",
                "new_password2": "ResetPass789!",
            },
            follow=True,
        )
        self.assertRedirects(confirm_post, reverse("auth_login"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("ResetPass789!"))

    def test_user_settings_view_auth_and_update(self):
        self.assertRedirects(
            self.client.get("/auth/profile/"),
            f"{reverse('auth_login')}?next=/auth/profile/",
        )

        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/auth/profile/").status_code, 200)

        # Invalid password prevents email change
        bad = self.client.post(
            "/auth/profile/",
            {
                "email": "changed@example.com",
                "password": "wrong",
                "timezone": "Europe/Warsaw",
                "page_length": "35",
                "website": "https://example.org",
            },
        )
        self.assertEqual(bad.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "member@example.com")

        # Valid POST updates both email and settings + session
        good = self.client.post(
            "/auth/profile/",
            {
                "email": "changed@example.com",
                "password": "OldPass123!",
                "timezone": "Europe/Warsaw",
                "page_length": "35",
                "website": "https://example.org",
            },
        )
        self.assertRedirects(good, reverse("auth_settings"))
        self.user.refresh_from_db()
        self.user.settings.refresh_from_db()
        self.assertEqual(self.user.email, "changed@example.com")
        self.assertEqual(self.user.settings.timezone, "Europe/Warsaw")
        self.assertEqual(self.user.settings.page_length, 35)
        self.assertEqual(self.client.session["page_length"], 35)


class CollectionsViewsTests(TestCase):
    def setUp(self):
        self.owner = UserFactory(username="owner")
        self.other = UserFactory(username="other")
        self.superuser = SuperUserFactory(username="superadmin")
        UserSettingsFactory(user=self.owner)
        UserSettingsFactory(user=self.other)
        UserSettingsFactory(user=self.superuser)

        self.event = EventFactory()
        self.entry = EntryFactory(event=self.event, is_visible=True, is_approved=True)
        EntryLineFactory(entry_version=EntryVersionFactory(entry=self.entry, is_approved=True), text="Col entry")

        self.pub_coll = UsersEntryCollectionFactory(user=self.owner, name="Public Col", public=True)
        self.pub_coll.entries.add(self.entry)
        self.priv_coll = UsersEntryCollectionFactory(user=self.owner, name="Private Col", public=False)
        self.priv_coll.entries.add(self.entry)

    def test_collection_list_and_show_permissions(self):
        self.assertRedirects(
            self.client.get("/collections/"),
            f"{reverse('auth_login')}?next=/collections/",
        )
        self.client.force_login(self.owner)
        resp = self.client.get("/collections/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Public Col", resp.content.decode())
        self.assertIn("Private Col", resp.content.decode())
        self.client.logout()

        # Public collection visible to anonymous
        self.assertEqual(self.client.get(f"/collections/{self.pub_coll.id}/").status_code, 200)

        # Private collection denied to anonymous & other user
        self.assertRedirects(self.client.get(f"/collections/{self.priv_coll.id}/"), "/")
        self.client.force_login(self.other)
        self.assertRedirects(self.client.get(f"/collections/{self.priv_coll.id}/"), "/")

        # Visible to owner and superuser
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(f"/collections/{self.priv_coll.id}/").status_code, 200)
        self.client.force_login(self.superuser)
        su_resp = self.client.get(f"/collections/{self.priv_coll.id}/")
        self.assertEqual(su_resp.status_code, 200)
        self.assertIn("viewing a private collection as superuser", su_resp.content.decode())

    @unittest.expectedFailure
    def test_show_collection_with_hidden_entry_skips_inaccessible_entries(self):
        """
        Bug in palanaeum/views.py:295-297 — show_collection queries all
        `collection.entries` IDs and indexes `entries[eid]` after `Entry.prefetch_entries`,
        raising KeyError if any entry in the collection is hidden from the viewer.
        """
        hidden_entry = EntryFactory(event=self.event, is_visible=False, is_approved=True)
        self.pub_coll.entries.add(hidden_entry)
        resp = self.client.get(f"/collections/{self.pub_coll.id}/")
        self.assertEqual(resp.status_code, 200)

    def test_edit_and_delete_collection(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get("/collections/create/").status_code, 200)
        invalid_resp = self.client.post("/collections/create/", {"name": "", "description": "x"})
        self.assertEqual(invalid_resp.status_code, 200)
        self.assertIn("This field is required.", invalid_resp.content.decode())
        msgs = [m.message for m in messages.get_messages(invalid_resp.wsgi_request)]
        self.assertIn("There were problems while saving your collection.", msgs)
        create_resp = self.client.post(
            "/collections/create/",
            {"name": "Created Col", "description": "Desc", "public": True},
        )
        self.assertRedirects(create_resp, reverse("collections_list"))
        self.assertTrue(UsersEntryCollection.objects.filter(name="Created Col", user=self.owner).exists())

        edit_resp = self.client.post(
            f"/collections/{self.priv_coll.id}/edit/",
            {"name": "Renamed Col", "description": "Updated", "public": True},
        )
        self.assertRedirects(edit_resp, reverse("collections_list"))
        self.priv_coll.refresh_from_db()
        self.assertEqual(self.priv_coll.name, "Renamed Col")

        # Non-owner and even superuser cannot edit someone else's collection
        for actor in (self.other, self.superuser):
            self.client.force_login(actor)
            self.assertRedirects(self.client.get(f"/collections/{self.priv_coll.id}/edit/"), "/")

        # Non-owner cannot delete; owner & superuser can
        self.client.force_login(self.other)
        self.assertRedirects(self.client.get(f"/collections/{self.priv_coll.id}/delete/"), "/")

        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(f"/collections/{self.priv_coll.id}/delete/").status_code, 200)
        del_resp = self.client.post(f"/collections/{self.priv_coll.id}/delete/")
        self.assertRedirects(del_resp, reverse("collections_list"))
        self.assertFalse(UsersEntryCollection.objects.filter(pk=self.priv_coll.pk).exists())

        self.client.force_login(self.superuser)
        su_del = self.client.post(f"/collections/{self.pub_coll.id}/delete/")
        self.assertRedirects(su_del, reverse("collections_list"))
        self.assertFalse(UsersEntryCollection.objects.filter(pk=self.pub_coll.pk).exists())

    def test_ajax_collection_endpoints(self):
        long_coll = UsersEntryCollectionFactory(user=self.owner, name="X" * 40, public=False)
        self.client.force_login(self.owner)

        # GET list
        list_resp = self.client.get("/collections/ajax/get/", {"entry_id": self.entry.id})
        self.assertEqual(list_resp.status_code, 200)
        payload = json.loads(list_resp.content)
        self.assertTrue(payload["success"])
        names = {item["id"]: item for item in payload["list"]}
        self.assertEqual(names[long_coll.id]["name"], ("X" * 27) + "...")
        self.assertFalse(names[long_coll.id]["has_entry"])
        self.assertTrue(names[self.pub_coll.id]["has_entry"])

        # Add & remove entry
        add_resp = self.client.post(
            "/collections/ajax/edit/",
            {"entry_id": self.entry.id, "collection_id": long_coll.id, "action": "add"},
        )
        self.assertEqual(json.loads(add_resp.content)["size"], 1)
        self.assertTrue(long_coll.entries.filter(pk=self.entry.pk).exists())

        rem_resp = self.client.post(
            "/collections/ajax/edit/",
            {"entry_id": self.entry.id, "collection_id": long_coll.id, "action": "remove"},
        )
        self.assertEqual(json.loads(rem_resp.content)["size"], 0)

        # Invalid params & unauthorized user
        self.assertEqual(self.client.get("/collections/ajax/edit/").status_code, 405)
        bad_action = json.loads(
            self.client.post(
                "/collections/ajax/edit/",
                {"entry_id": self.entry.id, "collection_id": long_coll.id, "action": "toggle"},
            ).content
        )
        self.assertFalse(bad_action["success"])
        missing_param = json.loads(self.client.post("/collections/ajax/edit/", {}).content)
        self.assertFalse(missing_param["success"])
        bad_int = json.loads(
            self.client.post(
                "/collections/ajax/edit/",
                {"entry_id": "abc", "collection_id": long_coll.id, "action": "add"},
            ).content
        )
        self.assertFalse(bad_int["success"])

        self.client.force_login(self.other)
        unauth = json.loads(
            self.client.post(
                "/collections/ajax/edit/",
                {"entry_id": self.entry.id, "collection_id": long_coll.id, "action": "add"},
            ).content
        )
        self.assertFalse(unauth["success"])

        # AJAX create collection
        self.client.force_login(self.owner)
        create_ajax = json.loads(
            self.client.post(
                "/collections/ajax/create/",
                {"name": "Quick List", "entry_id": self.entry.id},
            ).content
        )
        self.assertTrue(create_ajax["success"])
        self.assertEqual(create_ajax["name"], "Quick List")
        created_coll = UsersEntryCollection.objects.get(pk=create_ajax["id"])
        self.assertFalse(created_coll.public)
        self.assertTrue(created_coll.entries.filter(pk=self.entry.pk).exists())

        missing_create = json.loads(self.client.post("/collections/ajax/create/", {}).content)
        self.assertFalse(missing_create["success"])
        bad_create = json.loads(
            self.client.post("/collections/ajax/create/", {"name": "N", "entry_id": "bad"}).content
        )
        self.assertFalse(bad_create["success"])
