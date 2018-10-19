from django.urls import reverse
from django.contrib.gis.geos import GEOSGeometry
from json import dumps
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from rest_framework_jwt import utils
from rest_framework.utils.serializer_helpers import ReturnDict
from people.models import *
from gtfs.models import *
from gtfs.serializers import *


class GtfsApiTests(APITestCase):

    def setUp(self):
        # self.csrf_client = APIClient(enforce_csrf_checks=True)
        # company
        self.user = User.objects.create_user("test_user", "test@user.com", "123456")
        company = Company.objects.create(name='God', slug='god')
        company.users.add(self.user)
        # agency
        self.owl = Agency.objects.create(agency_id='owl', name='OWL',
                                         company=company)
        # route
        self.route = Route.objects.create(
            route_id='route_test',
            short_name='test_short',
            long_name='test_long',
            company=company)
        # stop
        pnt_a = GEOSGeometry('POINT(98 7)', srid=4326)
        pnt_b = GEOSGeometry('POINT(98.1 7.1)', srid=4326)
        pnt_c = GEOSGeometry('POINT(98.2 7.2)', srid=4326)
        self.stop_a = Stop.objects.create(stop_id='S01', name='01-A', location=pnt_a, company=company)
        self.stop_b = Stop.objects.create(stop_id='S02', name='02-B', location=pnt_b, company=company)
        self.stop_c = Stop.objects.create(stop_id='S03', name='03-C', location=pnt_c, company=company)
        # fare-attribute
        self.fare50 = FareAttribute.objects.create(
            fare_id='fare-50',
            price=50,
            currency_type='THB',
            transfer_duration='0',
            company=company,
        )
        self.fare100 = FareAttribute.objects.create(
            fare_id='owl-fare-100',
            price=100,
            currency_type='THB',
            transfer_duration='0',
            agency=self.owl,
            company=company,
        )
        self.fare150 = FareAttribute.objects.create(
            fare_id='owl-fare-150',
            price=150,
            currency_type='THB',
            transfer_duration='0',
            agency=self.owl,
            company=company,
        )

    def test_create_fare_rule(self):
        """
        Ensure we can create a new account object.
        """
        serialized_fare50 = FareAttributeSerializer(self.fare50).data
        serialized_fare100 = FareAttributeSerializer(self.fare100).data
        serialized_fare150 = FareAttributeSerializer(self.fare150).data

        serialized_route = RouteSerializer(self.route).data

        payload = utils.jwt_payload_handler(self.user)
        token = utils.jwt_encode_handler(payload)
        auth = 'Bearer {0}'.format(token)

        url = reverse('farerule-list')
        # Invalid rule: fare, route, origin_id, NO destination_id/contains_id
        data = {
            'fare': serialized_fare50,
            'route': serialized_route,
            'origin_id': self.stop_a.stop_id,
            'destination_id': '',
            'contains_id': '',
        }
        # no authorization
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        resp = self.client.post(
            url, data,
            HTTP_AUTHORIZATION=auth, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid rule fare, origin_id but NO destination_id/contains_id
        data = {
            'fare': serialized_fare50,
            'route': None,
            'origin_id': self.stop_a.stop_id,
            'destination_id': '',
            'contains_id': '',
        }
        resp = self.client.post(
            url, data,
            HTTP_AUTHORIZATION=auth, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Good Rule - fare, route
        data = {
            'fare': serialized_fare50,
            'route': serialized_route,
            'origin_id': self.stop_a.stop_id,
            'destination_id': '',
            'contains_id': '',
        }
        resp = self.client.post(
            url, data,
            HTTP_AUTHORIZATION=auth, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = {
            'fare': serialized_fare50,
            'route': None,
            'origin_id': self.stop_a.stop_id,
            'destination_id': self.stop_b.stop_id,
            'contains_id': '',
        }
        resp = self.client.post(
            url, data,
            HTTP_AUTHORIZATION=auth, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(type(resp.data), ReturnDict)

        data = {
            'fare': serialized_fare50,
            'route': None,
            'origin_id': self.stop_a.stop_id,
            'destination_id': ','.join([self.stop_b.stop_id, self.stop_c.stop_id]),
            'contains_id': '',
        }
        resp = self.client.post(
            url, data,
            HTTP_AUTHORIZATION=auth, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(resp.data), 2)

        data = {
            'fare': serialized_fare100,
            'route': serialized_route,
            'origin_id': self.stop_a.stop_id,
            'destination_id': ','.join([self.stop_b.stop_id, self.stop_c.stop_id]),
            'contains_id': '',
        }
        resp = self.client.post(
            url, data,
            HTTP_AUTHORIZATION=auth, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(resp.data), 2)

        data = {
            'fare': serialized_fare100,
            'route': serialized_route,
            'origin_id': self.stop_c.stop_id,
            'destination_id': '',
            'contains_id': ','.join([self.stop_b.stop_id, self.stop_a.stop_id]),
        }
        resp = self.client.post(
            url, data,
            HTTP_AUTHORIZATION=auth, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(resp.data), 2)
