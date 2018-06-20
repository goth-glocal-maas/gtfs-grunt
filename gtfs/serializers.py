from rest_framework.serializers import ModelSerializer, SerializerMethodField, CurrentUserDefault

from .models import Agency, Stop, Route, Trip, Calendar, CalendarDate, \
    FareAttribute, FareRule
import json


class AgencySerializer(ModelSerializer):

    class Meta:
        model = Agency
        fields = ('id', 'agency_id', 'name', 'url', 'timezone',
                  'phone', 'lang', 'fare_url', 'email')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['company'] = user.company
        agency = Agency.objects.create(**validated_data)
        return agency


class StopSerializer(ModelSerializer):
    geojson = SerializerMethodField()

    class Meta:
        model = Stop
        exclude = ['location', ]

    def get_geojson(self, obj):
        if not obj.location:
            return None
        return json.loads(obj.location.geojson)


class RouteSerializer(ModelSerializer):
    geojson = SerializerMethodField()

    class Meta:
        model = Route
        exclude = ['shapes', ]

    def get_geojson(self, obj):
        if not obj.shapes:
            return None
        return json.loads(obj.shapes.geojson)


class TripSerializer(ModelSerializer):

    class Meta:
        model = Trip
        fields = '__all__'


class CalendarSerializer(ModelSerializer):

    class Meta:
        model = Calendar
        fields = '__all__'


class CalendarDateSerializer(ModelSerializer):

    class Meta:
        model = CalendarDate
        fields = '__all__'


class FareAttributeSerializer(ModelSerializer):

    class Meta:
        model = FareAttribute
        fields = '__all__'


class FareRuleSerializer(ModelSerializer):

    class Meta:
        model = FareRule
        fields = '__all__'