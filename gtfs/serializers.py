from rest_framework.serializers import ModelSerializer
from .models import Agency, Stop, Route, Trip, Calendar, CalendarDate, \
    FareAttribute, FareRule


class AgencySerializer(ModelSerializer):

    class Meta:
        model = Agency
        fields = ('agency_id', 'name', 'url', 'timezone', 'phone',
            'lang', 'fare_url', 'email')


class StopSerializer(ModelSerializer):

    class Meta:
        model = Stop
        fields = '__all__'


class RouteSerializer(ModelSerializer):

    class Meta:
        model = Route
        fields = '__all__'


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