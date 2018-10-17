from __future__ import print_function
from django.core.management.base import BaseCommand, CommandError
from gtfs.models import (
    Agency, Route, FareRule, Frequency, Calendar, CalendarDate,
    StopTime, Stop, FareAttribute, Trip
)
from shutil import make_archive, rmtree
import tempfile
import sys
import csv
import os

help = '''
Export GTFS to the whole feed

./manage.py gtfs_feed <command> [options]

Command:
list          list available agency/route for exporting
export        output as gtfs zip

Options:
--output      zip name (default: output.zip)
--agency      agency_id with comma (,) as separator
--route       route_id with comma (,) as separator
              NOTE: route will override agency always
'''

class Command(BaseCommand):
    help = help
    header = Route.gtfs_header
    # google doesn't need this, then make them blank
    google_spec_optional = ['stop_desc', 'trip_short_name', 'route_short_name']

    def add_arguments(self, parser):
        parser.add_argument('op', nargs='+', type=str, help='list / export')
        parser.add_argument(
            '--output',
            action='store',
            dest='output',
            default='output',
            help='GTFS feed file name')
        parser.add_argument(
            '--agency',
            action='store',
            dest='agency_ids',
            default='',
            help='agency_id with comma (,) as separator')
        parser.add_argument(
            '--route',
            action='store',
            dest='route_ids',
            default='',
            help='route_id with comma (,) as separator')
        parser.add_argument(
            '--google',
            action='store_true',
            dest='google_spec',
            default=False,
            help='no stop_desc, no trip_short_name, no route_short_name')

    def help_and_exit(self, message=''):
        if message:
            print()
            print(message)
        print(self.help)
        sys.exit()

    def get_route(self, route_id):
        try:
            route = Route.objects.get(route_id=route_id)
            return route.gtfs_routes_format()
        except Route.DoesNotExist:
            return []

    def print_row(self, row):
        data = []
        for i in self.header.split(','):
            data.append(row[i])
        data = [i.encode('utf-8') for i in data]
        print(','.join(data))

    def list_possible_agency_and_route(self):
        rs = Route.objects.filter(trip__isnull=False).distinct()
        if rs.count():
            print('Route:')
            order = 1
            for r in rs:
                print('%s. %s' % (order, r.route_id))
                order += 1

        ags = Agency.objects.filter(route__isnull=False).distinct()
        if ags.count():
            print('Agency:')
            order = 1
            for a in ags:
                print('%s. %s' % (order, a.agency_id))
                order += 1

    def shapes_file(self, dir, route_qs):
        route_qs = route_qs.distinct()
        if not route_qs:  # just skip if there is nothing at all
            return
        _header = route_qs[0].shapes_gtfs_header
        with open(os.path.join(dir, 'shapes.txt'), 'a') as f:
            cf = csv.DictWriter(f, fieldnames=_header)
            cf.writeheader()
            for route in route_qs:
                for shape in route.export_to_shapes():
                    cf.writerow(shape)

    def gtfs_file(self, dir, queryset, filename, ):
        queryset = queryset.distinct()
        if not queryset:  # just skip if there is nothing at all
            return
        _header = queryset[0].gtfs_header
        with open(os.path.join(dir, filename), 'a') as f:
            cf = csv.DictWriter(f, fieldnames=_header)
            cf.writeheader()
            for row in queryset:
                data = row.gtfs_format()
                if self.google_spec:
                    for _field in self.google_spec_optional:
                        if _field in data:
                            data[_field] = ''
                cf.writerow(data)

    def handle_fare(self, agency):
        # fare_rules = FareRule.objects.filter(route__in=routes)
        # fare_attrs = FareAttribute.objects.filter(farerule__in=fare_rules)
        # self.gtfs_file(dir, fare_rules, 'fare_rules.txt')
        # self.gtfs_file(dir, fare_attrs, 'fare_attributes.txt')
        fare_attrs = FareAttributes.objects.filter(agency=agency)
        fare_rules = FareRule.objects.filter(fare__in=fare_attrs)
        return None

    def export_feed(self, routes, dir):
        # agency
        agencies = Agency.objects.filter(route__in=routes)
        self.gtfs_file(dir, agencies, 'agency.txt')

        # route
        self.gtfs_file(dir, routes, 'routes.txt')
        # shapes need special treatments
        self.shapes_file(dir, routes)

        # fare
        for agency in agencies:
            self.handle_fare(agency)

        # trip, shapes
        trips = Trip.objects.filter(route__in=routes)
        self.gtfs_file(dir, trips, 'trips.txt')

        # frequency
        freqs = Frequency.objects.filter(trip__in=trips)
        self.gtfs_file(dir, freqs, 'frequencies.txt')

        # stop_times, stop, transfer
        stoptimes = StopTime.objects.filter(trip__in=trips)
        stops = Stop.objects.filter(stoptime__in=stoptimes).distinct()
        self.gtfs_file(dir, stoptimes, 'stop_times.txt')
        self.gtfs_file(dir, stops, 'stops.txt')

        # Calendar
        srv_ids = [s['service'] for s in trips.values('service').distinct()]
        calendars = Calendar.objects.filter(pk__in=srv_ids)
        cal_exceptions = CalendarDate.objects.filter(service__in=calendars)
        self.gtfs_file(dir, calendars, 'calendar.txt')
        self.gtfs_file(dir, cal_exceptions, 'calendar_dates.txt')


    def handle(self, *args, **options):
        self.google_spec = options['google_spec']
        print('Google spec: {}'.format('enabled' if self.google_spec else 'disabled'))

        if 'list' in options['op']:
            return self.list_possible_agency_and_route()

        if 'export' in options['op']:
            agency_ids = options['agency_ids']
            route_ids = options['route_ids']
            if route_ids:
                rts = Route.objects.filter(route_id__in=route_ids.split(','))
            elif agency_ids:
                q = { 'agency__agency_id__in': agency_ids.split(',') }
                rts = Route.objects.filter(**q)
            else:
                self.help_and_exit('Missing parameters')

            if not rts:
                self.help_and_exit('Route could not be found')

            tmpdir = tempfile.mkdtemp()
            try:
                _build = os.path.join(tmpdir, '_build')
                print(_build)
                if not os.path.isdir(_build):
                    os.mkdir(_build)
                self.export_feed(rts, _build)
                print(options['output'])
                # data = open(make_archive(tmparchive, 'zip', root_dir), 'rb').read()
                make_archive(options['output'], 'zip', _build)
            finally:
                rmtree(tmpdir)
                pass
            return

        self.help_and_exit()
