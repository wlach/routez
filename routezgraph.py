#!/usr/bin/python2.5

import sys, os
import time
import datetime
from datetime import date, timedelta
import copy
import transitfeed
import math
from heapq import heappush, heappop

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
    def __init__(self, id, lat, lng):
        self.id = id
        self.triphops = {}
        self.lat = lat
        self.lng = lng

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

class TripGraph:
    def __init__(self):
        self.tripstops = {}

    def add_tripstop(self, id, lat, lng):
        self.tripstops[id] = TripStop(id, lat, lng)
    
    def add_triphop(self, start_time, end_time, src_id, dest_id, route_id, service_id):
        self.tripstops[src_id].add_triphop(start_time, end_time, dest_id, 
                                           route_id, service_id)

    def get_nearest_tripstops(self, lat, lng, n=1):
      """Return the n nearest stops to lat,lon"""
      dist_stop_list = []
      for s in self.tripstops.values():
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
            self.add_tripstop(stop.stop_id, stop.stop_lat, stop.stop_lon)

        trips = sched.GetTripList()
        for trip in trips:
            interpolated_stops = trip.GetTimeInterpolatedStops()
            prevstop = None
            prevsecs = 0
            idx = 0
            for (secs, stoptime, is_timepoint) in interpolated_stops:
                stop = stoptime.stop
                if prevstop:                    
                    self.add_triphop(prev_secs, secs, prevstop.stop_id, 
                                      stop.stop_id, trip.route_id, 
                                      trip.service_id)                
                prevstop = stop
                prev_secs = secs        
        
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
        print "Service period: %s" % service_period

        # Find path
        visited_ids = {}

        # FIXME: calculate and use a base case where we just walk between
        # the two points

        # first, find the 20 closest start nodes and create paths based on that
        trip_paths = [ ]
        best_path = None
        for s in self.get_nearest_tripstops(src_lat, src_lng, 20):
          p = TripPath(today_secs, src_lat, src_lng, dest_lat, dest_lng, s)
          heappush(trip_paths, p)
          print "full weight %s for s %s" % (p.full_weight, s.id)
          if not best_path or best_path.full_weight > p.full_weight:
            best_path = p

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
        if not visited_ids.get(last_src_id):       
          visited_ids[last_src_id] = {}
        visited_ids[last_src_id][last_route_id] = 1

      print "Extending path at vertice %s (on %s)" % (src_id, last_route_id)

      # find outgoing nodes from the source and get a list of paths to
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
            print "-- NOT Extending path to %s (via %s), been there, done that" % (triphop.dest_id, route_id)                  
          # if we could have transferred at the previous node, don't
          # transfer now
          elif route_id != last_route_id and last_routes.count(route_id) > 0:
            print "-- NOT Extending path to %s (via %s), pointless transfer" % (triphop.dest_id, route_id)
          else:
            print "-- Extending path to %s (via %s)" % (triphop.dest_id, route_id)
            tripaction = TripAction(src_id, triphop.dest_id, \
                                      triphop.route_id, \
                                      triphop.start_time, \
                                      triphop.end_time)
            trip_path2 = copy.copy(trip_path)
            trip_path2.add_action(tripaction, self.tripstops)
            #print "--- trip actions length: %s" % len(trip_path2.actions)
            trip_paths.append(trip_path2)

      return trip_paths

