from libroutez.tripgraph import TripGraph
from neocoder import GeoCoder
from django.conf import settings

# These are expensive to load, and don't change, so do it just once per server
graph = TripGraph()
graph.load(settings.GRAPH_FILE)

geocoder = GeoCoder(settings.GEOCODER_FILE)
