from tripgraph import TripGraph
from django.conf import settings

# This is expensive to load, and doesn't change, so do it just once per server
graph = TripGraph()
graph.load(settings.GRAPH_FILE)

