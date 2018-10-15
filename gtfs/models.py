# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.gis.db.models import (
    Model, CharField, IntegerField, DateField, BooleanField, ForeignKey,
    LineStringField, EmailField, PointField, DecimalField, TimeField,
)
from django.utils import timezone
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import GEOSGeometry
from django.db import connection
from collections import OrderedDict


class CompanyBoundModel(Model):
    company = ForeignKey('people.Company')

    class Meta:
        abstract = True

    @property
    def gtfs_header(self):
        raise NotImplementedError("Please Implement this property")


@python_2_unicode_compatible
class Agency(CompanyBoundModel):
    """Transit agencies that provide the data in this feed.

    """
    agency_id = CharField('agency_id', max_length=25)
    name = CharField('Agency Name', max_length=500)
    url = CharField('Agency URL', max_length=240, blank=True)
    timezone = CharField('Agency Timezone', max_length=50, blank=True)
    phone = CharField('Agency Phone', max_length=50, blank=True)
    lang = CharField('Agency Language', max_length=10, blank=True)
    fare_url = CharField('Agency URL', max_length=240, blank=True)
    email = EmailField('Email', blank=True)

    class Meta:
        unique_together = ('company', 'agency_id')
        verbose_name_plural = "agencies"

    def __str__(self):
        return self.agency_id

    @property
    def gtfs_header(self):
        return [
            'agency_id', 'agency_name', 'agency_url', 'agency_timezone',
            'agency_phone', 'agency_lang', 'agency_fare_url', 'agency_email'
        ]

    def gtfs_format(self):
        data = [
            ('agency_id', self.agency_id),
            ('agency_name', self.name.encode('utf-8')),
            ('agency_url', self.url),
            ('agency_timezone', self.timezone),
            ('agency_phone', self.phone),
            ('agency_lang', self.lang),
            ('agency_fare_url', self.fare_url),
            ('agency_email', self.email),
        ]
        return OrderedDict(data)


@python_2_unicode_compatible
class Stop(CompanyBoundModel):
    """Individual locations where vehicles pick up or drop off passengers.

    "stop_id", "stop_code", "stop_name", "stop_desc", "stop_lat",
		"stop_lon", "zone_id", "stop_url", "location_type", "parent_station",
		"direction"

    stop_id,stop_name,stop_desc,stop_lat,stop_lon,stop_url,location_type,parent_station

    """
    stop_id = CharField('stop_id', max_length=25)
    name = CharField('name', max_length=500)
    location = PointField('Location')
    # optinal
    stop_code = CharField('Stop code', max_length=100, blank=True)
    stop_desc = CharField('Stop code', max_length=500, blank=True)
    zone_id = CharField('Zone ID', max_length=100, blank=True)
    LOCATION_TYPES = (
        ('0', 'Stop'),
        ('1', 'Station'),
        ('2', 'Station Entrance/Exit'),
    )
    location_type = CharField('Location types', max_length=1,
                              default='0', choices=LOCATION_TYPES)
    parent_station = ForeignKey('Stop', null=True, blank=True)
    stop_timezone = CharField('Stop timezone', max_length=20, blank=True)
    WHEELCHAIR_CHOICES = (
        ('0', 'No wheelchair accessibility'),
        ('1', 'at least some vehicles at this stop can be boarded ' \
              'by a rider in a wheelchair'),
        ('2', 'wheelchair boarding is not possible at this stop'),
    )
    wheelchair_boarding = CharField('Wheelchair boarding', max_length=1,
                                    default='0', choices=WHEELCHAIR_CHOICES)

    class Meta:
        unique_together = ('company', 'stop_id')

    def __str__(self):
        return self.stop_id

    @property
    def gtfs_header(self):
        return [
            'stop_id', 'stop_name', 'stop_desc', 'stop_lat', 'stop_lon',
            'zone_id', 'stop_url', 'location_type', 'parent_station',
        ]

    def gtfs_format(self):
        _parent = self.parent_station.stop_id if self.parent_station else ''
        data = [
            ('stop_id', self.stop_id.encode('utf-8')),
            ('stop_name', self.name.encode('utf-8')),
            ('stop_desc', self.stop_desc.encode('utf-8')),
            ('stop_lat', self.location.coords[1]),
            ('stop_lon', self.location.coords[0]),
            ('zone_id', self.zone_id),
            ('stop_url', ''),
            ('location_type', self.location_type),
            ('parent_station', _parent),
        ]
        return OrderedDict(data)

    def merge_with(self, another_stop):
        # change stop_times to this stop
        another_stop.stoptime_set.all().update(stop=self)
        # NOTE: if Transfer introduces, then should add something here too
        another_stop.delete()

    def distance(self, coords):
        if not self.location:
            return None
        lon, lat = coords
        pnt = GEOSGeometry('POINT(%s %s)' % (lon, lat), srid=4326)
        qs = Stop.objects.filter(pk=self.pk)
        return qs.annotate(distance=Distance('location', pnt))[0].distance


@python_2_unicode_compatible
class Route(CompanyBoundModel):
    """Transit routes. A route is a group of trips that are displayed to riders
    as a single service.

    # GTFS Feed

    ## routes.txt

    This is obvious, basic fields

        "route_id", "agency_id", "route_short_name", "route_long_name",
		"route_desc", "route_type", "route_url", "route_color",
		"route_text_color"

    ## shapes.txt

    This is generated by `self.shapes` for `trips.txt`

    ### required

    shape_id,
    shape_pt_lat,
    shape_pt_lon,
    shape_pt_sequence,

    ### optional

    shape_dist_traveled (in km)


    """
    route_id = CharField('route_id', max_length=25)
    short_name = CharField('short name', max_length=150)
    long_name = CharField('long name', max_length=500)
    shapes = LineStringField(srid=4326, null=True, blank=True)

    agency = ForeignKey('Agency', blank=True, null=True)
    desc = CharField('Route desc', max_length=250, blank=True)
    ROUTE_TYPES = (
        ('0', 'Tram, Streetcar, Light rail'),
        ('1', 'Subway, Metro. Any underground rail system ' \
              'within a metropolitan area.'),
        ('2', 'Rail'),
        ('3', 'Bus'),
        ('4', 'Ferry'),
        ('5', 'Cable car'),
        ('6', 'Gondola, Suspended cable car'),
        ('7', 'Funicular. Any rail system designed for steep inclines.'),
    )
    route_type = CharField('Route type', max_length=1,
                           default='2', choices=ROUTE_TYPES)
    route_url = CharField('Route URL', max_length=240, blank=True)
    route_color = CharField('Route color', max_length=6, blank=True)
    route_text_color = CharField('Route text color', max_length=6, blank=True)
    route_sort_order = IntegerField('Route sort order', default=0, blank=True)

    class Meta:
        unique_together = ('company', 'route_id')
        ordering = ('agency', 'route_id')

    def __str__(self):
        return self.route_id

    @property
    def route_length(self):
        '''return length of line in meter

        it does need to project to another system; otherwise,
        we'll get length in degree

        ref: https://gis.stackexchange.com/questions/180776/
             get-linestring-length-in-meters-python-geodjango#181251
        '''
        if not self.shapes:
            return -1

        l = self.shapes
        l.transform(3857)
        _m = l.length
        return _m / 1000.0

    def line_locate_point(self, coords):
        if not self.shapes:
            return None
        lon, lat = coords
        cursor = connection.cursor()
        q = 'SELECT ST_LineLocatePoint(shapes, ' \
            'ST_SetSRID(ST_Point(%s,%s),4326))' \
            ' FROM gtfs_route WHERE id=%s'
        cursor.execute(q, [lon, lat, self.pk])
        row = cursor.fetchone()
        return row[0]

    @property
    def gtfs_header(self):
        return [
            'route_type', 'route_id', 'route_short_name', 'route_long_name',
            'agency_id', 'route_url', 'route_color', 'route_text_color',
            'route_sort_order'
        ]

    @property
    def routes_gtfs_header(self):
        return self.gtfs_header

    @property
    def shapes_gtfs_header(self):
        return [
            'shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence'
        ]

    def gtfs_format(self):
        data = [
            ('route_type', self.route_type),
            ('route_id', self.route_id.encode('utf-8')),
            ('route_short_name', self.short_name.encode('utf-8')),
            ('route_long_name', self.long_name.encode('utf-8')),
            ('agency_id', self.agency.agency_id),
            ('route_url', self.route_url.encode('utf-8')),
            ('route_color', self.route_color.upper()),
            ('route_text_color', self.route_text_color.upper()),
            ('route_sort_order', str(self.route_sort_order)),
        ]
        return OrderedDict(data)

    def export_to_shapes(self):
        """Export to shapes

        Output:
        list of dict for shapes.txt
        """
        if not self.shapes:
            return []
        results = []
        seq = 1
        for o in self.shapes.coords:
            _ = [
                ('shape_id', self.route_id),
                ('shape_pt_lat', o[1]),
                ('shape_pt_lon', o[0]),
                ('shape_pt_sequence', seq),
            ]
            seq += 1
            results.append(OrderedDict(_))
        return results

    def get_one_trip(self):
        trips = self.trip_set.all()
        if trips.exists():
            return trips[0]
        trip_id = '{}01'.format(self.route_id)
        calendar = Calendar.objects.all()[0]
        t = Trip(company=self.company,
                 route=self,
                 trip_id=trip_id,
                 service=calendar,
                 direction_id='0')
        t.save()
        return t


@python_2_unicode_compatible
class StopTime(CompanyBoundModel):
    """
    "trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence",
		"stop_headsign", "pickup_type", "drop_off_type", "shape_dist_traveled",
		"timepoint", "continuous_drop_off", "continuous_pickup"

    """
    trip = ForeignKey('trip')
    stop = ForeignKey('stop')
    arrival = TimeField('Arrival time')
    departure = TimeField('Departure time')
    sequence = IntegerField('Stop sequence', default=0)
    # optional
    stop_headsign = CharField('Stop headsign', max_length=30, blank=True)
    PICKUP_CHOICES = (
        ('0', 'Regularly scheduled pickup'),
        ('1', 'No pickup available'),
        ('2', 'Must phone agency to arrange pickup'),
        ('3', 'Must coordinate with driver to arrange pickup'),
    )
    pickup_type = CharField('Pickup type', max_length=1, default='0',
                            choices=PICKUP_CHOICES)
    DROPOFF_CHOICES = (
        ('0', 'Regularly scheduled drop off'),
        ('1', 'No drop off available'),
        ('2', 'Must phone agency to arrange drop off'),
        ('3', 'Must coordinate with driver to arrange drop off'),
    )
    drop_off_type = CharField('Drop off type', max_length=1, default='0',
                              choices=DROPOFF_CHOICES)
    shape_dist_traveled = CharField('Travel distance in km', max_length=5,
                                    blank=True)
    TIMEPOINT_CHOICES = (
        ('', 'Times are considered exact.'),
        ('0', 'Times are considered approximate.'),
        ('1', 'Times are considered exact.'),
    )
    timepoint = CharField('Timepoint', max_length=1, default='',
                          choices=TIMEPOINT_CHOICES)

    class Meta:
        verbose_name_plural = "Stop times"
        ordering = ['sequence', ]

    def __str__(self):
        return 'trip #%s seq#%s-%s' % (
            self.trip.id, self.sequence, self.arrival)

    @property
    def gtfs_header(self):
        return [
            'trip_id', 'arrival_time', 'departure_time', 'stop_id',
            'stop_sequence', 'stop_headsign', 'pickup_type', 'drop_off_type',
            'shape_dist_traveled', 'timepoint'
        ]

    def gtfs_format(self):
        data = [
            ('trip_id', self.trip.trip_id),
            ('arrival_time', self.arrival),
            ('departure_time', self.departure),
            ('stop_id', self.stop.stop_id.encode('utf-8')),
            ('stop_sequence', self.sequence),
            ('stop_headsign', self.stop_headsign.encode('utf-8')),
            ('pickup_type', self.pickup_type),
            ('drop_off_type', self.drop_off_type),
            ('shape_dist_traveled', self.shape_dist_traveled),
            ('timepoint', self.timepoint),
        ]
        return OrderedDict(data)


@python_2_unicode_compatible
class Calendar(CompanyBoundModel):
    """This indicates normal service set
    """
    service_id = CharField('service_id', max_length=25, unique=True)
    start_date = DateField('Start Date', default=timezone.now)
    end_date = DateField('Start Date', default=timezone.now)
    monday = BooleanField('Monday', default=False)
    tuesday = BooleanField('Tuesday', default=False)
    wednesday = BooleanField('Wednesday', default=False)
    thursday = BooleanField('Thursday', default=False)
    friday = BooleanField('Friday', default=False)
    saturday = BooleanField('Saturday', default=False)
    sunday = BooleanField('Sunday', default=False)

    class Meta:
        unique_together = ('company', 'service_id')

    def __str__(self):
        return self.service_id

    @property
    def gtfs_header(self):
        return [
            'service_id', 'monday', 'tuesday', 'wednesday', 'thursday',
            'friday', 'saturday', 'sunday', 'start_date', 'end_date'
        ]

    def gtfs_format(self):
        data = [
            ('service_id', self.service_id),
            ('monday', '1' if self.monday else '0'),
            ('tuesday', '1' if self.tuesday else '0'),
            ('wednesday', '1' if self.wednesday else '0'),
            ('thursday', '1' if self.thursday else '0'),
            ('friday', '1' if self.friday else '0'),
            ('saturday', '1' if self.saturday else '0'),
            ('sunday', '1' if self.sunday else '0'),
            ('start_date', self.start_date.strftime('%Y%m%d')),
            ('end_date', self.end_date.strftime('%Y%m%d')),
        ]
        return OrderedDict(data)


@python_2_unicode_compatible
class CalendarDate(CompanyBoundModel):
    """This is an exception for Calendar
    """
    EXCEPTION_TYPES = (
        ('1', 'Add to service'),
        ('2', 'Remove from service'),
    )
    service = ForeignKey(Calendar)
    date = DateField('Date')
    exception_type = CharField('Exception Type', max_length=1,
                               default='2',
                               choices=EXCEPTION_TYPES)

    class Meta:
        verbose_name_plural = "Calendar Dates"

    def __str__(self):
        return '%s-%s' % (self.pk, self.date)

    @property
    def gtfs_header(self):
        return 'service_id,date,exception_type'

    def gtfs_format(self):
        data = [
            ('service_id', self.service.service_id),
            ('date', self.date.strftime('%Y-%m-%d')),
            ('exception_type', self.exception_type),
        ]
        return OrderedDict(data)


@python_2_unicode_compatible
class Trip(CompanyBoundModel):
    """
    route_id,service_id,trip_id,trip_headsign,block_id
    """
    route = ForeignKey(Route)
    service = ForeignKey(Calendar)
    trip_id = CharField('trip_id', max_length=50)
    # optional
    trip_headsign = CharField('Trip headsign', max_length=30, blank=True)
    short_name = CharField('Trip short name', max_length=150, blank=True)
    DIRECTION_CHOICES = (
        ('0', 'travel in one direction (e.g. outbound travel)'),
        ('1', 'travel in the opposite direction (e.g. inbound travel)'),
    )
    direction_id = CharField('Direction', max_length=1, default='',
                             choices=DIRECTION_CHOICES)
    block_id = CharField('Block ID', max_length=15, blank=True)

    WHEELCHAIR_ACCESSIBLE_CHOICES = (
        ('', 'No wheelchair accessibility'),
        ('0', 'No wheelchair accessibility'),
        ('1', 'indicates that the vehicle being used on this particular '
              'trip can accommodate at least one rider in a wheelchair'),
        ('2', 'No riders in wheelchairs can be accommodated '
              'on this trip'),
    )
    wheelchair_accessible = CharField(
        'Wheelchair accessible',
        max_length=1,
        default='',
        choices=WHEELCHAIR_ACCESSIBLE_CHOICES)

    BIKE_CHOICES = (
        ('', 'indicates that there is no bike information for the trip'),
        ('0', 'indicates that there is no bike information for the trip'),
        ('1', 'indicates that the vehicle being used on this particular '
              'trip can accommodate at least one bicycle'),
        ('2', 'No bicycles are allowed on this trip'),
    )
    bike_allowed = CharField(
        'Wheelchair accessible',
        max_length=1,
        default='',
        choices=BIKE_CHOICES)

    class Meta:
        ordering = ('trip_id', )

    def __str__(self):
        return self.trip_id

    @property
    def gtfs_header(self):
        return [
            'route_id', 'service_id', 'trip_id', 'trip_headsign',
            'trip_short_name', 'direction_id', 'block_id', 'shape_id',
            'wheelchair_accessible', 'bikes_allowed'
        ]

    def gtfs_format(self):
        has_shape = self.route.shapes
        data = [
            ('route_id', self.route.route_id),
            ('service_id', self.service.service_id),
            ('trip_id', self.trip_id),
            ('trip_headsign', self.trip_headsign.encode('utf-8')),
            ('trip_short_name', self.short_name.encode('utf-8')),
            ('direction_id', self.direction_id),
            ('block_id', self.block_id),
            ('shape_id', self.route.route_id if has_shape else ''),
            ('wheelchair_accessible', self.wheelchair_accessible),
            ('bikes_allowed', self.bike_allowed),
        ]
        return OrderedDict(data)


@python_2_unicode_compatible
class FareAttribute(CompanyBoundModel):
    """Fare information for a transit organization's routes.

    currency_type          e.g. USD, THB
                           http://en.wikipedia.org/wiki/ISO_4217
    transfer_duration      When used with a transfers value of 0, the
                           transfer_duration field indicates how long a ticket
                           is valid for a fare where no transfers are allowed.
                           Unless you intend to use this field to indicate
                           ticket validity, transfer_duration should be omitted
                           or empty when transfers is set to 0.
    """
    fare_id = CharField('trip_id', max_length=50)
    price = DecimalField('Price', default=0.0, decimal_places=2, max_digits=6)
    currency_type = CharField('Currency type', max_length=3)
    PAYMENT_CHOICES = (
        ('0', 'Fare is paid on board'),
        ('1', 'Fare must be paid before boarding')
    )
    payment_method = CharField('Payment method', max_length=1, default='0',
                               choices=PAYMENT_CHOICES)
    TRANSFER_CHOICES = (
        ('', 'unlimited transfers are permitted.'),
        ('0', 'No transfers permitted on this fare.'),
        ('1', 'Passenger may transfer once.'),
        ('2', 'Passenger may transfer twice.'),
    )
    transfer = CharField('Transfer', max_length=1, default='0',
                         choices=TRANSFER_CHOICES)
    # optional
    agency = ForeignKey('Agency', null=True, blank=True,
                        related_name='fare_agency')
    transfer_duration = CharField('Transfer duration', max_length=4)

    class Meta:
        unique_together = ('company', 'fare_id')

    def __str__(self):
        return self.pk

    @property
    def gtfs_header(self):
        return [
            'fare_id', 'price', 'currency_type', 'payment_method', 'transfers',
            'transfer_duration'
        ]

    def gtfs_format(self):
        data = [
            ('fare_id', self.fare.fare_id),
            ('price', self.route.route_id),
            ('currency_type', self.currency_type),
            ('payment_method', self.payment_method),
            ('transfers', self.transfer),
            ('agency_id', self.agency.agency_id),
            ('transfer_duration', self.transfer_duration),
        ]
        return OrderedDict(data)


@python_2_unicode_compatible
class FareRule(CompanyBoundModel):
    """The fare_rules table allows you to specify how fares in
    fare_attributes.txt apply to an itinerary. Most fare structures use some
    combination of the following rules:

    * Fare depends on origin or destination stations.
    * Fare depends on which zones the itinerary passes through.
    * Fare depends on which route the itinerary uses.

    https://code.google.com/archive/p/googletransitdatafeed/wikis/FareExamples.wiki
    """
    fare = ForeignKey('FareAttribute')

    '''optional

    it's overly complicated for zoning thing
    https://developers.google.com/transit/gtfs/reference/#fare_attributestxt
    '''
    route = ForeignKey('Route', blank=True, null=True)
    origin_id = CharField('Origin ID', max_length=100)
    destination_id = CharField('Destination ID', max_length=100)
    contains_id = CharField('Contains ID', max_length=100)

    def __str__(self):
        return self.pk

    @property
    def gtfs_header(self):
        return [
            'fare_id', 'route_id', 'origin_id', 'destination_id', 'contains_id'
        ]

    def gtfs_format(self):
        data = [
            ('fare_id', self.fare.fare_id),
            ('route_id', self.route.route_id),
            ('origin_id', ''),
            ('destination_id', ''),
            ('contains_id', ''),
        ]
        return OrderedDict(data)


@python_2_unicode_compatible
class Frequency(CompanyBoundModel):
    """Headway (time between trips) for routes with variable frequency of
    service.

    This will be used instead of writing so many stop_times.txt; however,
    transitfeed.ScheduleViewer can't verified or display them yet.

    headway_secs    the time between departures from the same stop (headway)
                    for this trip type, during the time interval specified by
                    start_time and end_time. The headway value must be entered
                    in seconds.
    """
    trip = ForeignKey('Trip')
    start_time = TimeField('Start time')
    end_time = TimeField('End time')
    headway_secs = IntegerField('Headway seconds', default=1800)
    # optional
    EXACT_TIME_CHOICES = (
        ('0', 'Frequency-based trips are not exactly scheduled.'),
        ('1', 'Frequency-based trips are exactly scheduled'),
        # For a frequencies.txt row, trips are scheduled starting with
        # trip_start_time = start_time + x * headway_secs for all x in
        # (0, 1, 2, ...) where trip_start_time < end_time.
    )
    exact_times = CharField(
        'Exact times', max_length=1, default='0', choices=EXACT_TIME_CHOICES)

    class Meta:
        verbose_name_plural = "Frequencies"


    def __str__(self):
        return '%s [%s-%s] %s' % (
            self.trip.trip_id, self.start_time, self.end_time,
            self.headway_secs)

    @property
    def gtfs_header(self):
        return [
            'trip_id', 'start_time', 'end_time', 'headway_secs', 'exact_times'
        ]

    def gtfs_format(self):
        data = [
            ('trip_id', self.trip.trip_id),
            ('start_time', self.start_time),
            ('end_time', self.end_time),
            ('headway_secs', self.headway_secs),
            ('exact_times', self.exact_times),
        ]
        return OrderedDict(data)
