#!/usr/bin/python

import math
import os
import sqlite3
import string
import struct
import sys
import xml.sax

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

    def insert_into_db(self, side, cursor):
        even = 0
        if (side['firstNumber'] % 2 == 0):
            even = 1

        coords_buf = struct.pack("l", len(self.coords),)
        for coord in self.coords:
            coords_buf += struct.pack("ff", coord[0], coord[1],)
        
        cursor.execute("insert into road values " \
        "('%s', '%s', '%s', '%s', '%s', '%s', ?);" % (side['name'], side['suffix'], 
                                                      side['firstNumber'], side['lastNumber'],
                                                      even, self.length),
                                                      [sqlite3.Binary(coords_buf)])
      
class GMLHandler(xml.sax.ContentHandler):
    def __init__(self, min_lat, min_lng, max_lat, max_lng, conn):
        self.min_lat = min_lat
        self.min_lng = min_lng
        self.max_lat = max_lat
        self.max_lng = max_lng
        self.placenames = set()
        self.nodes = {}

        self.inRoadSegment = False
        self.inRoadLineString = False
        self.curRoadSegment = None
        self.cdata = ""
        
    def setDocumentLocator(self,loc):
        pass
        
    def startDocument(self):
        pass

    def endDocument(self):
        cursor = conn.cursor()

        intersections_inserted = {}
        for latlng in self.nodes.keys():
            roadsegs = self.nodes[latlng]["roadsegs"]
            
            if len(roadsegs) > 1:
                (lat, lng) = self.nodes[latlng]["latlng"]
                
                for i in range (0, len(roadsegs)):
                    for j in range (0, len(roadsegs)):
                        if i != j:
                            roadseg1 = roadsegs[i].right
                            roadseg2 = roadsegs[j].right
                            name1 = roadseg1['name']
                            name2 = roadseg2['name']
                            if name1 > name2:
                                name1, name2 = name2, name1
                                if name1 and name2 and name1 != name2:
                                    
                                    intersection_key = name1+roadseg1['suffix']+","+name2+roadseg2['suffix']
                                    if not intersections_inserted.get(intersection_key):
                                        # FIXME: this will eventually insert into an intersections table
                                        pass
                                        intersections_inserted[intersection_key] = 1

        print "Writing placenames"
        for placename in self.placenames:
            cursor.execute("insert into placename values (\"%s\");" % placename)
        
    def startElement(self, name, attrs):
        if name=='nrn:RoadSegment':
            self.inRoadSegment = True
            self.curRoadSegment = RoadSegment()
        elif name=='gml:lineStringProperty' and self.inRoadSegment:
            self.inRoadLineString = True
        self.cdata = ""

    def endElement(self,name):
        def setNameAndSuffix(hash):
            hash['name'] = string.join(self.cdata.split(" ")[0:-1], " ")
            hash['suffix'] = string.lower(self.cdata.split(" ")[-1])

        if name=='nrn:RoadSegment':
            self.inRoadSegment = False
            inRange = False
            for (lat, lng) in self.curRoadSegment.coords:
                if lat > self.min_lat and lat < self.max_lat and \
                        lng > self.min_lng and lng < self.max_lng:
                    inRange = True
            if inRange:
                cursor = conn.cursor()
                if self.curRoadSegment.right['name'] != "Unknown":
                    if self.curRoadSegment.right['firstNumber'] > 0 and \
                            self.curRoadSegment.right['lastNumber'] > 0:
                        self.curRoadSegment.insert_into_db(self.curRoadSegment.right, cursor)
                if self.curRoadSegment.left['name'] != "Unknown":
                    if self.curRoadSegment.left['firstNumber'] > 0 and \
                            self.curRoadSegment.left['lastNumber'] > 0:
                        self.curRoadSegment.insert_into_db(self.curRoadSegment.left, cursor)

        elif name == 'gml:lineStringProperty':
            self.inRoadLineString = False
        # left side
        elif name=='nrn:left_OfficialStreetNameConcat':
            setNameAndSuffix(self.curRoadSegment.left)
        elif name=="nrn:left_FirstHouseNumber":
            self.curRoadSegment.left['firstNumber'] = int(self.cdata)
        elif name=="nrn:left_LastHouseNumber":
            self.curRoadSegment.left['lastNumber'] = int(self.cdata)
        # right side
        elif name=='nrn:right_OfficialStreetNameConcat':
            setNameAndSuffix(self.curRoadSegment.right)
        elif name=="nrn:right_FirstHouseNumber":
            self.curRoadSegment.right['firstNumber'] = int(self.cdata)
        elif name=="nrn:right_LastHouseNumber":
            self.curRoadSegment.right['lastNumber'] = int(self.cdata)
        elif name=="nrn:left_OfficialPlaceName":
            self.curRoadSegment.left['placeName'] = self.cdata
            self.placenames.add(string.lower(self.cdata))
        elif name=="nrn:right_OfficialPlaceName":
            self.curRoadSegment.right['placeName'] = self.cdata
            self.placenames.add(string.lower(self.cdata))
        elif name=='gml:coordinates' and self.inRoadLineString:
            prevcoord = None
            self.curRoadSegment.length = 0.0
            for coordtuple_str in self.cdata.split(" "):
                coordtuple = coordtuple_str.split(",")
                (lng, lat) = (float(coordtuple[0]), float(coordtuple[1]))
                # updating intersection db (only if lat,lng in range of
                # interest!)
                if lat > self.min_lat and lat < self.max_lat and \
                        lng > self.min_lng and lng < self.max_lng:
                    inRange = True
                    key = str(round(lat,3))+","+str(round(lng,3))
                    if not self.nodes.get(key):
                        self.nodes[key] = { "latlng": (lat, lng),
                                            "roadsegs": [] }
                    self.nodes[key]["roadsegs"].append(self.curRoadSegment)
                # updating road db
                self.curRoadSegment.coords.append((lat, lng))
                if prevcoord:
                    self.curRoadSegment.length += latlng_dist(lat, lng, 
                                                              prevcoord[0], 
                                                              prevcoord[1])
                prevcoord = (lat, lng)

    def characters(self, chars):
        self.cdata += chars

if __name__ == '__main__':
    if len(sys.argv) < 7:
        print "Usage: %s <gml file> <min lat> <min lng> <max lat> <max lng> <sqlite db>" % \
            sys.argv[0]
        exit(1)

    conn = sqlite3.connect(sys.argv[6])
    cursor = conn.cursor()
    cursor.execute("create table placename (name text)")
    cursor.execute("create table road (name text, suffix text, firstHouseNumber integer, "
                   "lastHouseNumber integer, numberingTypeEven boolean, length real, coords blob)")
    conn.commit()

    print "Parsing geodb and writing road segments"
    xml.sax.parse(sys.argv[1], GMLHandler(float(sys.argv[2]), 
                                          float(sys.argv[3]),
                                          float(sys.argv[4]),
                                          float(sys.argv[5]), conn))
    conn.commit()
    conn.close()
