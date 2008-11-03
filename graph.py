#!/usr/bin/python

import sys, os
import time
import datetime
from datetime import date, timedelta
import unittest
import copy
import transitfeed

class TripHop:
    def __init__(self, start_time, end_time, dest_id, route_id):
        self.start_time = start_time
        self.end_time = end_time
        self.dest_id = dest_id
        self.route_id = route_id

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
        self.triphops[service_id][route_id].sort(
            lambda x, y: x.start_time - y.end_time)

    def find_triphop(self, time, route_id, service_id):
        if not self.triphops.get(service_id) or \
        not self.triphops[service_id].get(route_id):
            return None
        for triphop in self.triphops[service_id][route_id]:
            if triphop.start_time >= time:
                return triphop

        return None

    def get_routes(self, service_period):
        if self.triphops.get(service_period):
            return self.triphops[service_period].keys()
        else:
            return []

class TripAction:
    def __init__(self, src_id, dest_id, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time
        self.src_id = src_id
        self.dest_id = dest_id
        pass

    def __eq__(self, tripaction):
        return self.start_time == tripaction.start_time and \
            self.end_time == tripaction.end_time and \
            self.src_id == tripaction.src_id and \
            self.dest_id == tripaction.dest_id

    def get_weight(self):
        return self.end_time - self.start_time

class TripPath:
    def __init__(self, time, src_id):
        self.actions = []
        self.start_time = time
        self.src_id = src_id

    def get_end_time(self):
        if len(self.actions):
            return self.actions[-1].end_time
        return self.start_time

    def get_end_id(self):
        if len(self.actions):
            return self.actions[-1].dest_id
        return self.src_id

    def get_weight(self):
        weight = 0
        for action in self.actions:
            weight = weight + action.get_weight()

        return weight

class TripGraph:
    def __init__(self):
        self.tripstops = {}

    def add_tripstop(self, id, lat, lng):
        self.tripstops[id] = TripStop(id, lat, lng)
    
    def add_triphop(self, start_time, end_time, src_id, dest_id, route_id, service_id):
        self.tripstops[src_id].add_triphop(start_time, end_time, dest_id, \
                                               route_id, service_id)
        
    def find_path(self, time, src_id, dest_id):
        # translate the time to an offset from the beginning of the day
        # and determine service period
        now = datetime.datetime.fromtimestamp(time)
        today_secs = (now.hour * 60 * 60) + (now.minute * 60) + (now.second)
        service_period = 'weekday'
        if now.weekday == 5:
            service_period = 'saturday'
        elif now.weekday == 6:
            service_period = 'sunday'

        # Find path
        trip_paths = [ TripPath(today_secs, src_id) ]
        completed_paths = []
        visited_ids = []

        while len(completed_paths) == 0 and len(trip_paths) > 0:
            trip_path = trip_paths.pop(0)           
            new_trip_paths = self.extend_path(dest_id, trip_path, 
                                              service_period, visited_ids)
            for new_trip_path in new_trip_paths:
                if new_trip_path.get_end_id() == dest_id:
                    print "found completed path"
                    completed_paths.append(new_trip_path)
                else:
                    print "found uncompleted path"
                    trip_paths.append(new_trip_path)
                trip_paths.sort(lambda x, y: x.get_weight() - y.get_weight())
                completed_paths.sort(lambda x, y: x.get_weight() - y.get_weight())
            # if we've still got open paths, but their weight exceeds that
            # of any completed paths, break
            if len(completed_paths) > 0 and len(trip_paths) > 0 and \
                     completed_paths[0].get_weight() < trip_paths[0].get_weight():
                 break;

        if len(completed_paths) > 0:
            return completed_paths.pop()

        return None

    def extend_path(self, dest_id, trip_path, service_period, visited_ids):
        trip_paths = []
        
        time = trip_path.get_end_time()
        src_id = trip_path.get_end_id()

        print "Extending path at vertice %s" % src_id

        # if we're extending the path from this source id, then that must
        # by definition mean we've found the shortest path to it. don't
        # extend any other nodes here
        visited_ids.append(src_id)
        
        # find outgoing nodes from the source and get a list of paths to
        # them. ignore paths which extend to nodes we've already visited.
        for route_id in self.tripstops[src_id].get_routes(service_period):
            print "Processing %s" % route_id
            triphop = self.tripstops[src_id].find_triphop(time, route_id, service_period)
            if triphop and visited_ids.count(triphop.dest_id) == 0:
                print "-- Extending path to %s" % triphop.dest_id
                tripaction = TripAction(src_id, triphop.dest_id, \
                                            triphop.start_time, \
                                            triphop.end_time)
                trip_path2 = copy.deepcopy(trip_path)
                trip_path2.actions.append(tripaction)
                print "--- trip actions length: %s" % len(trip_path2.actions)
                trip_paths.append(trip_path2)

        return trip_paths

class TestStop(unittest.TestCase):
    def test_basic(self):
        stop = TripStop(123, 0.0, 0.0)
        stop.add_triphop(110, 115, 124, 1)
        stop.add_triphop(100, 105, 124, 1)
        assert stop.find_triphop(95, 1).start_time == 100
        assert stop.find_triphop(101, 1).start_time == 110
        assert stop.find_triphop(111, 1) == None

class TestGraph(unittest.TestCase):
    def test_find_path(self):
        graph = TripGraph()
        graph.tripstops[123] = TripStop(123, 0.0, 0.0)
        graph.tripstops[124] = TripStop(124, 1.0, 0.0)
        graph.tripstops[125] = TripStop(125, 2.0, 0.0)
        graph.tripstops[123].add_triphop(110, 115, 124, 1)
        graph.tripstops[123].add_triphop(110, 115, 124, 2)
        graph.tripstops[124].add_triphop(115, 120, 125, 2)
        # stupid path: 123->124
        trippath = graph.find_path(100, 123, 124)
        assert len(trippath.actions) == 1
        assert trippath.actions[0] == TripAction(123, 124, 110, 115)
        # slightly less stupid path: 123->124->125
        trippath = graph.find_path(100, 123, 125)
        assert len(trippath.actions) == 2
        assert trippath.actions[0] == TripAction(123, 124, 110, 115) 
        assert trippath.actions[1] == TripAction(124, 125, 115, 120) 

class GTFSGraph(unittest.TestCase):
    def test_import_feed(self):
        graph = TripGraph()

        sched = transitfeed.Schedule(
            problem_reporter=transitfeed.ProblemReporter())
        print "Loading schedule."
        sched.Load("hfxfeed.zip")
        print "Done loading schedule."
        stops = sched.GetStopList()
        for stop in stops:
            graph.add_tripstop(stop.stop_id, stop.stop_lat, stop.stop_lon)

        trips = sched.GetTripList()
        for trip in trips:
            interpolated_stops = trip.GetTimeInterpolatedStops()
            prevstop = None
            prevsecs = 0
            idx = 0
            for (secs, stoptime, is_timepoint) in interpolated_stops:
                stop = stoptime.stop
                if prevstop:                    
                    graph.add_triphop(prev_secs, secs, prevstop.stop_id, 
                                      stop.stop_id, trip.route_id, 
                                      trip.service_id)                
                prevstop = stop
                prev_secs = secs
        
        def find_stop_by_code(stops, stop_code):
            for stop in stops:
                if str(stop.stop_code) == str(stop_code):
                    return stop
            return None
        
        stop1 = find_stop_by_code(sched.GetStopList(), 7378) # samuel prince manor
        stop2 = find_stop_by_code(sched.GetStopList(), 8165) # northridge road (richmond manor)
        testtime1 = 1225730967 # Mon 3 Nov 2008 @ 12:49PM AST
        trippath = graph.find_path(testtime1, stop1.stop_id, stop2.stop_id)
        def secs_to_time(secs):
            hours = int(secs/60/60) % 24
            minutes = int((secs % (60 * 60))/60)
            subsecs = (secs % 60)
            return datetime.time(hours, minutes, subsecs)

        for action in trippath.actions:
            print "action.src_id: %s action.dest_id: %s action.start_time: %s action.end_time: %s" % (action.src_id, action.dest_id, secs_to_time(action.start_time), secs_to_time(action.end_time))

if __name__ == '__main__':
    tl = unittest.TestLoader()
    testables = [\
        GTFSGraph,
        #TestGraph,
        #TestStop,
        ]
    for testable in testables:
        suite = tl.loadTestsFromTestCase(testable)
        unittest.TextTestRunner(verbosity=2).run(suite)
