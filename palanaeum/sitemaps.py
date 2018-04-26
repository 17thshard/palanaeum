from datetime import timedelta

from django.contrib.sitemaps import Sitemap
from django.utils import timezone

from palanaeum.models import Event, Entry, ImageSource, AudioSource


class EventSitemap(Sitemap):
    protocol = 'https'
    limit = 1000

    def items(self):
        return Event.all_visible.all()

    @staticmethod
    def lastmod(obj):
        assert(isinstance(obj, Event))
        entry = Entry.all_visible.filter(event=obj, modified_date__isnull=False).order_by('-modified_date').first()
        img_source = ImageSource.all_visible.filter(event=obj, modified_date__isnull=False).order_by('-modified_date').first()
        audio_source = AudioSource.all_visible.filter(event=obj, modified_date__isnull=False).order_by('-modified_date').first()
        return max(
            obj.modified_date,
            getattr(entry, 'modified_date', obj.modified_date),
            getattr(img_source, 'modified_date', obj.modified_date),
            getattr(audio_source, 'modified_date', obj.modified_date)
        )

    @staticmethod
    def changefreq(obj):
        assert (isinstance(obj, Event))
        diff = timezone.now().date() - obj.date

        if diff < timedelta(days=30):
            return 'daily'
        elif diff < timedelta(days=90):
            return 'monthly'

        return 'yearly'

    @staticmethod
    def priority(obj):
        assert (isinstance(obj, Event))
        events_count = Event.all_visible.count()
        older_events = Event.all_visible.filter(date__lt=obj.date).count()

        return older_events / events_count