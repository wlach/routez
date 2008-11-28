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
  def __init__(self, src_id, dest_id, route_id, route_ids, start_time, end_time):
    self.src_id = src_id
    self.dest_id = dest_id
    self.route_id = route_id
    self.route_ids = route_ids
    self.start_time = start_time
    self.end_time = end_time

class TripPath:
    def __init__(self, time, fastest_speed, src_lat, src_lng, dest_lat, dest_lng, src_stop,
                 dest_stop, last_stop=None):
        self.actions = []
        self.start_time = time
        self.fastest_speed = fastest_speed
        self.src_lat = src_lat
        self.src_lng = src_lng
        self.dest_lat = dest_lat
        self.dest_lng = dest_lng
        self.src_stop = src_stop
        self.dest_stop = dest_stop
        self.last_stop = last_stop
        self.walking_time = 0
        self.traversed_route_ids = 0
        self.weight = self._get_weight()
        self.route_ids = {}

    def __copy__(self):
        newinst = self.__class__(self.start_time, self.fastest_speed, self.src_lat, self.src_lng,
                                 self.dest_lat, self.dest_lng, self.src_stop, 
                                 self.dest_stop, self.last_stop)
        newinst.actions = copy.copy(self.actions)
        newinst.weight = self.weight
        newinst.walking_time = self.walking_time
        newinst.route_ids = copy.copy(self.route_ids)        
        return newinst

    def __cmp__(self, trippath):
        return self.weight - trippath.weight

    def add_action(self, action, tripstops):
        if action.route_id == -1:
          self.walking_time = self.walking_time + (action.end_time - action.start_time)
        elif len(self.actions) > 0 and action.route_id != self.actions[-1].route_id:
          self.traversed_route_ids = self.traversed_route_ids + 1
        for route_id in action.route_ids:
          self.route_ids[route_id] = 1

        self.actions.append(action)
        self.last_stop = tripstops[action.dest_id]
        self.weight = self._get_weight()


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

        last_lat = self.src_stop.lat
        last_lng = self.src_stop.lng
        last_route_id = -1

        if len(self.actions):
            # first, calculate the time already elapsed and add that
            traversed_route_ids = 0
            prevaction = None
            for action in self.actions:
                weight = weight + (action.end_time - action.start_time)
                weight = weight + (action.start_time - prevtime)
                prevaction = action
                prevtime = prevaction.end_time
                
            last_lat = self.last_stop.lat
            last_lng = self.last_stop.lng
            weight = weight + ((self.traversed_route_ids**2) * 5 * 60)            

        # then, calculate the time remaining based on going directly
        # from the last vertice to the destination vertice at the fastest
        # possible speed in the graph
        remaining_distance = calc_latlng_distance(last_lat, last_lng, 
                                                  self.dest_stop.lat, self.dest_stop.lng)
        weight = weight + (remaining_distance / self.fastest_speed)

        # double the cost of walking after 5 mins, then exponentially make 
        # walking time more expensive as it exceeds 10mins
        if self.walking_time > (5*60):
          if self.walking_time > (10*60):            
            weight = weight + 2 * (5*60) + (self.walking_time - (10*60))**2
          else:            
            weight = weight + self.walking_time*2
          
        # add 5 mins to our weight if we were walking and remaining distance
        # >500m, to account for the fact that we're probably going to
        # want to wait for another bus
        if last_route_id == -1 and remaining_distance > 1000:
          weight = weight + (5*60)

        return weight

class TripGraph(object):

  def __init__(self):
      self.tripstops = {}        
      self.osmstops = {}
      self.fastest_speed = 1.1
      pass

  def add_tripstop(self, id, lat, lng, type):
    tripstop = TripStop(id, lat, lng, type)
    self.tripstops[id] = tripstop
    if type == "osm":
      self.osmstops[id] = tripstop

  def add_triphop(self, start_time, end_time, src_id, dest_id, route_id, 
                  service_id):
    s1 = self.tripstops[src_id]
    s2 = self.tripstops[dest_id]
    dist = calc_latlng_distance(s1.lat, s1.lng, s2.lat, s2.lng)
    total_time = end_time - start_time
    speed = float(dist) / float(total_time)
    if total_time > 30 and dist > 0 and speed > self.fastest_speed:
      self.fastest_speed = speed
    self.tripstops[src_id].add_triphop(start_time, end_time, dest_id, 
                                       route_id, service_id)

  def add_walkhop(self, src_id, dest_id):
    w1 = self.tripstops[src_id]
    w2 = self.tripstops[dest_id]
    time = calc_latlng_distance(w1.lat, w1.lng, w2.lat, w2.lng) / 1.1
    self.tripstops[src_id].add_walkhop(dest_id, time)

  def get_nearest_osmstop(self, lat, lng):
    """Return the n nearest stops to lat,lon"""
    closest_stop = None
    min_dist = 0
    for s in self.osmstops.values():
      dist = (s.lat - lat)**2 + (s.lng - lng)**2
      if not closest_stop or dist < min_dist:
        closest_stop = s
        min_dist = dist
    return closest_stop
        
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
      # note, strangely enough the stops in a trip go in reverse order:
      # ie, we start with later ones, going back to earlier ones
      for (secs, stoptime, is_timepoint) in interpolated_stops:
        stop = stoptime.stop
        if prevstop:
          # stupid side-effect of google's transit feed python script being broken
          if int(secs) < int(prevsecs):
            print "WARNING: Negative edge in gtfs %s %s secs: %s, prevsecs: %s %s->%s" % (trip.trip_id, trip.trip_headsign, 
                                                                                          secs, prevsecs, prevstop.stop_id, stop.stop_id)
          #print "Adding triphop %s %s %s->%s" % (trip.trip_id, trip.trip_headsign, prevstop.stop_id, stop.stop_id)
          self.add_triphop(prevsecs, secs, "gtfs"+prevstop.stop_id, 
                           "gtfs"+stop.stop_id, trip.route_id, 
                           trip.service_id)                
        prevstop = stop
        prevsecs = secs

  def load_osm(self, osm):
    for node in osm.nodes.values():
      self.add_tripstop("osm"+node.id, node.lat, node.lon, "osm")

    for way in osm.ways.values():
      prev_id = None
      for id in way.nds:
        if prev_id:
          self.add_walkhop("osm"+prev_id, "osm"+id)
          self.add_walkhop("osm"+id, "osm"+prev_id)
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
        
    uncompleted_paths = [ ]
    completed_paths = [ ]
    best_path = None
    start_node = self.get_nearest_osmstop(src_lat, src_lng)
    end_node = self.get_nearest_osmstop(dest_lat, dest_lng)
    print "Start: %s End: %s" % (start_node.id, end_node.id)

    # stupid case: start is equal to end
    if start_node == end_node:
      return None

    heappush(uncompleted_paths, TripPath(today_secs, self.fastest_speed, 
                                         src_lat, 
                                         src_lng, dest_lat, dest_lng, 
                                         start_node, end_node))
    
    # then keep on extending paths until we've exhausted all possibilities
    # or we can't do any better
    num_paths_considered = 0
    while len(uncompleted_paths) > 0:
      trip_path = heappop(uncompleted_paths)
      print "Extending path with weight: %s" % trip_path.weight
      new_trip_paths = self.extend_path(trip_path, service_period, visited_ids)
      num_paths_considered = num_paths_considered + len(new_trip_paths)
      for p in new_trip_paths:
        if p.get_end_id() == end_node.id:
          heappush(completed_paths, p)
        else:
          heappush(uncompleted_paths, p)

      # if we've still got open paths, but their weight exceeds that
      # of the weight of a completed path, break
      if len(uncompleted_paths) > 0 and len(completed_paths) > 0 and \
            uncompleted_paths[0].weight > completed_paths[0].weight:
        print "Breaking with %s uncompleted paths (paths considered: %s)." % (len(uncompleted_paths), num_paths_considered)
        return completed_paths[0]

      if len(completed_paths) > 0 and len(uncompleted_paths) > 0:
        print "Weight of best completed path: %s, uncompleted: %s" % \
            (completed_paths[0].weight, uncompleted_paths[0].weight)

    if len(completed_paths) > 0:
      return completed_paths[0]
    else:
      return None      

  def extend_path(self, trip_path, service_period, visited_ids):
    trip_paths = []
      
    time = trip_path.get_end_time()
    src_id = trip_path.get_end_id()
        
    if not visited_ids.get(src_id):
      visited_ids[src_id] = {}

    last_route_id = trip_path.get_last_route_id()
    last_routes = []

    if trip_path.get_len() > 0:
      last_src_id = trip_path.get_last_src_id()
      last_routes = self.tripstops[last_src_id].get_routes(service_period)
      if last_route_id != -1 and visited_ids[last_src_id].get(last_route_id):
        return trip_paths
      visited_ids[last_src_id][last_route_id] = 1

    print "Extending path at vertice %s (on %s), walk time: %s" % (src_id, last_route_id, trip_path.walking_time)      

    # keep track of outgoing route ids at this node: make sure that we don't
    # get on a route later when we could have gotten on here
    outgoing_route_ids = self.tripstops[src_id].get_routes(service_period)

    # if we haven't visited this node before, find outgoing walkhops (to nodes
    # that we haven't visited before). 
    # if we've already visited this node via walking, don't visit it again
    if not visited_ids[src_id].get(-1):
      for dest_id in self.tripstops[src_id].walkhops.keys():
        walktime = self.tripstops[src_id].walkhops[dest_id]
        tripaction = TripAction(src_id, dest_id, -1, 
                                outgoing_route_ids, time, 
                                time + walktime)
        trip_path2 = copy.copy(trip_path)
        trip_path2.add_action(tripaction, self.tripstops)
        trip_paths.append(trip_path2)

      # explore any unvisited nodes via links
      for triplink_id in self.tripstops[src_id].triplinks.keys():
        walktime = self.tripstops[src_id].triplinks[triplink_id]
        tripaction = TripAction(src_id, triplink_id, -1, outgoing_route_ids, 
                                time, time + walktime)
        trip_path2 = copy.copy(trip_path)
        trip_path2.add_action(tripaction, self.tripstops)
        trip_paths.append(trip_path2)

    # find outgoing triphops from the source and get a list of paths to
    # them. 
    for route_id in outgoing_route_ids:
      # print "Processing %s" % route_id
      triphop = self.tripstops[src_id].find_triphop(time, route_id, 
                                                    service_period)
      if triphop:
        # don't extend from this node via this route if we've already
        # extended the path this way: if we have before, that indicates
        # that we've found a more optimal path
        if visited_ids[src_id].get(route_id):
          pass
        # if we've been on the route before (or could have been), don't get on 
        # again
        elif route_id != last_route_id and trip_path.route_ids.get(route_id):
          pass
        else:          
          tripaction = TripAction(src_id, triphop.dest_id, \
                                    triphop.route_id, \
                                    outgoing_route_ids, \
                                    triphop.start_time, \
                                    triphop.end_time)
          trip_path2 = copy.copy(trip_path)
          trip_path2.add_action(tripaction, self.tripstops)
          #print "--- trip actions length: %s" % len(trip_path2.actions)
          trip_paths.append(trip_path2)

    return trip_paths
