import cPickle as pickle
import math
import parser
import re
import string

from routez.geocoder.models import Road, Intersection
import routez.geocoder.parser as geoparser

__suffix_mapping = { "ave": "avenue",
                   "av": "avenue",
                   "aven": "avenue",
                   "avenu": "avenue",
                   "avn": "avenue",
                   "avnue": "avenue",
                   "st": "street",
                   "streets": "street",
                   "strt": "street"
                   }                   

def __latlng_dist(src_lat, src_lng, dest_lat, dest_lng):

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

def __get_interpolated_latlng(coords, length, pct):
    distance_to_travel = pct * length
    distance_travelled = 0
    prevcoord = None
    for coord in coords:
        if prevcoord:
            seg_travel = __latlng_dist(prevcoord[0], prevcoord[1],
                                     coord[0], coord[1])
            if distance_travelled + seg_travel >= distance_to_travel:
                seg_pct = (distance_to_travel - distance_travelled) / \
                    seg_travel
                    
                new_lat = prevcoord[0] + ((coord[0] - prevcoord[0]) * seg_pct)
                new_lng = prevcoord[1] + ((coord[1] - prevcoord[1]) * seg_pct)
                return (new_lat, new_lng)
            distance_travelled += seg_travel

        prevcoord = coord

def __normalize_suffix(suffix):
    tmpsuffix = string.lower(suffix)

    if __suffix_mapping.get(tmpsuffix):
        return __suffix_mapping[tmpsuffix]

    return tmpsuffix

def get_location(location_str):
    myre = re.compile("\W*and|&\W*", re.I)
    streets = myre.split(location_str)
    if len(streets) == 1:
        addr = geoparser.streetAddress.parseString(location_str)

        r = Road.objects.filter(name__iexact=addr.street.name)        
        if addr.street.type:
            r = r.filter(suffix=__normalize_suffix(addr.street.type))
        if addr.street.number:
            r = r.filter(firstHouseNumber__lte=addr.street.number, 
                         lastHouseNumber__gte=addr.street.number)

        if len(r) > 0:
            coords = pickle.loads(str(r[0].coords))
            percent = float(float(addr.number) - r[0].firstHouseNumber) / \
                float(r[0].lastHouseNumber - r[0].firstHouseNumber)
            return __get_interpolated_latlng(coords, r[0].length, percent)
        else:
            return None
                                               
    elif len(streets) == 2:
        addr1 = geoparser.streetAddress.parseString(streets[0])
        addr2 = geoparser.streetAddress.parseString(streets[1])
        if addr1.street.name > addr2.street.name:
            addr2, addr1 = addr1, addr2
        r = Intersection.objects.filter(name1__iexact=addr1.street.name, 
                                        name2__iexact=addr2.street.name)
        if addr1.street.type:
            r.filter(suffix1=__normalize_suffix(addr1.street.type))
        if addr2.street.type:
            r.filter(suffix2=__normalize_suffix(addr2.street.type))            
        if len(r) > 0:
            return (r[0].lat, r[0].lng)
        return None

    else:
        return None

