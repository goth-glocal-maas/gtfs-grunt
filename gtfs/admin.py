# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.gis import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import Agency, Stop, Route, Trip, Calendar, CalendarDate, \
    FareAttribute, FareRule, StopTime, Frequency


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


class CalendarAdmin(OSMGeoAdmin):
    list_display = ('service_id', 'start_date', 'end_date')
    search_fields = ('service_id', )


class CalendarDateAdmin(OSMGeoAdmin):
    list_display = ('service', 'date', 'exception_type')
    list_filter = ('exception_type', )
    search_fields = ('date', 'service__service_id')


class FareAttributeAdmin(OSMGeoAdmin):
    list_display = ('fare_id', 'price', 'currency_type', 'payment_method')
    list_filter = ('currency_type', 'agency')
    search_fields = ('fare_id', )


class FareRuleAdmin(OSMGeoAdmin):
    list_filter = ('fare', 'origin_id', 'destination_id', 'contains_id')
    search_fields = ('origin_id', 'destination_id', 'contains_id')
    list_display = ('fare', 'origin_id', 'destination_id', 'contains_id')


class FrequencyAdmin(OSMGeoAdmin):
    list_display = ('trip', 'start_time', 'end_time', 'headway_secs',
                    'exact_times')


class TripAdmin(OSMGeoAdmin):
    list_filter = ('route', 'service')
    list_display = ('trip_id', 'route', 'service', 'short_name',
                    'trip_headsign', 'direction_id')


class StopTimeAdmin(OSMGeoAdmin):
    list_filter = ('trip', 'stop', )
    list_display = ('trip_id', 'sequence', 'stop', 'arrival', 'departure', )

    def trip_id(self, obj):
        return obj.trip.trip_id


admin.site.register(Agency, AgencyAdmin)
admin.site.register(Stop, StopAdmin)
admin.site.register(Route, RouteAdmin)
admin.site.register(Trip, TripAdmin)
admin.site.register(Calendar, CalendarAdmin)
admin.site.register(CalendarDate, CalendarDateAdmin)
admin.site.register(FareAttribute, FareAttributeAdmin)
admin.site.register(FareRule, FareRuleAdmin)
admin.site.register(StopTime, StopTimeAdmin)
admin.site.register(Frequency, FrequencyAdmin)
