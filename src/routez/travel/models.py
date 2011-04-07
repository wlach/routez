from django.db import models

class Map(models.Model):
    min_lat = models.FloatField()
    min_lng = models.FloatField()
    max_lat = models.FloatField()
    max_lng = models.FloatField()
