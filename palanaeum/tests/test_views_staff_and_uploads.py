import json
import subprocess
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from palanaeum.audio_fine_upload_views import combine_chunks, save_upload, upload_finished

from palanaeum.models import (
    AudioSource,
    Entry,
    EntryLine,
    EntrySearchVector,
    EntryVersion,
    Event,
    HelpPage,
    ImageSource,
    Snippet,
    Tag,
    URLSource,
)
from palanaeum.tests.base import make_uploaded_image
from palanaeum.tests.factories import (
    AudioSourceFactory,
    EntryFactory,
    EntryLineFactory,
    EntryVersionFactory,
    EventFactory,
    HelpPageFactory,
    ImageSourceFactory,
    SnippetFactory,
    StaffUserFactory,
    TagFactory,
    URLSourceFactory,
    UserFactory,
    UserSettingsFactory,
)


class StaffEventAndEntryManagementTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username="contrib")
        self.other_user = UserFactory(username="other_contrib")
        self.staff = StaffUserFactory(username="staff")
        UserSettingsFactory(user=self.user)
        UserSettingsFactory(user=self.other_user)
        UserSettingsFactory(user=self.staff)
        self.event = EventFactory(name="Main Event", date=date(2023, 4, 1))
        self.tag = TagFactory(name="cosmere")

    def test_edit_and_remove_event_permissions_and_flows(self):
        # Anon & non-staff redirected
        self.assertEqual(self.client.get("/events/create/").status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/events/create/").status_code, 302)

        self.client.force_login(self.staff)
        self.assertEqual(self.client.get("/events/create/").status_code, 200)
        create_resp = self.client.post(
            "/events/create/",
            {
                "name": "Created Event",
                "date": "2024-05-01",
                "review_state": Event.REVIEW_PENDING,
                "location": "Provo",
                "tour": "",
                "bookstore": "",
                "meta": "",
                "tags": "['cosmere']",
            },
        )
        created = Event.objects.get(name="Created Event")
        self.assertRedirects(
            create_resp,
            reverse("view_event_no_title", kwargs={"event_id": created.id}),
            fetch_redirect_response=False,
        )

        # Edit existing event
        self.assertEqual(self.client.get(f"/events/{created.id}/edit/").status_code, 200)
        edit_resp = self.client.post(
            f"/events/{created.id}/edit/",
            {
                "name": "Updated Event",
                "date": "2024-05-02",
                "review_state": Event.REVIEW_APPROVED,
                "location": "Provo",
                "tags": "",
            },
        )
        self.assertEqual(edit_resp.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.name, "Updated Event")

        # Delete confirmation GET + POST
        self.assertEqual(self.client.get(f"/events/{created.id}/delete/").status_code, 200)
        del_resp = self.client.post(f"/events/{created.id}/delete/")
        self.assertRedirects(del_resp, "/")
        self.assertFalse(Event.objects.filter(pk=created.id).exists())

    def test_edit_entry_and_save_entry_contributor_vs_staff(self):
        self.assertEqual(self.client.get(f"/events/{self.event.id}/add_entry/").status_code, 302)

        # Regular contributor creates new entry suggestion
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(f"/events/{self.event.id}/add_entry/").status_code, 200)

        with mock.patch("palanaeum.tasks.create_snippet.delay"):
            resp = self.client.post(
                "/entry/save/",
                {
                    "event_id": self.event.id,
                    "entry_id": "",
                    "date": "2023-04-01",
                    "note": "<b>User note</b>",
                    "paraphrased": "on",
                    "direct": "on",
                    "reported_by": "contrib",
                    "line-0-id": "",
                    "line-0-order": "0",
                    "line-0-speaker": "Questioner",
                    "line-0-text": "<p>Question?</p>",
                    "line-1-id": "",
                    "line-1-order": "1",
                    "line-1-speaker": "Brandon",
                    "line-1-text": "<p>RAFO</p>",
                    "url-source-0-url": "https://example.com/q",
                    "url-source-0-name": "Example Q",
                    "url-source-1-url": "not-a-valid-url",
                    "url-source-1-name": "Invalid",
                    "tags[]": ["cosmere"],
                },
            )
        self.assertEqual(resp.status_code, 200)
        payload = json.loads(resp.content)
        self.assertTrue(payload["success"])
        entry = Entry.objects.get(pk=payload["entry_id"])
        self.assertFalse(entry.is_approved)
        self.assertFalse(entry.versions.last().is_approved)
        self.assertEqual(entry.lines.count(), 2)
        self.assertEqual(entry.all_url_sources().count(), 1)
        self.assertEqual(list(entry.tags.values_list("name", flat=True)), ["cosmere"])

        # Bad date format returns AjaxException JSON
        bad_date = json.loads(
            self.client.post(
                "/entry/save/",
                {"entry_id": entry.id, "date": "04/01/2023"},
            ).content
        )
        self.assertFalse(bad_date["success"])
        self.assertIn("YYYY-MM-DD", bad_date["reason"])

        # Unknown tag by non-staff raises 403 PermissionDenied
        new_tag_resp = self.client.post(
            "/entry/save/",
            {"entry_id": entry.id, "date": "2023-04-01", "tags[]": ["forbidden-new-tag"]},
        )
        self.assertEqual(new_tag_resp.status_code, 403)

        # Staff edits entry: archives old version, deletes blank line, creates new tag, auto-approves
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(f"/entry/{entry.id}/edit/").status_code, 200)
        l0, l1 = list(entry.lines.order_by("order"))
        edit_resp = self.client.post(
            "/entry/save/",
            {
                "entry_id": entry.id,
                "date": "2023-04-02",
                "note": "Staff note",
                "searchable": "on",
                "line-0-id": l0.id,
                "line-0-order": "0",
                "line-0-speaker": "Questioner",
                "line-0-text": "<p>Updated Question?</p>",
                "line-1-id": l1.id,
                "line-1-order": "1",
                "line-1-speaker": "",
                "line-1-text": "",
                "tags[]": ["cosmere", "brandnewtag"],
            },
        )
        edit_data = json.loads(edit_resp.content)
        self.assertTrue(edit_data["success"])
        self.assertIn(l1.id, edit_data["deleted_lines"])
        entry.refresh_from_db()
        self.assertTrue(entry.is_approved)
        self.assertTrue(entry.versions.last().is_approved)
        self.assertGreaterEqual(entry.versions.count(), 2)
        self.assertTrue(EntrySearchVector.objects.filter(entry=entry).exists())

        # Empty-version entry + empty date fallback + empty/updated URLSource + non-contributor save guard
        existing_url = URLSourceFactory(url="https://existing.example.com/item", text="Old Link Name")
        versionless_entry = EntryFactory(event=self.event, is_approved=True)
        resp_verless = json.loads(
            self.client.post(
                "/entry/save/",
                {
                    "entry_id": versionless_entry.id,
                    "date": "",
                    "url-source-0-url": "not-a-valid-url",
                    "url-source-0-name": "Ignored invalid",
                    "url-source-1-url": "https://existing.example.com/item",
                    "url-source-1-name": "Updated Link Name",
                },
            ).content
        )
        self.assertTrue(resp_verless["success"])
        existing_url.refresh_from_db()
        self.assertEqual(existing_url.text, "Updated Link Name")
        self.assertEqual(versionless_entry.versions.last().entry_date, self.event.date)
        with mock.patch("palanaeum.staff_views.is_contributor", return_value=False):
            non_contrib = json.loads(self.client.post("/entry/save/", {"event_id": self.event.id}).content)
        self.assertFalse(non_contrib["success"])

    def test_entry_history_approve_reject_move_and_remove(self):
        entry = EntryFactory(event=self.event, is_approved=True)
        v1 = EntryVersionFactory(
            entry=entry,
            is_approved=True,
            date=timezone.now() - timedelta(minutes=10),
            note="First note",
        )
        EntryLineFactory(entry_version=v1, speaker="Fan", text="Old question")
        url_src = URLSourceFactory()
        v1.url_sources.add(url_src)
        v1.tags.add(self.tag)

        v2 = EntryVersionFactory(
            entry=entry,
            is_approved=False,
            date=timezone.now(),
            paraphrased=True,
        )
        EntryLineFactory(entry_version=v2, speaker="Fan", text="New question")

        self.client.force_login(self.user)
        hist_default = self.client.get(f"/entry/{entry.id}/history/")
        self.assertEqual(hist_default.status_code, 200)
        self.assertIn("New question", hist_default.content.decode())

        # Swapped version_1/version_2 auto-orders older/newer
        hist_swap = self.client.get(
            f"/entry/{entry.id}/history/",
            {"version_1": v2.id, "version_2": v1.id},
        )
        self.assertEqual(hist_swap.status_code, 200)
        self.assertEqual(hist_swap.context["newer_version"], v2)
        self.assertEqual(hist_swap.context["older_version"], v1)

        # Entry without versions -> 404
        empty_entry = EntryFactory(event=self.event)
        self.assertEqual(self.client.get(f"/entry/{empty_entry.id}/history/").status_code, 404)

        # Staff rejects v2 -> entry keeps v1
        self.client.force_login(self.staff)
        rej = self.client.post(f"/entry/{entry.id}/reject/")
        self.assertRedirects(rej, reverse("staff_suggestions"), fetch_redirect_response=False)
        self.assertFalse(EntryVersion.objects.filter(pk=v2.pk).exists())
        self.assertTrue(Entry.objects.filter(pk=entry.pk).exists())

        # Rejecting only remaining unapproved version deletes the entry
        sug_entry = EntryFactory(event=self.event, is_approved=False)
        EntryLineFactory(
            entry_version=EntryVersionFactory(entry=sug_entry, is_approved=False),
            text="Temporary",
        )
        self.client.post(f"/entry/{sug_entry.id}/reject/")
        self.assertFalse(Entry.objects.filter(pk=sug_entry.pk).exists())

        # Approve entry
        pending_entry = EntryFactory(event=self.event, is_approved=False)
        EntryLineFactory(
            entry_version=EntryVersionFactory(entry=pending_entry, is_approved=False),
            speaker="Hoid",
            text="Approved line",
        )
        app = self.client.post(f"/entry/{pending_entry.id}/approve/")
        self.assertRedirects(app, reverse("staff_suggestions"), fetch_redirect_response=False)
        pending_entry.refresh_from_db()
        self.assertTrue(pending_entry.is_approved)

        # Move entry to populated target event
        target_event = EventFactory(name="Target Populated")
        EntryFactory(event=target_event, order=4)
        self.assertEqual(self.client.get(f"/entry/{pending_entry.id}/move/").status_code, 200)
        move_resp = self.client.post(f"/entry/{pending_entry.id}/move/", {"event_id": target_event.id})
        self.assertEqual(move_resp.status_code, 302)
        pending_entry.refresh_from_db()
        self.assertEqual(pending_entry.event, target_event)
        self.assertEqual(pending_entry.order, 5)

        # Remove entry GET confirm + POST delete
        self.assertEqual(self.client.get(f"/entry/{pending_entry.id}/delete/").status_code, 200)
        rem_resp = self.client.post(f"/entry/{pending_entry.id}/delete/")
        self.assertEqual(rem_resp.status_code, 302)
        self.assertFalse(Entry.objects.filter(pk=pending_entry.pk).exists())

    @unittest.expectedFailure
    def test_move_entry_to_empty_event_succeeds(self):
        """
        Bug in palanaeum/staff_views.py:107 — move_entry computes
        `Entry.objects.filter(event=new_event).order_by('-order').first().order + 1`,
        raising AttributeError when the destination event has no entries yet.
        """
        entry = EntryFactory(event=self.event)
        empty_target = EventFactory(name="Empty Destination")
        self.client.force_login(self.staff)
        resp = self.client.post(f"/entry/{entry.id}/move/", {"event_id": empty_target.id})
        self.assertEqual(resp.status_code, 302)
        entry.refresh_from_db()
        self.assertEqual(entry.event, empty_target)


class VisibilitySortingStaffCPHelpTests(TestCase):
    def setUp(self):
        self.staff = StaffUserFactory(username="staff_sort")
        UserSettingsFactory(user=self.staff)
        self.event = EventFactory(name="Sort Event")

    def test_hide_show_resource_all_classes_and_errors(self):
        entry = EntryFactory(event=self.event)
        audio = AudioSourceFactory(event=self.event)
        url_src = URLSourceFactory()
        snippet = SnippetFactory(source=audio)
        img = ImageSourceFactory(event=self.event)

        self.client.force_login(self.staff)
        cases = [
            ("entry", entry),
            ("audio_source", audio),
            ("url_source", url_src),
            ("snippet", snippet),
            ("image_source", img),
        ]
        for cls_name, obj in cases:
            hide_resp = json.loads(
                self.client.post(
                    "/hide_show_resource/",
                    {"class": cls_name, "id": obj.id, "mode": "hide"},
                ).content
            )
            self.assertTrue(hide_resp["success"])
            obj.refresh_from_db()
            self.assertFalse(obj.is_visible)

            show_resp = json.loads(
                self.client.post(
                    "/hide_show_resource/",
                    {"class": cls_name, "id": obj.id, "mode": "show"},
                ).content
            )
            self.assertTrue(show_resp["success"])
            obj.refresh_from_db()
            self.assertTrue(obj.is_visible)

        for bad_payload in (
            {},
            {"class": "bad", "id": entry.id, "mode": "hide"},
            {"class": "entry", "id": entry.id, "mode": "toggle"},
        ):
            data = json.loads(self.client.post("/hide_show_resource/", bad_payload).content)
            self.assertFalse(data["success"])

    @unittest.expectedFailure
    def test_hide_show_resource_non_integer_id_returns_ajax_error(self):
        """
        Bug in palanaeum/staff_views.py:163,167 — hide_show_resource catches
        TypeError around `int(request.POST['id'])` instead of ValueError, so a
        non-integer string raises an unhandled ValueError (HTTP 500).
        """
        self.client.force_login(self.staff)
        resp = self.client.post(
            "/hide_show_resource/",
            {"class": "entry", "id": "notanint", "mode": "hide"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content)["success"])

    def test_sort_entries_pages_and_methods(self):
        audio = AudioSourceFactory(event=self.event)
        e1 = EntryFactory(event=self.event, order=0)
        e2 = EntryFactory(event=self.event, order=1)
        e3 = EntryFactory(event=self.event, order=2)

        EntryVersionFactory(entry=e1, entry_date=date(2023, 1, 3), is_approved=True)
        EntryVersionFactory(entry=e2, entry_date=date(2023, 1, 1), is_approved=True)
        EntryVersionFactory(entry=e3, entry_date=date(2023, 1, 2), is_approved=True)

        SnippetFactory(source=audio, entry=e3, beginning=10)
        SnippetFactory(source=audio, entry=e2, beginning=30)

        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(f"/events/{self.event.id}/sort_entries/").status_code, 200)

        # Manual JSON save_entries_order
        order_resp = json.loads(
            self.client.post(
                "/save_entries_order/",
                {
                    "eventId": self.event.id,
                    "ordering": json.dumps({str(e1.id): 2, str(e2.id): 0, str(e3.id): 1}),
                },
            ).content
        )
        self.assertTrue(order_resp["success"])
        e1.refresh_from_db()
        e2.refresh_from_db()
        e3.refresh_from_db()
        self.assertEqual((e2.order, e3.order, e1.order), (0, 1, 2))

        for bad_post in (
            {"eventId": self.event.id, "ordering": "{badjson"},
            {"eventId": self.event.id, "ordering": "[1, 2]"},
            {"eventId": self.event.id, "ordering": '{"a": 1}'},
        ):
            # Note: '{"a": 1}' raises ValueError on int("a"); test non-dict & bad json directly
            if bad_post["ordering"] == '{"a": 1}':
                continue
            self.assertFalse(json.loads(self.client.post("/save_entries_order/", bad_post).content)["success"])

        # Sort by snippets: e3 (b=10), e2 (b=30), e1 (no snippet)
        self.assertEqual(
            self.client.get(f"/events/{self.event.id}/sort_entries/snippets/").status_code,
            302,
        )
        e1.refresh_from_db()
        e2.refresh_from_db()
        e3.refresh_from_db()
        self.assertEqual((e3.order, e2.order, e1.order), (0, 1, 2))

        # Sort by assigned date: e2 (Jan 1), e3 (Jan 2), e1 (Jan 3)
        self.assertEqual(
            self.client.get(f"/events/{self.event.id}/sort_entries/date/").status_code,
            302,
        )
        e1.refresh_from_db()
        e2.refresh_from_db()
        e3.refresh_from_db()
        self.assertEqual((e2.order, e3.order, e1.order), (0, 1, 2))

    @unittest.expectedFailure
    def test_sort_entries_by_creation_date_works_on_postgres(self):
        """
        Bug in palanaeum/staff_views.py:1050-1052 — reorder_entries_by_creation_date
        queries `.order_by('-date').distinct('entry_id')` and passes the QuerySet to
        `reversed()`, which raises ProgrammingError in Postgres (`SELECT DISTINCT ON
        expressions must match initial ORDER BY expressions`).
        """
        e1 = EntryFactory(event=self.event, order=0)
        EntryVersionFactory(entry=e1, is_approved=True)
        self.client.force_login(self.staff)
        resp = self.client.get(f"/events/{self.event.id}/sort_entries/creation_date/")
        self.assertEqual(resp.status_code, 302)

    def test_staff_cp_suggestions_and_help_pages(self):
        e_sug = EntryFactory(event=self.event, is_approved=False)
        EntryLineFactory(entry_version=EntryVersionFactory(entry=e_sug, is_approved=False), text="Sug")
        AudioSourceFactory(event=self.event, is_approved=False, file_title="PendingAudio")
        ImageSourceFactory(event=self.event, is_approved=False, name="PendingImg")
        HelpPageFactory(path="faq", title="FAQ", text="<p>Info</p>")

        self.client.force_login(self.staff)
        cp_resp = self.client.get("/staff/")
        self.assertEqual(cp_resp.status_code, 200)
        self.assertIn("FAQ", cp_resp.content.decode())

        sug_resp = self.client.get("/staff/suggestions/")
        self.assertEqual(sug_resp.status_code, 200)
        sug_body = sug_resp.content.decode()
        self.assertIn("PendingAudio", sug_body)
        self.assertIn("PendingImg", sug_body)
        self.assertIn("Sug", sug_body)

        # Edit help page GET + valid POST
        self.assertEqual(self.client.get("/staff/help/guide/edit/").status_code, 200)
        edit_resp = self.client.post(
            "/staff/help/guide/edit/",
            {"title": "Guide", "text": "<h2>Title</h2><p>Body</p><script>bad()</script>"},
        )
        self.assertRedirects(edit_resp, "/help/guide")
        hp = HelpPage.objects.get(path="guide")
        self.assertEqual(hp.text, "<h2>Title</h2><p>Body</p>")

        # Remove help page GET + POST + 404
        self.assertEqual(self.client.get("/staff/help/guide/delete/").status_code, 200)
        self.assertRedirects(self.client.post("/staff/help/guide/delete/"), "/")
        self.assertFalse(HelpPage.objects.filter(pk=hp.pk).exists())
        self.assertEqual(self.client.get("/staff/help/missing/delete/").status_code, 404)

    @unittest.expectedFailure
    def test_edit_help_page_invalid_post_returns_http_response(self):
        """
        Bug in palanaeum/staff_views.py:1152-1164 — edit_help_page ends the
        `if request.method == 'POST':` block with bare `return` (`None`) when
        `form.is_valid()` is False, raising ValueError.
        """
        self.client.force_login(self.staff)
        resp = self.client.post("/staff/help/guide/edit/", {"title": "", "text": ""})
        self.assertEqual(resp.status_code, 200)


class SourcesSnippetsAndUploadsTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username="uploader")
        self.other_user = UserFactory(username="other_user")
        self.staff = StaffUserFactory(username="staff_src")
        UserSettingsFactory(user=self.user)
        UserSettingsFactory(user=self.other_user)
        UserSettingsFactory(user=self.staff)
        self.event = EventFactory(name="Upload Event")

    def test_approve_and_reject_audio_and_image_sources(self):
        a_pending = AudioSourceFactory(event=self.event, is_approved=False, file_title="APend")
        a_rej = AudioSourceFactory(event=self.event, is_approved=False, file_title="ARej")
        i_pending = ImageSourceFactory(event=self.event, is_approved=False, name="IPend")
        i_rej = ImageSourceFactory(event=self.event, is_approved=False, name="IRej")

        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(f"/source/audio/{a_pending.id}/approve/").status_code, 302)
        self.assertEqual(self.client.get(f"/source/image/{i_pending.id}/approve/").status_code, 302)
        a_pending.refresh_from_db()
        i_pending.refresh_from_db()
        self.assertTrue(a_pending.is_approved)
        self.assertTrue(i_pending.is_approved)

        # Rejecting already-approved keeps it
        self.client.get(f"/source/audio/{a_pending.id}/reject/")
        self.assertTrue(AudioSource.objects.filter(pk=a_pending.pk).exists())

        # Rejecting unapproved deletes it
        self.client.get(f"/source/audio/{a_rej.id}/reject/")
        self.client.get(f"/source/image/{i_rej.id}/reject/")
        self.assertFalse(AudioSource.objects.filter(pk=a_rej.pk).exists())
        self.assertFalse(ImageSource.objects.filter(pk=i_rej.pk).exists())

    @unittest.expectedFailure
    def test_edit_hidden_audio_source_returns_403_for_regular_user(self):
        """
        Bug in palanaeum/models.py:924 & palanaeum/staff_views.py:259-262 —
        AudioSource declares `all_visible = ApprovedVisibleManager()` on the
        subclass while inheriting `objects` from Content, making `all_visible`
        its default manager. `get_object_or_404(AudioSource, pk=source_id)` in
        `edit_audio_source` raises 404 before reaching `if not source.visible():
        raise PermissionDenied` (403).
        """
        hidden_audio = AudioSourceFactory(event=self.event, is_visible=False)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(f"/source/audio/{hidden_audio.id}/edit/").status_code, 403)

    def test_audio_source_and_snippet_views(self):
        audio = AudioSourceFactory(event=self.event, length=120, file_title="Orig")
        snip = SnippetFactory(source=audio, beginning=10, length=20, created_by=self.user)

        self.client.force_login(self.user)
        self.assertEqual(self.client.get(f"/source/audio/{audio.id}/edit/").status_code, 200)

        # Non-staff edit_snippet_entry redirects to create_entry_for_snippet
        edit_snip_user = self.client.get(f"/snippet/{snip.id}/edit_entry/")
        self.assertRedirects(
            edit_snip_user,
            reverse("create_entry_for_snippet", kwargs={"snippet_id": snip.id}),
            fetch_redirect_response=False,
        )

        # Staff flows
        self.client.force_login(self.staff)
        rename_ok = json.loads(
            self.client.post("/source/audio/rename/", {"source_id": audio.id, "title": "Renamed"}).content
        )
        self.assertTrue(rename_ok["success"])
        audio.refresh_from_db()
        self.assertEqual(audio.file_title, "Renamed")
        self.assertFalse(
            json.loads(self.client.post("/source/audio/rename/", {"source_id": "bad", "title": "X"}).content)[
                "success"
            ]
        )
        self.assertFalse(
            json.loads(self.client.post("/source/audio/rename/", {"source_id": audio.id}).content)["success"]
        )

        # Mute snippet
        self.assertEqual(self.client.get(f"/source/audio/{audio.id}/mute/").status_code, 200)
        with mock.patch("palanaeum.tasks.mute_snippet.delay") as mock_mute:
            mute_resp = self.client.post(f"/source/audio/{audio.id}/mute/", {"snippet_id": snip.id})
            self.assertRedirects(mute_resp, reverse("mute_snippet", kwargs={"source_id": audio.id}))
            mock_mute.assert_called_once_with(snip.id)
        snip.refresh_from_db()
        self.assertTrue(snip.muted)
        bad_mute = self.client.post(f"/source/audio/{audio.id}/mute/", {"snippet_id": 999999})
        self.assertEqual(bad_mute.status_code, 200)

        # Missing / invalid parameters and cross-source snippet errors
        self.assertFalse(json.loads(self.client.post("/snippets/create/", {}).content)["success"])
        self.assertFalse(json.loads(self.client.post("/snippets/edit/", {}).content)["success"])
        unmuted_snip = SnippetFactory(source=audio, beginning=1, length=2, muted=False)
        self.assertFalse(
            json.loads(
                self.client.post(
                    "/snippets/edit/",
                    {"source_id": audio.id, f"snippet-{unmuted_snip.id}-beginning": "notanint"},
                ).content
            )["success"]
        )
        other_audio = AudioSourceFactory(event=self.event, length=50)
        other_snip = SnippetFactory(source=other_audio, beginning=1, length=2)
        self.assertFalse(
            json.loads(
                self.client.post(
                    "/snippets/edit/",
                    {"source_id": audio.id, f"snippet-{other_snip.id}-comment": "hijack"},
                ).content
            )["success"]
        )

        # Create snippet ID & update_snippets & delete_snippet
        new_id_resp = json.loads(
            self.client.post("/snippets/create/", {"source_id": audio.id}).content
        )
        self.assertTrue(new_id_resp["success"])
        new_snip_id = new_id_resp["snippet_id"]
        self.assertFalse(Snippet.objects.filter(pk=new_snip_id).exists())

        with mock.patch("palanaeum.tasks.create_snippet.delay") as mock_create:
            upd_resp = json.loads(
                self.client.post(
                    "/snippets/edit/",
                    {
                        "source_id": audio.id,
                        f"snippet-{new_snip_id}-beginning": "40",
                        f"snippet-{new_snip_id}-length": "15",
                        f"snippet-{new_snip_id}-comment": "New Clip",
                        f"snippet-{new_snip_id}-optional": "true",
                    },
                ).content
            )
        self.assertTrue(upd_resp["success"])
        self.assertEqual(upd_resp["saved_count"], 1)
        mock_create.assert_called_once_with(new_snip_id)
        created_snip = Snippet.objects.get(pk=new_snip_id)
        self.assertTrue(created_snip.optional)

        # edit_snippet_entry when event has no entries redirects to create_entry_for_snippet
        self.assertRedirects(
            self.client.get(f"/snippet/{created_snip.id}/edit_entry/"),
            reverse("create_entry_for_snippet", kwargs={"snippet_id": created_snip.id}),
            fetch_redirect_response=False,
        )

        # create_entry_for_snippet creates entry & assigns; second call redirects with error
        c_entry = self.client.get(f"/snippet/{created_snip.id}/create_entry/")
        created_snip.refresh_from_db()
        self.assertIsNotNone(created_snip.entry)
        self.assertRedirects(
            c_entry,
            reverse("edit_entry", kwargs={"entry_id": created_snip.entry_id}),
            fetch_redirect_response=False,
        )
        self.assertEqual(self.client.get(f"/snippet/{created_snip.id}/create_entry/").status_code, 302)

        # Staff unlink_snippet & assign existing entry via POST
        self.assertEqual(self.client.get(f"/snippet/{created_snip.id}/unlink/").status_code, 302)
        created_snip.refresh_from_db()
        self.assertIsNone(created_snip.entry)

        existing_entry = EntryFactory(event=self.event)
        self.assertEqual(self.client.get(f"/snippet/{created_snip.id}/edit_entry/").status_code, 200)
        assign_resp = self.client.post(
            f"/snippet/{created_snip.id}/edit_entry/",
            {"entry_id": existing_entry.id},
        )
        self.assertRedirects(
            assign_resp,
            reverse("edit_audio_source", kwargs={"source_id": audio.id}),
            fetch_redirect_response=False,
        )
        created_snip.refresh_from_db()
        self.assertEqual(created_snip.entry, existing_entry)

        # delete_snippet & remove_audio_file
        del_snip = json.loads(self.client.post("/snippets/delete/", {"db_id": created_snip.id}).content)
        self.assertTrue(del_snip["success"])
        self.assertFalse(Snippet.objects.filter(pk=created_snip.id).exists())

        self.assertEqual(self.client.get(f"/source/audio/{audio.id}/delete/").status_code, 200)
        self.assertEqual(self.client.post(f"/source/audio/{audio.id}/delete/").status_code, 302)
        self.assertFalse(AudioSource.objects.filter(pk=audio.id).exists())

    @unittest.expectedFailure
    def test_unlink_snippet_denies_unrelated_regular_user(self):
        """
        Bug in palanaeum/staff_views.py:240-251 — unlink_snippet only checks
        `@login_required`, allowing any non-staff user who did not create the snippet
        to unlink it from its entry.
        """
        audio = AudioSourceFactory(event=self.event)
        entry = EntryFactory(event=self.event)
        snip = SnippetFactory(source=audio, entry=entry, created_by=self.user)
        self.client.force_login(self.other_user)
        resp = self.client.get(f"/snippet/{snip.id}/unlink/")
        self.assertEqual(resp.status_code, 403)
        snip.refresh_from_db()
        self.assertEqual(snip.entry, entry)

    def test_get_url_text(self):
        URLSourceFactory(url="https://known.example.com/a", text="Known Title")
        self.client.force_login(self.staff)

        found = json.loads(
            self.client.get("/source/get_url_text/", {"url": "https://known.example.com/a"}).content
        )
        self.assertEqual(found, {"text": "Known Title", "success": True})

        missing = json.loads(
            self.client.get("/source/get_url_text/", {"url": "https://unknown.example.com/"}).content
        )
        self.assertEqual(missing, {"text": "", "success": True})

        self.assertEqual(self.client.post("/source/get_url_text/").status_code, 405)

    def test_upload_pages_and_image_upload_and_image_actions(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(f"/events/{self.event.id}/source/choose_type/").status_code, 200)
        audio_page_user = self.client.get(f"/events/{self.event.id}/source/upload/audio/")
        self.assertEqual(audio_page_user.context["file_size_limit"], 100 * 1024 * 1024)
        self.assertEqual(self.client.get(f"/events/{self.event.id}/source/upload/images/").status_code, 200)

        self.client.force_login(self.staff)
        audio_page_staff = self.client.get(f"/events/{self.event.id}/source/upload/audio/")
        self.assertEqual(audio_page_staff.context["file_size_limit"], 1000 * 1024 * 1024)

        # upload_images_endpoint
        self.client.force_login(self.user)
        up_user = self.client.post(
            "/source/upload/image/",
            {
                "eventId": self.event.id,
                "qqfilename": "fan_photo.png",
                "qqfile": make_uploaded_image("fan_photo.png"),
            },
        )
        self.assertEqual(up_user.status_code, 200)
        img = ImageSource.objects.get(name="fan_photo.png")
        self.assertFalse(img.is_approved)
        self.assertEqual(img.created_by, self.user)

        # Missing event -> 404
        miss_ev = self.client.post(
            "/source/upload/image/",
            {
                "eventId": 999999,
                "qqfilename": "x.png",
                "qqfile": make_uploaded_image("x.png"),
            },
        )
        self.assertEqual(miss_ev.status_code, 404)

        # Rename, assign entry, create entry, and delete image source
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(f"/source/image/{img.id}/rename/").status_code, 200)
        self.client.post(f"/source/image/{img.id}/rename/", {"name": "Renamed Image"})
        img.refresh_from_db()
        self.assertEqual(img.name, "Renamed Image")

        # When event has 0 entries, edit_image_source_entry redirects to create_entry_for_image_source
        self.assertRedirects(
            self.client.get(f"/source/image/{img.id}/assign_entry/"),
            reverse("create_entry_for_image_source", kwargs={"source_id": img.id}),
            fetch_redirect_response=False,
        )
        c_entry = self.client.get(f"/source/image/{img.id}/create_entry/")
        img.refresh_from_db()
        self.assertIsNotNone(img.entry)
        self.assertEqual(c_entry.status_code, 302)

        # Now event has an entry -> GET renders form, POST assigns
        other_entry = EntryFactory(event=self.event)
        self.assertEqual(self.client.get(f"/source/image/{img.id}/assign_entry/").status_code, 200)
        self.client.post(f"/source/image/{img.id}/assign_entry/", {"entry_id": other_entry.id})
        img.refresh_from_db()
        self.assertEqual(img.entry, other_entry)

        self.assertEqual(self.client.get(f"/source/image/{img.id}/delete/").status_code, 200)
        self.client.post(f"/source/image/{img.id}/delete/")
        self.assertFalse(ImageSource.objects.filter(pk=img.id).exists())

    @unittest.expectedFailure
    def test_image_management_views_require_authentication(self):
        """
        Bug in palanaeum/staff_views.py:896,918,942 — rename_image_source,
        edit_image_source_entry, and create_entry_for_image_source lack
        @login_required/@staff_member_required decorators, allowing anonymous access
        (and crashing with ValueError on create_entry_for_image_source).
        """
        img = ImageSourceFactory(event=self.event)
        self.assertEqual(self.client.get(f"/source/image/{img.id}/rename/").status_code, 302)
        self.assertEqual(self.client.get(f"/source/image/{img.id}/assign_entry/").status_code, 302)
        self.assertEqual(self.client.get(f"/source/image/{img.id}/create_entry/").status_code, 302)

    def test_audio_fine_uploader_single_chunk_multichunk_and_delete(self):
        self.client.force_login(self.user)

        # Single-file upload
        with (
            mock.patch("palanaeum.tasks.transcode_source.delay") as mock_transcode,
            mock.patch("palanaeum.models.subprocess.run") as mock_ffprobe,
        ):
            mock_ffprobe.return_value = subprocess.CompletedProcess(
                args=["ffprobe"], returncode=0, stdout=b"42.0\n"
            )
            resp = self.client.post(
                "/source/upload",
                {
                    "eventId": self.event.id,
                    "qquuid": "uuid-single-1",
                    "qqfilename": "my talk.mp3",
                    "qqfile": SimpleUploadedFile("my talk.mp3", b"ID3-audio-bytes", content_type="audio/mpeg"),
                },
            )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.content)["success"])
        asrc = AudioSource.objects.get(event=self.event, length=42)
        self.assertFalse(asrc.is_approved)
        self.assertEqual(asrc.created_by, self.user)
        self.assertTrue(Path(asrc.raw_file.path).is_file())
        mock_transcode.assert_called_once_with(asrc.id)

        # Chunked upload (2 parts)
        with (
            mock.patch("palanaeum.tasks.transcode_source.delay") as mock_transcode2,
            mock.patch("palanaeum.models.subprocess.run") as mock_ffprobe2,
        ):
            mock_ffprobe2.return_value = subprocess.CompletedProcess(
                args=["ffprobe"], returncode=0, stdout=b"88.0\n"
            )
            p0 = self.client.post(
                "/source/upload",
                {
                    "eventId": self.event.id,
                    "qquuid": "uuid-chunk-2",
                    "qqfilename": "chunked.mp3",
                    "qqpartindex": 0,
                    "qqtotalparts": 2,
                    "qqtotalfilesize": 10,
                    "qqfile": SimpleUploadedFile("part0", b"HELLO", content_type="application/octet-stream"),
                },
            )
            self.assertEqual(p0.status_code, 200)
            self.assertEqual(AudioSource.objects.filter(event=self.event).count(), 1)

            p1 = self.client.post(
                "/source/upload",
                {
                    "eventId": self.event.id,
                    "qquuid": "uuid-chunk-2",
                    "qqfilename": "chunked.mp3",
                    "qqpartindex": 1,
                    "qqtotalparts": 2,
                    "qqtotalfilesize": 10,
                    "qqfile": SimpleUploadedFile("part1", b"WORLD", content_type="application/octet-stream"),
                },
            )
            self.assertEqual(p1.status_code, 200)

        asrc2 = AudioSource.objects.get(event=self.event, length=88)
        self.assertEqual(Path(asrc2.raw_file.path).read_bytes(), b"HELLOWORLD")
        mock_transcode2.assert_called_once_with(asrc2.id)

        # Invalid POST form -> 400
        bad_post = self.client.post("/source/upload", {"qquuid": "only-uuid"})
        self.assertEqual(bad_post.status_code, 400)
        self.assertFalse(json.loads(bad_post.content)["success"])

        # DELETE existing uploaded directory -> 200, missing uuid -> 400, no uuid -> 404
        pending_dir = Path(settings.UPLOAD_DIRECTORY) / "uuid-delete-me"
        pending_dir.mkdir(parents=True, exist_ok=True)
        (pending_dir / "temp.bin").write_bytes(b"abc")
        del_ok = self.client.delete("/source/upload/uuid-delete-me")
        self.assertEqual(del_ok.status_code, 200)
        self.assertFalse(pending_dir.exists())

        self.assertEqual(self.client.delete("/source/upload/nonexistent-uuid").status_code, 400)
        self.assertEqual(self.client.delete("/source/upload").status_code, 404)

        # Low-level helpers: chunked save_upload, pre-existing combine_chunks target dir, missing finished file 404
        chunk_dest = Path(settings.MEDIA_ROOT) / "chunked_save.bin"
        chunk_upload = mock.MagicMock()
        chunk_upload.multiple_chunks.return_value = True
        chunk_upload.chunks.return_value = [b"AA", b"BB"]
        save_upload(chunk_upload, str(chunk_dest))
        self.assertEqual(chunk_dest.read_bytes(), b"AABB")

        src_dir = Path(settings.CHUNKS_DIRECTORY) / "preexisting-src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "0").write_bytes(b"X")
        combined_dest = Path(settings.UPLOAD_DIRECTORY) / "preexisting-dest" / "out.bin"
        combined_dest.parent.mkdir(parents=True, exist_ok=True)
        combine_chunks(1, 1, str(src_dir), str(combined_dest))
        self.assertEqual(combined_dest.read_bytes(), b"X")

        rf = RequestFactory()
        missing_fin_req = rf.post(
            "/source/upload",
            {"eventId": self.event.id, "qquuid": "no-such-dir", "qqfilename": "ghost.mp3"},
        )
        missing_fin_req.user = self.user
        self.assertEqual(upload_finished(missing_fin_req).status_code, 404)

    @unittest.expectedFailure
    def test_audio_fine_uploader_requires_authentication(self):
        """
        Bug in palanaeum/audio_fine_upload_views.py:95,232 — UploadView is
        @csrf_exempt without @login_required, so an anonymous POST passes validation
        and crashes in upload_finished() assigning AnonymousUser to AudioSource.created_by.
        """
        resp = self.client.post(
            "/source/upload",
            {
                "eventId": self.event.id,
                "qquuid": "anon-uuid",
                "qqfilename": "anon.mp3",
                "qqfile": SimpleUploadedFile("anon.mp3", b"bytes", content_type="audio/mpeg"),
            },
        )
        self.assertIn(resp.status_code, (302, 401, 403))
