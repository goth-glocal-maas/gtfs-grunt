# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework import filters, viewsets, status
from rest_framework.viewsets import ModelViewSet

from .models import Agency, Stop, Route, Trip, Calendar, CalendarDate, \
    FareAttribute, FareRule
from .serializers import AgencySerializer, StopSerializer, RouteSerializer, \
    TripSerializer, CalendarSerializer, CalendarDateSerializer, \
    FareAttributeSerializer, FareRuleSerializer


class AgencyViewSet(ModelViewSet):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    # filter_fields = ('slug', )
    # search_fields = ('slug', 'tags')


class StopViewSet(ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer


class RouteViewSet(ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


class TripViewSet(ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer


class CalendarViewSet(ModelViewSet):
    queryset = Calendar.objects.all()
    serializer_class = CalendarSerializer


class CalendarDateViewSet(ModelViewSet):
    queryset = CalendarDate.objects.all()
    serializer_class = CalendarDateSerializer


class FareAttributeViewSet(ModelViewSet):
    queryset = FareAttribute.objects.all()
    serializer_class = FareAttributeSerializer


class FareRuleViewSet(ModelViewSet):
    queryset = FareRule.objects.all()
    serializer_class = FareRuleSerializer
