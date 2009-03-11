from django.db import models

class Road(models.Model):
    name = models.CharField(max_length=80)
    suffix = models.CharField(max_length=50)
    coords = models.TextField()
    firstHouseNumber = models.PositiveIntegerField()
    lastHouseNumber = models.PositiveIntegerField()
    numberingTypeEven = models.BooleanField()
    length = models.FloatField()

