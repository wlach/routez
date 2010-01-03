#!/usr/bin/python2.5

import sys, os
import time
import datetime
import copy
import transitfeed
import osm
import math
import latlng_ext
from trippath import *
from heapq import heappush, heappop

class TripHop:
    def __init__(self, start_time, end_time, dest_id, route_id):
        self.start_time = start_time
        self.end_time = end_time
        self.dest_id = dest_id

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

    def add_walkhop(self, dest_id, time):
      self.walkhops[dest_id] = time

    def add_triphop(self, start_time, end_time, dest_id, route_id, service_id):
        if not self.triphops.get(service_id):
          self.triphops[service_id] = {}
        if not self.triphops[service_id].get(route_id):
          self.triphops[service_id][route_id] = []
        self.triphops[service_id][route_id].append(TripHop(start_time, end_time, dest_id, route_id))
        self.triphops[service_id][route_id].sort()

    def find_triphop(self, time, route_id, service_id):
        if not self.triphops.get(service_id) or \
                not self.triphops[service_id].get(str(route_id)):
            return None
        triphops = self.triphops[service_id][str(route_id)]
        for triphop in triphops:
            if triphop.start_time >= time:
                return triphop
        return None

    def get_routes(self, service_period):
        if self.triphops.get(service_period):
            # big hack to make sure boost::python gets integers, if we
            # didn't need to do this, we could use the simpler method below
            array = []
            for route in self.triphops.get(service_period):
                array.append(int(route))
            return array
            #return self.triphops[service_period].keys()
        else:
            return []

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
    dist = latlng_ext.distance(s1.lat, s1.lng, s2.lat, s2.lng)
    total_time = end_time - start_time
    speed = float(dist) / float(total_time)
    if total_time > 30 and dist > 0 and speed > self.fastest_speed:
      self.fastest_speed = speed
    self.tripstops[src_id].add_triphop(start_time, end_time, dest_id, 
                                       route_id, service_id)

  def add_walkhop(self, src_id, dest_id):
    w1 = self.tripstops[src_id]
    w2 = self.tripstops[dest_id]
    time = latlng_ext.distance(w1.lat, w1.lng, w2.lat, w2.lng) / 1.1
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
            dist = latlng_ext.distance(s1.lat, s1.lng, s2.lat, s2.lng)
            if not nearest_osm or dist < min_dist:
              nearest_osm = s2
              min_dist = dist
        time = latlng_ext.distance(nearest_osm.lat, nearest_osm.lng, s1.lat, s1.lng) / 1.1
        print "Adding triplink %s->%s" %(nearest_osm.id, s1.id)
        self.add_walkhop(nearest_osm.id, s1.id)
        self.add_walkhop(s1.id, nearest_osm.id)

  def find_path(self, time, src_lat, src_lng, dest_lat, dest_lng, cb=None):
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

    dist_from_start = latlng_ext.distance(src_lat, src_lng, start_node.lat, start_node.lng)
    today_secs += dist_from_start / 1.1

    heappush(uncompleted_paths, TripPath(int(today_secs), self.fastest_speed, 
                                         end_node, start_node))
    
    # then keep on extending paths until we've exhausted all possibilities
    # or we can't do any better
    num_paths_considered = 0
    while len(uncompleted_paths) > 0:
      trip_path = heappop(uncompleted_paths)
      #print "Extending path with weight: %s" % (trip_path.heuristic_weight)
      new_trip_paths = self.extend_path(trip_path, service_period, visited_ids, cb)
      num_paths_considered += len(new_trip_paths)
      for p in new_trip_paths:
        if p.last_stop.id == end_node.id:
          heappush(completed_paths, p)
        else:
          heappush(uncompleted_paths, p)

      # if we've still got open paths, but their weight exceeds that
      # of the weight of a completed path, break
      if len(uncompleted_paths) > 0 and len(completed_paths) > 0 and \
            uncompleted_paths[0].heuristic_weight > completed_paths[0].heuristic_weight:
        print "Breaking with %s uncompleted paths (paths considered: %s)." % (len(uncompleted_paths), num_paths_considered)
        return completed_paths[0]

      #if len(completed_paths) > 0 and len(uncompleted_paths) > 0:
      #  print "Weight of best completed path: %s, uncompleted: %s" % \
      #      (completed_paths[0].heuristic_weight, uncompleted_paths[0].heuristic_weight)

    if len(completed_paths) > 0:
      return completed_paths[0]
    else:
      return None      

  def extend_path(self, trip_path, service_period, visited_ids, cb):     
    src_id = trip_path.last_stop.id
        
    if not visited_ids.get(src_id):
      visited_ids[src_id] = {}

    last_route_id = trip_path.last_route_id

    if trip_path.last_action:
      last_src_id = trip_path.last_action.src_id
      if cb:
        cb(last_src_id, src_id, last_route_id)
      if last_route_id != -1 and visited_ids[last_src_id].get(last_route_id):
        return []
      visited_ids[last_src_id][last_route_id] = trip_path

    #print "Extending path at vertice %s (on %s)" % (src_id, last_route_id)

    # keep track of outgoing route ids at this node: make sure that we don't
    # get on a route later when we could have gotten on here
    outgoing_route_ids = self.tripstops[src_id].get_routes(service_period)

    # now start keeping track of new trip paths
    trip_paths = []

    # if we haven't visited this node before, find outgoing walkhops (to nodes
    # that we haven't visited before). 
    # if we've already visited this node via walking, don't visit it again
    # also, if we're on a bus, don't allow a transfer if we've been on for
    # less than 10 minutes
    if not visited_ids[src_id].get(-1):
        if last_route_id != -1 and trip_path.route_time < (10 * 60):
            pass
        else:
            for dest_id in self.tripstops[src_id].walkhops.keys():
                walktime = self.tripstops[src_id].walkhops[dest_id]
                tripaction = TripAction(str(src_id), str(dest_id), -1, 
                                        trip_path.time, 
                                        trip_path.time + walktime)
                trip_path2 = trip_path.add_action(tripaction, 
                                                  outgoing_route_ids, 
                                                  self.tripstops[dest_id])
                trip_paths.append(trip_path2)

    # find outgoing triphops from the source and get a list of paths to
    # them. 
    for route_id in outgoing_route_ids:
      triphop = self.tripstops[src_id].find_triphop(trip_path.time, 
                                                    route_id, 
                                                    service_period)
      if triphop:
        # don't extend from this node via this route if we've already
        # extended the path this way: if we have before, that indicates
        # that we've found a more optimal path
        # FIXME: this isn't actually true, sometimes we find a more optimal
        # path later-- in these cases we need to be able to measure the putative
        # new path against the one that exists
        #if visited_ids[src_id].get(route_id):
        #  pass
        # if we've been on the route before (or could have been), don't get on 
        # again
        if route_id != last_route_id and route_id in trip_path.possible_route_ids:
          pass
        # disallow more than three transfers
        elif route_id != last_route_id and trip_path.traversed_route_ids > 3:
            pass
        else:
            tripaction = TripAction(str(src_id), str(triphop.dest_id), 
                                    int(route_id), 
                                    triphop.start_time, 
                                    triphop.end_time)
            trip_path2 = trip_path.add_action(tripaction, outgoing_route_ids, 
                                              self.tripstops[triphop.dest_id])
            existing_path = visited_ids[src_id].get(route_id)
            if not existing_path or \
                    existing_path.heuristic_weight > trip_path2.heuristic_weight or \
                    (existing_path.heuristic_weight == trip_path2.heuristic_weight and \
                         existing_path.walking_time > trip_path2.walking_time):
                trip_paths.append(trip_path2)

    return trip_paths
