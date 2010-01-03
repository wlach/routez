import cPickle as pickle
import math
import parser
import re
import string

from routez.geocoder.models import Road, Intersection
import routez.geocoder.parser as geoparser

latlngre = re.compile("^(-?[0-9]+(\.[0-9]+)?)\ *,\ *(-?[0-9]+(\.[0-9]+)?)$")

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
            if seg_travel > 0.0 and \
                    distance_travelled + seg_travel >= distance_to_travel:
                seg_pct = (distance_to_travel - distance_travelled) / \
                    seg_travel                   
                new_lat = prevcoord[0] + ((coord[0] - prevcoord[0]) * seg_pct)
                new_lng = prevcoord[1] + ((coord[1] - prevcoord[1]) * seg_pct)
                return (new_lat, new_lng)
            distance_travelled += seg_travel

        prevcoord = coord
    
    return (prevcoord[0], prevcoord[1])


def get_location(location_str):
    match = latlngre.match(location_str)
    if match:
        return (float(match.group(1)), float(match.group(3)))

    streets = geoparser.parse_address(location_str)
    if len(streets) == 1:
        r = Road.objects.filter(name__iexact=streets[0].name)
        if streets[0].suffix:
            r = r.filter(suffix=streets[0].suffix)
        if streets[0].number:
            # the actual geocoder doesn't understand "a", so just grab
            # the numeric portion of any street
            r = r.filter(firstHouseNumber__lte=streets[0].number, 
                         lastHouseNumber__gte=streets[0].number)
        if len(r) > 0:
            coords = pickle.loads(str(r[0].coords))
            percent = 0.0
            if streets[0].number and r[0].lastHouseNumber > r[0].firstHouseNumber:
                number = float(streets[0].number)
                percent = float(number - r[0].firstHouseNumber) / \
                    float(r[0].lastHouseNumber - r[0].firstHouseNumber)
            return __get_interpolated_latlng(coords, r[0].length, percent)
        else:
            return None

    elif len(streets) == 2:
        if streets[0].name.lower() > streets[1].name.lower():
            streets[1], streets[0] = streets[0], streets[1]
        r = Intersection.objects.filter(name1__iexact=streets[0].name, 
                                        name2__iexact=streets[1].name)
        if streets[0].suffix:
            r.filter(suffix1=streets[0].suffix)
        if streets[1].suffix:
            r.filter(suffix2=streets[1].suffix)
        if len(r) > 0:
            return (r[0].lat, r[0].lng)
        return None

    else:
        return None

