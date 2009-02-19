from django.conf.urls.defaults import *
from django.conf import settings
import os

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'routez.travel.views.main_page'),
    (r'^iphone$', 'routez.travel.views.iphone'),
    (r'^about$', 'routez.travel.views.about'),
    (r'^privacy$', 'routez.travel.views.privacy'),
    (r'^json/routeplan$', 'routez.travel.views.routeplan'),

    # Uncomment this for admin:
    #(r'^admin/(.*)', admin.site.root),
)

# Only serve media from Django in debug mode.  In non-debug mode, the regular
# web server should do this.
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 
            'django.views.static.serve', 
            {'document_root': os.path.join(settings.PROJECT_PATH, 'site_media'), 
                'show_indexes': True}),
    )

