from django.db import models

class Trip(models.Model):
    headsign = models.CharField(max_length=80)

class StopHeadsign(models.Model):
    headsign = models.CharField(max_length=80)
