import datetime
import random

from django.core.management.base import BaseCommand

from palanaeum.models import Event


class Command(BaseCommand):
    """
    Autogenerates random test events and loads them into the database.
    """
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('-n', '--num_events', type=int, default=3)

    def handle(self, *args, **options):
        """
        Auto-generate n test events and return them in the fixture format
        expected by django.
        """
        n = options['num_events']
        review_states = [s[0] for s in Event.REVIEW_STATES]

        for i in range(n):
            event = Event()
            event.date = datetime.date(2017, 1, 1) + datetime.timedelta(days=i)
            event.name = 'auto_generated_event_{}'.format(i + 1)
            event.review_state = random.choice(review_states)
            event.save()
