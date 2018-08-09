from __future__ import print_function
from django.core.management.base import BaseCommand, CommandError
from gtfs.models import (Agency, Route, FareRule, Frequency, Calendar,
                         CalendarDate, StopTime, Stop, FareAttribute, Trip)
from shutil import make_archive, rmtree
import tempfile
import sys
import csv
import os

HELP = '''
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


KM_PER_HR = 30
KM_PER_MIN = 0.5


class Command(BaseCommand):
    help = HELP
    header = Route.gtfs_header

    def add_arguments(self, parser):
        parser.add_argument('op', nargs='+', type=str)
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default='force',
            help='Force re-processing stoptime arrival ' \
              'time although it already has')
        parser.add_argument(
            '--input',
            action='store',
            dest='input_file',
            default='input_file',
            help='Input data')
        parser.add_argument(
            '--trip',
            action='store',
            dest='trip_id',
            default='trip_id',
            help='Input data')

    def help_and_exit(self, message=''):
        if message:
            print()
            print(message)
        print(self.HELP)
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
        stop_seq_time = [{
            stop: s,
            linear_ref: route.line_locate_point(s.location.coords),
            arrival: None,
        } for s in kwargs.get('stops')]
        ordered_stopseq = sorted(stop_seq_time, key=lambda i: i['linear_ref'])
        route_km = route.route_length
        ordered_stopseq = map(
            lambda i: i['arrival']=i['linear_ref'] * route_km * KM_PER_MIN,
            ordered_stopseq)
        print(ordered_stopseq)

    def get_stop_in_object(self, stops):
        return map(lambda i: Stop.objects.get(stop_id=i), stops)

    def handle(self, *args, **options):
        fp = options['input_file']
        trip_id = options['trip_id']
        if not (fp or trip_id):
            self.help_and_exit()
        ssss = [
            'pt-1-37', 'pt-2-22', 'pt-2-23', 'pt-2-24', 'pt-2-27', 'PK143',
            'PK244', 'PK245', 'PK246', 'PK249', 'PK20', 'PK19', 'PK250',
            'PK16', 'PK252', 'PK15'
        ]
        trip = Trip.objects.get(trip_id=trip_id)
        self.process_trip_stoptime(trip, stops=ssss)
        self.help_and_exit()
