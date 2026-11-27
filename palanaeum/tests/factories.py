from datetime import date

import factory
from django.contrib.auth.models import User

from palanaeum.models import (
    AudioSource,
    Entry,
    EntryLine,
    EntryVersion,
    Event,
    FAQEntry,
    HelpPage,
    ImageSource,
    Link,
    NavbarItem,
    RelatedSite,
    Snippet,
    Tag,
    URLSource,
    UserSettings,
    UsersEntryCollection,
)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: "User {}".format(n))
    email = factory.Sequence(lambda n: "user{}@palanaeum.org".format(n))


class StaffUserFactory(UserFactory):
    username = factory.Sequence(lambda n: "staff_{}".format(n))
    email = factory.Sequence(lambda n: "staff{}@palanaeum.org".format(n))
    is_staff = True


class SuperUserFactory(UserFactory):
    username = factory.Sequence(lambda n: "admin_{}".format(n))
    email = factory.Sequence(lambda n: "admin{}@palanaeum.org".format(n))
    is_staff = True
    is_superuser = True


class UserSettingsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserSettings

    user = factory.SubFactory(UserFactory)
    timezone = "UTC"
    page_length = 20
    website = ""


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: "tag-{}".format(n))


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    name = factory.Sequence(lambda n: "Test event {}!".format(n))
    date = date.today()


class EntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Entry

    event = factory.SubFactory(EventFactory)


class EntryVersionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EntryVersion

    entry = factory.SubFactory(EntryFactory)
    user = factory.SubFactory(UserFactory)


class EntryLineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EntryLine

    entry_version = factory.SubFactory(EntryVersionFactory)
    speaker = factory.Sequence(lambda n: "Speaker {}".format(n))
    text = "Line text"


class URLSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = URLSource

    url = factory.Sequence(lambda n: "https://example.com/source/{}".format(n))
    text = factory.Sequence(lambda n: "URL Source {}".format(n))


class ImageSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ImageSource

    event = factory.SubFactory(EventFactory)
    entry = None
    name = factory.Sequence(lambda n: "Image {}".format(n))
    file = factory.django.ImageField(filename="test.png", width=20, height=20)


class AudioSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AudioSource

    event = factory.SubFactory(EventFactory)
    length = 60
    original_filename = factory.Sequence(lambda n: "audio_{}.mp3".format(n))
    file_title = factory.Sequence(lambda n: "Audio Source {}".format(n))
    status = AudioSource.READY


class SnippetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Snippet

    source = factory.SubFactory(AudioSourceFactory)
    beginning = 0
    length = 10
    comment = factory.Sequence(lambda n: "Snippet {}".format(n))


class UsersEntryCollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UsersEntryCollection

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: "Collection {}".format(n))
    description = "Collection description"
    public = False


class RelatedSiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RelatedSite

    name = factory.Sequence(lambda n: "Related Site {}".format(n))
    url = factory.Sequence(lambda n: "https://related{}.example.com/".format(n))
    image = factory.django.ImageField(filename="site.png", width=34, height=34)
    order = factory.Sequence(lambda n: n)


class HelpPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HelpPage

    path = factory.Sequence(lambda n: "help-{}".format(n))
    title = factory.Sequence(lambda n: "Help {}".format(n))
    text = "<p>Help content</p>"
    author = factory.SubFactory(StaffUserFactory)


class FAQEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FAQEntry

    ordering = factory.Sequence(lambda n: n)
    header = factory.Sequence(lambda n: "FAQ Question {}".format(n))
    text = "FAQ answer text"
    author = factory.SubFactory(StaffUserFactory)


class LinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Link

    url = factory.Sequence(lambda n: "https://link{}.example.com/".format(n))
    label = factory.Sequence(lambda n: "Link {}".format(n))
    icon_class = "link"


class NavbarItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NavbarItem

    position = factory.Sequence(lambda n: n)
    label = factory.Sequence(lambda n: "Nav {}".format(n))
    url = factory.Sequence(lambda n: "https://nav{}.example.com/".format(n))
    icon_class = "star"
    single_link = True
