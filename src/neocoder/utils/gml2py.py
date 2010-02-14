#!/usr/bin/python

import re
import sys
import xml.sax

# A simple script which turns a gml file into a set of python dictionaries with
# the same set of information, restricted to a bounding box. The goal is to 
# speed up subsequent processing of the same data as well as to distribute 
# the complexity of parsing an XML file from the complexity of generating a 
# of database suitable for geocoding.

class RoadSegment:
    def __init__(self):
        self.coords = []
        self.left = {}
        self.right = {}

class GMLHandler(xml.sax.ContentHandler):
    def __init__(self, min_lat, min_lng, max_lat, max_lng):
        self.min_lat = min_lat
        self.min_lng = min_lng
        self.max_lat = max_lat
        self.max_lng = max_lng

        self.inRoadSegment = False
        self.inRoadLineString = False
        self.curRoadSegment = None
        self.cdata = ""

    def setDocumentLocator(self,loc):
        pass
        
    def startDocument(self):
        pass

    def endDocument(self):
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
            match = re.search('([A-z0-9\']+(?:\ [A-z\']+)*)\ ([A-z]+)(?:\ \ ([A-z-]+))?', self.cdata)
            if match:
                (name, suffix, direction) = (match.group(1), match.group(2), match.group(3))
                hash['name'] = name
                hash['suffix'] = suffix
                hash['direction'] = direction

        if name=='nrn:RoadSegment':
            self.inRoadSegment = False
            inRange = False
            for (lat, lng) in self.curRoadSegment.coords:
                if lat > self.min_lat and lat < self.max_lat and \
                        lng > self.min_lng and lng < self.max_lng:
                    inRange = True
            if inRange:
                print { "left": self.curRoadSegment.left, 
                        "right": self.curRoadSegment.right, 
                        "coords": self.curRoadSegment.coords }

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
        elif name=="nrn:right_OfficialPlaceName":
            self.curRoadSegment.right['placeName'] = self.cdata
        elif name=='gml:coordinates' and self.inRoadLineString:
            self.curRoadSegment.length = 0.0
            for coordtuple_str in self.cdata.split(" "):
                coordtuple = coordtuple_str.split(",")
                self.curRoadSegment.coords.append((float(coordtuple[1]), float(coordtuple[0])))

    def characters(self, chars):
        self.cdata += chars

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print "Usage: %s <gml file> <min lat> <min lng> <max lat> <max lng>" % \
            sys.argv[0]
        exit(1)

    xml.sax.parse(sys.argv[1], GMLHandler(float(sys.argv[2]), 
                                          float(sys.argv[3]),
                                          float(sys.argv[4]),
                                          float(sys.argv[5])))

