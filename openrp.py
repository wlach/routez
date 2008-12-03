#!/usr/bin/python

import BaseHTTPServer, sys, urlparse
from django.conf import settings as DjangoSettings
import mimetypes
from optparse import OptionParser
import os
import pwd
import re
import signal
import simplejson
import time
import datetime
import urllib
import math
import cPickle

import parsedatetime as pdt
import transitfeed
import routezsettings
from routezgraph import *


LOGFILE = '/var/log/openrp.log'
PIDFILE = '/var/run/openrp.pid'


class ResultEncoder(simplejson.JSONEncoder):
  def default(self, obj):
    try:
      iterable = iter(obj)
    except TypeError:
      pass
    else:
      return list(iterable)
    return simplejson.JSONEncoder.default(self, obj)

class ScheduleRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  def __init__(self, request, client_address, socket_server):
    BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, socket_server)

  def do_GET(self):
    scheme, host, path, x, params, fragment = urlparse.urlparse(self.path)
    parsed_params = {}
    for k in params.split('&'):
      k = urllib.unquote(k)
      if '=' in k:
        k, v = k.split('=', 1)
        parsed_params[k] = unicode(v, 'utf8')
      else:
        parsed_params[k] = ''

    if path == '/':
      return self.handle_GET_home()

    m = re.match(r'/json/([a-z]{1,64})', path)
    if m:
      handler_name = 'handle_json_GET_%s' % m.group(1)
      handler = getattr(self, handler_name, None)
      if callable(handler):
        return self.handle_json_wrapper_GET(handler, parsed_params)

    # Restrict allowable file names to prevent relative path attacks etc
    m = re.match(r'\/([a-z0-9_-]{1,64}\.?[a-z0-9_-]{1,64})$', path)
    if m and m.group(1):
      try:
        f, mime_type = self.OpenFile(m.group(1))
        return self.handle_static_file_GET(f, mime_type)
      except IOError, e:
        print "Error: unable to open %s" % m.group(1)
        # Ignore and treat as 404

    m = re.match(r'/([a-z]{1,64})', path)
    if m:
      handler_name = 'handle_GET_%s' % m.group(1)
      handler = getattr(self, handler_name, None)
      if callable(handler):
        return handler(parsed_params)

    return self.handle_GET_default(parsed_params, path)

  def OpenFile(self, filename):
    """Try to open filename in the static files directory of this server.
    Return a tuple (file object, string mime_type) or raise an exception."""
    (mime_type, encoding) = mimetypes.guess_type(filename)
    assert mime_type
    # A crude guess of when we should use binary mode. Without it non-unix
    # platforms may corrupt binary files.
    if mime_type.startswith('text/'):
      mode = 'r'
    else:
      mode = 'rb'
    return open(os.path.join(self.server.file_dir, filename), mode), mime_type

  def handle_GET_home(self):
    schedule = self.server.schedule
    (min_lat, min_lon, max_lat, max_lon) = schedule.GetStopBoundingBox()

    key = self.server.key

    # use django's templating system to send a response
    t = get_template('index.html')
    c = t.render(Context({'min_lat': min_lat, 'min_lon': min_lon, 
                          'max_lat': max_lat, 'max_lon': max_lon, 'key': key}))

    self.send_response(200)
    self.send_header('Content-Type', 'text/html')
    self.send_header('Content-Length', str(len(c)))
    self.end_headers()
    self.wfile.write(c)

  def handle_GET_default(self, parsed_params, path):
    self.send_error(404)

  def handle_static_file_GET(self, fh, mime_type):
    content = fh.read()
    self.send_response(200)
    self.send_header('Content-Type', mime_type)
    self.send_header('Content-Length', str(len(content)))
    self.end_headers()
    self.wfile.write(content)

  def handle_json_wrapper_GET(self, handler, parsed_params):
    """Call handler and output the return value in JSON."""
    result = handler(parsed_params)
    content = ResultEncoder().encode(result)
    self.send_response(200)
    self.send_header('Content-Type', 'text/plain')
    self.send_header('Content-Length', str(len(content)))
    self.end_headers()
    self.wfile.write(content)

  def handle_json_GET_stoplist(self, params):
    matches = []
    for s in self.server.schedule.GetStopList():
      matches.append({ 'id':"gtfs"+s.stop_id, 'name':s.stop_name, 
                       'lat':s.stop_lat, 'lng':s.stop_lon })
    return matches

  def handle_json_GET_routelist(self, params):
    matches = []
    for r in self.server.schedule.GetRouteList():
      matches.append({ 'id':r.route_id, 'shortname':r.route_short_name, 
                       'longname':r.route_long_name } )
    return matches

  def handle_json_GET_routeplan(self, params):
    schedule = self.server.schedule
    graph = self.server.graph

    start_lat = float(params.get('startlat', None))
    start_lng = float(params.get('startlng', None))
    end_lat = float(params.get('endlat', None))
    end_lng = float(params.get('endlng', None))
    time_str = params.get('time', None)

    startstops = schedule.GetNearestStops(start_lat, start_lng, 10)
    endstops = schedule.GetNearestStops(end_lat, end_lng, 10)

    start_time = self.server.calendar.parse(time_str)[0]
    daysecs = time.mktime((start_time[0], start_time[1], start_time[2],
                                  0, 0, 0, 0, 0, 0))
    def human_time(secs, daysecs):
      dt = datetime.datetime.fromtimestamp(secs+daysecs)
      dtstr = dt.strftime("%I:%M%p")
      return dtstr

    trippath = graph.find_path(time.mktime(start_time), start_lat, start_lng, 
                               end_lat, end_lng)

    actions_desc = []
    last_action = None
    for action in trippath.get_actions():
      # order is always: get off (if applicable), board (if applicable), 
      # then move
      if last_action and last_action.route_id != action.route_id:
        if last_action.route_id != -1:
          actions_desc.append({ 'type':'alight', 
                              'lat': graph.tripstops[last_action.dest_id].lat, 
                              'lng': graph.tripstops[last_action.dest_id].lng, 
                              'time':human_time(daysecs, 
                                                last_action.start_time) })
      if not last_action or last_action.route_id != action.route_id:
        if action.route_id >= 0:
          actions_desc.append({ 'type':'board', 'id':action.src_id, 
                                'time':human_time(daysecs, action.start_time), 
                                'route_id':action.route_id })
      actions_desc.append({ 'type':'pass', 'id':action.src_id, 
                            'lat': graph.tripstops[action.src_id].lat, 
                            'lng': graph.tripstops[action.src_id].lng,
                            'dest_id':action.dest_id })
      last_action = action

    # if we had a path at all, append the last getting off action here
    if last_action:
        actions_desc.append({ 'type':'arrive', 
                              'time':human_time(daysecs, 
                                                last_action.end_time) })

    return actions_desc

def StartServerThread(server):
  """Start server in its own thread because KeyboardInterrupt doesn't
  interrupt a socket call in Windows."""
  # Code taken from
  # http://mail.python.org/pipermail/python-list/2003-July/212751.html
  # An alternate approach is shown at
  # http://groups.google.com/group/webpy/msg/9f41fd8430c188dc
  import threading
  th = threading.Thread(target=lambda: server.serve_forever())
  th.setDaemon(1)
  th.start()
  # I don't care about shutting down the server thread cleanly. If you kill
  # python while it is serving a request the browser may get an incomplete
  # reply.

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
  parser.add_option('--feed_filename', '--feed', dest='feed_filename',
                    help='file name of feed to load', default="")
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
  
  if not os.path.isfile(options.feed_filename):
    print "Can't find feed file '%s'" % options.feed_filename
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

  schedule = transitfeed.Schedule(
    problem_reporter=transitfeed.ProblemReporter())
  print "Loading schedule."
  schedule.Load(options.feed_filename)

  print "Loading graph."
  FILE = open(options.graph_filename, 'r')
  graph = cPickle.load(FILE)
  FILE.close()

  server = BaseHTTPServer.HTTPServer(server_address=('', options.port),
                                     RequestHandlerClass=ScheduleRequestHandler)
  server.key = options.key
  server.schedule = schedule
  server.graph = graph
  server.file_dir = options.file_dir
  server.calendar = pdt.Calendar()

  DjangoSettings.configure(TEMPLATE_DIRS=routezsettings.TEMPLATE_DIRS)
  from django.template.loader import get_template
  from django.template import Context

  StartServerThread(server)  # Spawns a thread for server and returns
  print "To view, point your browser at http://%s:%d/" \
      % (server.server_name, server.server_port)

  try:
    while 1:
      time.sleep(0.5)
  except KeyboardInterrupt:
    pass
