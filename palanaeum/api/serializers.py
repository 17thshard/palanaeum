from rest_framework import serializers, fields

from palanaeum.models import Event, Entry, EntryLine


class TagsSerializer(serializers.Serializer):
    name = serializers.CharField()
    entries = serializers.ReadOnlyField(source='entries_count')
    events = serializers.ReadOnlyField(source='events_count')

    def update(self, instance, validated_data):
        raise NotImplementedError

    def create(self, validated_data):
        raise NotImplementedError


class EntryLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryLine
        fields = ('speaker', 'text')


class EntrySerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True)
    lines = EntryLineSerializer(many=True)
    event_date = fields.DateField(source='event.date')
    event_name = fields.CharField(source='event.name')
    event_state = fields.CharField(source='event.review_state')

    class Meta:
        model = Entry
        fields = ('id', 'event', 'event_name', 'event_date', 'event_state',
                  'date', 'paraphrased', 'modified_date', 'tags', 'lines', 'note')


class EventSerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True)
    entries = serializers.PrimaryKeyRelatedField(read_only=True, many=True)

    class Meta:
        model = Event
        fields = ('id', 'name', 'location', 'date', 'tour', 'bookstore', 'review_state', 'modified_date', 'tags',
                  'entries')
