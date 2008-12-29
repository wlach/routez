from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.conf import settings

import datetime
import simplejson
import time

from routez.travel.models import Route, Stop, Map, Shape

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
    m = Map.objects.get(id=1)
    now_str = human_time()
    return render_to_response('index.html', 
        {'min_lat': m.min_lat, 'min_lon': m.min_lng, 
            'max_lat': m.max_lat, 'max_lon': m.max_lng, 
            'key': settings.GMAPS_API_KEY, 'now': " " + now_str})

def stoplist(request):
    matches = []
    for s in Stop.objects.all():
        matches.append({'id': "gtfs" + s.stop_id, 
                        'name': s.name, 
                        'lat': s.lat, 
                        'lng': s.lng })
    return HttpResponse(simplejson.dumps(matches), mimetype="application/json")

def routelist(request):
    matches = []
    for r in Route.objects.all():
        matches.append({ 'id':r.route_id, 'shortname':r.short_name, 
                       'longname':r.long_name } )
    return HttpResponse(simplejson.dumps(matches), mimetype="application/json")

def routeplan(request):
    start_lat = float(request.GET['startlat'])
    start_lng = float(request.GET['startlng'])
    end_lat = float(request.GET['endlat'])
    end_lng = float(request.GET['endlng'])
    time_str = request.GET.get('time', "")

    import parsedatetime.parsedatetime as pdt
    calendar = pdt.Calendar()
    start_time = calendar.parse(time_str)[0]
    daysecs = time.mktime((start_time[0], start_time[1], start_time[2],
                0, 0, 0, 0, 0, 0))
    now = datetime.datetime.fromtimestamp(time.mktime(start_time))
    today_secs = (now.hour * 60 * 60) + (now.minute * 60) + (now.second)
    print "weekday: %s" % now.weekday()
    service_period = 'weekday'
    if now.weekday() == 5:
        service_period = 'saturday'
    elif now.weekday() == 6:
        service_period = 'sunday'

    # Use the TripGraph loaded in __init__.py, so we don't load it per request
    import routez
    graph = routez.travel.graph
    trippath = graph.find_path(today_secs, service_period, False,
                    start_lat, start_lng, end_lat, end_lng, None)

    actions_desc = []
    last_action = None
    for action in trippath.get_actions():
        # order is always: get off (if applicable), board (if applicable), 
        # then move
        if last_action and last_action.route_id != action.route_id:
            if last_action.route_id != -1:
                ts = graph.get_tripstop(last_action.dest_id)
                action_time = human_time(daysecs + last_action.end_time)
                actions_desc.append({ 'type':'alight', 
                                    'lat': ts.lat, 
                                    'lng': ts.lng, 
                                    'time': action_time })

        if not last_action or last_action.route_id != action.route_id:
            if action.route_id >= 0:
                action_time = human_time(daysecs + action.start_time)
                actions_desc.append({ 'type':'board', 'id':action.src_id, 
                                    'time': action_time,
                                    'route_id':action.route_id })

        shape = None
        ts = graph.get_tripstop(action.src_id)
        if action.route_id != -1:
            shapes = Shape.objects.filter(src_id=action.src_id, 
                                              dest_id=action.dest_id)
            shape = None
            if len(shapes):
                shape = simplejson.loads(shapes[0].polyline)
        actions_desc.append({ 'type':'pass', 'id':action.src_id, 
                              'lat': ts.lat, 
                              'lng': ts.lng,
                              'dest_id':action.dest_id,
                              'shape':shape })
        last_action = action

    # if we had a path at all, append the last getting off action here
    if last_action:
        action_time = human_time(daysecs + last_action.end_time)
        actions_desc.append({ 'type': 'arrive', 
                              'time': action_time })

    return HttpResponse(simplejson.dumps(actions_desc), 
        mimetype="application/json")
