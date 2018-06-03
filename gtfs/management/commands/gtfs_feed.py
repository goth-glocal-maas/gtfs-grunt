from __future__ import print_function
from django.core.management.base import BaseCommand, CommandError
from gtfs.models import Agency, Route
import sys

help = '''
Export GTFS to the whole feed

./manage.py gtfs_feed <command> [options]

Command:
list          list available agency/route for exporting
export        output as gtfs zip

Options:
--output      zip name (default: output.zip)
--route       route_id with comma (,) as separator
--agency      agency_id with comma (,) as separator
              NOTE: agency will override route always
'''

class Command(BaseCommand):
    help = help
    header = Route.gtfs_header

    def add_arguments(self, parser):
        parser.add_argument('op', nargs='+', type=str)
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

    def print_header(self):
        print(self.header)

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

    def handle(self, *args, **options):
        if 'list' in options['op']:
            return self.list_possible_agency_and_route()

        if 'export' in options['op']:
            pass

        self.help_and_exit()
