from django.db import models

class Stop(models.Model):
    stop_id = models.CharField(max_length=20)
    stop_code = models.CharField(max_length=20)
    name = models.CharField(max_length=80)
    lat = models.FloatField()
    lng = models.FloatField()
