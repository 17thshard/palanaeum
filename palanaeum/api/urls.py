from rest_framework import routers

from palanaeum.api.views import EventViewSet, TagsViewSet, SearchEntryViewSet, RandomEntryViewSet, \
    UpcomingEventsViewSet, EntryViewSet

api_router = routers.DefaultRouter()
api_router.register('events', EventViewSet, basename='events')
api_router.register('upcoming_events', UpcomingEventsViewSet, basename='upcoming_events')
api_router.register('tags', TagsViewSet)
api_router.register('entry', EntryViewSet, basename='entry')
api_router.register('search_entry', SearchEntryViewSet, basename='search_entry')
api_router.register('random_entry', RandomEntryViewSet, basename='random_entry')
