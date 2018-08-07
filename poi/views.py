# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import GEOSGeometry
from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from poi.serializers import POISerializer
from poi.models import POI


class POIViewSet(ModelViewSet):
    filter_backends = (filters.SearchFilter, )
    queryset = POI.objects.all()
    serializer_class = POISerializer
    search_fields = ('name', 'street', )

    def get_queryset(self):
        qs = super(POIViewSet, self).get_queryset()
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
