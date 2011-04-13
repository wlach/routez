from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.conf import settings

from routez.travel.models import Map

def index(request):
    if request.META.get('HTTP_USER_AGENT') and request.META['HTTP_USER_AGENT'].find("iPhone") > 0:
        return iphone(request)

    m = Map.objects.get(id=1)
    return render_to_response('index.html', 
        {'min_lat': m.min_lat, 'min_lon': m.min_lng, 
         'max_lat': m.max_lat, 'max_lon': m.max_lng, 
         'key': settings.CMAPS_API_KEY,
         'style_id': settings.CMAPS_STYLE_ID,
         'analytics_key': settings.ANALYTICS_KEY })

def index_iphone(request):
    m = Map.objects.get(id=1)
    return render_to_response('iphone.html', 
        {'min_lat': m.min_lat, 'min_lon': m.min_lng, 
         'max_lat': m.max_lat, 'max_lon': m.max_lng, 
         'key': settings.CMAPS_API_KEY,
         'analytics_key': settings.ANALYTICS_KEY })

def about(request):
    return render_to_response('about.html', 
                              { 'analytics_key': settings.ANALYTICS_KEY })

def help(request):
    return render_to_response('help.html', 
                              { 'analytics_key': settings.ANALYTICS_KEY })

def privacy(request):
    return render_to_response('privacy.html',
                              { 'analytics_key': settings.ANALYTICS_KEY })
