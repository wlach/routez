#!/usr/bin/python

# This script imports a transit feed into the django database
# It must be run after creategraph, so that the shapes can be
# created

import transitfeed
from tripgraph import *
import sys
import os
import simplejson
import settings

# Manually import django
sys.path.append(os.path.join(os.getcwd(), os.pardir))
os.environ['DJANGO_SETTINGS_MODULE'] = "settings"

from routez.travel.models import Route, Stop, Map, Shape

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: %s: <gtfs feed> <routez graph>" % sys.argv[0]
        exit(1)

    schedule = transitfeed.Schedule(
        problem_reporter=transitfeed.ProblemReporter())
    print "Loading schedule."
    schedule.Load(sys.argv[1])

    print "Loading graph."
    graph = TripGraph()
    graph.load(sys.argv[2])

    print "Exporting schedule as database"
    
    # zap any existing info
    Route.objects.all().delete()
    Stop.objects.all().delete()
    Map.objects.all().delete()
    Shape.objects.all().delete()

    # import it all into the db again
    for r in schedule.GetRouteList():
        r2 = Route(route_id=r.route_id, short_name=r.route_short_name, long_name=r.route_long_name)
        r2.save()

    for s in schedule.GetStopList():
        s2 = Stop(stop_id=s.stop_id, name=s.stop_name, lat=s.stop_lat, lng=s.stop_lon)
        s2.save()

    (_min_lat, _min_lon, _max_lat, _max_lon) = schedule.GetStopBoundingBox()
    m = Map(min_lat=_min_lat, min_lng=_min_lon, max_lat=_max_lat, max_lng=_max_lon)
    m.save()

    # evil code to generate shapes by running trip planner repeatedly
    print "Calculating shapes and storing in database"
    visited_stops = {}
    trips = schedule.GetTripList()
    for trip in trips:
        prevstopid = None
        for stoptime in trip.GetStopTimes():
            # don't calculate the same shape twice
            if not visited_stops.get(prevstopid):
                visited_stops[prevstopid] = {}
            if visited_stops[prevstopid].get(stoptime.stop_id):
                prevstopid = stoptime.stop_id
                continue
            elif prevstopid:
                print "Calculating shape from %s -> %s" % (prevstopid, 
                                                           stoptime.stop_id)
                visited_stops[prevstopid][stoptime.stop_id] = 1
                path = []
                stop1 = schedule.GetStop(prevstopid)
                stop2 = schedule.GetStop(stoptime.stop_id)
                # FIXME: this currently sometimes creates paths which seem
                # to backtrack, when two stops lie between an intersection
                # (because they're not connected to each other, only the
                # way intersections). 
                trippath = graph.find_path(0, "", True,
                                                stop1.stop_lat, stop1.stop_lon, 
                                                stop2.stop_lat, stop2.stop_lon,
                                           None)
                points = []
                prevaction = False
                for action in trippath.get_actions():
                    dest = graph.get_tripstop(action.dest_id)
                    points.append([dest.lat, dest.lng])
                if len(points) > 1:
                    s = Shape(src_id="gtfs"+prevstopid, 
                              dest_id = "gtfs"+stoptime.stop_id, 
                              polyline=simplejson.dumps(points[0:-1]))
                    s.save()
            prevstopid = stoptime.stop_id
