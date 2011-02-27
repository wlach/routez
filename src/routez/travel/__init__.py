from libroutez.tripgraph import TripGraph
from django.conf import settings

# The tripgraph is expensive to load, and don't change, so do it just once per server
graph = TripGraph()
graph.load(settings.GRAPH_FILE)
