from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings

import datetime
import simplejson

from routez.travel.models import Route, Stop, Map, Shape
import routez.geocoder.geocoder as geocoder
from libroutez.tripgraph import TripStop

def stoptimes_for_stop(request, stop_code, secs):
    stop = Stop.objects.filter(stop_code=stop_code)
    if not len(stop):
        return HttpResponseNotFound(simplejson.dumps(
                { 'errors': ["Stop not found"] }), mimetype="application/json")

    stop = stop[0]
    import routez
    graph = routez.travel.graph
    today = datetime.date.today()
    service_period = 'weekday'
    if today.weekday() == 5:
        service_period = 'saturday'
    elif today.weekday() == 6:
        service_period = 'sunday'

    ts = graph.get_tripstop(int(stop.stop_id));
    route_ids = ts.get_routes(service_period)
    routes = []
    for route_id in route_ids:
        thops = ts.find_triphops(int(secs), int(route_id), service_period, 3)
        times = []
        if len(thops):
            for thop in thops:
                times.append(thop.start_time)
            route = Route.objects.filter(route_id=route_id)[0]
            routes.append({ "short_name": route.short_name, "long_name": route.long_name,
                            "times": times })

    return HttpResponse(simplejson.dumps({ 'routes': routes }), 
                        mimetype="application/json")

def stoptimes_in_range(request, location, secs):
    latlng = geocoder.get_location(location)
    import routez
    graph = routez.travel.graph

    today = datetime.date.today()
    service_period = 'weekday'
    if today.weekday() == 5:
        service_period = 'saturday'
    elif today.weekday() == 6:
        service_period = 'sunday'

    # checking 500 meters. FIXME: make configurable
    tstops = graph.find_tripstops_in_range(latlng[0], latlng[1], TripStop.GTFS,
                                           500)
    routehash = {}
    route_id_thops = {}
    routes = []
    for ts in tstops:
        distance_to_stop = (latlng[0] - ts.lat)**2 + (latlng[1] - ts.lng)**2
        for route_id in ts.get_routes(service_period):
            if not routehash.get(route_id) or \
                    routehash[route_id][0] >= distance_to_stop:
                routehash[route_id] = (distance_to_stop, ts)

        
        for route_id in routehash:
            ts = routehash[route_id][1]
            thops = ts.find_triphops(int(secs), int(route_id), service_period, 
                                     3)              
            times = []
            if len(thops):
                for thop in thops:
                    times.append(thop.start_time)
                stop = Stop.objects.filter(stop_id=ts.id)[0]
                route = Route.objects.filter(route_id=route_id)[0]
                routes.append({
                        "stop_name": stop.name,
                        "stop_code": stop.stop_code,
                        "route_short_name": route.short_name,
                        "route_long_name": route.long_name,
                        "times": times })

    return HttpResponse(simplejson.dumps({ 'routes': routes }), 
                        mimetype="application/json")
