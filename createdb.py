#!/usr/bin/python

# This script imports a transit feed into the django database
# It must be run after creategraph, so that the shapes can be
# created

import transitfeed
from libroutez.tripgraph import *
import sys
import os
import simplejson
import settings

# Manually import django
sys.path.append(os.path.join(os.getcwd(), os.pardir))
os.environ['DJANGO_SETTINGS_MODULE'] = "settings"

from routez.travel.models import Route, Stop, Map, Shape

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Usage: %s: <gtfs feed> <routez graph>" % sys.argv[0]
        exit(1)

    schedule = transitfeed.Schedule(
        problem_reporter=transitfeed.ProblemReporter())
    print "Loading schedule."
    schedule.Load(sys.argv[1])

    print "Loading graph."
    #graph = TripGraph()
    #graph.load(sys.argv[2])

    print "Exporting schedule as database"
    
    # zap any existing info
    #Route.objects.all().delete()
    #Stop.objects.all().delete()
    #Map.objects.all().delete()
    #Shape.objects.all().delete()

    # import it all into the db again
    for r in schedule.GetRouteList():
        r2 = Route(route_id=r.route_id, short_name=r.route_short_name, long_name=r.route_long_name)
        r2.save()

    for s in schedule.GetStopList():
        s2 = Stop(stop_id="gtfs"+s.stop_id, name=s.stop_name, lat=s.stop_lat, lng=s.stop_lon)
        s2.save()

    (_min_lat, _min_lon, _max_lat, _max_lon) = schedule.GetStopBoundingBox()
    m = Map(min_lat=_min_lat, min_lng=_min_lon, max_lat=_max_lat, max_lng=_max_lon)
    m.save()

