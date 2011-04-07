from django.db import models

class Route(models.Model):
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
