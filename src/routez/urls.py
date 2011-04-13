from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import os

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'routez.webapp.views.index'),
    (r'^iphone$', 'routez.webapp.views.index_iphone'),
    (r'^about$', 'routez.webapp.views.about'),
    (r'^help$', 'routez.webapp.views.help'),
    (r'^privacy$', 'routez.webapp.views.privacy'),
    (r'^json/routeplan$', 'routez.travel.views.routeplan'),
    (r'^api/v1/stop/(\d+)/upcoming_stoptimes$', 
     'routez.stops.views.stoptimes_for_stop'),
    (r'^api/v1/place/([^/]+)/upcoming_stoptimes$',
     'routez.stops.views.stoptimes_in_range')

    # Uncomment this for admin:
    #(r'^admin/(.*)', admin.site.root),
)

# Only serve media from Django in debug mode.  In non-debug mode, the regular
# web server should do this.
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
