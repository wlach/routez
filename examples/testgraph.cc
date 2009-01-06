#include "tripgraph.h"

using namespace boost;
using namespace std;


void print_actions(shared_ptr<TripAction> &action)
{
    shared_ptr<TripAction> parent(action->parent);
    if (parent)
        print_actions(parent);

    printf("%s->%s; route: %d; start time: %.2f; end time: %.2f\n", 
           action->src_id.c_str(), action->dest_id.c_str(), action->route_id, 
           action->start_time, action->end_time);
}


int main(int argc, char *argv[])
{
    if (argc < 8)
    {
        printf("Usage: %s <graph file> <src lat> <src lng> <dest lat> "
               "<dest lng> <start time (seconds since day start)> "
               "<service period (e.g. 'weekday')>\n", argv[0]);
        exit(1);
    }

    float src_lat = atof(argv[2]);
    float src_lng = atof(argv[3]);
    float dest_lat = atof(argv[4]);
    float dest_lng = atof(argv[5]);
    int start_time = atoi(argv[6]);
    string service_period = argv[7];

    TripGraph g;
    g.load(argv[1]);

    TripPath p = g.find_path(start_time, service_period, false, src_lat, 
                             src_lng, dest_lat, dest_lng);

    print_actions(p.last_action);

    return 0;
}
