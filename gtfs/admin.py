# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.gis import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import Agency, Stop, Route, Trip, Calendar, CalendarDate, \
    FareAttribute, FareRule


def pk_nakhon_agency_action(modeladmin, request, queryset):
    target = Agency.objects.get(agency_id='phuket-nakhon')
    queryset.update(agency=target)


pk_nakhon_agency_action.short_description = 'Apply PK-nakhon as agency'


def bmta_agency_action(modeladmin, request, queryset):
    user = request.user
    target = Agency.objects.get(agency_id='bmta', company=user.company)
    queryset.update(agency=target)


bmta_agency_action.short_description = 'Apply BMTA as agency'


class AgencyAdmin(OSMGeoAdmin):
    list_display = ('agency_id', 'name', 'url')
    search_fields = ('agency_id', 'name', 'url')


class StopAdmin(OSMGeoAdmin):
    list_filter = ('zone_id', 'wheelchair_boarding')
    list_display = ('stop_id', 'location', 'zone_id', 'parent_station',
        'wheelchair_boarding')
    search_fields = ('stop_id', 'stop_desc', 'name')


class RouteAdmin(OSMGeoAdmin):
    list_display = ('route_id', 'short_name', 'long_name')
    list_filter = ('agency', 'route_type')
    search_fields = ('route_id', 'short_name', 'long_name', 'desc')
    actions = [pk_nakhon_agency_action, bmta_agency_action, ]


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
