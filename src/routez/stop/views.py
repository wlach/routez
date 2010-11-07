from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings

import datetime
import simplejson
import time
import parsedatetime.parsedatetime as pdt

from routez.travel.models import Route, Map
from routez.stop.models import Stop
from routez.trip.models import Trip, StopHeadsign
from libroutez.tripgraph import TripStop

# fixme: this function is a disaster. put a latlng function in libroutez
# for goodness sakes!
import math
def latlng_dist(src_lat, src_lng, dest_lat, dest_lng):
    if round(src_lat, 4) == round(dest_lat, 4) and \
            round(src_lng, 4) == round(dest_lng, 4):
        return 0.0

    theta = src_lng - dest_lng
    src_lat_radians = math.radians(src_lat)
    dest_lat_radians = math.radians(dest_lat)
    dist = math.sin(src_lat_radians) * math.sin(dest_lat_radians) + \
        math.cos(src_lat_radians) * math.cos(dest_lat_radians) * \
        math.cos(math.radians(theta))
    dist = math.degrees(math.acos(dist)) * (60.0 * 1.1515 * 1.609344 * 1000.0)
    return dist

def get_route_ids_for_stop(graph, stop_id, secs):
    ts = graph.get_tripstop(stop_id)

    route_id_hash = {}

    sptuples = graph.get_service_period_ids_for_time(int(secs))
    for sptuple in sptuples:
        route_ids = ts.get_routes(sptuple[0])
        for route_id in route_ids:
            route_id_hash[route_id] = 1

    return route_id_hash.keys()

def find_triphops_for_stop(graph, stop_id, route_id, secs, num):
    t = time.localtime(float(secs))
    elapsed_daysecs = t.tm_sec + (t.tm_min * 60) + (t.tm_hour * 60 * 60)
    daystart_secs = int(secs - elapsed_daysecs)

    ts = graph.get_tripstop(stop_id)

    all_triphops = []
    sptuples = graph.get_service_period_ids_for_time(int(secs))
    for sptuple in sptuples:
        triphops = ts.find_triphops(elapsed_daysecs + sptuple[1], route_id,
                                    sptuple[0], num)
        for triphop in triphops:
            triphop.start_time += (daystart_secs - sptuple[1])
            triphop.end_time += (daystart_secs - sptuple[1])
            all_triphops.append(triphop)

    all_triphops.sort(lambda x, y: x.start_time-y.start_time)
    if len(all_triphops) > num:
        all_triphops = all_triphops[0:num]

    return all_triphops

def stoptimes_for_stop(request, stop_code):
    starttime = request.GET.get('time')
    if not starttime:
        starttime = time.time()
    else:
        starttime = int(starttime) # cast to integer

    stop = Stop.objects.filter(stop_code=stop_code)
    if not len(stop):
        return HttpResponse(simplejson.dumps(
                { "stops": [ ] }), mimetype="application/json")

    stop = stop[0]

    import routez
    graph = routez.travel.graph

    route_ids = get_route_ids_for_stop(graph, int(stop.stop_id), starttime)
    routes = []
    for route_id in route_ids:
        thops = find_triphops_for_stop(graph, int(stop.stop_id), route_id,
                                       starttime, 3)
        times = []
        trips = []
        if len(thops):
            for thop in thops:
                times.append(thop.start_time)
                if thop.headsign_id >= 0:
                    headsign = StopHeadsign.objects.filter(
                        id=thop.headsign_id)[0].headsign
                else:
                    headsign = Trip.objects.filter(
                        trip_id=thop.trip_id)[0].headsign
                trips.append({ "headsign": headsign, "time": thop.start_time })
            route = Route.objects.filter(route_id=route_id)[0]
            routes.append({ "short_name": route.short_name,
                            "long_name": route.long_name,
                            "type": route.type,
                            "trips": trips,
                            "times": times })

    return HttpResponse(simplejson.dumps({ "stops": [ {'name': stop.name, 
                                                       'code': stop.stop_code,
                                                       "lat": stop.lat,
                                                       "lng": stop.lng,
                                                       'routes': routes } ]
                                           }),
                        mimetype="application/json")

def stoptimes_in_range(request, location):
    timestr = request.GET.get('time')
    starttime = None

    if not timestr:
        starttime = time.time()
    else:
        if timestr.isdigit():
            starttime = int(starttime) # cast to integer
        else:
            calendar = pdt.Calendar()
            starttime = time.mktime(calendar.parse(timestr)[0])

    import routez

    geocoder = routez.travel.geocoder
    latlng = geocoder.get_latlng(str(location))
    if not latlng:
        return HttpResponseNotFound(simplejson.dumps(
                { 'errors': ["Location not found"] }), 
                                    mimetype="application/json")

    # checking 500 meters. FIXME: make configurable
    graph = routez.travel.graph
    tstops = graph.find_tripstops_in_range(latlng[0], latlng[1], TripStop.GTFS,
                                           500)

    # filter twice, once to get all the stops we're interested in, then
    # remove any duplicate trips at stops that are further away
    stoplist = []
    distance_to_stop_hash = {}
    for ts in tstops:
        distance_to_stop = latlng_dist(latlng[0], latlng[1], ts.lat, ts.lng)
        distance_to_stop_hash[ts.id] = distance_to_stop
        route_ids = get_route_ids_for_stop(graph, int(ts.id), starttime)
        stoplist.append([ ts.id, distance_to_stop, route_ids ])
    stoplist.sort(lambda x, y: cmp(x[1], y[1]))

    stopsjson = []
    thophash = set()
    for stop in stoplist:
        routedicts = []
        for route_id in stop[2]:
            thops = find_triphops_for_stop(graph, stop[0], route_id, starttime, 3)

            if len(thops):
                # if ANY trip ids are duplicated between stops, omit (we don't
                # want to return ANY duplicate information, even if it means
                # we omit some information which is slightly different)
                unique_tripstop = True
                for thop in thops:
                    if thop.trip_id in thophash:
                        unique_tripstop = False
                    else:
                        thophash.add(thop.trip_id)
                if unique_tripstop:
                    times = []
                    trips = []
                    for thop in thops:
                        times.append(thop.start_time)
                        if thop.headsign_id >= 0:
                            headsign = StopHeadsign.objects.filter(
                                id=thop.headsign_id)[0].headsign
                        else:
                            headsign = Trip.objects.filter(
                                trip_id=thop.trip_id)[0].headsign

                        trips.append({ "headsign": headsign, "time": thop.start_time })
                    route = Route.objects.filter(route_id=route_id)[0]
                    routedict = { 
                        "short_name": route.short_name,
                        "long_name": route.long_name,
                        "trips": trips,
                        "type": route.type,
                        "times": times }
                    routedicts.append(routedict)
        if len(routedicts) > 0:
            dbstop = Stop.objects.filter(stop_id=stop[0])[0]

            stopsjson.append({ 
                    "name": dbstop.name,
                    "code": dbstop.stop_code,
                    "lat": dbstop.lat,
                    "lng": dbstop.lng,
                    "distance": distance_to_stop_hash[stop[0]],
                    "routes": routedicts })
            
    return HttpResponse(simplejson.dumps({ 'stops': stopsjson }), 
                        mimetype="application/json")
