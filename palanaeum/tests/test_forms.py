import unittest
from datetime import date

from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, SimpleTestCase, TestCase

from palanaeum.audio_fine_upload_views import UploadFileForm
from palanaeum.forms import (
    AudioConfig,
    CloudConfig,
    EmailChangeForm,
    EventForm,
    FaviconsConfig,
    GeneralConfig,
    HelpPageForm,
    ImageConfig,
    ImageRenameForm,
    RelatedSiteForm,
    SortForm,
    UserCreationFormWithEmail,
    UserSettingsForm,
    UsersEntryCollectionForm,
)
from palanaeum.models import Event, HelpPage, Tag
from palanaeum.tests.base import make_uploaded_image, set_current_request
from palanaeum.tests.factories import (
    HelpPageFactory,
    ImageSourceFactory,
    StaffUserFactory,
    UserFactory,
    UserSettingsFactory,
    UsersEntryCollectionFactory,
)


class AuthAndSettingsFormTests(TestCase):
    def test_user_creation_form_with_email(self):
        UserFactory(username="taken", email="dup@example.com")
        bad_form = UserCreationFormWithEmail({
            "username": "newuser",
            "email": "dup@example.com",
            "password1": "Str0ng!Pass#99",
            "password2": "Str0ng!Pass#99",
        })
        self.assertFalse(bad_form.is_valid())
        self.assertIn("email", bad_form.errors)

        good_form = UserCreationFormWithEmail({
            "username": "newuser",
            "email": "fresh@example.com",
            "password1": "Str0ng!Pass#99",
            "password2": "Str0ng!Pass#99",
        })
        self.assertTrue(good_form.is_valid(), good_form.errors)
        created = good_form.save()
        self.assertEqual(created.email, "fresh@example.com")

    def test_email_change_form_validation_and_save(self):
        user = UserFactory(username="alice", email="alice@example.com")
        user.set_password("secret123")
        user.save()
        UserFactory(username="bob", email="bob@example.com")

        with self.assertRaises(AssertionError):
            EmailChangeForm()

        # Same email requires no password
        same_form = EmailChangeForm(
            {"email": "alice@example.com", "password": ""},
            user=user,
        )
        self.assertTrue(same_form.is_valid(), same_form.errors)

        # Duplicate email fails
        dup_form = EmailChangeForm(
            {"email": "bob@example.com", "password": "secret123"},
            user=user,
        )
        self.assertFalse(dup_form.is_valid())
        self.assertIn("email", dup_form.errors)

        # Wrong password when changing email fails
        bad_pw_form = EmailChangeForm(
            {"email": "alice2@example.com", "password": "wrong"},
            user=user,
        )
        self.assertFalse(bad_pw_form.is_valid())
        self.assertIn("password", bad_pw_form.errors)

        # Valid email change saves
        ok_form = EmailChangeForm(
            {"email": "alice2@example.com", "password": "secret123"},
            user=user,
        )
        self.assertTrue(ok_form.is_valid(), ok_form.errors)
        ok_form.save()
        user.refresh_from_db()
        self.assertEqual(user.email, "alice2@example.com")

    def test_user_settings_form_bounds(self):
        us = UserSettingsFactory()
        self.assertFalse(
            UserSettingsForm({"timezone": "UTC", "page_length": 9, "website": ""}, instance=us).is_valid()
        )
        self.assertFalse(
            UserSettingsForm({"timezone": "UTC", "page_length": 101, "website": ""}, instance=us).is_valid()
        )
        self.assertFalse(
            UserSettingsForm({"timezone": "Invalid/Zone", "page_length": 20, "website": ""}, instance=us).is_valid()
        )
        for edge in (10, 100):
            form = UserSettingsForm(
                {"timezone": "Europe/Warsaw", "page_length": edge, "website": "https://example.com"},
                instance=us,
            )
            self.assertTrue(form.is_valid(), form.errors)


class EventAndModelFormTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.staff = StaffUserFactory()

    def test_event_form_staff_tags_attr_and_save(self):
        with set_current_request(self.user):
            user_form = EventForm()
            self.assertNotIn("data-tags", user_form.fields["tags"].widget.attrs)

        with set_current_request(self.staff) as req:
            req.session = {}
            req._messages = FallbackStorage(req)

            staff_form = EventForm(
                data={
                    "name": "Dragonsteel Con",
                    "date": "2024-12-05",
                    "review_state": Event.REVIEW_APPROVED,
                    "location": "Salt Lake City",
                    "tour": "Wind and Truth",
                    "bookstore": "",
                    "meta": "Notes",
                    "tags": "['cosmere']",
                    "update_entry_dates": True,
                }
            )
            self.assertEqual(staff_form.fields["tags"].widget.attrs.get("data-tags"), "true")
            self.assertTrue(staff_form.is_valid(), staff_form.errors)
            event = staff_form.save()
            self.assertEqual(event.name, "Dragonsteel Con")
            self.assertEqual(event.date, date(2024, 12, 5))
            self.assertEqual(set(event.tags.values_list("name", flat=True)), {"cosmere"})
            msgs = [str(m) for m in get_messages(req)]
            self.assertTrue(any("update entry dates" in m.lower() for m in msgs))

    @unittest.expectedFailure
    def test_event_form_save_multiple_tags_strips_whitespace_around_quotes(self):
        """
        Bug in palanaeum/forms.py:130-131 — EventForm.save splits `cleaned_data['tags'][1:-1]`
        on ',' and strips quotes without first stripping spaces, leaving a leading quote
        on every tag after the first (e.g. " 'stormlight'" -> "'stormlight").
        """
        with set_current_request(self.staff) as req:
            req.session = {}
            req._messages = FallbackStorage(req)
            form = EventForm(
                data={
                    "name": "Multi Tag Event",
                    "date": "2024-12-06",
                    "review_state": Event.REVIEW_NA,
                    "tags": "['cosmere', 'stormlight']",
                }
            )
            self.assertTrue(form.is_valid(), form.errors)
            event = form.save()
            self.assertEqual(set(event.tags.values_list("name", flat=True)), {"cosmere", "stormlight"})

    @unittest.expectedFailure
    def test_event_form_without_request_does_not_crash(self):
        """
        Bug in palanaeum/forms.py:119-120 — EventForm.__init__ reads
        `get_request().user.is_staff` without checking if `get_request()` is None,
        raising AttributeError when instantiated outside a request context.
        """
        EventForm()

    def test_image_rename_related_site_collection_and_help_page_forms(self):
        img = ImageSourceFactory(name="Old Name")
        rename_form = ImageRenameForm({"name": "New Name"}, instance=img)
        self.assertTrue(rename_form.is_valid())
        self.assertEqual(rename_form.save().name, "New Name")

        site_form = RelatedSiteForm(
            data={"name": "17th Shard", "url": "https://17thshard.com/", "order": 1},
            files={"image": make_uploaded_image("17s.png")},
        )
        self.assertTrue(site_form.is_valid(), site_form.errors)
        site = site_form.save()
        self.assertEqual(site.name, "17th Shard")
        site.delete()

        coll = UsersEntryCollectionFactory(user=self.user)
        coll_form = UsersEntryCollectionForm(
            {"name": "Favorites", "description": "<b>Best</b>", "public": True},
            instance=coll,
        )
        self.assertTrue(coll_form.is_valid())
        saved_coll = coll_form.save()
        self.assertTrue(saved_coll.public)

        hp = HelpPageFactory(path="about", title="About", text="Old")
        hp_form = HelpPageForm(
            {"path": "tampered", "title": "New About", "text": "<p>Updated</p>"},
            instance=hp,
        )
        self.assertTrue(hp_form.fields["path"].disabled)
        self.assertTrue(hp_form.is_valid(), hp_form.errors)
        saved_hp = hp_form.save()
        self.assertEqual(saved_hp.path, "about")
        self.assertEqual(saved_hp.title, "New About")


class SortConfigAndUploadFormTests(SimpleTestCase):
    def test_sort_form(self):
        choices = (("name", "name"), ("date", "date"))
        self.assertTrue(SortForm(choices, {"sort_by": "date", "sort_ord": "-"}).is_valid())
        self.assertTrue(SortForm(choices, {"sort_by": "name", "sort_ord": ""}).is_valid())
        self.assertFalse(SortForm(choices, {"sort_by": "unknown", "sort_ord": "-"}).is_valid())

    def test_admin_config_forms(self):
        self.assertTrue(
            GeneralConfig({
                "page_title": "Palanaeum",
                "index_hello": "Welcome",
                "default_page_length": 20,
                "google_analytics": "",
                "approval_message": "Reviewed",
                "review_pending_explanation": "",
                "review_reviewed_explanation": "",
            }).is_valid()
        )
        self.assertFalse(
            GeneralConfig({
                "page_title": "Palanaeum",
                "index_hello": "Welcome",
                "default_page_length": 5,
                "approval_message": "Reviewed",
            }).is_valid()
        )

        self.assertTrue(FaviconsConfig({}).is_valid())
        self.assertTrue(
            FaviconsConfig({}, files={"favicon16": make_uploaded_image("f16.png")}).is_valid()
        )

        self.assertTrue(
            AudioConfig({
                "audio_keep_original_file": True,
                "audio_quality": "128k",
                "audio_staff_size_limit": 1000,
                "audio_user_size_limit": 100,
            }).is_valid()
        )
        self.assertFalse(
            AudioConfig({
                "audio_quality": "999k",
                "audio_staff_size_limit": 5,
                "audio_user_size_limit": 2500,
            }).is_valid()
        )

        self.assertTrue(ImageConfig({"image_size_limit": 10}).is_valid())
        self.assertFalse(ImageConfig({"image_size_limit": 0}).is_valid())
        self.assertFalse(ImageConfig({"image_size_limit": 21}).is_valid())

        self.assertTrue(CloudConfig({"cloud_backend": "b2", "cloud_b2_bucket_id": "bucket123"}).is_valid())
        self.assertFalse(CloudConfig({"cloud_backend": "s3"}).is_valid())

    def test_upload_file_form(self):
        valid_form = UploadFileForm(
            data={
                "qquuid": "1111-2222",
                "qqfilename": "recording.mp3",
                "qqpartindex": 0,
                "qqtotalparts": 2,
                "qqtotalfilesize": 2048,
            },
            files={"qqfile": make_uploaded_image("recording.mp3")},
        )
        self.assertTrue(valid_form.is_valid(), valid_form.errors)

        missing_file = UploadFileForm(data={"qquuid": "1111-2222", "qqfilename": "recording.mp3"})
        self.assertFalse(missing_file.is_valid())
        self.assertIn("qqfile", missing_file.errors)
