from datetime import date

from django.test import TestCase
from django.urls import reverse
from django.utils.text import slugify

from palanaeum.configuration import get_config
from palanaeum.models import Event, Entry
from palanaeum.tests.factories import EventFactory, EntryFactory


class EventTests(TestCase):
    def setUp(self):
        self.event1 = EventFactory(date=date(2028, 2, 3))
        self.event2 = EventFactory(date=date(2028, 2, 2))
        self.event3 = EventFactory(date=date(2028, 2, 1))
        # Make events visible
        EntryFactory(event=self.event1)
        EntryFactory(event=self.event2)
        EntryFactory(event=self.event3)

    def tearDown(self) -> None:
        Entry.objects.all().delete()
        Event.objects.all().delete()

    def test_event_page(self):
        self.event1.name = "Test event 1"
        self.event1.date = date(2018, 2, 3)
        self.event1.location = 'Warsaw'
        self.event1.tour = 'Test tour'
        self.event1.bookstore = 'Empik'
        self.event1.meta = 'Meta comment'
        self.event1.review_state = Event.REVIEW_APPROVED
        self.event1.save()

        response = self.client.get('/events/{}/'.format(self.event1.id), follow=True)
        body = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertInHTML('Warsaw', body)
        self.assertInHTML('Test tour', body)
        self.assertInHTML('Empik', body)
        self.assertNotIn('Meta comment', body)
        self.assertInHTML(get_config('review_reviewed_explanation'), body)

        self.event1.review_state = Event.REVIEW_PENDING
        self.event1.save()

        response = self.client.get('/events/{}/'.format(self.event1.id), follow=True)
        body = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(get_config('review_pending_explanation'), body)

        self.event1.review_state = Event.REVIEW_NA
        self.event1.save()

        response = self.client.get('/events/{}/'.format(self.event1.id), follow=True)
        body = response.content.decode()
        self.assertEqual(response.status_code, 200)

    def test_events_list(self):
        Entry.objects.all().delete()
        Event.objects.all().delete()
        events = [EventFactory(date=date(2018, 5, x+1)) for x in range(30)]

        response = self.client.get('/events/',)
        body1 = response.content.decode()

        response = self.client.get('/events/', data={'page': '2'})
        body2 = response.content.decode()

        response = self.client.get('/events/', data={'page': '200'})
        body200 = response.content.decode()

        response = self.client.get('/events/', data={'page': 'bad'})
        body_bad = response.content.decode()

        response = self.client.get('/events/', data={'page': '1', 'sort_ord': '', 'sort_by': 'date'})
        body_sort = response.content.decode()

        for event in events[10:30]:
            self.assertIn(event.name, body1)
            self.assertNotIn(event.name, body2)
            self.assertNotIn(event.name, body200)
            self.assertIn(event.name, body_bad)

        for event in events[:20]:
            self.assertIn(event.name, body_sort)

        for event in events[:10]:
            self.assertNotIn(event.name, body1)
            self.assertIn(event.name, body2)
            self.assertIn(event.name, body200)
            self.assertNotIn(event.name, body_bad)

        for event in events[20:30]:
            self.assertNotIn(event.name, body_sort)

    def test_prev_url(self):
        self.assertEqual(
            self.event3.get_prev_url(),
            None
        )

        self.assertEqual(
            self.event2.get_prev_url(),
            reverse('view_event', args=(self.event3.pk, slugify(self.event3.name)))
        )

    def test_next_url(self):
        self.assertEqual(
            self.event1.get_next_url(),
            None
        )

        self.assertEqual(
            self.event2.get_next_url(),
            reverse('view_event', args=(self.event1.pk, slugify(self.event1.name)))
        )

    def test_event_view_no_slug(self):
        ret = self.client.get('/events/{}/'.format(self.event1.id), follow=True)
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.redirect_chain[0],
                         ('/events/{}-{}/'.format(self.event1.id, slugify(self.event1.name)), 302))

    def test_view_entry(self):
        entry = EntryFactory(event=self.event1)
        ret = self.client.get('/entry/{}/'.format(entry.id), follow=True)
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(
            ret.redirect_chain[0],
            ('/events/{}-{}/#e{}'.format(self.event1.id, slugify(self.event1.name), entry.id), 302))

    def test_view_event_invisible(self):
        self.event1.is_visible = False
        self.event1.save()
        ret = self.client.get('/events/{}/'.format(self.event1.id), follow=True)
        self.assertEqual(ret.status_code, 403)

