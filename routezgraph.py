#!/usr/bin/python2.5

import sys, os
import time
import datetime
import copy
import transitfeed
import osm
import math
from heapq import heappush, heappop
import bisect

def calc_latlng_distance(src_lat, src_lng, dest_lat, dest_lng):
  # fixme: use a less ridiculous calculation
  # this one from: http://www.zipcodeworld.com/samples/distance.cs.html
  # note: this function returns distance in meters
  if src_lat == dest_lat and src_lng == dest_lng:
    return 0

  theta = src_lng - dest_lng
  dist = math.sin(math.radians(src_lat)) * math.sin(math.radians(dest_lat)) + math.cos(math.radians(src_lat)) * math.cos(math.radians(dest_lat)) * math.cos(math.radians(theta))
  dist = math.acos(dist)
  dist = math.degrees(dist)
  dist = dist * 60 * 1.1515 * 1.609344 * 1000
  return dist

def get_walking_time(src_lat, src_lng, dest_lat, dest_lng):
  return calc_latlng_distance(src_lat, src_lng, dest_lat, dest_lng) / 1.1

class TripHop:
    def __init__(self, start_time, end_time, dest_id, route_id):
        self.start_time = start_time
        self.end_time = end_time
        self.dest_id = dest_id
        self.route_id = route_id

    def __cmp__(self, other):
        if type(other) == int:
            return self.start_time - other
        
        return self.start_time - other.start_time
 
class TripStop:
    def __init__(self, id, lat, lng, type):
        self.id = id
        self.lat = lat
        self.lng = lng
        self.type = type
        self.walkhops = {}
        self.triphops = {}
        self.triplinks = {}

    def add_walkhop(self, dest_id, time):
        self.walkhops[dest_id] = time

    def add_triplink(self, dest_id, time):
      self.triplinks[dest_id] = time

    def add_triphop(self, start_time, end_time, dest_id, route_id, service_id):
        if not self.triphops.get(service_id):
            self.triphops[service_id] = {}
        if not self.triphops[service_id].get(route_id):
                self.triphops[service_id][route_id] = []
        self.triphops[service_id][route_id].append(TripHop(start_time, end_time, dest_id, route_id))
        self.triphops[service_id][route_id].sort()

    def find_triphop(self, time, route_id, service_id):
        if not self.triphops.get(service_id) or \
        not self.triphops[service_id].get(route_id):
            return None
        triphops = self.triphops[service_id][route_id]
        for triphop in triphops:
          if triphop.start_time >= time:
            return triphop

        return None

    def get_routes(self, service_period):
        if self.triphops.get(service_period):
            return self.triphops[service_period].keys()
        else:
            return []

class TripAction:
  def __init__(self, src_id, dest_id, route_id, start_time, end_time):
    self.src_id = src_id
    self.dest_id = dest_id
    self.route_id = route_id
    self.start_time = start_time
    self.end_time = end_time

class TripPath:
    def __init__(self, time, src_lat, src_lng, dest_lat, dest_lng, src_stop,
                 dest_stop=None):
        self.actions = []
        self.start_time = time
        self.src_lat = src_lat
        self.src_lng = src_lng
        self.dest_lat = dest_lat
        self.dest_lng = dest_lng
        self.src_stop = src_stop
        self.dest_stop = dest_stop
        (self.weight, self.full_weight) = self._get_weight()

    def __copy__(self):
        newinst = self.__class__(self.start_time, self.src_lat, self.src_lng,
                                 self.dest_lat, self.dest_lng, self.src_stop, 
                                 self.dest_stop)
        newinst.actions = copy.copy(self.actions)
        newinst.weight = self.weight
        newinst.full_weight = self.full_weight
        return newinst

    def __cmp__(self, trippath):
        return self.weight - trippath.weight

    def add_action(self, action, tripstops):
        self.actions.append(action)
        self.dest_stop = tripstops[action.dest_id]
        (self.weight, self.full_weight) = self._get_weight()

    def get_end_time(self):
        if len(self.actions):
            return self.actions[-1].end_time
        
        dist = calc_latlng_distance(self.src_lat, self.src_lng, 
                                    self.src_stop.lat, self.src_stop.lng)
        return self.start_time + (dist / 1.1)

    def get_end_id(self):
        if len(self.actions):
            return self.actions[-1].dest_id
        return self.src_stop.id

    def get_len(self):
        return len(self.actions)

    def get_last_src_id(self):
      if len(self.actions):
        return self.actions[-1].src_id
      return -1

    def get_last_route_id(self):
      if len(self.actions):
        return self.actions[-1].route_id
      return -1
    
    def _get_weight(self):
        weight = self.start_time
        prevtime = self.start_time

        last_lat = self.src_lat
        last_lng = self.src_lng

        if len(self.actions):
            # first, calculate the time already elapsed and add that
            prevaction = None
            for action in self.actions:
                weight = weight + (action.end_time - action.start_time)
                weight = weight + (action.start_time - prevtime)
                # transfer penalty of 5 minutes if we're switching routes
                if prevaction and prevaction.route_id != action.route_id:
                  weight = weight + (5 * 60)
                prevaction = action
                prevtime = prevaction.end_time

            last_lat = self.dest_stop.lat
            last_lng = self.dest_stop.lng

        # then, calculate the time remaining based on going directly
        # from the last vertice to the destination at a ridiculous speed
        # (200km/h) for the heuristic weight, and a more realistic speed for
        # the full weight.
        remaining_distance = calc_latlng_distance(last_lat, last_lng, 
                                                  self.dest_lat, self.dest_lng)
        full_weight = weight + (remaining_distance / 1.1) # walking speed
        weight = weight + (remaining_distance / 55.55) # 200km/h==55.55m/s

        return (weight, full_weight)

class TripGraph(object):

  def __init__(self):
      self.tripstops = {}        
      self.osmstops = {}
      pass

  def add_tripstop(self, id, lat, lng, type):
    tripstop = TripStop(id, lat, lng, type)
    self.tripstops[id] = tripstop
    if type == "osm":
      self.osmstops[id] = tripstop

  def add_triphop(self, start_time, end_time, src_id, dest_id, route_id, 
                  service_id):
    self.tripstops[src_id].add_triphop(start_time, end_time, dest_id, 
                                       route_id, service_id)

  def add_walkhop(self, src_id, dest_id):
    w1 = self.tripstops[src_id]
    w2 = self.tripstops[dest_id]
    time = calc_latlng_distance(w1.lat, w1.lng, w2.lat, w2.lng) / 1.1
    self.tripstops[src_id].add_walkhop(dest_id, time)

  def get_nearest_osmstops(self, lat, lng, n=1):
    """Return the n nearest stops to lat,lon"""
    dist_stop_list = []
    for s in self.osmstops.values():
      dist = (s.lat - lat)**2 + (s.lng - lng)**2
      if len(dist_stop_list) < n:
        bisect.insort(dist_stop_list, (dist, s))
      elif dist < dist_stop_list[-1][0]:
        bisect.insort(dist_stop_list, (dist, s))
        dist_stop_list.pop()  # Remove stop with greatest distance
    return [stop for dist, stop in dist_stop_list]
        
  def load_gtfs(self, sched):
    stops = sched.GetStopList()
    for stop in stops:
      self.add_tripstop("gtfs" + stop.stop_id, stop.stop_lat, 
                        stop.stop_lon, "gtfs")
      
    trips = sched.GetTripList()
    for trip in trips:
      interpolated_stops = trip.GetTimeInterpolatedStops()
      prevstop = None
      prevsecs = 0
      idx = 0
      for (secs, stoptime, is_timepoint) in interpolated_stops:
        stop = stoptime.stop
        if prevstop:                    
          self.add_triphop(prev_secs, secs, "gtfs"+prevstop.stop_id, 
                           "gtfs"+stop.stop_id, trip.route_id, 
                           trip.service_id)                
        prevstop = stop
        prev_secs = secs        

  def load_osm(self, osm):
    for node in osm.nodes.values():
      self.add_tripstop("osm"+node.id, node.lat, node.lon, "osm")

    for way in osm.ways.values():
      prev_id = None
      for id in way.nds:
        if prev_id:
          self.add_walkhop("osm"+prev_id, "osm"+id)
        prev_id = id

  def link_osm_gtfs(self):
    mylen = len(self.tripstops.values())
    for s1 in self.tripstops.values():
      if s1.type == "gtfs":
        nearest_osm = None
        min_dist = 0
        for s2 in self.tripstops.values():
          if s2.type == "osm":
            dist = calc_latlng_distance(s1.lat, s1.lng, s2.lat, s2.lng)
            if not nearest_osm or dist < min_dist:
              nearest_osm = s2
              min_dist = dist
        time = calc_latlng_distance(nearest_osm.lat, nearest_osm.lng, s1.lat, s1.lng) / 1.1
        s1.add_triplink(nearest_osm.id, time)
        print "Adding triplink %s->%s" %(nearest_osm.id, s1.id)
        nearest_osm.add_triplink(s1.id, time)

  def find_path(self, time, src_lat, src_lng, dest_lat, dest_lng):
    # translate the time to an offset from the beginning of the day
    # and determine service period
    now = datetime.datetime.fromtimestamp(time)
    today_secs = (now.hour * 60 * 60) + (now.minute * 60) + (now.second)
    service_period = 'weekday'
    if now.weekday() == 5:
      service_period = 'saturday'
    elif now.weekday() == 6:
      service_period = 'sunday'

    # Find path
    visited_ids = {}
        
    # first, find the 5 closest start nodes and create paths based on that
    trip_paths = [ ]
    best_path = None
    for s in self.get_nearest_osmstops(src_lat, src_lng, 5):
      p = TripPath(today_secs, src_lat, src_lng, dest_lat, dest_lng, s)
      heappush(trip_paths, p)
      print "full weight %s for s %s" % (p.full_weight, s.id)
      if not best_path or best_path.full_weight > p.full_weight:
        best_path = p
    
    # then keep on extending paths until we've exhausted all possibilities
    # or we can't do any better
    while len(trip_paths) > 0:
      trip_path = heappop(trip_paths)
      print "Extending path with weight: %s" % trip_path.weight
      new_trip_paths = self.extend_path(dest_lat, dest_lng, trip_path, 
                                        service_period, visited_ids)
      for p in new_trip_paths:
        print "--Adding trip path with weight %s (full: %s)" % \
            (p.weight, p.full_weight)
        heappush(trip_paths, p)
        if best_path.full_weight > p.full_weight:
          best_path = p
            
      # if we've still got open paths, but their weight exceeds that
      # of the weight of a completed path, break
      if len(trip_paths) > 0 and best_path.full_weight <= trip_paths[0].weight:
        print "Breaking with %s uncompleted paths." % len(trip_paths)
        return best_path

      if len(trip_paths) > 0:
        print "Weight of best completed path: %s, uncompleted: %s" % \
            (best_path.weight, trip_paths[0].weight)
        
    return best_path

  def extend_path(self, dest_lat, dest_lng, trip_path, service_period, visited_ids):
    trip_paths = []
      
    time = trip_path.get_end_time()
    src_id = trip_path.get_end_id()
        
    last_route_id = trip_path.get_last_route_id()
    last_routes = []
    if trip_path.get_len() > 0:
      last_src_id = trip_path.get_last_src_id()
      last_routes = self.tripstops[last_src_id].get_routes(service_period)
      visited_ids[last_src_id][last_route_id] = 1

    print "Extending path at vertice %s (on %s)" % (src_id, last_route_id)

    # if we haven't visited this node before, find outgoing walkhops.
    if not visited_ids.get(src_id):
      for dest_id in self.tripstops[src_id].walkhops.keys():
        walktime = self.tripstops[src_id].walkhops[dest_id]
        tripaction = TripAction(src_id, dest_id, -1, time, 
                                time + walktime)
        trip_path2 = copy.copy(trip_path)
        trip_path2.add_action(tripaction, self.tripstops)
        trip_paths.append(trip_path2)

    # forbid further visits to this node using walking immediately: if
    # we're visiting it now, that means that all optimal routes to it
    # have already been found (unlike with buses, where you might want
    # to explore slightly less optimal routes to this node to reduce
    # the need for transfers)
    if not visited_ids.get(src_id):       
      visited_ids[src_id] = {}

    # explore any unvisited nodes via links
    for triplink_id in self.tripstops[src_id].triplinks.keys():
      if not visited_ids.get(triplink_id):
        print "Adding link path (%s->%s)" % (src_id, triplink_id)
        # 5 seconds to make the link (probably a dumb assumption)
        tripaction = TripAction(src_id, triplink_id, -1, time, 
                                time + self.tripstops[src_id].triplinks[triplink_id])
        trip_path2 = copy.copy(trip_path)
        trip_path2.add_action(tripaction, self.tripstops)
        trip_paths.append(trip_path2)
    
    # find outgoing triphops from the source and get a list of paths to
    # them. 
    for route_id in self.tripstops[src_id].get_routes(service_period):
      print "Processing %s" % route_id
      triphop = self.tripstops[src_id].find_triphop(time, route_id, 
                                                      service_period)
      if triphop:
        # don't extend from this node via this route if we've already
        # extended the path this way: if we have before, that indicates
        # that we've found a more optimal path
        if visited_ids.get(src_id) and \
              visited_ids[src_id].get(route_id):
          pass
        # if we could have transferred at the previous node, don't
        # transfer now
        elif route_id != last_route_id and last_routes.count(route_id) > 0:
          pass
        else:
          
          tripaction = TripAction(src_id, triphop.dest_id, \
                                    triphop.route_id, \
                                    triphop.start_time, \
                                    triphop.end_time)
          trip_path2 = copy.copy(trip_path)
          trip_path2.add_action(tripaction, self.tripstops)
          #print "--- trip actions length: %s" % len(trip_path2.actions)
          trip_paths.append(trip_path2)
    return trip_paths
