# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.gis.db.models import (
    Model, CharField, PointField, DateTimeField,
)
# from django.utils import timezone
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import GEOSGeometry
from collections import OrderedDict


@python_2_unicode_compatible
class POI(Model):
    gd_id = CharField('GoodWalk ID', max_length=50, blank=True)
    name = CharField('Name', max_length=500)
    branch = CharField('Branch', max_length=200, blank=True)
    category = CharField('Category', max_length=50)
    location = PointField('Location')
    street = CharField('Street', max_length=500, blank=True)

    created_on = DateTimeField('Created on', auto_now_add=True)
    updated_on = DateTimeField('Updated on', auto_now=True)

    def __str__(self):
        return '%s - %s' % (self.name, self.location.coords)

    def distance(self, lat, lon):
        if not self.location:
            return None

        pnt = GEOSGeometry('POINT(%s %s)' % (lon, lat), srid=4326)
        qs = POI.objects.filter(pk=self.pk)
        return qs.annotate(distance=Distance('location', pnt))[0].distance
