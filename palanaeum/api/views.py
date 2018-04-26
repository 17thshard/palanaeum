from django.utils import timezone
from rest_framework.mixins import ListModelMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from palanaeum.api.serializers import EntrySerializer, EventSerializer, TagsSerializer
from palanaeum.models import Entry, Event, Tag
from palanaeum.search import execute_filters, get_search_results, init_filters


class VariantPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 250


class EventViewSet(ReadOnlyModelViewSet):
    queryset = Event.all_visible.all()
    serializer_class = EventSerializer
    pagination_class = VariantPagination

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = self.serializer_class(instance, context={'request': request})
        return Response(serializer.data)


class UpcomingEventsViewSet(ListModelMixin, GenericViewSet):
    queryset = Event.all_visible.filter(date__gte=timezone.now().date()).order_by('date')
    serializer_class = EventSerializer
    pagination_class = VariantPagination


class TagsViewSet(ListModelMixin, GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
    pagination_class = VariantPagination


class EntryViewSet(ReadOnlyModelViewSet):
    queryset = Entry.all_visible.all()
    serializer_class = EntrySerializer
    pagination_class = VariantPagination


class SearchEntryViewSet(ListModelMixin, GenericViewSet):
    queryset = Entry.all_visible.all()
    serializer_class = EntrySerializer
    pagination_class = VariantPagination

    def get_queryset(self):
        ordering = self.request.query_params.get('ordering', 'rank')
        filters = init_filters(self.request)
        scores = execute_filters(filters)
        entries_ids = scores.keys()
        entries_map = Entry.prefetch_entries(entries_ids)
        return [entries_map[i[0]] for i in get_search_results(scores, ordering)]


class RandomEntryViewSet(ListModelMixin, GenericViewSet):
    queryset = Entry.all_visible.order_by('?')
    serializer_class = EntrySerializer

    def list(self, request, *args, **kwargs):
        random_entry = Entry.all_visible.order_by('?').first()
        serializer = EntrySerializer(random_entry, context={'request': request})
        return Response(serializer.data)
