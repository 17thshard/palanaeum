from datetime import date

import factory
from django.contrib.auth.models import User

from palanaeum.models import Event, Entry


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: "User {}".format(n))
    email = factory.Sequence(lambda n: "user{}@palanaeum.org".format(n))


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    name = factory.Sequence(lambda n: 'Test event {}'.format(n))
    date = date.today()
    modified_by = None


class EntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Entry

    event = factory.SubFactory(EventFactory)
