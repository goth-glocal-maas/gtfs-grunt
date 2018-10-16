from rest_framework.serializers import (
    ModelSerializer, SerializerMethodField, CurrentUserDefault, ValidationError
)
from drf_extra_fields.geo_fields import PointField

from .models import Agency, Stop, Route, Trip, Calendar, CalendarDate, \
    FareAttribute, FareRule, StopTime, Frequency
import json
import polyline



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
    agency = AgencySerializer(allow_null=True)

    class Meta:
        model = FareAttribute
        exclude = ['company', ]

    def create(self, validated_data):
        agency_data = validated_data.pop('agency')
        agency = None
        if isinstance(agency_data, dict):
            agency = Agency.objects.get(agency_id=agency_data['agency_id'])
        elif isinstance(agency_data, int):
            agency = Agency.objects.get(pk=agency_data)
        validated_data['agency'] = agency
        saved_obj = super(FareAttributeSerializer, self).create(validated_data)
        return saved_obj

    def update(self, instance, validated_data):
        agency_data = validated_data.pop('agency')
        saved_obj = super(FareAttributeSerializer, self).update(instance, validated_data)
        try:
            if isinstance(agency_data, dict):
                agency = Agency.objects.get(agency_id=agency_data['agency_id'])
            elif isinstance(agency_data, int):
                agency = Agency.objects.get(pk=agency_data)
            if instance.agency != agency:
                saved_obj.agency = agency
                saved_obj.save()
        except Exception as e:
            pass
        return saved_obj


class RouteAsChildSerializer(CompanyModelSerializer):

    class Meta:
        model = Route
        fields = ['id', 'route_id', 'short_name', 'long_name', 'route_type',
                  'agency', 'route_color', 'route_text_color', ]


class FareRuleSerializer(CompanyModelSerializer):
    fare = FareAttributeSerializer()
    route = RouteAsChildSerializer(allow_null=True)

    class Meta:
        model = FareRule
        exclude = ['company', ]

    def validate(self, data):
        if not (data['destination_id'] or data['contains_id']):
            _msg = 'Either one of destination_id or contains_id needed'
            raise ValidationError(_msg)
        if len(data['destination_id']) and len(data['contains_id']):
            _msg = 'Either one of destination_id or contains_id is accepted,' \
                   ' not both'
            raise ValidationError(_msg)
        return data

    def create(self, validated_data):
        fare_data = validated_data.pop('fare')
        fare = None
        if isinstance(fare_data, dict):
            fare = FareAttribute.objects.get(fare_id=fare_data['fare_id'])
        elif isinstance(fare_data, int):
            fare = FareAttribute.objects.get(pk=fare_data)
        validated_data['fare'] = fare

        route_data = validated_data.pop('route')
        route = None
        if isinstance(route_data, dict):
            route = Route.objects.get(route_id=route_data['route_id'])
        elif isinstance(route_data, int):
            route = Route.objects.get(pk=route_data)
        validated_data['route'] = route

        return super(FareRuleSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        fare_data = validated_data.pop('fare')
        try:
            route_data = validated_data.pop('route')
        except KeyError:
            route_data = None
        saved_obj = super(FareRuleSerializer, self).update(instance, validated_data)
        changes = 0
        try:
            if isinstance(fare_data, dict):
                fare = FareAttribute.objects.get(fare_id=fare_data['fare_id'])
            elif isinstance(fare_data, int):
                fare = FareAttribute.objects.get(pk=fare_data)
            if instance.fare != fare:
                saved_obj.fare = fare
                changes += 1
        except Exception as e:
            pass
        try:
            if isinstance(route_data, dict):
                route = Route.objects.get(route_id=route_data['route_id'])
            elif isinstance(route_data, int):
                route = Route.objects.get(pk=route_data)
            if instance.route != route:
                saved_obj.route = route
                changes += 1
        except Exception as e:
            pass

        if changes > 0:
            saved_obj.save()
        return saved_obj


class RouteSerializer(CompanyModelSerializer):
    geojson = SerializerMethodField()
    trip_set = TripSerializer(many=True, required=False)
    # farerule_set = FareRuleSerializer(many=True, required=False)

    class Meta:
        model = Route
        exclude = ['company', 'shapes', ]

    def get_geojson(self, obj):
        if not obj.shapes:
            return None
        _geojson = json.loads(obj.shapes.geojson)
        _geojson['coordinates'] = polyline.encode(_geojson['coordinates'])
        return _geojson

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
