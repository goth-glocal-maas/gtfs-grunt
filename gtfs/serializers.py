from rest_framework.serializers import ModelSerializer, SerializerMethodField, CurrentUserDefault

from .models import Agency, Stop, Route, Trip, Calendar, CalendarDate, \
    FareAttribute, FareRule, StopTime, Frequency
import json


class CompanyModelSerializer(ModelSerializer):

    class Meta:
        extra_kwargs = {'company': {'write_only': True}}
        exclude = ['company', ]

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['company'] = user.company
        obj = self.Meta.model.objects.create(**validated_data)
        return obj


class AgencySerializer(CompanyModelSerializer):

    class Meta:
        model = Agency
        fields = ('id', 'agency_id', 'name', 'url', 'timezone',
                  'phone', 'lang', 'fare_url', 'email')


class StopSerializer(CompanyModelSerializer):
    geojson = SerializerMethodField()

    class Meta:
        model = Stop
        exclude = ['company', 'location', ]

    def get_geojson(self, obj):
        if not obj.location:
            return None
        return json.loads(obj.location.geojson)


class StopTimeSerializer(CompanyModelSerializer):
    stop = StopSerializer()

    class Meta:
        model = StopTime
        exclude = ['company', ]


class CalendarDateSerializer(CompanyModelSerializer):

    class Meta:
        model = CalendarDate
        exclude = ['company', ]


class CalendarSerializer(CompanyModelSerializer):
    exceptions = SerializerMethodField()

    class Meta:
        model = Calendar
        exclude = ['company', ]

    def get_exceptions(self, obj):
        exceptions = CalendarDate.objects.filter(service=obj)
        return CalendarDateSerializer(exceptions, many=True).data


class FrequencySerializer(CompanyModelSerializer):

    class Meta:
        model = Frequency
        exclude = ['company', ]


class TripSerializer(CompanyModelSerializer):
    service = CalendarSerializer()
    frequency_set = FrequencySerializer(many=True, required=False)
    stoptime = SerializerMethodField()

    class Meta:
        model = Trip
        exclude = ['company', ]

    def get_stoptime(self, obj):
        st = obj.stoptime_set.all()
        if not st:
            return None
        return {
            'count': st.count(),
            'period': [st[0].arrival, st[len(st)-1].arrival],
        }


class FareAttributeSerializer(CompanyModelSerializer):

    class Meta:
        model = FareAttribute
        exclude = ['company', ]


class RouteSerializer(CompanyModelSerializer):
    geojson = SerializerMethodField()
    trip_set = TripSerializer(many=True, required=False)
    farerule_set = FareAttributeSerializer(many=True, required=False)

    class Meta:
        model = Route
        exclude = ['company', 'shapes', ]

    def get_geojson(self, obj):
        if not obj.shapes:
            return None
        return json.loads(obj.shapes.geojson)


class FareRuleSerializer(CompanyModelSerializer):
    fare = FareAttributeSerializer()

    class Meta:
        model = FareRule
        exclude = ['company', ]
