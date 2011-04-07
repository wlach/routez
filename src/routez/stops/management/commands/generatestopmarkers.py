from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from routez.stops.models import Stop
import os

class Command(BaseCommand):
    help = 'Creates a set of stop icons'

    def handle(self, *args, **options):
        stop_image = settings.PROJECT_PATH + "/site_media/images/marker_stop.png"
        generated_path = settings.PROJECT_PATH + "/site_media/images/generated/"
        for stop in Stop.objects.all():
            stop_display = stop.stop_code
            if stop.stop_code:
                ret = os.system('convert %s -weight Bold -annotate +24+15 %s %s' %
                                (stop_image, stop_display,
                                 ("%smarker_stop%s.png" % (generated_path, stop.stop_code))))
                if ret != 0:
                    raise CommandError('Error writing stop with code %s' % stop.stop_code)

