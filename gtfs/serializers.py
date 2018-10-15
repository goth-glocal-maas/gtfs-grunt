from rest_framework.serializers import (
    ModelSerializer, SerializerMethodField, CurrentUserDefault, ValidationError
)
from drf_extra_fields.geo_fields import PointField

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
        return super(CompanyModelSerializer, self).create(validated_data)


class AgencySerializer(CompanyModelSerializer):

    class Meta:
        model = Agency
        fields = ('id', 'agency_id', 'name', 'url', 'timezone',
                  'phone', 'lang', 'fare_url', 'email')


class StopSerializer(CompanyModelSerializer):
    geojson = SerializerMethodField()
    location = PointField()
    distance_m = SerializerMethodField()

    class Meta:
        model = Stop
        exclude = ['company', ]

    def get_geojson(self, obj):
        if not obj.location:
            return None
        return json.loads(obj.location.geojson)

    def get_distance_m(self, obj):
        try:
            return obj.distance.m
        except Exception:
            return None


class StopTimeSerializer(CompanyModelSerializer):
    stop = StopSerializer()

    class Meta:
        model = StopTime
        exclude = ['company', ]

    def create(self, validated_data):
        stop_data = validated_data.pop('stop')
        if isinstance(stop_data, dict):
            stop = Stop.objects.get(stop_id=stop_data['stop_id'])
        elif isinstance(stop_data, int):
            stop = Stop.objects.get(pk=stop_data)
        validated_data['stop'] = stop
        saved_obj = super(StopTimeSerializer, self).create(validated_data)
        return saved_obj

    def update(self, instance, validated_data):
        stop_data = validated_data.pop('stop')
        saved_obj = super(StopTimeSerializer, self).update(instance, validated_data)
        try:
            if isinstance(stop_data, dict):
                stop = Stop.objects.get(stop_id=stop_data['stop_id'])
            elif isinstance(stop_data, int):
                stop = Stop.objects.get(pk=stop_data)
            if instance.stop != stop:
                saved_obj.stop = stop
                saved_obj.save()
        except Exception as e:
            # NOTE: handle new Calendar creation?
            pass
        return saved_obj


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
    stoptime = SerializerMethodField(read_only=True)

    class Meta:
        model = Trip
        exclude = ['company', ]

    def get_stoptime(self, obj):
        st = obj.stoptime_set.all()
        if not st:
            return {
                'count': 0,
                'period': [],
            }
        return {
            'count': st.count(),
            'period': [st[0].arrival, st[len(st)-1].arrival],
        }

    def to_internal_value(self, data):
        if 'stoptime' in data:
            data.pop('stoptime')
        if 'route' in data:
            data['route'] = Route.objects.get(pk=data['route'])
        return data

    def validate(self, data):
        if 'route' not in data:
            raise ValidationError({'route': 'missing route'})
        if 'service' not in data:
            raise ValidationError({'service': 'missing service'})
        if 'frequency_set' not in data:
            raise ValidationError({'frequency_set': 'missing frequency set'})
        return data

    def create(self, validated_data):
        service_data = validated_data.pop('service')
        freq_data = validated_data.pop('frequency_set')
        # TODO: handle frequency set
        if isinstance(service_data, dict):
            serv = Calendar.objects.get(service_id=service_data['service_id'])
        elif isinstance(service_data, int):
            serv = Calendar.objects.get(pk=service_data)
        validated_data['service'] = serv
        saved_obj = super(TripSerializer, self).create(validated_data)
        return saved_obj

    def update(self, instance, validated_data):
        service_data = validated_data.pop('service')
        freq_data = validated_data.pop('frequency_set')
        # TODO: handle frequency set
        saved_obj = super(TripSerializer, self).update(instance, validated_data)
        try:
            if isinstance(service_data, dict):
                serv = Calendar.objects.get(service_id=service_data['service_id'])
            elif isinstance(service_data, int):
                serv = Calendar.objects.get(pk=service_data)
            if instance.service != serv:
                saved_obj.service = serv
                saved_obj.save()
        except Exception as e:
            # NOTE: handle new Calendar creation?
            pass
        return saved_obj


class FareAttributeSerializer(CompanyModelSerializer):
    agency = AgencySerializer()

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

    def validate(self, data):
        if 'agency' not in data and data['agency']:
            raise ValidationError('missing agency')
        return data

    def to_internal_value(self, data):
        obj, agency = None, 0
        agency = data.pop('agency')
        agency_pk = agency if isinstance(agency, int) else agency['id']
        obj = Agency.objects.get(pk=agency_pk)
        data['agency'] = obj
        return data

class FareRuleSerializer(CompanyModelSerializer):
    fare = FareAttributeSerializer()

    class Meta:
        model = FareRule
        exclude = ['company', ]
