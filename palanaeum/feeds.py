from django.contrib.syndication.views import Feed
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse

from palanaeum.configuration import get_config
from palanaeum.models import Entry, Event

class RecentEntriesFeed(Feed):
    title = "%s - Recent Entries" % get_config('page_title')
    link = "/recent/"
    title_template = "palanaeum/feeds/entry_title.html"
    description_template = "palanaeum/feeds/entry_description.html"

    def items(self):
        entries_ids = Entry.all_visible.order_by('-created').values_list('id', flat=True)[:5]
        entries_map = Entry.prefetch_entries(entries_ids, show_unapproved=True)
        return [entries_map[entry_id] for entry_id in entries_ids]

    def item_pubdate(self, entry):
        return entry.created

    def item_updateddate(self, entry):
        return entry.modified


class EventEntriesFeed(Feed):
    description_template = "palanaeum/feeds/entry_description.html"

    def get_object(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)

        if not event.visible():
            raise PermissionDenied

        return event
    
    def title(self, event):
        return event.name

    def link(self, event):
        return event.get_absolute_url()

    def items(self, event):
        entry_ids = Entry.all_visible.filter(event=event).values_list('id', flat=True)
        entries_map = Entry.prefetch_entries(entry_ids, show_unapproved=True)
        return sorted(entries_map.values(), key=lambda e: e.order)
    
    def item_title(self, entry):
        return "Entry #%d" % entry.order

    def item_pubdate(self, entry):
        return entry.created

    def item_updateddate(self, entry):
        return entry.modified
