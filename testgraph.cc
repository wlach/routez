#include "tripgraph.h"

int main(int argc, char *argv[])
{
    TripGraph g;
    g.load("mygraph.routez");

    g.find_path(46167, "weekday", 44.657304, -63.591096, 
                44.7321379, -63.657304, NULL);
}
