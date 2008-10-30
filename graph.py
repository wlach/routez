#!/usr/bin/python

import sys, os
import time
import unittest
import copy

class TripHop:
    def __init__(self, start_time, end_time, dest_id, route_id):
        self.start_time = start_time
        self.end_time = end_time
        self.dest_id = dest_id
        self.route_id = route_id

class TripStop:
    def __init__(self, id):
        self.id = id
        self.triphops = {}

    def add_triphop(self, start_time, end_time, dest_id, route_id):
        if not self.triphops.get(route_id):
            self.triphops[route_id] = []
        self.triphops[route_id].append(TripHop(start_time, end_time, dest_id, route_id))
        self.triphops[route_id].sort(lambda x, y: x.start_time - y.end_time)

    def find_triphop(self, time, route_id):
        for triphop in self.triphops[route_id]:
            if triphop.start_time >= time:
                return triphop
        return None

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

    def find_path(self, time, src_id, dest_id):
        trip_paths = [ TripPath(time, src_id) ]
        completed_paths = []
        visited_ids = []

        while len(completed_paths) == 0 and len(trip_paths) > 0:
            trip_path = trip_paths.pop(0)           
            new_trip_paths = self.extend_path(dest_id, trip_path, \
                                                  visited_ids)
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

    def extend_path(self, dest_id, trip_path, visited_ids):
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
        for route_id in self.tripstops[src_id].triphops.keys():
            triphop = self.tripstops[src_id].find_triphop(time, route_id)
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
        stop = TripStop(123)
        stop.add_triphop(110, 115, 124, 1)
        stop.add_triphop(100, 105, 124, 1)
        assert stop.find_triphop(95, 1).start_time == 100
        assert stop.find_triphop(101, 1).start_time == 110
        assert stop.find_triphop(111, 1) == None

class TestGraph(unittest.TestCase):
    def test_find_path(self):
        graph = TripGraph()
        graph.tripstops[123] = TripStop(123)
        graph.tripstops[124] = TripStop(124)
        graph.tripstops[125] = TripStop(125)
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

if __name__ == '__main__':
    tl = unittest.TestLoader()
    testables = [\
        TestGraph,
        TestStop,                 
        ]
    for testable in testables:
        suite = tl.loadTestsFromTestCase(testable)
        unittest.TextTestRunner(verbosity=2).run(suite)
