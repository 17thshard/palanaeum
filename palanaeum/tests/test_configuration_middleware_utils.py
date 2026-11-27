import json
import unittest
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import caches
from django.core.paginator import Paginator
from django.db import ProgrammingError
from django.http import HttpResponse, HttpResponseRedirect
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from palanaeum import configuration, context_processors, middleware, utils
from palanaeum.decorators import AjaxException, json_response
from palanaeum.models import ConfigEntry, NavbarItem, UserSettings
from palanaeum.tests.base import make_LocMem_caches_setting, make_uploaded_image
from palanaeum.tests.factories import (
    AudioSourceFactory,
    EntryFactory,
    EntryVersionFactory,
    ImageSourceFactory,
    NavbarItemFactory,
    StaffUserFactory,
    UserFactory,
    UserSettingsFactory,
)


@override_settings(CACHES=make_LocMem_caches_setting("cfg-tests"))
class ConfigurationTests(TestCase):
    def tearDown(self):
        caches["config"].clear()
        super().tearDown()

    def test_config_update_populates_missing_without_overwriting_existing(self):
        ConfigEntry.objects.filter(key="page_title").delete()
        configuration.set_config("index_hello", "Custom hello")
        configuration.config_update()

        self.assertEqual(
            ConfigEntry.objects.get(key="page_title").value,
            "Palanaeum",
        )
        self.assertEqual(
            ConfigEntry.objects.get(key="index_hello").value,
            "Custom hello",
        )

    def test_serialize_and_deserialize_all_types_and_unknown_type(self):
        self.assertEqual(configuration._serialize_value("page_title", "X"), "X")
        self.assertEqual(configuration._deserialize_value("page_title", "X"), "X")

        self.assertEqual(configuration._serialize_value("default_page_length", 35), "35")
        self.assertEqual(configuration._deserialize_value("default_page_length", "35"), 35)

        self.assertEqual(configuration._serialize_value("audio_keep_original_file", True), "1")
        self.assertEqual(configuration._serialize_value("audio_keep_original_file", False), "0")
        self.assertTrue(configuration._deserialize_value("audio_keep_original_file", "1"))
        self.assertFalse(configuration._deserialize_value("audio_keep_original_file", "0"))

        self.assertIsNone(configuration._deserialize_value("logo_file", ""))
        self.assertEqual(
            configuration._deserialize_value("logo_file", "config/logo.png"),
            "/media/config/logo.png",
        )

        with mock.patch.dict(configuration.CONFIG_ENTRIES, {"bad_key": ("float", 1.5)}):
            with self.assertRaises(NotImplementedError):
                configuration._serialize_value("bad_key", 1.5)
            with self.assertRaises(NotImplementedError):
                configuration._deserialize_value("bad_key", "1.5")

    def test_get_config_cache_hit_miss_and_does_not_exist(self):
        ConfigEntry.objects.filter(key="page_title").delete()
        caches["config"].clear()

        # Falls back to default when row doesn't exist
        self.assertEqual(configuration.get_config("page_title"), "Palanaeum")

        # Miss populates cache from DB
        ConfigEntry.objects.create(key="page_title", value="Shard Archive")
        self.assertEqual(configuration.get_config("page_title"), "Shard Archive")

        # Subsequent call hits cache without DB queries
        with self.assertNumQueries(0):
            self.assertEqual(configuration.get_config("page_title"), "Shard Archive")

    def test_get_config_programming_error_returns_none(self):
        caches["config"].clear()
        with (
            mock.patch.object(ConfigEntry.objects, "get", side_effect=ProgrammingError("missing table")),
            self.assertLogs("palanaeum.admin", level="ERROR"),
        ):
            self.assertIsNone(configuration.get_config("page_title"))

    def test_set_config_and_get_config_dict(self):
        configuration.set_config("audio_keep_original_file", False)
        configuration.set_config("default_page_length", 40)

        cfg = configuration.get_config_dict()
        self.assertFalse(cfg["audio_keep_original_file"])
        self.assertEqual(cfg["default_page_length"], 40)
        self.assertEqual(caches["config"].get("audio_keep_original_file"), "0")

    def test_set_config_file_creates_overwrites_unlinks_and_handles_missing(self):
        # 1. Existing entry with empty value
        img1 = make_uploaded_image(name="logo1.png")
        configuration.set_config_file("logo_file", img1)
        first_path = Path(settings.CONFIG_UPLOADS) / "logo1.png"
        self.assertTrue(first_path.is_file())
        self.assertEqual(configuration.get_config("logo_file"), "/media/config/logo1.png")

        # 2. Overwrite unlinks previous file
        img2 = make_uploaded_image(name="logo2.png")
        configuration.set_config_file("logo_file", img2)
        second_path = Path(settings.CONFIG_UPLOADS) / "logo2.png"
        self.assertFalse(first_path.exists())
        self.assertTrue(second_path.is_file())

        # 3. Missing file on disk is ignored
        second_path.unlink()
        img3 = make_uploaded_image(name="logo3.png")
        configuration.set_config_file("logo_file", img3)
        self.assertTrue((Path(settings.CONFIG_UPLOADS) / "logo3.png").is_file())

        # 4. Missing ConfigEntry row is created cleanly
        ConfigEntry.objects.filter(key="favicon16").delete()
        caches["config"].delete("favicon16")
        fav = make_uploaded_image(name="fav16.png")
        configuration.set_config_file("favicon16", fav)
        self.assertEqual(configuration.get_config("favicon16"), "/media/config/fav16.png")


class MiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_timezone_middleware_anonymous_deactivates(self):
        timezone.activate("America/New_York")
        req = self.factory.get("/")
        req.user = AnonymousUser()

        seen_tz = []

        def get_response(_request):
            seen_tz.append(timezone.get_current_timezone_name())
            return HttpResponse("ok")

        mw = middleware.TimezoneMiddleware(get_response)
        mw(req)
        self.assertEqual(seen_tz, ["UTC"])

    def test_timezone_middleware_authenticated_with_settings(self):
        user = UserFactory()
        UserSettingsFactory(user=user, timezone="Europe/Warsaw")
        req = self.factory.get("/")
        req.user = user

        seen_tz = []

        def get_response(_request):
            seen_tz.append(timezone.get_current_timezone_name())
            return HttpResponse("ok")

        mw = middleware.TimezoneMiddleware(get_response)
        mw(req)
        self.assertEqual(seen_tz, ["Europe/Warsaw"])

    def test_timezone_middleware_auto_creates_missing_user_settings(self):
        user = UserFactory()
        self.assertFalse(UserSettings.objects.filter(user=user).exists())
        req = self.factory.get("/")
        req.user = user

        mw = middleware.TimezoneMiddleware(lambda _r: HttpResponse("ok"))
        mw(req)
        self.assertTrue(UserSettings.objects.filter(user=user).exists())
        self.assertEqual(timezone.get_current_timezone_name(), "UTC")

    def test_global_request_keeper_sets_request_during_call(self):
        user = UserFactory()
        req = self.factory.get("/events/")
        req.user = user

        observed = {}

        def get_response(_request):
            observed["request"] = middleware.get_request()
            return HttpResponse("ok")

        mw = middleware.GlobalRequestKeeper(get_response)
        mw(req)
        self.assertIs(observed["request"], req)

    @unittest.expectedFailure
    def test_global_request_keeper_clears_request_after_response(self):
        """
        Bug in palanaeum/middleware.py:42-45 — GlobalRequestKeeper.__call__ stores
        the request in _GLOBAL_REQUEST_BOX.request but never clears it after
        get_response(request) returns, leaking thread-local state across requests.
        """
        req = self.factory.get("/")
        req.user = UserFactory()
        mw = middleware.GlobalRequestKeeper(lambda _r: HttpResponse("ok"))
        mw(req)
        self.assertIsNone(middleware.get_request())


class DecoratorsTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_json_response_dict_adds_success_true(self):
        @json_response
        def view(_request):
            return {"count": 3}

        resp = view(self.factory.get("/"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertEqual(json.loads(resp.content), {"count": 3, "success": True})

    def test_json_response_preserves_existing_success_key(self):
        @json_response
        def view(_request):
            return {"success": False, "custom": 1}

        resp = view(self.factory.get("/"))
        self.assertEqual(json.loads(resp.content), {"success": False, "custom": 1})

    def test_json_response_none_returns_success_true(self):
        @json_response
        def view(_request):
            return None

        resp = view(self.factory.get("/"))
        self.assertEqual(json.loads(resp.content), {"success": True})

    def test_json_response_catches_ajax_exception(self):
        @json_response
        def view(_request):
            raise AjaxException("invalid id")

        resp = view(self.factory.get("/"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content), {"success": False, "reason": "invalid id"})

    def test_json_response_passes_through_http_responses_and_warns_on_200(self):
        @json_response
        def redirect_view(_request):
            return HttpResponseRedirect("/login/")

        redirect_resp = redirect_view(self.factory.get("/"))
        self.assertEqual(redirect_resp.status_code, 302)

        @json_response
        def plain_view(_request):
            return HttpResponse("raw", status=200)

        with self.assertLogs("palanaeum", level="WARNING"):
            plain_resp = plain_view(self.factory.get("/"))
        self.assertEqual(plain_resp.status_code, 200)
        self.assertEqual(plain_resp.content, b"raw")

    @unittest.expectedFailure
    def test_ajax_exception_inherits_exception_and_sets_args(self):
        """
        Bug in palanaeum/decorators.py:8-17 — AjaxException inherits from
        BaseException instead of Exception and calls super(AjaxException).__init__()
        instead of super().__init__(msg).
        """
        err = AjaxException("boom")
        self.assertIsInstance(err, Exception)
        self.assertEqual(str(err), "boom")


class ContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Ensure predictable suggestions count
        entry_multi = EntryFactory(is_approved=False)
        EntryVersionFactory(entry=entry_multi, is_approved=False)
        EntryVersionFactory(entry=entry_multi, is_approved=False)
        AudioSourceFactory(is_approved=False)
        ImageSourceFactory(is_approved=False)
        # Approved items must not count
        approved_entry = EntryFactory(is_approved=True)
        EntryVersionFactory(entry=approved_entry, is_approved=True)
        AudioSourceFactory(is_approved=True)
        ImageSourceFactory(is_approved=True)

    def test_palanaeum_context_anonymous_and_regular_user(self):
        req = self.factory.get("/events/", HTTP_HOST="testserver")
        req.user = AnonymousUser()
        ctx = context_processors.palanaeum_context(req)
        self.assertFalse(ctx["STAFF"])
        self.assertEqual(ctx["SUGGESTIONS_COUNT"], 0)
        self.assertEqual(ctx["BASE_URL"], "http://testserver")
        self.assertEqual(ctx["GENERAL_SEARCH_PARAM_NAME"], "query")
        self.assertEqual(ctx["PALANAEUM_VERSION"], settings.PALANAEUM_VERSION)
        self.assertEqual(ctx["PALANAEUM_STYLE"], settings.PALANAEUM_STYLE)
        self.assertIn("palanaeum_logo.svg", ctx["PALANAEUM_LOGO_URL"])
        for size in (16, 32, 96, 120, 152, 167, 180, 200):
            self.assertIn(f"favicon{size}.png", ctx[f"FAVICON{size}"])

        req.user = UserFactory()
        ctx_user = context_processors.palanaeum_context(req)
        self.assertFalse(ctx_user["STAFF"])
        self.assertEqual(ctx_user["SUGGESTIONS_COUNT"], 0)

    def test_palanaeum_context_staff_counts_distinct_suggestions_and_custom_logo(self):
        NavbarItemFactory(label="Custom Nav")
        configuration.set_config_file("logo_file", make_uploaded_image(name="custom_logo.png"))
        req = self.factory.get("/", HTTP_HOST="testserver")
        req.user = StaffUserFactory()

        ctx = context_processors.palanaeum_context(req)
        self.assertTrue(ctx["STAFF"])
        # 1 distinct Entry with 2 unapproved versions + 1 AudioSource + 1 ImageSource = 3
        self.assertEqual(ctx["SUGGESTIONS_COUNT"], 3)
        self.assertEqual(ctx["PALANAEUM_LOGO_URL"], "/media/config/custom_logo.png")
        self.assertEqual(list(ctx["NAVBAR_ITEMS"]), list(NavbarItem.objects.all()))


class UtilsTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_clean_html_sanitizes_xss_and_allows_safe_markup(self):
        raw = (
            '<p>Keep?</p><b>Bold</b> '
            '<a href="https://example.com" title="ok" onclick="evil()">Link</a> '
            '<a href="javascript:alert(1)">Bad</a> '
            '<script>alert(1)</script><!-- secret -->'
        )
        cleaned = utils.clean_html(raw)
        self.assertNotIn("<script>", cleaned)
        self.assertNotIn("onclick", cleaned)
        self.assertNotIn("javascript:", cleaned)
        self.assertNotIn("secret", cleaned)
        self.assertNotIn("<p>", cleaned)
        self.assertIn("<b>Bold</b>", cleaned)
        self.assertIn('href="https://example.com"', cleaned)
        self.assertIn('title="ok"', cleaned)

        self.assertEqual(utils.clean_html("<b>Hi</b>", tags=set()), "Hi")
        self.assertEqual(
            utils.clean_html("<p>Hi</p>", tags=utils.ALLOWED_HTML_TAGS | {"p"}),
            "<p>Hi</p>",
        )

    def test_is_contributor(self):
        req_no_user = self.factory.get("/")
        self.assertFalse(utils.is_contributor(req_no_user))

        req_anon = self.factory.get("/")
        req_anon.user = AnonymousUser()
        self.assertFalse(utils.is_contributor(req_anon))

        req_auth = self.factory.get("/")
        req_auth.user = UserFactory.build()
        self.assertTrue(utils.is_contributor(req_auth))

    def test_page_numbers_to_show(self):
        p_single = Paginator(list(range(5)), 10)
        self.assertEqual(utils.page_numbers_to_show(p_single, 1), [1])

        p_small = Paginator(list(range(50)), 10)
        self.assertEqual(utils.page_numbers_to_show(p_small, 3), [1, 2, 3, 4, 5])

        p_large = Paginator(list(range(200)), 10)  # 20 pages
        self.assertEqual(
            utils.page_numbers_to_show(p_large, 1),
            [1, 2, 3, 0, -4, -5, -6, -7, -8, -9, -10, -11, -12, -13, -14, -15, -16, -17, -18, 19, 20],
        )
        self.assertEqual(
            utils.page_numbers_to_show(p_large, 10),
            [1, 2, 0, -3, -4, -5, -6, -7, 8, 9, 10, 11, 12, 0, -13, -14, -15, -16, -17, -18, 19, 20],
        )
        self.assertEqual(
            utils.page_numbers_to_show(p_large, 20),
            [1, 2, 0, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12, -13, -14, -15, -16, -17, 18, 19, 20],
        )
