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
        ('\ *<DND>\ *', ''),
        ('\ *<NB>\ *', ''),
        ('\ *<INBOUND>\ *', ''), 
        ('\ *<OUTBOUND>\ *', ''), 
        ('<TO HFX>', ''), 
        ('<TO DART>', ''), 
        (' <GOTTINGE$', ''), 
        ('\ <([^>]|\ )+>$', ''), 
        (' TO\ [^<]+$', ''),
        (' <[^>]+$', ''), # ending with <...
        ]
    for subst in place_substitutions1:
        stopname = re.sub(subst[0], subst[1], stopname)

    # replace '... <...> CIVIC XX' w/ 'Near XX ...'
    m = re.match('([^<]*) .* CIVIC ([0-9]+)', stopname)
    if m:
        return "Near %s %s" % (m.group(2), string.capwords(m.group(1)))

    boring_street_suffixes = [ "AVE", "BLVD", "CR", "CRT", "CT", "DR", "GATE", "PKWY", "RD", "ROW", 
                               "ST" ]
    boring_street_regex = '(?:' + '|'.join(boring_street_suffixes) + ')'
    def strip_boring_street_suffix(text):
        m = re.match('(.*) ' + boring_street_regex, text)
        if m:
            return m.group(1)

        return text

    street_suffixes = boring_street_suffixes + [ "HWY", "TERR" ]
    street_regex = '(?:' + '|'.join(street_suffixes) + ')'

    m = re.match('^([^<]* ' + street_regex + ').*> ([^>]* ' + street_regex + ')$', stopname)
    if m:
        return "%s & %s" % (string.capwords(strip_boring_street_suffix(m.group(1))), 
                            string.capwords(strip_boring_street_suffix(m.group(2))))
    else:
        # if that didn't match, check to see if we need to use a more vague "near"
        # description
        m = re.match('^([^<]*) .*> ([^>]*)$', stopname)
        if m:
            return "%s near %s" % (string.capwords(m.group(1)), string.capwords(m.group(2)))

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
    "bjhs-90",
    "cp1-90",
    "ecrl-90",
    "ecs-90",
    "fv01-90",
    "hwst-90",
    "s14-90",
    "sp14-90",
    "sp53-90",
    "sp58-90",
    "sp6-90",
    "sp65-90",
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
