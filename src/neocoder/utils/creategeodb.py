#!/usr/bin/python

import math
import os
import re
import sqlite3
import string
import struct
import sys
import xml.sax

import mappings

def latlng_dist(src_lat, src_lng, dest_lat, dest_lng):

    if round(src_lat, 4) == round(dest_lat, 4) and \
            round(src_lng, 4) == round(dest_lng, 4):
        return 0.0

    theta = src_lng - dest_lng
    src_lat_radians = math.radians(src_lat)
    dest_lat_radians = math.radians(dest_lat)
    dist = math.sin(src_lat_radians) * math.sin(dest_lat_radians) + \
        math.cos(src_lat_radians) * math.cos(dest_lat_radians) * \
        math.cos(math.radians(theta))
    dist = math.degrees(math.acos(dist)) * (60.0 * 1.1515 * 1.609344 * 1000.0)
    return dist

class RoadSegment:
    def __init__(self):
        self.coords = []
        self.left = {}
        self.right = {}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: %s <python file> <sqlite db>" % sys.argv[0]
        exit(1)
    
    try:
        os.unlink(sys.argv[2])
    except OSError:
        pass

    conn = sqlite3.connect(sys.argv[2])

    cursor = conn.cursor()
    cursor.execute("create table placename (name text)")
    cursor.execute("create table road (name text, firstHouseNumber integer, "\
                       "lastHouseNumber integer, numberingTypeEven boolean, " \
                       "suffixType integer, direction integer, length real, " \
                       "placeName text, coords blob)")
    cursor.execute("create table intersection (name1 text, suffix1 text, name2 text, suffix2 text, placeName text, lat real, lng real)")
    conn.commit()

    nodes = {} # keep track of all nodes to parse intersections later
    placenames = set() # keep track of all placenames (e.g. Edmonton, Dartmouth)

    print "Parsing geodb and writing road segments"
    if sys.argv[1] == "-":
        f = sys.stdin
    else:
        f = open(sys.argv[1])
    line = f.readline()
    while line:
        dict = eval(line)
        for side in [ dict["left"], dict["right"] ]:
            if side.get('name') and side['name'] != "Unknown":
                if side['firstNumber'] > 0 and side['lastNumber'] > 0:
                    even = 0
                    if side['firstNumber'] % 2 == 0:
                        even = 1

                    coords_buf = struct.pack("l", len(dict['coords']),)
                    prevcoord = None
                    length = 0.0
                    for coord in dict['coords']:
                        coords_buf += struct.pack("ff", coord[0], coord[1],)
                        if prevcoord:
                            length += latlng_dist(coord[0], coord[1], prevcoord[0], prevcoord[1])
                            
                        key = str(round(coord[0],3))+","+str(round(coord[1],3))
                        if not nodes.get(key):
                            nodes[key] = { "latlng": (coord[0], coord[1]),
                                           "roadsegs": [] }
                        nodes[key]["roadsegs"].append(side)

                        prevcoord = coord
                    
                    suffix_type = 0 # unknown
                    direction = 0 # unknown
                    if mappings.suffix_dict.get(side['suffix'].lower()):
                        suffix_type = mappings.suffix_dict[side['suffix'].lower()]
                    if side.get('direction') and mappings.direction_dict.get(side['direction'].lower()):
                        direction = mappings.direction_dict[side['direction'].lower()]

                    cursor.execute("insert into road values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', ?);" % (
                            side['name'].replace("'", "''"), 
                            side['firstNumber'], side['lastNumber'],
                            even, suffix_type, direction, length, side['placeName']),
                                   [sqlite3.Binary(coords_buf)])
                    placenames.add(side['placeName'])

        line = f.readline()

    print "Writing intersections"
    intersections_inserted = {}
    for latlng in nodes.keys():
        roadsegs = nodes[latlng]["roadsegs"]
            
        if len(roadsegs) > 1:
            (lat, lng) = nodes[latlng]["latlng"]
                
            for i in range (0, len(roadsegs)):
                for j in range (0, len(roadsegs)):
                    if i != j:
                        roadseg1 = roadsegs[i]
                        roadseg2 = roadsegs[j]
                        name1 = roadseg1.get('name')
                        name2 = roadseg2.get('name')
                        if name1 and name2 and name1 != name2:
                            if name1 > name2:
                                roadseg1, roadseg2 = roadseg2, roadseg1
                                    
                            intersection_key = name1+roadseg1['suffix']+","+name2+roadseg2['suffix']
                            if not intersections_inserted.get(intersection_key):
                                cursor.execute("insert into intersection " \
                                                   "values ('%s', '%s', '%s', '%s', '%s', '%s', '%s');" % 
                                               (name1.replace("'", "''"), 
                                                roadseg1['suffix'].replace("'", "''"), 
                                                name2.replace("'", "''"), 
                                                roadseg2['suffix'].replace("'", "''"), 
                                                roadseg1['placeName'], lat, lng))
                                intersections_inserted[intersection_key] = 1

    print "Writing placenames"
    for placename in placenames:
        cursor.execute("insert into placename values (\"%s\");" % placename)

    conn.commit()
    conn.close()
