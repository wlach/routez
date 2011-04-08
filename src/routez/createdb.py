#!/usr/bin/python

# This script imports a transit feed into the django database
# It must be run after creategraph, as it sets up internal
# mappings to the data in the graph

import transitfeed
import sys
import os
import routez.settings
import simplejson
import yaml

# Manually import django
sys.path.append(os.path.join(os.getcwd(), os.pardir))
os.environ['DJANGO_SETTINGS_MODULE'] = "routez.settings"

from django.db import transaction

from routez.travel.models import Map
from routez.routes.models import Route
from routez.stops.models import Stop
from routez.trips.models import Trip, StopHeadsign

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
    import routez.travel
    graph = routez.travel.graph

    print "Exporting schedule as database"
    
    transaction.enter_transaction_management()
    transaction.managed(True)

    # zap any existing info
    Route.objects.all().delete()
    Stop.objects.all().delete()
    Map.objects.all().delete()
    Trip.objects.all().delete()
    StopHeadsign.objects.all().delete()

    # import it all into the db again
    for r in schedule.GetRouteList():
        if mapping['Routes'].has_key(r.route_id):
            #print "%s" % (mapping['Routes'][r.route_id])
            r2 = Route(id=mapping['Routes'][r.route_id], 
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
            print "WARNING: route with no mapping. probably no trips assc. with it."
            #print "WARNING: Route %s (%s) has no mapping... probably means it "
            #"has no trips associated with it." % (short_name, long_name)

    for s in schedule.GetStopList():
        if s.stop_id in mapping['Stops']:
            stop_code = s.stop_code
            if not stop_code:
                stop_code = s.stop_id
            s2 = Stop(id=mapping['Stops'][s.stop_id], stop_code=stop_code,
                      name=s.stop_name, lat=s.stop_lat, lng=s.stop_lon)
            s2.save()
        else:
            print "WARNING: Stop with no mapping '%s'" % s.stop_id

    print "Importing trips!"
    for t in schedule.GetTripList():
        if t.trip_id in mapping['Trips']:
            t2 = Trip(id=mapping['Trips'][t.trip_id], headsign=t.trip_headsign)
            t2.save()
        else:
            print "WARNING: Trip with no mapping '%s'" % t.trip_id

    for headsign in mapping['Headsigns'].keys():
        h = StopHeadsign(id=mapping['Headsigns'][headsign], headsign=headsign)
        h.save()

    (_min_lat, _min_lon, _max_lat, _max_lon) = schedule.GetStopBoundingBox()
    m = Map(min_lat=_min_lat, min_lng=_min_lon, max_lat=_max_lat, max_lng=_max_lon)
    m.save()

    transaction.commit()
    transaction.leave_transaction_management()

