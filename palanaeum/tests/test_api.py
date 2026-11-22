import unittest
from datetime import date, timedelta
from unittest import mock

from django.core.cache import caches
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token
from rest_framework.throttling import SimpleRateThrottle

from palanaeum.api.serializers import TagsSerializer
from palanaeum.models import EntrySearchVector
from palanaeum.tests.base import make_LocMem_caches_setting
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


class APIRouterViewsTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username="api_user")
        self.staff = StaffUserFactory(username="api_staff")
        UserSettingsFactory(user=self.user)
        UserSettingsFactory(user=self.staff)
        self.staff_token = Token.objects.create(user=self.staff)

        self.tag_cosmere = TagFactory(name="cosmere")
        self.tag_exclude = TagFactory(name="spoiler")

        self.past_event = EventFactory(
            name="Past Con", date=date.today() - timedelta(days=30), is_visible=True, is_approved=True
        )
        self.future_event = EventFactory(
            name="Future Con", date=date.today() + timedelta(days=30), is_visible=True, is_approved=True
        )
        self.hidden_event = EventFactory(
            name="Hidden Con", date=date.today() + timedelta(days=10), is_visible=False, is_approved=True
        )

        self.entry_vis = EntryFactory(event=self.past_event, is_visible=True, is_approved=True)
        v1 = EntryVersionFactory(entry=self.entry_vis, entry_date=date(2023, 1, 5), is_approved=True)
        v1.tags.add(self.tag_cosmere)
        EntryLineFactory(entry_version=v1, speaker="Brandon", text="Investiture in Roshar")
        esv1 = EntrySearchVector(entry=self.entry_vis)
        esv1.update()

        self.entry_unapp = EntryFactory(event=self.future_event, is_visible=True, is_approved=False)
        v2 = EntryVersionFactory(entry=self.entry_unapp, entry_date=date(2024, 1, 5), is_approved=False)
        v2.tags.add(self.tag_exclude)
        EntryLineFactory(entry_version=v2, speaker="Hoid", text="Unapproved API text")
        esv2 = EntrySearchVector(entry=self.entry_unapp)
        esv2.update()

        self.entry_hidden = EntryFactory(event=self.past_event, is_visible=False, is_approved=True)
        v3 = EntryVersionFactory(entry=self.entry_hidden, is_approved=True)
        EntryLineFactory(entry_version=v3, speaker="Kelsier", text="Hidden API entry")

    def test_events_viewset_and_pagination_and_readonly(self):
        resp = self.client.get("/api/events/", {"page_size": 1})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 1)

        detail = self.client.get(f"/api/events/{self.past_event.id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["name"], "Past Con")

        self.assertEqual(self.client.get(f"/api/events/{self.hidden_event.id}/").status_code, 404)
        self.assertEqual(self.client.post("/api/events/", {"name": "New"}).status_code, 405)

    @unittest.expectedFailure
    def test_events_viewset_staff_session_sees_hidden_event(self):
        """
        Bug in palanaeum/api/views.py:19 — EventViewSet binds
        `queryset = Event.all_visible.all()` at module import time when
        `get_request()` is None (AnonymousUser), pinning the cached anonymous SQL
        filter so even session-authenticated staff cannot access hidden events.
        """
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get("/api/events/").json()["count"], 3)
        self.assertEqual(self.client.get(f"/api/events/{self.hidden_event.id}/").status_code, 200)

    def test_upcoming_events_viewset(self):
        resp = self.client.get("/api/upcoming_events/")
        self.assertEqual(resp.status_code, 200)
        names = [e["name"] for e in resp.json()["results"]]
        self.assertIn("Future Con", names)
        self.assertNotIn("Past Con", names)
        self.assertNotIn("Hidden Con", names)

    def test_tags_viewset(self):
        resp = self.client.get("/api/tags/")
        self.assertEqual(resp.status_code, 200)
        by_name = {t["name"]: t for t in resp.json()["results"]}
        self.assertEqual(by_name["cosmere"]["entries"], 1)
        self.assertEqual(by_name["cosmere"]["events"], 0)
        with self.assertRaises(NotImplementedError):
            TagsSerializer().create({})
        with self.assertRaises(NotImplementedError):
            TagsSerializer().update(None, {})

    def test_entry_viewset_session_visibility(self):
        # Anonymous sees only visible+approved entry
        anon_ids = [e["id"] for e in self.client.get("/api/entry/").json()["results"]]
        self.assertEqual(anon_ids, [self.entry_vis.id])

    @unittest.expectedFailure
    def test_entry_viewset_session_visibility_for_contributor_and_staff(self):
        """
        Bug in palanaeum/api/views.py:43 — EntryViewSet binds
        `queryset = Entry.all_visible.all()` at module import time when
        `get_request()` is None (AnonymousUser), pinning the cached anonymous SQL
        filter so session-authenticated contributors and staff only see approved
        visible entries.
        """
        # Session contributor sees visible unapproved entry too
        self.client.force_login(self.user)
        user_ids = {e["id"] for e in self.client.get("/api/entry/").json()["results"]}
        self.assertEqual(user_ids, {self.entry_vis.id, self.entry_unapp.id})

        # Staff sees hidden entry too
        self.client.force_login(self.staff)
        staff_ids = {e["id"] for e in self.client.get("/api/entry/").json()["results"]}
        self.assertEqual(staff_ids, {self.entry_vis.id, self.entry_unapp.id, self.entry_hidden.id})

    @unittest.expectedFailure
    def test_entry_viewset_token_authentication_visible_to_visible_manager(self):
        """
        Bug in palanaeum/middleware.py:44 & palanaeum/api/views.py:43 —
        GlobalRequestKeeper captures Django's HttpRequest before DRF runs
        TokenAuthentication, so `request.user` in VisibleManager stays AnonymousUser
        for token-authenticated API requests.
        """
        resp = self.client.get(
            "/api/entry/",
            HTTP_AUTHORIZATION=f"Token {self.staff_token.key}",
        )
        self.assertEqual(resp.status_code, 200)
        ids = {e["id"] for e in resp.json()["results"]}
        self.assertIn(self.entry_hidden.id, ids)

    def test_search_entry_viewset(self):
        r_query = self.client.get("/api/search_entry/", {"query": "investiture", "ordering": "rank"})
        self.assertEqual(r_query.status_code, 200)
        self.assertEqual([e["id"] for e in r_query.json()["results"]], [self.entry_vis.id])

        r_speaker = self.client.get("/api/search_entry/", {"speaker": "brandon"})
        self.assertEqual([e["id"] for e in r_speaker.json()["results"]], [self.entry_vis.id])

        r_tags = self.client.get("/api/search_entry/", {"tags": "cosmere"})
        self.assertEqual([e["id"] for e in r_tags.json()["results"]], [self.entry_vis.id])

        r_anti = self.client.get(
            "/api/search_entry/",
            {"query": "investiture", "antitag": "spoiler"},
        )
        self.assertEqual([e["id"] for e in r_anti.json()["results"]], [self.entry_vis.id])

        r_date = self.client.get(
            "/api/search_entry/",
            {"date_from": "2023-01-01", "date_to": "2023-12-31", "ordering": "-date"},
        )
        self.assertEqual([e["id"] for e in r_date.json()["results"]], [self.entry_vis.id])

    def test_random_entry_viewset_populated_and_empty(self):
        resp = self.client.get("/api/random_entry/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], self.entry_vis.id)

        # Empty visible entries -> returns serialized empty structure without crashing
        self.entry_vis.hide()
        empty_resp = self.client.get("/api/random_entry/")
        self.assertEqual(empty_resp.status_code, 200)
        empty_data = empty_resp.json()
        self.assertNotIn("id", empty_data)
        self.assertIsNone(empty_data["event"])
        self.assertEqual(empty_data["lines"], [])

    @override_settings(CACHES=make_LocMem_caches_setting("api-throttle-tests"))
    def test_anon_rate_throttling_enforced(self):
        caches["default"].clear()
        self.addCleanup(caches["default"].clear)

        # UserRateThrottle applies 10/second by IP even for anonymous requests
        with mock.patch.object(SimpleRateThrottle, "timer", new=staticmethod(lambda: 5000.0)):
            for idx in range(10):
                resp = self.client.get("/api/tags/")
                self.assertEqual(resp.status_code, 200, f"Unexpected status on burst request {idx + 1}")
            burst_throttled = self.client.get("/api/tags/")
            self.assertEqual(burst_throttled.status_code, 429)

        # Spaced >0.2s apart avoids 10/second so AnonRateThrottle (30/min) triggers on request 31
        caches["default"].clear()
        current_time = [10000.0]
        with mock.patch.object(SimpleRateThrottle, "timer", new=staticmethod(lambda: current_time[0])):
            for idx in range(30):
                current_time[0] += 0.25
                resp = self.client.get("/api/tags/")
                self.assertEqual(resp.status_code, 200, f"Unexpected status on spaced request {idx + 1}")
            current_time[0] += 0.25
            anon_throttled = self.client.get("/api/tags/")
            self.assertEqual(anon_throttled.status_code, 429)
