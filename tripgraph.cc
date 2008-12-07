#include "tripgraph.h"
#include <assert.h>
#include <queue>
#include <boost/python.hpp>

using namespace boost;
using namespace std;


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


static bool operator>(const shared_ptr<TripPath> &x, 
                      const shared_ptr<TripPath> &y)
{
    return x->heuristic_weight > y->heuristic_weight;
}

TripGraph::TripGraph()
{
}


void TripGraph::load(string fname)
{
    FILE *fp = fopen(fname.c_str(), "r");
    if (!fp)
    {
        printf("ERROR: Couldn't open graph.");
        return;
    }
        
    uint32_t num_tripstops = 0;
    if (fread(&num_tripstops, sizeof(uint32_t), 1, fp) != 1)
    {
        printf("Error reading num tripstops.");
        return;
    }
        
    uint32_t i = 0;
    while (i < num_tripstops)
    {
        shared_ptr<TripStop> s(new TripStop(fp));
        tripstops.insert(pair<string,shared_ptr<TripStop> >(s->id, s));
        if (strcmp(s->type, "osm") == 0)
            osmstops.insert(pair<string,shared_ptr<TripStop> >(s->id, s));
        i++;
    }
}


void TripGraph::save(string fname)
{
    FILE *fp = fopen(fname.c_str(), "w");
    if (!fp)
    {
        printf("ERROR: Couldn't open graph %s for writing.", fname.c_str());
        return;
    }

    uint32_t num_tripstops = tripstops.size();
    assert(fwrite(&num_tripstops, sizeof(uint32_t), 1, fp) == 1);
    for (TripStopDict::iterator i = tripstops.begin(); 
         i != tripstops.end(); i++)
    {
        i->second->write(fp);
    }
}


void TripGraph::add_triphop(int32_t start_time, int32_t end_time, string src_id, 
                            string dest_id, int route_id, string service_id)
{
    assert(tripstops.count(src_id) > 0);
    tripstops[src_id]->add_triphop(start_time, end_time, dest_id, 
                                   route_id, service_id);
}


void TripGraph::add_tripstop(string id, string type, float lat, float lng)
{
    shared_ptr<TripStop> s(new TripStop(id, type, lat, lng));
    tripstops.insert(pair<string,shared_ptr<TripStop> >(id, s));
    if (type == "osm")
        osmstops.insert(pair<string,shared_ptr<TripStop> >(id, s));        
}


void TripGraph::add_walkhop(string src_id, string dest_id)
{
    double dist = distance(tripstops[src_id]->lat, tripstops[src_id]->lng,
                           tripstops[dest_id]->lat, 
                           tripstops[dest_id]->lng);

    tripstops[src_id]->add_walkhop(dest_id, dist/1.1);
}


void TripGraph::link_osm_gtfs()
{
    for (TripStopDict::iterator i = tripstops.begin(); 
         i != tripstops.end(); i++)
    {
        if (strcmp(i->second->type, "gtfs") == 0)
        {
            shared_ptr<TripStop> nearest_osm;
            double min_dist;
            for (TripStopDict::iterator j = osmstops.begin(); 
                 j != osmstops.end(); j++)
            {
                double dist = distance(i->second->lat, i->second->lng, 
                                      j->second->lat, j->second->lng);
                if (!nearest_osm || dist < min_dist)
                {
                    nearest_osm = j->second;
                    min_dist = dist;
                }
            }
            
            assert(nearest_osm);
            printf("Linking %s -> %s\n", i->second->id, nearest_osm->id);
            add_walkhop(i->second->id, nearest_osm->id);
            add_walkhop(nearest_osm->id, i->second->id);
        }
    }
}


shared_ptr<TripStop> TripGraph::get_nearest_osmstop(double lat, double lng)
{
    shared_ptr<TripStop> closest_stop;
    double min_dist = 0.0f;
    for (TripStopDict::iterator i = osmstops.begin(); 
         i != osmstops.end(); i++)
    {
        shared_ptr<TripStop> s = i->second;
        double dist = pow((s->lat - lat), 2) + pow((s->lng - lng), 2);
        if (!closest_stop || dist < min_dist)
        {
            closest_stop = s;
            min_dist = dist;
        }
    }

    return closest_stop;
}


TripPath TripGraph::find_path(int secs, string service_period, 
                              double src_lat, double src_lng, 
                              double dest_lat, double dest_lng, PyObject *cb)
{
    VisitedRouteMap visited_routes;
    VisitedWalkMap visited_walks;
    typedef priority_queue<shared_ptr<TripPath>, vector<shared_ptr<TripPath> >, greater<shared_ptr<TripPath> > > PathQueue;

    PathQueue uncompleted_paths;
    PathQueue completed_paths;
        
    shared_ptr<TripStop> start_node = get_nearest_osmstop(src_lat, src_lng);
    shared_ptr<TripStop> end_node = get_nearest_osmstop(dest_lat, dest_lng);
    printf("Start: %s End: %s\n", start_node->id, end_node->id);

    // consider distance required to reach the start node from the 
    // beginning, add that to our start time
    double dist_from_start = distance(src_lat, src_lng, 
                                      start_node->lat, start_node->lng);
    secs += (int)(dist_from_start / 1.1);
    
    printf("Start time - %d\n", secs);
    shared_ptr<TripPath> start_path(new TripPath(secs, 1.1f, end_node, 
                                                 start_node));
    if (start_node == end_node)
        return TripPath(*start_path);

    uncompleted_paths.push(start_path);

    int num_paths_considered = 0;

    while (uncompleted_paths.size() > 0)
    {
        shared_ptr<TripPath> path = uncompleted_paths.top();
        uncompleted_paths.pop();
        TripPathList new_paths = extend_path(path, service_period, 
                                             visited_routes, visited_walks, cb);
        num_paths_considered += new_paths.size();
        for (TripPathList::iterator i = new_paths.begin(); 
             i != new_paths.end(); i++)
        {
            shared_ptr<TripPath> t = (*i);
            if (t->last_stop->id == end_node->id)
                completed_paths.push(t);
            else
                uncompleted_paths.push(t);
        }

        //# if we've still got open paths, but their weight exceeds that
        // of the weight of a completed path, break
        if (uncompleted_paths.size() > 0 && completed_paths.size() > 0 &&
            uncompleted_paths.top()->heuristic_weight > 
            completed_paths.top()->heuristic_weight)
        {
            printf("Breaking with %d uncompleted paths (paths "
                   "considered: %d).\n", uncompleted_paths.size(), 
                   num_paths_considered);
            return TripPath(*(completed_paths.top()));
        }

        //if len(completed_paths) > 0 and len(uncompleted_paths) > 0:
        //  print "Weight of best completed path: %s, uncompleted: %s" % \
        //      (completed_paths[0].heuristic_weight, uncompleted_paths[0].heuristic_weight)
    }

    if (completed_paths.size())
        return TripPath(*(completed_paths.top()));

    return TripPath();
}


TripStop TripGraph::get_tripstop(string id)
{
    return TripStop(*(tripstops[id]));
}


TripGraph::TripPathList TripGraph::extend_path(shared_ptr<TripPath> &path, 
                                               string service_period, 
                                               VisitedRouteMap &visited_routes,
                                               VisitedWalkMap &visited_walks, 
                                               PyObject *cb)
{
    TripPathList newpaths;
    string src_id = path->last_stop->id;        
    int last_route_id = path->last_route_id;

    if (path->last_action)
    {
        string last_src_id = path->last_action->src_id;
#if 0
        if (cb)
            python::call<void>(cb, tripstops[last_src_id]->lat, 
                               tripstops[last_src_id]->lng,
                               tripstops[src_id]->lat, 
                               tripstops[src_id]->lng,
                               last_route_id);
#endif
    }
    
    // printf("Extending path at vertice %s (on %d) @ %f (walktime: %f, routetime:%f)\n", src_id.c_str(), 
    //        last_route_id, path->time, path->walking_time, path->route_time);

    shared_ptr<TripStop> src_stop(tripstops[src_id]);

    // keep track of outgoing route ids at this node: make sure that we 
    // don't get on a route later when we could have gotten on here
    set<int> outgoing_route_ids = src_stop->get_routes(service_period);


    // explore walkhops that are better than the ones we've already visited
    // if we're on a bus, don't allow a transfer if we've been on for
    // less than 5 minutes (FIXME: probably better to measure distance travelled?)
    if (last_route_id == -1 || path->route_time > (5 * 60))
    {
        for (TripStop::WalkHopDict::iterator i = src_stop->wdict.begin();
             i != src_stop->wdict.end(); i++)
        {
            string dest_id = i->first;
            double walktime = i->second;
            shared_ptr<TripAction> action(
                new TripAction(src_id, dest_id, -1, 
                               path->time, (path->time + walktime)));
            shared_ptr<TripPath> path2 = path->add_action(
                action, outgoing_route_ids, tripstops[dest_id]);

            //printf("- Considering walkpath to %s\n", dest_id.c_str());
            if (!visited_walks[src_id].count(dest_id) || 
                visited_walks[src_id][dest_id]->heuristic_weight > path2->heuristic_weight ||
                ((visited_walks[src_id][dest_id]->heuristic_weight - path2->heuristic_weight) < 1.0f &&
                 visited_walks[src_id][dest_id]->walking_time > path2->walking_time))
            {
                //printf("-- Adding walkpath to %s\n", dest_id.c_str());
                newpaths.push_back(path2);
                visited_walks[src_id][dest_id] = path2;
            }
        }
    }

    // find outgoing triphops from the source and get a list of paths to
    // them. 
    for (set<int>::iterator i = outgoing_route_ids.begin();
         i != outgoing_route_ids.end(); i++)
    {
        shared_ptr<TripHop> t = src_stop->find_triphop((int)path->time, 
                                                       (*i), 
                                                       service_period);
        if (t)
        {
            // if we've been on the route before (or could have been), 
            // don't get on again
            if ((*i) != last_route_id && path->possible_route_ids.count(*i))
            {
                // pass
            }
            // disallow more than three transfers
            else if ((*i) != last_route_id && 
                     path->traversed_route_ids > 3)
            {
                // pass
            }
            else
            {
                shared_ptr<TripAction> action = shared_ptr<TripAction>(
                    new TripAction(src_id, t->dest_id, (*i), t->start_time,
                                   t->end_time));
                shared_ptr<TripPath> path2 = path->add_action(
                    action, outgoing_route_ids, tripstops[t->dest_id]);
                
                if (!visited_routes[src_id].count(*i) || 
                    visited_routes[src_id][*i]->heuristic_weight > path2->heuristic_weight ||
                    (fabs(visited_routes[src_id][*i]->heuristic_weight - path2->heuristic_weight) < 1.0f &&
                     visited_routes[src_id][*i]->walking_time > path2->walking_time))
                {
                    newpaths.push_back(path2);
                    visited_routes[src_id][(*i)] = path2;
                }
            }
        }
    }
        
    return newpaths;
}    


BOOST_PYTHON_MODULE(tripgraph)
{
    using namespace boost::python;
    class_<TripGraph>("TripGraph")
    .def("add_tripstop", &TripGraph::add_tripstop)
    .def("add_triphop", &TripGraph::add_triphop)
    .def("add_walkhop", &TripGraph::add_walkhop)
    .def("link_osm_gtfs", &TripGraph::link_osm_gtfs)
    .def("save", &TripGraph::save)
    .def("load", &TripGraph::load)
    .def("find_path", &TripGraph::find_path)    
    .def("get_tripstop", &TripGraph::get_tripstop)
    ;

    class_<TripStop>("TripStop")
    .def_readonly("lat", &TripStop::lat)
    .def_readonly("lng", &TripStop::lng);

    class_<TripPath>("TripPath")
    .def("get_actions", &TripPath::get_actions);
    
    class_<TripAction>("TripAction", init<string, string, int, double, double>())
    .def_readonly("src_id", &TripAction::src_id)
    .def_readonly("dest_id", &TripAction::dest_id)
    .def_readonly("route_id", &TripAction::route_id)
    .def_readonly("start_time", &TripAction::start_time)
    .def_readonly("end_time", &TripAction::end_time);
}
