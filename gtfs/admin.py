# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.gis import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import Agency, Stop, Route, Trip, Calendar, CalendarDate, \
    FareAttribute, FareRule


class AgencyAdmin(OSMGeoAdmin):
    pass


class StopAdmin(OSMGeoAdmin):
    pass


class RouteAdmin(OSMGeoAdmin):
    pass


class TripAdmin(OSMGeoAdmin):
    pass


class CalendarAdmin(OSMGeoAdmin):
    pass


class CalendarDateAdmin(OSMGeoAdmin):
    pass


class FareAttributeAdmin(OSMGeoAdmin):
    pass


class FareRuleAdmin(OSMGeoAdmin):
    pass


admin.site.register(Agency, AgencyAdmin)
admin.site.register(Stop, StopAdmin)
admin.site.register(Route, RouteAdmin)
admin.site.register(Trip, TripAdmin)
admin.site.register(Calendar, CalendarAdmin)
admin.site.register(CalendarDate, CalendarDateAdmin)
admin.site.register(FareAttribute, FareAttributeAdmin)
admin.site.register(FareRule, FareRuleAdmin)
