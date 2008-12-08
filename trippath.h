#ifndef __TRIPPATH_H
#define __TRIPPATH_H
#include <tr1/unordered_set>
#include <vector>
#include <boost/python.hpp>
#include <boost/shared_ptr.hpp>
#include "tripstop.h"


struct TripAction
{
    std::string src_id;
    std::string dest_id;
    int route_id;
    float start_time;
    float end_time;
    boost::shared_ptr<TripAction> parent;

    TripAction(const char *_src_id, const char *_dest_id, int _route_id, 
               double _start_time, double _end_time);

};


struct TripPath
{
    double time;
    double fastest_speed;
    boost::shared_ptr<TripStop> dest_stop;
    boost::shared_ptr<TripStop> last_stop;
    boost::shared_ptr<TripAction> last_action;

    double walking_time;
    double route_time;
    int traversed_route_ids;
    std::tr1::unordered_set<int> possible_route_ids;
    int last_route_id;
    double weight;
    double heuristic_weight;

    TripPath(double _time, double _fastest_speed, 
             boost::shared_ptr<TripStop> &_dest_stop, 
             boost::shared_ptr<TripStop> &_last_stop);
    TripPath(); 

    //double cmp(const TripPath &t);

    boost::shared_ptr<TripPath> add_action(
        boost::shared_ptr<TripAction> &action, 
        std::tr1::unordered_set<int> &_possible_route_ids,
        boost::shared_ptr<TripStop> &_last_stop);

    void _get_heuristic_weight();

    // the following are for the benefit of our python wrapper
    boost::python::list get_actions();
    boost::python::object get_last_action();
};

#endif // __TRIPPATH_H
