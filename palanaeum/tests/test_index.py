from django.test import TestCase

from palanaeum.tests.factories import EventFactory, EntryFactory


class IndexTests(TestCase):

    def test_empty_page(self):
        ret = self.client.get('/')
        self.assertEqual(ret.status_code, 200)
        self.assertInHTML('There are no events in the system yet.',
                          ret.content.decode())

    def test_index_events(self):
        event = EventFactory()
        ret = self.client.get('/')
        self.assertEqual(ret.status_code, 200)
        # No entries = event invisible on index page
        self.assertNotIn(event.name, ret.content.decode())

        # Adding entry to make event visible on index page
        EntryFactory(event=event)
        ret = self.client.get('/')
        self.assertEqual(ret.status_code, 200)
        self.assertInHTML(event.name, ret.content.decode())
