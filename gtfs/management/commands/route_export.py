from __future__ import print_function
from django.core.management.base import BaseCommand, CommandError
from gtfs.models import Agency, Route
import sys

help = '''
Export route to route.txt

./manage.py route_export <command> [options]

Command:
list          list available route for exporting
list_agnecy   list available agencies
export        use with --route_id to have routes.txt data

Options:
--route_id   route_id with comma (,) as separator
'''

class Command(BaseCommand):
    help = help
    header = Route.gtfs_header

    def add_arguments(self, parser):
        parser.add_argument('op', nargs='+', type=str)
        parser.add_argument(
            '--agency',
            action='store',
            dest='agency_id',
            default='',
            help='Export all routes belong to this agency')
        parser.add_argument(
            '--route_id',
            action='store',
            dest='route_id',
            default='',
            help='Route ID (, as separator)')

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

    def handle(self, *args, **options):
        if 'list' in options['op']:
            routes = Route.objects.all()
            ind = 1
            for route in routes:
                print('%3d. %s' % (ind, route.route_id))
                ind += 1
            return

        if 'list_agency' in options['op']:
            agencies = Agency.objects.all()
            ind = 1
            for agency in agencies:
                print('%3d. %s' % (ind, agency.agency_id))
                ind += 1
            return

        if 'export' in options['op']:
            if 'route_id' not in options or 'agency_id' not in options:
                self.help_and_exit()
            if 'agency_id' in options:
                try:
                    agency = Agency.objects.get(agency_id=options['agency_id'])
                except Agency.DoesNotExist:
                    self.help_and_exit('Agency is not found')
                routes = Route.objects.filter(agency=agency)
            else:
                route_ids = options['route_id']
                routes = []
                for route_id in route_ids.split(','):
                    _route = self.get_route(route_id)
                    if _route:
                        routes += _route
            if not routes:
                self.help_and_exit('There is no route or route found')

            self.print_header()
            for row in routes:
                self.print_row(row.gtfs_routes_format())
            return

        self.help_and_exit()
