from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from palanaeum.models import Entry, Event, AudioSource
from palanaeum.tests.factories import EventFactory, EntryFactory, EntryVersionFactory, EntryLineFactory


class SuggestionVisibilityTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='pass', email='tester@gmail.com')
        self.user2 = User.objects.create_user(username='user2', password='pass', email='tester2@gmail.com')
        self.staff = User.objects.create_user(username='staffer', password='pass', is_staff=True,
                                              email='staff@shard.com')
        self.event = EventFactory(name='Testowy event!')
        self.entry = EntryFactory(event=self.event, is_approved=True)
        ev = EntryVersionFactory(entry=self.entry, is_approved=True)
        el = EntryLineFactory(entry_version=ev)
        el.text = 'normal_visible_entry'
        el.save()

        self.audio = AudioSource.objects.create(
            event=self.event, length=10, status=AudioSource.STORED_IN_CLOUD,
            original_filename='file.mp3', is_approved=True, created_by=self.user2,
            file_title="file.mp3")

        self.audio_unapproved = AudioSource.objects.create(
            event=self.event, length=10, status=AudioSource.STORED_IN_CLOUD, is_visible=True,
            original_filename='file2.mp3', is_approved=False, created_by=self.user2,
            file_title="file2.mp3"
        )

        self.audio_hidden = AudioSource.objects.create(
            event=self.event, length=10, status=AudioSource.STORED_IN_CLOUD,
            original_filename='file3.mp3', is_approved=True, is_visible=False,
            file_title="file3.mp3", created_by=self.user2
        )

        self.make_new_entry_suggestion()
        self.make_modified_entry_suggestion()
        self.make_hidden_entry()

    def tearDown(self):
        AudioSource.objects.all().delete()
        Entry.objects.all().delete()
        Event.objects.all().delete()
        self.event.delete()
        self.user.delete()
        self.user2.delete()
        self.staff.delete()

    def make_new_entry_suggestion(self):
        new_entry_line = EntryLineFactory()
        new_entry_line.text = 'new_entry_suggestion'
        new_entry_line.save()
        ev = new_entry_line.entry_version
        ev.is_approved = False
        ev.save()
        entry = ev.entry
        entry.is_approved = False
        entry.is_visible = True
        entry.event = self.event
        entry.save()
        return entry

    def make_modified_entry_suggestion(self):
        entry = EntryFactory(event=self.event, is_approved=True)
        ev = EntryVersionFactory(entry=entry, is_approved=True, date=timezone.now() - timedelta(seconds=10))
        EntryLineFactory(entry_version=ev, text='old_modified_entry_text')
        ev2 = EntryVersionFactory(entry=entry, is_approved=False, date=timezone.now())
        EntryLineFactory(entry_version=ev2, text='new_modified_entry_text', entry_version__user=self.user2)

    def make_hidden_entry(self):
        entry = EntryFactory(event=self.event, is_approved=True)
        ev = EntryVersionFactory(entry=entry, is_approved=True, date=timezone.now() - timedelta(seconds=10))
        EntryLineFactory(entry_version=ev, text='hidden_entry')
        entry.hide()
        entry.save()

    def _get_event_page(self, user=None):
        if user:
            self.client.login(username=user.username, password='pass')
        ret = self.client.get('/events/{}/'.format(self.event.pk), follow=True)
        if user:
            self.client.logout()
        self.assertEqual(ret.status_code, 200)
        return ret.content.decode()

    def _get_recent_page(self, user=None):
        if user:
            self.client.login(username=user.username, password='pass')
        ret = self.client.get('/recent/', {'mode': 'recorded'}, follow=True)
        if user:
            self.client.logout()
        self.assertEqual(ret.status_code, 200)
        return ret.content.decode()

    def test_anonymous_normal_entry(self):
        page = self._get_event_page()
        page2 = self._get_recent_page()
        self.assertIn('normal_visible_entry', page)
        self.assertIn('normal_visible_entry', page2)

    def test_anonymous_suggestion_new_entry(self):
        page = self._get_event_page()
        page2 = self._get_recent_page()
        self.assertNotIn('new_entry_suggestion', page)
        self.assertNotIn('new_entry_suggestion', page2)

    def test_anonymous_suggestion_modified_entry(self):
        page = self._get_event_page()
        page2 = self._get_recent_page()
        self.assertIn('old_modified_entry_text', page)
        self.assertIn('old_modified_entry_text', page2)
        self.assertNotIn('new_modified_entry_text', page)
        self.assertNotIn('new_modified_entry_text', page2)

    def test_anonymous_hidden_entry(self):
        page = self._get_event_page()
        page2 = self._get_recent_page()
        self.assertNotIn('hidden_entry', page)
        self.assertNotIn('hidden_entry', page2)

    def test_user_normal_entry(self):
        page = self._get_event_page(self.user)
        page2 = self._get_recent_page(self.user)
        self.assertIn('normal_visible_entry', page)
        self.assertIn('normal_visible_entry', page2)

    def test_user_suggestion_new_entry(self):
        page = self._get_event_page(self.user)
        page2 = self._get_recent_page(self.user)
        self.assertIn('new_entry_suggestion', page)
        self.assertIn('new_entry_suggestion', page2)

    def test_user_suggestion_modified_entry(self):
        page = self._get_event_page(self.user)
        page2 = self._get_recent_page(self.user)
        self.assertIn('new_entry_suggestion', page)
        self.assertIn('new_entry_suggestion', page2)

    def test_user_hidden_entry(self):
        page = self._get_event_page(self.user)
        page2 = self._get_recent_page(self.user)
        self.assertNotIn('hidden_entry', page)
        self.assertNotIn('hidden_entry', page2)

    def test_audio_source(self):
        page = self._get_event_page(self.user)
        self.assertIn('file.mp3', page)
        self.assertNotIn('file2.mp3', page)
        self.assertNotIn('file3.mp3', page)

    def test_audio_source_owner(self):
        page = self._get_event_page(self.user2)
        self.assertIn('file.mp3', page)
        self.assertIn('file2.mp3', page)
        self.assertNotIn('file3.mp3', page)

    def test_audio_source_staff(self):
        page = self._get_event_page(self.staff)
        self.assertIn('file.mp3', page)
        self.assertIn('file2.mp3', page)
        self.assertIn('file3.mp3', page)
