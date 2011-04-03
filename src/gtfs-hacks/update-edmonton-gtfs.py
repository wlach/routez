#!/usr/bin/python

import math
import re
import transitfeed
from optparse import OptionParser

def latlng_dist(src_lat, src_lng, dest_lat, dest_lng):
    if abs(src_lat-dest_lat) < 0.00001 and abs(src_lng-dest_lng) < 0.00001:
        return 0.0
    theta = src_lng - dest_lng
    src_lat_radians = math.radians(src_lat)
    dest_lat_radians = math.radians(dest_lat)
    dist = math.sin(src_lat_radians) * math.sin(dest_lat_radians) + \
        math.cos(src_lat_radians) * math.cos(dest_lat_radians) * \
        math.cos(math.radians(theta))
    dist = math.degrees(math.acos(dist)) * (60.0 * 1.1515 * 1.609344 * 1000.0)
    return dist

def closest_seg_distance(coords, linesegs):
    closest_distance = None
    for lineseg in linesegs:
        # slope of the sub-way
        slope1_lat = lineseg[0][0] - lineseg[1][0]
        slope1_lon = lineseg[0][1] - lineseg[1][1]

        # just ignore triphops that don't go anywhere
        if slope1_lat == 0 and slope1_lon == 0:
            continue

        # slope of the vector from the stop to the sub way
        slope2_lon = slope1_lat * (-1)
        slope2_lat = slope1_lon 
        
        # the scalar value of the intersection on the way: 
        # - < 0 = before the first pt,
        # - > 0 = after the last pt 
        # - between = between the two points
        intersection_scalar = (((lineseg[0][1] - coords[1]) * slope2_lat + \
                                    (coords[0] - lineseg[0][0]) * slope2_lon) / \
                                   (slope1_lat*slope2_lon - slope1_lon*slope2_lat))

        EPSILON=0.0005
        distance = 0.0
        if intersection_scalar <= EPSILON:
            distance = latlng_dist(lineseg[0][0], lineseg[0][1], coords[0], coords[1])
        elif intersection_scalar >= (1.0 - EPSILON):
            distance = latlng_dist(lineseg[1][0], lineseg[1][1], coords[0], coords[1])
        else:
            intersection_pt = (lineseg[0][0]+(intersection_scalar*slope1_lat), 
                               lineseg[0][1]+(intersection_scalar*slope1_lon))
            distance = latlng_dist(intersection_pt[0], intersection_pt[1], coords[0], coords[1])
        if not closest_distance or distance < closest_distance:
            closest_distance = distance
    return closest_distance

def get_headsigns(stops):
    linesegs = []
    closest_distances = []
    stop_headsigns = []
    num_min_distances_exceeded = 0    
    min_dist = 100
    inflection_stop = None
    reversed = False

    def update_headsign(headsign):
        # Abbreviate transit center to something shorter
        headsign = re.sub('Transit Center', 'TC', headsign)
        headsign = re.sub('Transit Centre', 'TC', headsign)

        # HACK: work around a ridiculous bug in your YAML intermediary format
        headsign = re.sub('\'', '', headsign)

        return headsign

    prevstop = None
    for stop in stops:
        if len(linesegs) > 0:
            closest_distance = closest_seg_distance((stop.stop_lat, stop.stop_lon), linesegs)
            closest_distances.append(closest_distance) 
            
            # if we consistently go under the min distance, assume we've turned 
            # around and are going in the opposite direction
            if not reversed:
                if closest_distance < min_dist:
                    num_min_distances_exceeded += 1
                    if not inflection_stop:
                        inflection_stop = prevstop
                else:
                    num_min_distances_exceeded = 0
                    inflection_stop = None
            
                if num_min_distances_exceeded > 3:
                    reversed = True
                    
        # Keep a list of stop headsigns: nothing until we hit our inflection 
        # stop (fall back to default), last stop in route afterwards
        if reversed:            
            stop_headsigns.append(update_headsign("To " + stops[-1].stop_name))
        else:
            stop_headsigns.append(None)
                
        if prevstop:
            linesegs.append(((prevstop.stop_lat, prevstop.stop_lon), 
                             (stop.stop_lat, stop.stop_lon)))
        prevstop = stop

    print "%s reverse_stop: %s end_stop: %s" % (stop_headsigns, inflection_stop, stops[-1].stop_name)
    
    def update_headsign(headsign):
        # Abbreviate transit center to something shorter
        headsign = re.sub('Transit Centre', 'TC', headsign)

        # HACK: work around a ridiculous bug in your YAML intermediary format
        headsign = re.sub('\'', '', headsign)

        return headsign

    if not inflection_stop:
        return ("To " + update_headsign(stops[-1].stop_name), stop_headsigns)
    else:
        return ("To " + update_headsign(inflection_stop.stop_name), stop_headsigns)


usage = "usage: %prog <input gtfs feed> <output gtfs feed>"
parser = OptionParser(usage)
(options, args) = parser.parse_args()

if len(args) < 2:
    parser.error("incorrect number of arguments")
    exit(1)

print "Loading schedule."
schedule = transitfeed.Schedule(
    problem_reporter=transitfeed.ProblemReporter())
schedule.Load(args[0])

patterns = []
for route in schedule.GetRouteList():
    print "Processing %s: %s" % (route.route_short_name, route.route_long_name)
    
    pattern_id_trip_dict = route.GetPatternIdTripDict()

    for pattern_id, trips in pattern_id_trip_dict.items():        
        stops = map(lambda stop: stop[2], trips[0].GetTimeStops())
        if len(stops) == 0:
            print "WARNING: Trip %s has no stops!" % trips[0].trip_id
            continue
        (trip_headsign, stop_headsigns) = get_headsigns(stops)

        for trip in trips:
            trip.trip_headsign = trip_headsign
            stoptime_index = 0
            for stoptime in trip.GetStopTimes():
                if stop_headsigns[stoptime_index]:
                    stoptime.stop_headsign = stop_headsigns[stoptime_index]
                    trip.ReplaceStopTimeObject(stoptime)
                stoptime_index+=1

schedule.WriteGoogleTransitFeed(args[1])
