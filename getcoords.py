#!/usr/bin/python

import os
import sys
import string
    
# Manually import django
sys.path.append(os.path.join(os.getcwd(), os.pardir))
os.environ['DJANGO_SETTINGS_MODULE'] = "settings"

import routez.geocoder.parser as geoparser
import routez.geocoder.geocoder as geocoder

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: %s: <name>"
        exit(1)

    name = string.join(sys.argv[1:], " ")
    print "looking up %s" % name
    latlng = geocoder.get_location(name)
    if latlng:
        print "latlng: %s,%s" % (latlng[0], latlng[1])
    else:
        print "No location found"
