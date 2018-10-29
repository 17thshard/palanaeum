from django.test import TestCase
from django.urls import reverse


class AuthTests(TestCase):
    def test_password_reset_completed(self):
        ret = self.client.get('/auth/reset/done/', follow=True)
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.redirect_chain[0], (reverse('auth_login'), 302))

    def test_password_change_completed(self):
        ret = self.client.get('/auth/password_change/done/', follow=True)
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.redirect_chain[0], (reverse('auth_settings'), 302))
