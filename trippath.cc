#include "trippath.h"

using namespace std;
using namespace tr1;
using namespace boost;


static inline double radians(double degrees)
{
    return degrees/180.0f*M_PI;
}

static inline double degrees(double radians)
{
    return radians*180.0f/M_PI;
}

static double distance(double src_lat, double src_lng, double dest_lat, double dest_lng)
{
    if (src_lat == dest_lat && src_lng == dest_lng)
        return 0.0f;

    double theta = src_lng - dest_lng;
    double src_lat_radians = radians(src_lat);
    double dest_lat_radians = radians(dest_lat);
    double dist = sin(src_lat_radians) * sin(dest_lat_radians) + 
                 cos(src_lat_radians) * cos(dest_lat_radians) * 
                 cos(radians(theta));
    dist = acos(dist);
    dist = degrees(dist);
    dist *= (60.0f * 1.1515 * 1.609344 * 1000.0f);
    return dist;
}


TripAction::TripAction(const char *_src_id, const char *_dest_id, int _route_id, 
                       double _start_time, double _end_time)
{
    src_id = _src_id;
    dest_id = _dest_id;
    route_id = _route_id;
    start_time = _start_time;
    end_time = _end_time;
}    


TripPath::TripPath()
{
    // FIXME: allowing this for now, but we really shouldn't-- should hide it
    // in a private constructor instead
    // assert(0);
}


TripPath::TripPath(double _time, double _fastest_speed, 
                   shared_ptr<TripStop> &_dest_stop, 
                   shared_ptr<TripStop> &_last_stop)
{
    fastest_speed = _fastest_speed;
    dest_stop = _dest_stop;
    last_stop = _last_stop;
    time = _time;
    
    walking_time = 0.0f;
    weight = _time;
    traversed_route_ids = 0;
    last_route_id = -1;
    route_time = 0.0f;
    _get_heuristic_weight();
}


python::object TripPath::get_last_action()
{
    if (last_action)
        return python::object(*last_action);

    return python::object();
}


void TripPath::_get_heuristic_weight() 
{
    // start off with heuristic weight being equivalent to its real weight
    heuristic_weight = weight;

    // then, calculate the time remaining based on going directly
    // from the last vertex to the destination vertex at the fastest
    // possible speed in the graph
    double remaining_distance = distance(last_stop->lat, last_stop->lng, 
                                        dest_stop->lat, dest_stop->lng);
    heuristic_weight += remaining_distance / 5; //(fastest_speed / 3);

    // now, add 5 minutes per each transfer, multiplied to the power of 2
    // (to make transfers exponentially more painful)
    if (traversed_route_ids > 1)
        heuristic_weight += (pow(2.0f, (int)(traversed_route_ids-2)) * 5.0f * 60.0f);
        
    // double the cost of walking after 5 mins, quadruple after 10 mins, 
    // octuple after 15, etc.
    double excess_walking_time = walking_time - 300.0f;
    int iter = 0;
    while (excess_walking_time > 0) 
    {
        double iter_walking_time = 0;
        if (excess_walking_time > 300.0f)
            iter_walking_time = 300.0f;
        else
            iter_walking_time = excess_walking_time;
        heuristic_weight += (iter_walking_time * pow(2.0f, iter));
        excess_walking_time -= 300.0f;
        iter++;
    }

    // add 5 mins to our weight if we were walking and remaining distance
    // >1000m, to account for the fact that we're probably going to
    // want to wait for another bus. this prevents us from repeatedly 
    // getting out of the bus and walking around
    if (last_route_id == -1 && remaining_distance > 1000)
        heuristic_weight += (5*60);
}

static void _add_actions_to_list(python::list &l, shared_ptr<TripAction> &action)
{
    if (action)
    {
        if (action->parent)
            _add_actions_to_list(l, action->parent);
        l.append(TripAction(*action));
    }            
}

python::list TripPath::get_actions()
{
    python::list l;
    // recursively add actions to list, so we get them back in the
    // correct order
    _add_actions_to_list(l, last_action);

    return l;
}

shared_ptr<TripPath> TripPath::add_action(shared_ptr<TripAction> &action, unordered_set<int> &_possible_route_ids,
                              shared_ptr<TripStop> &_last_stop)
{
    shared_ptr<TripPath> new_trippath(new TripPath(*this));

    if (action->route_id == -1)
    {
        new_trippath->walking_time += (action->end_time - action->start_time);
        new_trippath->route_time = 0;
    }
    else if (new_trippath->last_action && 
             action->route_id != new_trippath->last_action->route_id)
    {
        new_trippath->traversed_route_ids++;
        new_trippath->route_time = 0;
    }

    for (unordered_set<int>::iterator i = _possible_route_ids.begin(); 
         i != _possible_route_ids.end(); i++)
    {
        new_trippath->possible_route_ids.insert(*i);
    }

    new_trippath->route_time += (action->end_time - action->start_time);
    new_trippath->weight += (action->end_time - action->start_time);
    new_trippath->weight += (action->start_time - new_trippath->time);

    if (new_trippath->last_action)
        action->parent = new_trippath->last_action;
    new_trippath->last_action = shared_ptr<TripAction>(new TripAction(*action));
    new_trippath->last_stop = _last_stop;
    new_trippath->last_route_id = action->route_id;
    new_trippath->_get_heuristic_weight();
    new_trippath->time = action->end_time;

    return new_trippath;
}
