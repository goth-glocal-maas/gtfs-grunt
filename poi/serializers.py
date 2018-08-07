from rest_framework.serializers import (
    ModelSerializer, SerializerMethodField
)
from drf_extra_fields.geo_fields import PointField

from .models import POI
import json


class POISerializer(ModelSerializer):
    geojson = SerializerMethodField()
    location = PointField()
    distance_m = SerializerMethodField()

    class Meta:
        model = POI
        fields = '__all__'

    def get_geojson(self, obj):
        if not obj.location:
            return None
        return json.loads(obj.location.geojson)

    def get_distance_m(self, obj):
        try:
            return obj.distance.m
        except Exception:
            return None
