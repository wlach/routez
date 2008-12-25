from django.shortcuts import render_to_response
from django.http import HttpResponse

import datetime
import time

from routez.travel.models import Map

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
            'key': "", 'now': " " + now_str})

def stoplist(request):
    matches = []
    for s in Stop.objects.all():
        matches.append({ 'id':"gtfs"+s.stop_id, 'name':s.name, 
                        'lat':s.lat, 'lng':s.lng })
    return request.respond(asJSON(matches))

def routelist(request):
    matches = []
    for r in Route.objects.all():
        matches.append({ 'id':r.route_id, 'shortname':r.short_name, 
                       'longname':r.long_name } )
    return request.respond(asJSON(matches))

def routeplan(request):
    start_lat = float(request.get('startlat'))
    start_lng = float(request.get('startlng'))
    end_lat = float(request.get('endlat'))
    end_lng = float(request.get('endlng'))
    time_str = request.get('time') or ""

    start_time = self.calendar.parse(time_str)[0]
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

    trippath = self.graph.find_path(today_secs, service_period, 
                    start_lat, start_lng, end_lat, end_lng, None)

    actions_desc = []
    last_action = None
    for action in trippath.get_actions():
        # order is always: get off (if applicable), board (if applicable), 
        # then move
        if last_action and last_action.route_id != action.route_id:
            if last_action.route_id != -1:
                ts = self.graph.get_tripstop(last_action.dest_id)
                action_time = Main.human_time(
                    daysecs + last_action.start_time)
                actions_desc.append({ 'type':'alight', 
                                    'lat': ts.lat, 
                                    'lng': ts.lng, 
                                    'time': action_time })

        if not last_action or last_action.route_id != action.route_id:
            if action.route_id >= 0:
                action_time = Main.human_time(daysecs + action.start_time)
                actions_desc.append({ 'type':'board', 'id':action.src_id, 
                                    'time': action_time,
                                    'route_id':action.route_id })

        ts = self.graph.get_tripstop(action.src_id)
        actions_desc.append({ 'type':'pass', 'id':action.src_id, 
                            'lat': ts.lat, 
                            'lng': ts.lng,
                            'dest_id':action.dest_id })
        last_action = action

    # if we had a path at all, append the last getting off action here
    if last_action:
        action_time = Main.human_time(daysecs + last_action.end_time)
        actions_desc.append({ 'type': 'arrive', 
                              'time': action_time })

    return request.respond(asJSON(actions_desc))
