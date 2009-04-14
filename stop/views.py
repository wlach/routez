from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.conf import settings

import datetime
import simplejson

from routez.travel.models import Route, Stop, Map, Shape

def stoptime(request, stop_code, secs):
    stop = Stop.objects.filter(stop_code=stop_code)[0]
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
        for thop in thops:
            times.append(thop.start_time)
        route = Route.objects.filter(route_id=route_id)[0]
        routes.append({ "short_name": route.short_name, "long_name": route.long_name,
                        "times": times })

    return HttpResponse(simplejson.dumps([ { 'routes': routes } ]), 
                        mimetype="application/json")
