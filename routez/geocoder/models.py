from django.db import models

class Road(models.Model):
    name = models.CharField(max_length=80)
    suffix = models.CharField(max_length=50)
    coords = models.TextField()
    firstHouseNumber = models.PositiveIntegerField()
    lastHouseNumber = models.PositiveIntegerField()
    numberingTypeEven = models.BooleanField()
    length = models.FloatField()

class Intersection(models.Model):
    name1 = models.CharField(max_length=80)
    suffix1 = models.CharField(max_length=50)
    name2 = models.CharField(max_length=80)
    suffix2 = models.CharField(max_length=50)
    lat = models.FloatField()
    lng = models.FloatField()
