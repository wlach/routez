from django.db import models

class Trip(models.Model):
    trip_id = models.IntegerField()
    headsign = models.CharField(max_length=80)
