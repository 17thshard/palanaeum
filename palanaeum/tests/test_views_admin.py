import json
import unittest
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from palanaeum import configuration
from palanaeum.models import ConfigEntry, Link, NavbarItem, RelatedSite
from palanaeum.tests.base import make_uploaded_image
from palanaeum.tests.factories import (
    RelatedSiteFactory,
    StaffUserFactory,
    SuperUserFactory,
    UserFactory,
    UserSettingsFactory,
)


class AdminViewsTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username="regular")
        self.staff = StaffUserFactory(username="staff_only")
        self.superuser = SuperUserFactory(username="super")
        UserSettingsFactory(user=self.user)
        UserSettingsFactory(user=self.staff)
        UserSettingsFactory(user=self.superuser)

    def test_superuser_access_matrix(self):
        auth_login_routes = ["/admin/", "/admin/config/"]
        default_login_routes = [
            "/admin/users/",
            "/admin/realted_sites/",
            "/admin/navbar/",
            "/admin/config/reset_favicons/",
        ]

        # Anonymous, regular user, and non-superuser staff are redirected
        for actor in (None, self.user, self.staff):
            if actor is not None:
                self.client.force_login(actor)
            else:
                self.client.logout()
            for url in auth_login_routes + default_login_routes:
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 302, f"{url} allowed {actor}")

        # Superuser gets 200 on index, config, users, related_sites, navbar
        self.client.force_login(self.superuser)
        for url in [
            "/admin/",
            "/admin/config/",
            "/admin/users/",
            "/admin/realted_sites/",
            "/admin/navbar/",
        ]:
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_admin_index_disk_usage(self):
        sample_file = Path(settings.MEDIA_ROOT) / "sample_usage.bin"
        sample_file.parent.mkdir(parents=True, exist_ok=True)
        sample_file.write_bytes(b"0" * 1024)

        self.client.force_login(self.superuser)
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(resp.context["total_space"], 0)
        self.assertGreaterEqual(resp.context["available_space"], 0)
        self.assertIn("Gb", resp.context["total_space_str"])

    def test_admin_config_and_reset_favicons(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get("/admin/config/").status_code, 200)

        # Invalid POST leaves config unchanged
        bad_resp = self.client.post(
            "/admin/config/",
            {
                "page_title": "Changed",
                "index_hello": "Hi",
                "default_page_length": "999",  # max is 100
                "approval_message": "OK",
                "audio_quality": "128k",
                "audio_staff_size_limit": "500",
                "audio_user_size_limit": "50",
            },
        )
        self.assertEqual(bad_resp.status_code, 200)
        self.assertEqual(configuration.get_config("page_title"), "Palanaeum")

        # Valid POST saves all forms + file uploads
        good_resp = self.client.post(
            "/admin/config/",
            {
                "page_title": "Cosmere Archive",
                "index_hello": "Welcome!",
                "default_page_length": "30",
                "google_analytics": "G-TEST123",
                "approval_message": "Verified",
                "review_pending_explanation": "Pending.",
                "review_reviewed_explanation": "Done.",
                "audio_keep_original_file": "",
                "audio_quality": "96k",
                "audio_staff_size_limit": "500",
                "audio_user_size_limit": "50",
                "cloud_backend": "b2",
                "cloud_login": "id1",
                "cloud_passwd": "pw1",
                "cloud_b2_bucket_id": "bucket1",
                "logo_file": make_uploaded_image("site_logo.png"),
                "favicon16": make_uploaded_image("fav16.png"),
            },
        )
        self.assertEqual(good_resp.status_code, 200)
        self.assertEqual(configuration.get_config("page_title"), "Cosmere Archive")
        self.assertEqual(configuration.get_config("default_page_length"), 30)
        self.assertEqual(configuration.get_config("audio_quality"), "96k")
        self.assertEqual(configuration.get_config("cloud_backend"), "b2")
        self.assertEqual(configuration.get_config("logo_file"), "/media/config/site_logo.png")
        self.assertEqual(configuration.get_config("favicon16"), "/media/config/fav16.png")

        # Reset favicons deletes favicon16..200 ConfigEntry rows
        reset_resp = self.client.get("/admin/config/reset_favicons/")
        self.assertRedirects(reset_resp, reverse("admin_config"))
        self.assertFalse(ConfigEntry.objects.filter(key="favicon16").exists())

    def test_users_list_and_set_user_state(self):
        self.client.force_login(self.superuser)
        resp_all = self.client.get("/admin/users/", {"page": "1"})
        self.assertEqual(resp_all.status_code, 200)
        self.assertGreaterEqual(resp_all.context["page"].paginator.count, 3)

        resp_bad_page = self.client.get("/admin/users/", {"page": "notanint"})
        self.assertEqual(resp_bad_page.status_code, 200)
        self.assertEqual(resp_bad_page.context["page"].number, 1)

        resp_staff = self.client.get("/admin/users/", {"only_staff": "1", "page": "1"})
        staff_usernames = {u.username for u in resp_staff.context["page"]}
        self.assertNotIn("regular", staff_usernames)
        self.assertIn("staff_only", staff_usernames)

        # Hierarchy enforcement in set_user_state
        # 1. is_superuser=true forces is_staff=True and is_active=True
        r1 = json.loads(
            self.client.post(
                "/admin/users/edit/",
                {
                    "user_id": self.user.id,
                    "is_active": "false",
                    "is_staff": "false",
                    "is_superuser": "true",
                },
            ).content
        )
        self.assertFalse(r1["is_superuser"])  # false because is_staff & is_active were false!

        r2 = json.loads(
            self.client.post(
                "/admin/users/edit/",
                {
                    "user_id": self.user.id,
                    "is_active": "true",
                    "is_staff": "true",
                    "is_superuser": "true",
                },
            ).content
        )
        self.assertTrue(r2["is_active"] and r2["is_staff"] and r2["is_superuser"])

        # 2. Deactivating clears is_staff & is_superuser
        r3 = json.loads(
            self.client.post(
                "/admin/users/edit/",
                {
                    "user_id": self.user.id,
                    "is_active": "false",
                    "is_staff": "true",
                    "is_superuser": "true",
                },
            ).content
        )
        self.assertFalse(r3["is_active"] or r3["is_staff"] or r3["is_superuser"])

        # Missing user_id -> AjaxException; unknown user_id -> 404; GET -> 405
        self.assertFalse(json.loads(self.client.post("/admin/users/edit/", {}).content)["success"])
        self.assertEqual(self.client.post("/admin/users/edit/", {"user_id": 999999}).status_code, 404)
        self.assertEqual(self.client.get("/admin/users/edit/").status_code, 405)

    @unittest.expectedFailure
    def test_users_list_defaults_to_first_page(self):
        """
        Bug in palanaeum/admin_views.py:77 — users_list calls
        `paginator.page(request.GET.get('page', 0))`, defaulting to page 0 (EmptyPage),
        which falls back to `paginator.num_pages` (the last page) instead of page 1.
        """
        # Create >60 total users so Paginator(users, 50, 10) produces 2 pages.
        for idx in range(65):
            UserFactory(username=f"bulk_user_{idx:02d}")
        self.client.force_login(self.superuser)
        resp = self.client.get("/admin/users/")
        self.assertEqual(resp.context["page"].number, 1)

    def test_related_sites_crud(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get("/admin/realted_sites/edit/").status_code, 200)
        create_resp = self.client.post(
            "/admin/realted_sites/edit/",
            {
                "name": "Brandon Site",
                "url": "https://www.brandonsanderson.com/",
                "order": "1",
                "image": make_uploaded_image("bs.png"),
            },
        )
        self.assertRedirects(create_resp, reverse("admin_related_sites"))
        site = RelatedSite.objects.get(name="Brandon Site")
        img_path = Path(site.image.path)

        # Edit existing
        self.assertEqual(self.client.get(f"/admin/realted_sites/{site.id}/").status_code, 200)
        edit_resp = self.client.post(
            f"/admin/realted_sites/{site.id}/",
            {
                "name": "Brandon Updated",
                "url": "https://www.brandonsanderson.com/",
                "order": "2",
            },
        )
        self.assertRedirects(edit_resp, reverse("admin_related_sites"))
        site.refresh_from_db()
        self.assertEqual(site.name, "Brandon Updated")

        # POST delete removes site & image file
        del_resp = self.client.post(f"/admin/realted_sites/{site.id}/delete/")
        self.assertRedirects(del_resp, reverse("admin_related_sites"))
        self.assertFalse(RelatedSite.objects.filter(pk=site.pk).exists())
        self.assertFalse(img_path.exists())

    @unittest.expectedFailure
    def test_related_site_delete_confirmation_get_renders(self):
        """
        Bug in palanaeum/templates/palanaeum/admin/delete_related_site_confirm.html:17,20 —
        the template references `{% url 'view_event_no_title' event.id %}` (with undefined
        `event`), causing NoReverseMatch on GET, and posts to `remove_event`.
        """
        site = RelatedSiteFactory()
        self.client.force_login(self.superuser)
        resp = self.client.get(f"/admin/realted_sites/{site.id}/delete/")
        self.assertEqual(resp.status_code, 200)
        site.delete()

    def test_navbar_save_and_reset(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get("/admin/navbar/").status_code, 200)

        save_resp = self.client.post(
            "/admin/navbar_save/",
            {
                "count": "3",
                "0-type": "link",
                "0-label": "Home",
                "0-url": "https://example.com/home",
                "0-icon": "home",
                "1-type": "dropdown",
                "1-label": "More",
                "1-url": "",
                "1-icon": "bars",
                "2-type": "sublink",
                "2-label": "Sub",
                "2-url": "https://example.com/sub",
                "2-icon": "link",
            },
        )
        self.assertTrue(json.loads(save_resp.content)["success"])
        items = list(NavbarItem.objects.all())
        self.assertEqual(len(items), 2)
        self.assertTrue(items[0].single_link)
        self.assertFalse(items[1].single_link)
        self.assertEqual(list(items[1].links.values_list("label", flat=True)), ["Sub"])

        reset_resp = self.client.post("/admin/navbar_reset/")
        self.assertTrue(json.loads(reset_resp.content)["success"])
        self.assertEqual(
            list(NavbarItem.objects.values_list("label", flat=True)),
            ["Events", "Recent", "Tags", "Wiki", "Chat"],
        )
        self.assertEqual(Link.objects.count(), 0)

    @unittest.expectedFailure
    def test_navbar_save_sublink_without_preceding_dropdown_returns_error(self):
        """
        Bug in palanaeum/admin_views.py:169,198 — navbar_save initializes
        `currentDropdown = None` and calls `currentDropdown.links.add(link)` when
        a `sublink` appears before any `dropdown`, raising AttributeError (500).
        """
        self.client.force_login(self.superuser)
        resp = self.client.post(
            "/admin/navbar_save/",
            {
                "count": "1",
                "0-type": "sublink",
                "0-label": "Orphan Sub",
                "0-url": "https://example.com/orphan",
                "0-icon": "link",
            },
        )
        self.assertIn(resp.status_code, (200, 400))
        if resp.status_code == 200:
            self.assertFalse(json.loads(resp.content)["success"])
