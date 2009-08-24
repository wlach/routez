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
    ROUTE_TYPE_CHOICES = (
        (0, 'Tram'),
        (1, 'Subway'),
        (2, 'Rail'),
        (3, 'Bus'),
        (4, 'Ferry'),
        (5, 'Cable Car'),
        (6, 'Gondola'),
        (7, 'Funicular'),
        )
    type = models.IntegerField(choices=ROUTE_TYPE_CHOICES)

class Shape(models.Model):
    src_id = models.CharField(max_length=20)
    dest_id = models.CharField(max_length=20)
    polyline = models.CharField(max_length=512)
