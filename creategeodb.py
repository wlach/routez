#!/usr/bin/python

import os
import sys
import math
import xml.sax
import cPickle as pickle
import string

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

    def dumpsqls(self, side):
        even = 0
        if (side['firstNumber'] % 2 == 0):
            even = 1

        print "insert into geocoder_road (name,suffix,coords," \
        "firstHouseNumber,lastHouseNumber,numberingTypeEven,length) values " \
        "('%s', '%s', '%s', '%s', '%s', '%s', '%s');" % (
            side['name'], 
            side['suffix'], 
            pickle.dumps(self.coords),
            side['firstNumber'],
            side['lastNumber'],
            even,
            self.length)

class GMLHandler(xml.sax.ContentHandler):
    def __init__(self, min_lat, min_lng, max_lat, max_lng):
        self.min_lat = min_lat
        self.min_lng = min_lng
        self.max_lat = max_lat
        self.max_lng = max_lng
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
        for latlng in self.nodes.keys():
            roadsegs = self.nodes[latlng]
            
            if len(roadsegs) > 1:
                (lat, lng) = latlng.split(",")
                names_inserted = {}
                for i in range (1, len(roadsegs)):
                    roadseg1 = roadsegs[(i-1)].right
                    roadseg2 = roadsegs[i].right
                    name1 = roadseg1['name']
                    name2 = roadseg2['name']
                    if name1 > name2:
                        name1, name2 = name2, name1
                    if name1 and roadseg2['name'] and name1 != name2:
                        if not names_inserted.get(name1) or \
                                not names_inserted.get(name2):
                            print "insert into geocoder_intersection " \
                                "(name1, suffix1, name2, suffix2, lat, " \
                                "lng) values ('%s', '%s', '%s', '%s', '%s', " \
                                "'%s');" %  (name1, roadseg1['suffix'], 
                                             name2, roadseg2['suffix'], lat, lng)
                                
                            names_inserted[name1] = 1
                            names_inserted[name2] = 1
        pass
        
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
                if self.curRoadSegment.right['name'] != "Unknown":
                    if self.curRoadSegment.left['firstNumber'] > 0 and \
                            self.curRoadSegment.left['lastNumber'] > 0:
                        self.curRoadSegment.dumpsqls(self.curRoadSegment.left)
                    if self.curRoadSegment.right['firstNumber'] > 0 and \
                            self.curRoadSegment.right['lastNumber'] > 0:
                        self.curRoadSegment.dumpsqls(self.curRoadSegment.right)
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
                    key = str(lat)+","+str(lng)
                    if not self.nodes.get(key):
                        self.nodes[key] = []
                    self.nodes[key].append(self.curRoadSegment)
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
    if len(sys.argv) < 6:
        print "Usage: %s: <gml file> <min lat> <min lng> <max lat> <max lng>" \
            % sys.argv[0]
        exit(1)

    print "BEGIN;"
    xml.sax.parse(sys.argv[1], GMLHandler(float(sys.argv[2]), 
                                          float(sys.argv[3]),
                                          float(sys.argv[4]),
                                          float(sys.argv[5])))
    print "COMMIT;"
