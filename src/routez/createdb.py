#!/usr/bin/python

# This script imports a transit feed into the django database
# It must be run after creategraph, so that the shapes can be
# created

import transitfeed
import sys
import os
import simplejson
import settings
import yaml

# Manually import django
sys.path.append(os.path.join(os.getcwd(), os.pardir))
os.environ['DJANGO_SETTINGS_MODULE'] = "settings"

from django.db import transaction

from routez.travel.models import Route, Map, Shape
from routez.stop.models import Stop
from routez.trip.models import Trip

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Usage: %s: <gtfs feed> <routez graph mapping>" % sys.argv[0]
        exit(1)

    schedule = transitfeed.Schedule(
        problem_reporter=transitfeed.ProblemReporter())
    print "Loading schedule."
    schedule.Load(sys.argv[1])

    print "Loading gtfs->libroutez mapping"
    stream = open(sys.argv[2], 'r')
    mapping = yaml.load(stream)

    # Use the graph we specify in the config file
    import travel
    graph = travel.graph

    print "Exporting schedule as database"
    
    transaction.enter_transaction_management()
    transaction.managed(True)

    # zap any existing info
    Route.objects.all().delete()
    Stop.objects.all().delete()
    Map.objects.all().delete()
    Shape.objects.all().delete()
    Trip.objects.all().delete()

    # import it all into the db again
    for r in schedule.GetRouteList():
        if mapping['Routes'].has_key(r.route_id):
            #print "%s" % (mapping['Routes'][r.route_id])
            r2 = Route(route_id=mapping['Routes'][r.route_id], 
                       short_name=r.route_short_name, long_name=r.route_long_name,
                       type=r.route_type)
            r2.save()
        else:
            # perverse case where there's a route with no trips
            short_name = "<no short name>"
            long_name = "<long name>"
            if r.route_short_name:
                short_name = str(r.route_short_name)
            if r.route_long_name:
                long_name = str(r.route_long_name)
            # FIXME: why does this fail???
            print "route with no mapping. probably no trips assc. with it."
            #print "WARNING: Route %s (%s) has no mapping... probably means it "
            #"has no trips associated with it." % (short_name, long_name)

    for s in schedule.GetStopList():
        s2 = Stop(stop_id=mapping['Stops'][s.stop_id], stop_code = s.stop_id,
                  name=s.stop_name, lat=s.stop_lat, lng=s.stop_lon)
        s2.save()

    print "Importing trips!"
    for t in schedule.GetTripList():
        t2 = Trip(trip_id=mapping['Trips'][t.trip_id], headsign=t.trip_headsign)
        t2.save()

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
            stopid = stoptime.stop_id
            # don't calculate the same shape twice
            if not visited_stops.get(prevstopid):
                visited_stops[prevstopid] = {}
            if visited_stops[prevstopid].get(stopid):
                prevstopid = stopid
                continue
            elif prevstopid:
                visited_stops[prevstopid][stopid] = 1
                path = []
                stop1 = schedule.GetStop(prevstopid)
                stop2 = schedule.GetStop(stopid)
                print "Calculating shape from %s (%s, %s) -> %s (%s, %s)" % \
                    (prevstopid, stop1.stop_lat, stop1.stop_lon, 
                     stopid, stop2.stop_lat, stop2.stop_lon)
                # FIXME: this currently sometimes creates paths which seem
                # to backtrack, when two stops lie between an intersection
                # (because they're not connected to each other, only the
                # way intersections). 
                trippath = graph.find_path(0.0, True,
                                           stop1.stop_lat, stop1.stop_lon, 
                                           stop2.stop_lat, stop2.stop_lon)
                if trippath:
                    points = []
                    prevaction = False
                    for action in trippath.get_actions():
                        dest = graph.get_tripstop(action.dest_id)
                        points.append([dest.lat, dest.lng])
                    if len(points) > 1:
                        s = Shape(src_id=mapping['Stops'][prevstopid], 
                                  dest_id=mapping['Stops'][stopid], 
                                  polyline=simplejson.dumps(points[0:-1]))
                        s.save()
                else:
                    print "WARNING: Couldn't compute path from %s to %s." \
                    "This probably means your street graph isn't properly " \
                    "connected. This is normal if you haven't defined an OSM file " \
                    "for the graph. Otherwise you should worry about the connectedness of " \
                    "your OSM data." % (prevstopid, stopid)
            prevstopid = stopid

    transaction.commit()
    transaction.leave_transaction_management()

