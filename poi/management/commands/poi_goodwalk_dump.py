from __future__ import print_function
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import GEOSGeometry
import json as j
import os
import sys


from poi.models import POI

HELP = '''Import POI from GoodWalk POI dump (json files)

./manage.py poi_goodwalk_dump <dir>
'''

class Command(BaseCommand):
    help = HELP

    def add_arguments(self, parser):
        parser.add_argument('dir', nargs='+', type=str)

    def help_and_exit(self, message=''):
        if message:
            print()
            print(message)
        print(self.help)
        sys.exit()

    def process_json(self, fpath):
        count = {'new': 0, 'exist': 0}
        with open(fpath, 'rt') as f:
            try:
                data = j.loads(f.read())
            except:
                return count
            if data['count'] == 0:
                return count
            for i in data['poi']:
                found = POI.objects.filter(gd_id=i['id'])
                print('  new: %(new)6d  -- exist: %(exist)6d' % count, end='\r')
                if found:
                    count['exist'] += 1
                    continue
                p = POI(gd_id=i['id'],
                        name=i['title'],
                        category=i['type'],
                        branch=i['branch'],
                        street=i['street'])
                lat, lon = i['latlong'].replace(' ', '').split(',')
                pnt = GEOSGeometry('POINT(%s %s)' % (lon, lat), srid=4326)
                p.location = pnt
                p.save()
                count['new'] += 1

        return count

    def handle(self, *args, **options):
        if not options['dir']:
            return self.help_and_exit('Directory needed')

        _path = options['dir'][0]
        print('path: ', _path)
        if not os.path.isdir(_path):
            return self.help_and_exit('Directory not found')

        subdirs = []
        for _, dirs, _ in os.walk(_path):
            for _d in dirs:
                subdirs.append(os.path.join(_path, _d))

        total = {'new': 0, 'exist': 0}
        msg = 'new: %6d  exist: %6d >> %s'
        for subdir in subdirs:
            for _, _, files in os.walk(subdir):
                for f in files:
                    fp = os.path.join(subdir, f)
                    print(msg % (total['new'], total['exist'], f))
                    res = self.process_json(fp)
                    total['new'] += res['new']
                    total['exist'] += res['exist']
                    print('\033[F', end='')

        print('')
        print('Summary:')
        print('  NEW: %(new)5d    EXIST: %(exist)5d' % total)
        print('')
