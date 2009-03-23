from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.conf import settings

import datetime
import simplejson
import time

from routez.travel.models import Route, Stop, Map, Shape
import routez.geocoder.geocoder as geocoder

class TripPlan:
    def __init__(self, departure_time, actions):
        self.departure_time = departure_time
        self.actions = actions

# Returns the hours and minutes of the given Unix timestamp, formatted
# nicely.  If the timestamp is not given, defaults to the current time.
def human_time(secs = None):
    format_str = "%I:%M %p"
    dtstr = ""
    if secs is None:
        dtstr = time.strftime(format_str).lower()
    else:
        dt = datetime.datetime.fromtimestamp(secs)
        dtstr = dt.strftime(format_str).lower()
    # Remove leading zero. %_I would do almost the same thing on Linux,
    # but is non-standard and only works because Python happens to use
    # glibc's extended strftime implementation on Linux.
    if dtstr[0] == '0':
        dtstr = dtstr[1:]
    return dtstr

def main_page(request):

    if request.META.get('HTTP_USER_AGENT') and request.META['HTTP_USER_AGENT'].find("iPhone") > 0:
        return iphone(request)

    m = Map.objects.get(id=1)
    return render_to_response('index.html', 
        {'min_lat': m.min_lat, 'min_lon': m.min_lng, 
         'max_lat': m.max_lat, 'max_lon': m.max_lng, 
         'key': settings.CMAPS_API_KEY,
         'analytics_key': settings.ANALYTICS_KEY })

def iphone(request):
    m = Map.objects.get(id=1)
    return render_to_response('iphone.html', 
        {'min_lat': m.min_lat, 'min_lon': m.min_lng, 
         'max_lat': m.max_lat, 'max_lon': m.max_lng, 
         'key': settings.CMAPS_API_KEY,
         'analytics_key': settings.ANALYTICS_KEY })

def about(request):
    return render_to_response('about.html', 
                              { 'analytics_key': settings.ANALYTICS_KEY })

def privacy(request):
    return render_to_response('privacy.html',
                              { 'analytics_key': settings.ANALYTICS_KEY })

def routeplan(request):
    start = request.GET['start']
    end = request.GET['end']
    time_str = request.GET.get('time', "")

    errors = []
    start_latlng = geocoder.get_location(start)
    end_latlng = geocoder.get_location(end)

    if not start_latlng:
        errors.append("start_latlng_decode")
    if not end_latlng:
        errors.append("end_latlng_decode")

    if len(errors):
        return HttpResponse(simplejson.dumps({ 'errors': errors }), 
                            mimetype="application/json")


    import parsedatetime.parsedatetime as pdt
    calendar = pdt.Calendar()
    start_time = calendar.parse(time_str)[0]
    daysecs = time.mktime((start_time[0], start_time[1], start_time[2],
                0, 0, 0, 0, 0, -1))
    now = datetime.datetime.fromtimestamp(time.mktime(start_time))
    today_secs = (now.hour * 60 * 60) + (now.minute * 60) + (now.second)
    service_period = 'weekday'
    if now.weekday() == 5:
        service_period = 'saturday'
    elif now.weekday() == 6:
        service_period = 'sunday'

    # Use the TripGraph loaded in __init__.py, so we don't load it per request
    import routez
    graph = routez.travel.graph
    trippath = graph.find_path(today_secs, service_period, False,
                               start_latlng[0], start_latlng[1], end_latlng[0], 
                               end_latlng[1])

    actions_desc = []
    route_shortnames = []
    last_action = None
    for action in trippath.get_actions():
        # order is always: get off (if applicable), board (if applicable), 
        # then move
        if last_action and last_action.route_id != action.route_id:
            if last_action.route_id != -1:
                stop = Stop.objects.filter(stop_id=last_action.dest_id)[0]
                action_time = human_time(daysecs + last_action.end_time)
                actions_desc.append({ 'type':'alight', 
                                    'lat': stop.lat, 
                                    'lng': stop.lng, 
                                    'stopname': stop.name,
                                    'time': action_time })

        if not last_action or last_action.route_id != action.route_id:
            if action.route_id >= 0:
                action_time = human_time(daysecs + action.start_time)
                route = Route.objects.filter(route_id=action.route_id)[0]
                stop = Stop.objects.filter(stop_id=action.src_id)[0]
                actions_desc.append({ 'type':'board', 
                                      'lat':stop.lat,
                                      'lng':stop.lng,
                                      'stopname':stop.name,
                                      'time': action_time,
                                      'route_id': action.route_id,
                                      'route_shortname': route.short_name,
                                      'route_longname': route.long_name }) 

        shape = None
        ts = graph.get_tripstop(action.src_id)
        if action.route_id != -1:
            shapes = Shape.objects.filter(src_id=action.src_id, 
                                          dest_id=action.dest_id)
            shape = None
            if len(shapes):
                shape = simplejson.loads(shapes[0].polyline)
        action_time = human_time(daysecs + action.start_time);
        actions_desc.append({ 'type':'pass', 'id':action.src_id, 
                              'lat': ts.lat, 
                              'lng': ts.lng,
                              'time': action_time,
                              'dest_id':action.dest_id,
                              'shape':shape })
        last_action = action

    # if we had a path at all, append the last getting off action here
    if last_action:
        action_time = human_time(daysecs + last_action.end_time)
        actions_desc.append({ 'type': 'arrive', 
                              'lat': end_latlng[0],
                              'lng': end_latlng[1],
                              'time': action_time })

        
    trip_plan = { 
        'start': { "lat": start_latlng[0], "lng": start_latlng[1] },
        'end': { "lat": end_latlng[0], "lng": end_latlng[1] },
        'actions': actions_desc, 
                  'departure_time' : human_time(daysecs + today_secs) }
        
    return HttpResponse(simplejson.dumps(trip_plan), 
                        mimetype="application/json")

