#ifndef __TRIPGRAPH_H
#define __TRIPGRAPH_H
#include <string>
#include <stdint.h>
#include <tr1/unordered_map>

#include <vector>
#include <boost/shared_ptr.hpp>
#include "trippath.h"
#include "tripstop.h"


class TripGraph
{
public:
    TripGraph();
    void load(std::string fname);
    void save(std::string fname);

    void add_triphop(int32_t start_time, int32_t end_time, std::string src_id, 
                     std::string dest_id, int route_id, std::string service_id);

    void add_tripstop(std::string id, std::string type, float lat, float lng);
    void add_walkhop(std::string src_id, std::string dest_id);
    void link_osm_gtfs();

    TripStop get_tripstop(std::string id);

    boost::shared_ptr<TripStop> get_nearest_osmstop(double lat, double lng);

    typedef std::vector<boost::shared_ptr<TripPath> > TripPathList;
    typedef std::tr1::unordered_map<const char*, std::tr1::unordered_map<int, boost::shared_ptr<TripPath> > > VisitedRouteMap;
    typedef std::tr1::unordered_map<const char*, std::tr1::unordered_map<const char*, boost::shared_ptr<TripPath> > > VisitedWalkMap;

    TripPath find_path(int secs, std::string service_period, 
                       double src_lat, double src_lng, 
                       double dest_lat, double dest_lng, PyObject *cb);

    TripPathList extend_path(boost::shared_ptr<TripPath> &path, 
                             std::string service_period, 
                             VisitedRouteMap &visited_routes, 
                             VisitedWalkMap &visited_walks, 
                             PyObject *cb);

    typedef std::tr1::unordered_map<std::string, boost::shared_ptr<TripStop> > TripStopDict;
    TripStopDict tripstops;
    TripStopDict osmstops;
        
};

#endif // __TRIPGRAPH
