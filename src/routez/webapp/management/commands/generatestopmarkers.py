from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from routez.stops.models import Stop
from routez.travel import graph 
import time
import math
import os
import subprocess

class Command(BaseCommand):
    help = 'Creates a set of stop icons'

    def handle(self, *args, **options):
        generated_path = settings.PROJECT_PATH + "/webapp/static/images/generated/"

        now = time.time()
        t = time.localtime(now)
        elapsed_daysecs = t.tm_sec + (t.tm_min * 60) + (t.tm_hour * 60 * 60)
        cmds = []

        for stop in Stop.objects.all():
            for cmd in cmds:
                res = cmd.poll()
                if res is not None:
                    if res != 0:
                        raise CommandError('Error writing stop')
                    cmds.remove(cmd)

            stop_display = stop.stop_code
            if stop.stop_code:
                print "Processing stop %s" % stop.stop_code
                ts = graph.get_tripstop(stop.id)

                lat_v = 0.0
                lng_v = 0.0
            
                sptuples = graph.get_service_period_ids_for_time(int(now))
                for sptuple in sptuples:
                    for route_id in ts.get_routes(sptuple[0]):
                        thops = ts.find_triphops(elapsed_daysecs + sptuple[1],
                                                 route_id, sptuple[0], 1)
                        for thop in thops:
                            try:
                                dest_stop = Stop.objects.get(id=thop.dest_id)
                                lat_v += (dest_stop.lat - stop.lat)
                                lng_v += (dest_stop.lng - stop.lng)
                            except Stop.DoesNotExist:
                                print "WARNING: Stop with id %s (pointed to by triphop) does not exist!" % thop.dest_id
                        latlng_len = math.sqrt((lat_v*lat_v) + (lng_v*lng_v))
                        if latlng_len != 0.0:
                            lat_v = lat_v / latlng_len
                            lng_v = lng_v / latlng_len
                            
                        dir = ""
                        if lat_v >= 0.5:
                            dir += "n"
                        elif lat_v <= (-0.5):
                            dir += "s"
                        if lng_v >= 0.5:
                            dir += "e"
                        if lng_v <= (-0.5):
                            dir += "w"
                        if len(dir):
                            stop_image = settings.PROJECT_PATH + "/webapp/static/images/marker_stop_%s.png" % dir
                        else:
                            stop_image = settings.PROJECT_PATH + "/webapp/static/images/marker_stop.png" 

                
                generated_marker_name = "%smarker_stop%s" % (generated_path, stop.stop_code)
                if os.system('convert %s -weight Bold -annotate +24+15 %s %s.png' % (stop_image, stop_display,
                                                                                  generated_marker_name)) != 0:
                    raise CommandError('Error writing stop image')
                #os.system('convert %s.png -channel Alpha -evaluate Divide 4 %s_transparent.png' % (generated_marker_name, generated_marker_name))
