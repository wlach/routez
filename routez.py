#!/usr/bin/python

from optparse import OptionParser
import pwd
import re
import signal
import simplejson
import time
import datetime
import urllib
import math

import os, time, threading
from railways import *

import parsedatetime.parsedatetime as pdt

from django.conf import settings as DjangoSettings
import settings
os.environ['DJANGO_SETTINGS_MODULE'] = "settings"

from travel.models import Route, Stop, Map
from tripgraph import *


LOGFILE = '/var/log/openrp.log'
PIDFILE = '/var/run/openrp.pid'

__doc__ = """\
This example shows how to do implement a Comet service  with Railways. 
"""

class Main(Component):
  def __init__(self):
    Component.__init__(self)

  @on(GET="lib/{path:any}")
  def lib(self, request, path):
    """Serves the files located in the `Library` grand parent directory."""
    # This is really only useful when running standalone, as with normal
    # setups, this data should be served by a more poweful web server, with
    # caching and load balancing.
    return request.respondFile(self.file_dir + "/" + path)

  # Returns the hours and minutes of the given Unix timestamp, formatted
  # nicely.  If the timestamp is not given, defaults to the current time.
  @staticmethod
  def human_time(secs = None):
    format_str = "%I:%M %p"
    dtstr = ""
    if secs is None:
      dtstr = time.strftime(format_str).lower()
    else:
      dt = datetime.datetime.fromtimestamp(secs)
      dtstr = dt.strftime(format_str).lower()
    # Remove leading zero. %_I would do almost the same thing on Linux, but is
    # non-standard and only works because Python happens to use glibc's impl.
    if dtstr[0] == '0':
        dtstr = dtstr[1:]
    return dtstr

  @on(GET="/")
  def main(self, request):
    # use django's templating system to send a response
    m = Map.objects.get(id=1)
    t = get_template('index.html')
    now_str = Main.human_time()
    c = t.render(Context({'min_lat': m.min_lat, 'min_lon': m.min_lng, 
                          'max_lat': m.max_lat, 'max_lon': m.max_lng, 
                          'key': self.key, 'now': " " + now_str}))

    return request.respond(c, contentType="text/html")
  
  @on(GET="/json/stoplist")
  def get_stoplist(self, request):
    matches = []
    for s in Stop.objects.all():
      matches.append({ 'id':"gtfs"+s.stop_id, 'name':s.name, 
                       'lat':s.lat, 'lng':s.lng })
    return request.respond(asJSON(matches))

  @on(GET="/json/routelist")
  def get_routelist(self, request):
    matches = []
    for r in Route.objects.all():
      matches.append({ 'id':r.route_id, 'shortname':r.short_name, 
                       'longname':r.long_name } )
    return request.respond(asJSON(matches))

  @on(GET="/json/routeplan")
  def get_routeplan(self, request):
    start_lat = float(request.get('startlat'))
    start_lng = float(request.get('startlng'))
    end_lat = float(request.get('endlat'))
    end_lng = float(request.get('endlng'))
    time_str = request.get('time') or ""

    start_time = self.calendar.parse(time_str)[0]
    daysecs = time.mktime((start_time[0], start_time[1], start_time[2],
                                  0, 0, 0, 0, 0, 0))
    now = datetime.datetime.fromtimestamp(time.mktime(start_time))
    today_secs = (now.hour * 60 * 60) + (now.minute * 60) + (now.second)
    print "weekday: %s" % now.weekday()
    service_period = 'weekday'
    if now.weekday() == 5:
      service_period = 'saturday'
    elif now.weekday() == 6:
      service_period = 'sunday'

    trippath = self.graph.find_path(today_secs, service_period, start_lat, start_lng, 
                               end_lat, end_lng, None)

    actions_desc = []
    last_action = None
    for action in trippath.get_actions():
      # order is always: get off (if applicable), board (if applicable), 
      # then move
      if last_action and last_action.route_id != action.route_id:
        if last_action.route_id != -1:
          ts = self.graph.get_tripstop(last_action.dest_id)
          action_time = Main.human_time(daysecs + last_action.start_time)
          actions_desc.append({ 'type':'alight', 
                              'lat': ts.lat, 
                              'lng': ts.lng, 
                              'time': action_time })
      if not last_action or last_action.route_id != action.route_id:
        if action.route_id >= 0:
          action_time = Main.human_time(daysecs + action.start_time)
          actions_desc.append({ 'type':'board', 'id':action.src_id, 
                                'time': action_time,
                                'route_id':action.route_id })
      ts = self.graph.get_tripstop(action.src_id)
      actions_desc.append({ 'type':'pass', 'id':action.src_id, 
                            'lat': ts.lat, 
                            'lng': ts.lng,
                            'dest_id':action.dest_id })
      last_action = action

    # if we had a path at all, append the last getting off action here
    if last_action:
        action_time = Main.human_time(daysecs + last_action.end_time)
        actions_desc.append({ 'type': 'arrive', 
                              'time': action_time })

    return request.respond(asJSON(actions_desc))

def FindDefaultFileDir():
  """Return the path of the directory containing the static files. By default
  the directory is called 'web_content', just off the current working directory."""
  # For all other distributions 'files' is in the gtfsscheduleviewer
  # directory. 
  return os.path.join(os.getcwd(), 'web_content')

class Log:
    """file like for writes with auto flush after each write
    to ensure that everything is logged, even during an
    unexpected exit."""
    def __init__(self, f):
        self.f = f
    def write(self, s):
        self.f.write(s)
        self.f.flush()

def daemonize():
  # all of this gratuitously stolen from http://homepage.hispeed.ch/py430/python/daemon.py

  # do the UNIX double-fork magic, see Stevens' "Advanced
  # Programming in the UNIX Environment" for details (ISBN 0201563177)
  try:
    pid = os.fork()
    if pid > 0:
      # exit first parent
      sys.exit(0)
  except OSError, e:
    print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
    sys.exit(1)

    # decouple from parent environment
    os.chdir("/") # don't prevent unmounting....
    os.setsid()
    os.umask(0)

    # do second fork
  try:
    pid = os.fork()
    if pid > 0:
      # exit from second parent, print eventual PID before
      #print "Daemon PID %d" % pid
      open(PIDFILE,'w').write("%d"%pid)
      sys.exit(0)
  except OSError, e:
    print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
    sys.exit(1)

  # redirect outputs to a logfile
  sys.stdout = sys.stderr = Log(open(LOGFILE, 'a+'))

  # ensure the that the daemon runs a normal user
  pw = pwd.getpwnam("openrp")
  os.setegid(pw.pw_gid)
  os.seteuid(pw.pw_uid)
  # forget handling the exception where openrp doesn't exist, we check for 
  # that when the program starts. if said user disappears between then
  # and now, whatevs...

if __name__ == '__main__':
  parser = OptionParser()
  parser.add_option('--graph_filename', '--graph', dest='graph_filename',
                    help='file name of graph to load', default="")
  parser.add_option('--key', dest='key',
                    help='Google Maps API key or the name '
                    'of a text file that contains an API key')
  parser.add_option('--port', dest='port', type='int',
                    help='port on which to listen')
  parser.add_option("-d", action="store_true", dest="daemonize",
                    help="Daemonize process after startup")
  parser.add_option('--file_dir', dest='file_dir',
                    help='directory containing static files')

  parser.set_defaults(port=8765, file_dir=FindDefaultFileDir())

  (options, args) = parser.parse_args()

  if not os.path.isfile(os.path.join(options.file_dir, 'index.html')):
    print "Can't find index.html with --file_dir=%s" % options.file_dir
    exit(1)
  
  if not os.path.isfile(options.graph_filename):
    print "Can't find graph file '%s'" % options.graph_filename
    exit(1)

  if options.daemonize:
    if not os.getuid() == 0:
      print "uid must be zero for daemonization!"
      exit(1)
    else:
      try:
        pwd.getpwnam("openrp")
      except KeyError:
        print "No openrp user found!"
        exit(1)
      daemonize()

  if options.key and os.path.isfile(options.key):
    options.key = open(options.key).read().strip()

  print "Loading graph."
  graph = TripGraph()
  graph.load(options.graph_filename)

  main = Main()
  main.key = options.key
  main.graph = graph
  main.file_dir = options.file_dir
  main.calendar = pdt.Calendar()

  from django.template.loader import get_template
  from django.template import Context

  app = Application(main)
  name = os.path.splitext(os.path.basename(__file__))[0]
  run(app=app, name=name, method=STANDALONE, port=options.port, withReactor=True)
  REACTOR.debugMode = True
