# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db.models import Q
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models.functions import Distance
from rest_framework import filters, viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.viewsets import ModelViewSet as _ModelViewset
from rest_framework.response import Response
from rest_framework.exceptions import NotAcceptable
from json import loads

from .models import Agency, Stop, Route, Trip, Calendar, CalendarDate, \
    FareAttribute, FareRule, StopTime, Frequency
from .serializers import AgencySerializer, StopSerializer, RouteSerializer, \
    TripSerializer, CalendarSerializer, CalendarDateSerializer, \
    FareAttributeSerializer, FareRuleSerializer, StopTimeSerializer, \
    FrequencySerializer


class ModelViewSet(_ModelViewset):
    filter_backends = (filters.SearchFilter, )
    custom_get_param = None
    custom_fk_field = ''
    custom_fk_field_rel = ''

    def get_queryset(self):
        qs = super(ModelViewSet, self).get_queryset()
        has_custom_req_query = self.custom_get_param is not None and \
            len(self.custom_fk_field) > 0 and \
            len(self.custom_fk_field_rel) > 0
        if has_custom_req_query:
            _param = self.request.query_params.get(self.custom_get_param, None)
            if _param is not None:
                try:
                    q, k = {}, '%s__id' % self.custom_fk_field
                    q[k] = int(_param)
                    qs = qs.filter(**q)
                except ValueError:
                    q, k = {}, '%s__%s' % (self.custom_fk_field,
                                           self.custom_fk_field_rel)
                    q[k] = _param
                    qs = qs.filter(**q)
        return qs


class AgencyViewSet(ModelViewSet):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    # filter_fields = ('slug', )
    search_fields = ('name', 'url', 'email', 'agency_id')


class StopViewSet(ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer
    search_fields = (
        'stop_id',
        'name',
        'stop_code',
        'stoptime__trip__route__agency__name',
        'stoptime__trip__route__short_name',
        'stoptime__trip__route__route_id',
    )
    search_fields = ('stop_code', 'stop_id', 'name', 'stop_desc')

    def get_queryset(self):
        qs = super(StopViewSet, self).get_queryset()
        # lat,lon (string)
        near = self.request.query_params.get('near', None)
        # range in km
        range_param = self.request.query_params.get('range', 1)
        if near is not None and len(near.split(',')) == 2:
            lat, lon = near.split(',')
            pnt = GEOSGeometry('POINT(%s %s)' % (lon, lat), srid=4326)
            poly = pnt.buffer(0.008 * float(range_param))
            qs = qs.filter(location__within=poly)
            dist = Distance('location', pnt)
            qs = qs.annotate(distance=dist).order_by('distance')
        return qs

    @detail_route(methods=['post'], url_path='merge')
    def merge(self, request, *args, **kwargs):
        """Merge between 2 stops

        request.body
        stop <serializer-of-stop>  the stop that we're going to delete and
                                   merge its connections with

        return
        stop <obj>
        """
        try:
            stop_dict = request.data.get('stop')
            to_be_merged = Stop.objects.get(pk=stop_dict['id'])
            obj = self.get_object()
            obj.merge_with(to_be_merged)
            serialized = self.serializer_class(obj)
            return Response(serialized.data)
        except Exception:
            # TODO: add logger here
            raise NotAcceptable()


class RouteViewSet(ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    custom_get_param = 'agency'
    custom_fk_field = 'agency'
    custom_fk_field_rel = 'agency_id'
    search_fields = (
        'route_id', 'agency__agency_id', 'short_name', 'long_name', 'desc',
    )


class TripViewSet(ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    custom_get_param = 'route'
    custom_fk_field = 'route'
    custom_fk_field_rel = 'route_id'
    search_fields = (
        'route__agency__name',
        'route__agency__agency_id',
    )


class StopTimeViewSet(ModelViewSet):
    queryset = StopTime.objects.all()
    serializer_class = StopTimeSerializer
    custom_get_param = 'trip'
    custom_fk_field = 'trip'
    custom_fk_field_rel = 'trip_id'


class CalendarViewSet(ModelViewSet):
    queryset = Calendar.objects.all()
    serializer_class = CalendarSerializer
    search_fields = ('service_id', )


class CalendarDateViewSet(ModelViewSet):
    queryset = CalendarDate.objects.all()
    serializer_class = CalendarDateSerializer
    custom_get_param = 'service'
    custom_fk_field = 'service'
    custom_fk_field_rel = 'service_id'


class FrequencyViewSet(ModelViewSet):
    queryset = Frequency.objects.all()
    serializer_class = FrequencySerializer
    custom_get_param = 'trip'
    custom_fk_field = 'trip'
    custom_fk_field_rel = 'trip_id'


class FareAttributeViewSet(ModelViewSet):
    queryset = FareAttribute.objects.all()
    serializer_class = FareAttributeSerializer
    search_fields = ('fare_id', 'price')


class FareRuleViewSet(ModelViewSet):
    queryset = FareRule.objects.all()
    serializer_class = FareRuleSerializer
    custom_get_param = 'fareattr'
    custom_fk_field = 'fare'
    custom_fk_field_rel = 'fare_id'

    def create(self, request):
        body = request.body
        data = loads(body)
        dst_ids = data['destination_id'].split(',') if data['destination_id'] else []
        ctn_ids = data['contains_id'].split(',') if data['contains_id'] else []

        if len(dst_ids) < 2 and len(ctn_ids) < 2:
            return super(FareRuleViewSet, self).create(request)

        # dealing with multi
        _ids = dst_ids if dst_ids else ctn_ids
        field_name = 'destination_id' if dst_ids else 'contains_id'
        objs = []
        company = request.user.company
        for _id in _ids:
            one = data.copy()
            one[field_name] = _id
            one['company'] = company
            one['fare'] = FareAttribute.objects.get(pk=one['fare']['id'])
            if one['route']:
                one['route'] = Route.objects.get(pk=one['route']['id'])
            _instance = FareRule.objects.create(**one)
            objs.append(_instance)
        serialized = self.serializer_class(objs, many=True)
        return Response(serialized.data, status=status.HTTP_201_CREATED)
