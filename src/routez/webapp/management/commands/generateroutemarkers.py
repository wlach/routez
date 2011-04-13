from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from routez.routes.models import Route
import os

class Command(BaseCommand):
    help = 'Creates a set of stop icons'

    def handle(self, *args, **options):
        marker_basepath = settings.PROJECT_PATH + "/webapp/static/images/"
        generated_path = settings.PROJECT_PATH + "/webapp/static/images/generated/"
        for route in Route.objects.all():
            if route.type == 3:
                marker_basename = "marker_bus"
            elif route.type == 4:
                marker_basename = "marker_ferry"

            ret = os.system('convert %s -weight Bold -annotate +34+14 %s %s' %
                            (marker_basepath+ marker_basename + ".png", route.short_name, 
                             generated_path + marker_basename + route.short_name + ".png"))
            if ret != 0:
                raise CommandError('Error writing marker with route %s' % route.short_name)

