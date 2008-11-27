#!/usr/bin/python

import sys
import transitfeed
import routezsettings
from routezgraph import *
import cPickle

if __name__ == '__main__':

    if len(sys.argv) < 4:
        print "Usage: %s: <gtfs feed> <osm file> <graph>" % sys.argv[0]
        exit(1)

    schedule = transitfeed.Schedule(
        problem_reporter=transitfeed.ProblemReporter())
    print "Loading schedule."
    schedule.Load(sys.argv[1])
    
    print "Loading OSM."
    map = osm.OSM(sys.argv[2])

    graph = TripGraph()
    print "Creating graph from gtfs"
    graph.load_gtfs(schedule)
    print "Creating graph from osm"    
    graph.load_osm(map)
    print "Linking gtfs with osm"
    graph.link_osm_gtfs()
    
    print "Pickling graph to disk"
    FILE = open(sys.argv[3], 'wb')
    cPickle.dump(graph, FILE, -1)
