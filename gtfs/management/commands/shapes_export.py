from __future__ import print_function
from django.core.management.base import BaseCommand, CommandError
from gtfs.models import Route
import sys

help = '''
Export route to shapes.txt

./manage.py shapes_export <command> [options]

Command:
list       list available route for exporting
export     use with --route_id to have shapes.txt data

Options:
--route_id   route_id with comma (,) as separator
'''

class Command(BaseCommand):
    help = help
    header = Route.shapes_gtfs_header

    def add_arguments(self, parser):
        parser.add_argument('op', nargs='+', type=str)
        parser.add_argument('--route_id',
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

    def get_routes_shapes(self, route_id):
        try:
            route = Route.objects.get(route_id=route_id)
            return route.export_to_shapes()
        except Route.DoesNotExist:
            return []

    def print_header(self):
        print(self.header)

    def print_row(self, row):
        data = []
        for i in self.header.split(','):
            data.append(row[i])
        data = [str(i) for i in data]
        print(','.join(data))

    def handle(self, *args, **options):
        if 'list' in options['op']:
            routes = Route.objects.filter(shapes__isnull=False)
            ind = 1
            for route in routes:
                print('%3d. %s' % (ind, route.route_id))
                ind += 1
            return

        if 'export' in options['op']:
            if 'route_id' not in options:
                self.help_and_exit()
            route_ids = options['route_id']
            shapes = []
            for route_id in route_ids.split(','):
                _shapes = self.get_routes_shapes(route_id)
                if _shapes:
                    shapes += _shapes
            if not shapes:
                self.help_and_exit('There is no route or shapes found')

            self.print_header()
            for row in shapes:
                self.print_row(row)
            return

        self.help_and_exit()
