#!/usr/bin/python

# This script is intended to make the following modifications to the feed provided
# by Halifax Metro Transit, Nova Scotia:
# 1. Update the stop names to be more reader-friendly
# 2. Updating headsigns to be more reader friendly (stripping the number, 
# using mixed case)
# 2. Removes a series of special routes that are not open to the general 
# public from the feed

from optparse import OptionParser
import re
import string
import transitfeed

def revise_stopname(stopname):
    # we ALWAYS want to apply these
    place_substitutions1 = [
        ('\[[^\[\]]+\] ?', ''),
        ('and *$', ''), # trailing ands...
        ]
    for subst in place_substitutions1:
        stopname = re.sub(subst[0], subst[1], stopname)

    # replace '... <...> CIVIC XX' w/ 'Near XX ...'
    m = re.match('(.+) (in front of|before|after|opposite|before and opposite) civic address ([0-9]+)', stopname)
    if m:
        return "Near %s %s" % (m.group(3), string.capwords(m.group(1)))

    boring_street_suffixes = [ "Ave", "Blvd", "Cr", "Crt", "Ct", "Dr", "Gate", "Pkwy", "Rd", "Row", 
                               "St" ]
    boring_street_regex = '(?:' + '|'.join(boring_street_suffixes) + ')'
    def strip_boring_street_suffix(text):
        m = re.match('(.*) ' + boring_street_regex, text)
        if m:
            return m.group(1)

        return text

    street_suffixes = boring_street_suffixes + [ "Hwy", "Terr" ]
    street_regex = '(?:' + '|'.join(street_suffixes) + ')'

    m = re.match('^(.*) ' + street_regex + ' (after|before|opposite|in front of) (.*) ' + street_regex + '$', stopname)
    if m:
        return "%s & %s" % (string.capwords(strip_boring_street_suffix(m.group(1))), 
                            string.capwords(strip_boring_street_suffix(m.group(3))))

    return string.capwords(stopname)

def update_headsign(headsign):
    headsign_words = headsign.split(" ")
    headsign_words_new = []
    first = True
    for word in headsign_words:
        if first and re.match('[0-9]+', word):
            pass
        elif word=='TO' or word=='VIA':
            headsign_words_new.append(word.lower())
        else:
            headsign_words_new.append(word.capitalize())
    return ' '.join(headsign_words_new)
            

usage = "usage: %prog <input gtfs feed> <output gtfs feed>"
parser = OptionParser(usage)
(options, args) = parser.parse_args()

if len(args) < 2:
    parser.error("incorrect number of arguments")
    exit(1)

print "Loading schedule"
schedule = transitfeed.Schedule(
    problem_reporter=transitfeed.ProblemReporter())
schedule.Load(args[0])

print "Updating stop names"
for stop in schedule.GetStopList():
    stop.stop_name = revise_stopname(stop.stop_name)

print "Clearing routes not usable by general public"
special_routes = [
    "bjhs-104",
    "bjhs-111",
    "cp1-104",
    "cp1-111",
    "ecrl-104",
    "ecrl-111",
    "ecs-104",
    "ecs-111",
    "fv01-104",
    "fv01-111",
    "hwst-104",
    "hwst-111",
    "s14-104",
    "s14-111",
    "sp14-104",
    "sp14-111",
    "sp53-104",
    "sp53-111",
    "sp58-104",
    "sp58-111",
    "sp6-104",
    "sp6-111",
    "sp65-104",
    "sp65-111"
]
for special_route in special_routes:
    trip_ids_to_delete = []
    for trip in schedule.GetTripList():
        if trip.route_id == special_route:
            trip.ClearStopTimes()
            trip_ids_to_delete.append(trip.trip_id)
    for trip_id_to_delete in trip_ids_to_delete:
        del schedule.trips[trip_id_to_delete]
    del schedule.routes[special_route]

print "Updating headsigns"
for trip in schedule.GetTripList():
    trip.trip_headsign = update_headsign(trip.trip_headsign)

print "Saving feed"
schedule.WriteGoogleTransitFeed(args[1])
