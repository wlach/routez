#!/usr/bin/python

import os
from optparse import OptionParser
import logging

# Manually import django
sys.path.append(os.path.join(os.getcwd(), os.pardir))
os.environ['DJANGO_SETTINGS_MODULE'] = "routez.settings"

from routez.travel.models import Route

usage = "usage: %prog [options] <base path> <generated path>"
parser = OptionParser(usage)
parser.add_option("-v", action="store_true", dest="verbose", 
                  help='Verbose (turn on debugging messages)')
(options, args) = parser.parse_args()

if len(args) < 2:
    parser.error("incorrect number of arguments")
    exit(1)

logger = logging.getLogger("creategraph")
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(ch)
if options.verbose:
    logger.setLevel(logging.DEBUG)

routes = Route.objects.all()

marker_basepath = args[0]
marker_genpath = args[1]

os.system("mkdir -p " + marker_genpath)

for route in routes:
    marker_basename = None
    if route.type == 3:
        marker_basename = "marker_bus"
    elif route.type == 4:
        marker_basename = "marker_ferry"

    if marker_basename:
        logger.debug("Creating marker for %s" % route.short_name)
        os.system('convert %s -weight Bold -annotate +34+14 %s %s' %
                   (marker_basepath + marker_basename + ".png",
                   route.short_name, 
                   marker_genpath + marker_basename + route.short_name + \
                       ".png"))
