from django.db import models

class Map(models.Model):
    min_lat = models.FloatField()
    min_lng = models.FloatField()
    max_lat = models.FloatField()
    max_lng = models.FloatField()

class Route(models.Model):
    route_id = models.CharField(max_length=20)
    short_name = models.CharField(max_length=5)
    long_name = models.CharField(max_length=80)

class Stop(models.Model):
    stop_id = models.CharField(max_length=20)
    name = models.CharField(max_length=80)
    lat = models.FloatField()
    lng = models.FloatField()

class Shape(models.Model):
    src_id = models.CharField(max_length=20)
    dest_id = models.CharField(max_length=20)
    polyline = models.CharField(max_length=512)
