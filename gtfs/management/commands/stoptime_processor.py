from __future__ import print_function
from django.core.management.base import BaseCommand, CommandError
from gtfs.models import (Agency, Route, FareRule, Frequency, Calendar,
                         CalendarDate, StopTime, Stop, FareAttribute, Trip)
from shutil import make_archive, rmtree
from datetime import datetime, timedelta
import tempfile
import sys
import csv
import os

HELP = '''
Export GTFS to the whole feed

./manage.py stoptime_processor [options]

Options:
--input      input file
             e.g.
             trip_id,stop_id
             ZZ01,PK001

or

--trip       trip_id that we need to process
--stops      stop_id with comma (,) as separator
'''


KMPH = 30


class Command(BaseCommand):
    help = HELP

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Force re-processing stoptime arrival ' \
              'time although it already has')
        parser.add_argument(
            '--input',
            action='store',
            dest='input_file',
            default='',
            help='Input csv file with header: trip_id, stop_id')
        parser.add_argument(
            '--trip',
            action='store',
            dest='trip_id',
            default='',
            help='Trip we need to add StopTime')
        parser.add_argument(
            '--stops',
            action='store',
            dest='stop_ids',
            default='s',
            help='Stops that will align to the trip')

    def help_and_exit(self, message=''):
        if message:
            print()
            print(message)
        print(self.help)
        sys.exit()

    def process_trip_stoptime(self, trip, **kwargs):
        """Complete sequence of each stop and find the est. arrival time
        for each stop

        1. find linear_ref of every stops
            * get sequence
        2. find distance from linear_ref of every stop
            * get km -> travel time (considering a constant 30-kmph speed)
        """
        stoptimes = trip.stoptime_set.all()
        # is_completed = (
        #     stoptimes.filter(arrival__isnull=True).count() == 0 or
        #     stoptimes.filter(sequence=0).count() == 1
        # )
        stoptimes_total = stoptimes.count()
        if stoptimes_total > 0 and kwargs.get('force') is not True:
            return 'No need to process'

        if stoptimes_total == 0 and not kwargs.get('stops'):
            return 'No stop to work on'

        route = trip.route
        company = trip.company
        route_km = route.route_length
        speed = KMPH if route_km > 20 else KMPH * 0.7
        today = datetime.today()
        start = today.replace(hour=8, minute=0, second=0, microsecond=0)
        print('Route (km): {0:.2f}'.format(route_km))
        print('Time (min): {0:.2f}'.format(route_km / speed * 60))

        def add_arrival(stop):
            item = {
                'stop': stop,
                'linear_ref': route.line_locate_point(stop.location.coords),
            }
            minutes = item['linear_ref'] * route_km / speed * 60
            minutes = '{0:.1f}'.format(minutes)
            dt = start + timedelta(minutes=float(minutes))
            item['arrival'] = dt.strftime('%H:%M:%S')
            return item

        stopseq = map(add_arrival, kwargs.get('stops'))
        ordered_stopseq = sorted(stopseq, key=lambda i: i['linear_ref'])

        seq = 0
        # clear up stoptime related to this trip first
        trip.stoptime_set.all().delete()
        # then build a new list of stoptime
        for i in ordered_stopseq:
            seq += 1
            st = StopTime(stop=i['stop'], trip=trip, company=company)
            st.sequence = seq
            st.arrival = '08:00' if seq == 1 else i['arrival']
            st.departure = '08:00' if seq == 1 else i['arrival']
            st.pickup_type = '0' if seq == 1 else '3'
            st.drop_off_type = '3'
            st.timepoint = '0'
            st.save()

        return trip.stoptime_set.all()

    def get_stop_in_object(self, stops):
        return map(lambda i: Stop.objects.get(stop_id=i), stops)

    def handle_file(self, fp):
        result = {}
        with open(fp, 'rt') as f:
            cf = csv.DictReader(f)
            for row in cf:
                if row['route_id'] not in result:
                    result[row['route_id']] = []
                result[row['route_id']].append(row['stop_id'])

        for route_id, stop_ids in result.items():
            print('Route: {}'.format(route_id), end=' ')
            route = Route.objects.get(route_id=route_id)
            company = route.company
            trip = route.get_one_trip()
            print('Trip: {}'.format(trip))
            stops = self.get_stop_in_object(stop_ids)
            res = self.process_trip_stoptime(trip, stops=stops, force=True)
            print(res)

    def handle(self, *args, **options):
        force = options['force']
        fp = options['input_file']
        # TODO: handle input file with multiple trip_id
        trip_id = options['trip_id']
        stop_ids_arg = options['stop_ids']

        if not (fp or (trip_id and stop_ids_arg)):
            self.help_and_exit()

        # file has higher priority
        if fp:
            print('FILE mode')
            self.handle_file(fp)
        elif trip_id and stop_ids_arg:
            stop_ids = map(lambda i: i.strip(), stop_ids_arg.split(','))
            stops = self.get_stop_in_object(stop_ids)
            trip = Trip.objects.get(trip_id=trip_id)
            print('Trip: {}'.format(trip))
            result = self.process_trip_stoptime(trip, stops=stops, force=force)
            print(result)

        self.help_and_exit()
