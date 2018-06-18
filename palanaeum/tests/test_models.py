from datetime import date

from django.test import TestCase
from django.urls import reverse
from django.utils.text import slugify

from palanaeum.tests.factories import EventFactory, EntryFactory


class EventTests(TestCase):
    def setUp(self):
        self.event1 = EventFactory(date=date(2018, 5, 3))
        self.event2 = EventFactory(date=date(2018, 5, 2))
        self.event3 = EventFactory(date=date(2018, 5, 1))
        # Make events visible
        EntryFactory(event=self.event1)
        EntryFactory(event=self.event2)
        EntryFactory(event=self.event3)

    def test_prev_url(self):
        self.assertEqual(
            self.event1.get_prev_url(),
            None
        )

        self.assertEqual(
            self.event2.get_prev_url(),
            reverse('view_event', args=(self.event1.pk, slugify(self.event1.name)))
        )

    def test_next_url(self):
        self.assertEqual(
            self.event3.get_next_url(),
            None
        )

        self.assertEqual(
            self.event2.get_next_url(),
            reverse('view_event', args=(self.event3.pk, slugify(self.event3.name)))
        )
