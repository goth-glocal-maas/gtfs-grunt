# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

from django.db.models import (
    Model, CharField, IntegerField
)




@python_2_unicode_compatible
class Agency(Model):
    """
    agency_id, agency_name, agency_url, agency_timezone, agency_phone, agency_lang

    """
    agency_id = CharField('stop_id', max_lengh=25)
    name = CharField('name', max_length=500)

    def __str__(self):
        return self.id


@python_2_unicode_compatible
class Stop(Model):
    """
    "stop_id", "stop_code", "stop_name", "stop_desc", "stop_lat",
		"stop_lon", "zone_id", "stop_url", "location_type", "parent_station",
		"direction", "position"

    stop_id,stop_name,stop_desc,stop_lat,stop_lon,stop_url,location_type,parent_station

    """
    id = CharField('stop_id', max_lengh=25)
    name = CharField('name', max_length=500)

    def __str__(self):
        return self.id


@python_2_unicode_compatible
class Trip(Model):
    """
    route_id,service_id,trip_id,trip_headsign,block_id
    """
    id = CharField('route_id', max_lengh=25)
    short_name = CharField('short name', max_length=150)
    long_name = CharField('long name', max_length=500)

    def __str__(self):
        return self.id


@python_2_unicode_compatible
class Route(Model):
    """
    "route_id", "agency_id", "route_short_name", "route_long_name",
		"route_desc", "route_type", "route_url", "route_color",
		"route_text_color"

    """
    id = CharField('route_id', max_lengh=25)
    short_name = CharField('short name', max_length=150)
    long_name = CharField('long name', max_length=500)

    def __str__(self):
        return self.id


@python_2_unicode_compatible
class StopTime(Model):
    """
    "trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence",
		"stop_headsign", "pickup_type", "drop_off_type", "shape_dist_traveled",
		"timepoint", "continuous_drop_off", "continuous_pickup"

    """
    trip = CharField('route_id', max_lengh=25)
    short_name = CharField('short name', max_length=150)
    long_name = CharField('long name', max_length=500)

    def __str__(self):
        return self.id
