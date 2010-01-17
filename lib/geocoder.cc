#include "geocoder.h"
#include "address.h"

#include <stdlib.h>
#include <assert.h>
#include <sqlite3.h>
#include <math.h>
#include <sstream>

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


static double distance(double src_lat, double src_lng, double dest_lat, 
                       double dest_lng)
{
    // returns distance in meters
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


static pair<float, float> interpolated_latlng(float * latlng_array, int num_points,
                                              float length, float percent)
{
    float distance_to_travel = percent * length;
    float distance_travelled = 0.0f;

    pair<float, float> prevcoord;
    for (int i=0; i<num_points; i++)
    {
        pair<float, float> coord(latlng_array[i*2], latlng_array[(i*2)+1]);

        if (i > 0)
        {
            float seg_travel = distance(prevcoord.first, prevcoord.second,
                                        coord.first, coord.second);
            if (seg_travel > 0.0 && 
                (distance_travelled + seg_travel >= distance_to_travel))
            {
                float seg_percent = ((distance_to_travel - distance_travelled) /
                                 seg_travel);

                return pair<float, float>(
                    prevcoord.first + ((coord.first - prevcoord.first) * 
                                       seg_percent),
                    prevcoord.second + ((coord.second - prevcoord.second) * 
                                        seg_percent));
            }
            
            distance_travelled += seg_travel;
        }

        prevcoord = coord;
    }

    return prevcoord;
}



GeoCoder::GeoCoder(const char *dbname)
{
    db = NULL;
    int rc = sqlite3_open(dbname, &db);
    if (rc)
    {
        fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
        sqlite3_close(db);
        assert(0 && "Couldn't initialize geocoder!!!!");
    }

    parser = shared_ptr<GeoParser>(new GeoParser(db));
}


static int sqlite_intersection_cb(void *userdata, int argc, char **argv, 
                                  char **azColName)
{
    pair<float, float> *latlng = (pair<float, float> *)userdata;
    latlng->first = atof(argv[0]);
    latlng->second = atof(argv[1]);

    return 0;
}


static int sqlite_address_cb(void *userdata, int argc, char **argv, 
                             char **azColName)
{
    pair<pair<float, float>, int> * addr_tuple = 
        (pair<pair<float, float>, int> *)userdata;
    
    int first_number = atol(argv[2]);
    int last_number = atol(argv[3]);
    float percent = 0.5;
    if (addr_tuple->second)
        percent = ((float)(addr_tuple->second - first_number)) / (
            (float)(last_number - (float)first_number));

    float length = atof(argv[5]);
    long num_points = *(reinterpret_cast<long *>(&argv[7][0]));

    float *latlng_array = (reinterpret_cast<float *>(&argv[7][sizeof(long)]));
  
    addr_tuple->first = interpolated_latlng(latlng_array, num_points, length, percent);

    return 0;
}


pair<float, float> GeoCoder::get_latlng(const char *str)
{    
    Address *addr = parser->parse_address(str);

    if (addr && addr->is_intersection())
    {
        pair<float, float> latlng(0.0f, 0.0f);

        // sql db assumes first road name in intersection is  less than
        // (case insensitive) than the second. we swap them to satisfy this
        // condition
        Address *addr1 = addr, *addr2 = addr->cross_street;
        if (strcasecmp(addr->street.c_str(), 
                       addr->cross_street->street.c_str()) > 0)
        {
            addr1 = addr->cross_street; addr2 = addr;
        }

        stringstream sqlstr;
        sqlstr << "select lat,lng from intersection where "; 
        sqlstr << "name1 like '" << addr1->street << "' ";
        sqlstr << " and name2 like '" << addr2->street << "'";
        sqlstr << " limit 1";

        char *zErrMsg = 0;
        printf("SQL: %s\n", sqlstr.str().c_str());
        
        int rc = sqlite3_exec(db, sqlstr.str().c_str(), sqlite_intersection_cb, 
                              &latlng, &zErrMsg);
        if (rc != SQLITE_OK)
        {
            fprintf(stderr, "SQL error: %s\n", zErrMsg);
            sqlite3_free(zErrMsg);
            
            // we silently fail in this case... maybe it would be better to 
            // just assert?
        }

        return latlng;
    }

    if (addr && !addr->street.empty())
    {        
        pair<pair<float, float>, int> addr_tuple(pair<float, float>(0.0f, 0.0f), addr->number);

        stringstream sqlstr;
        sqlstr << "select * from road where "; 
        sqlstr << "name like '" << addr->street << "' ";

        if (addr->suffix)
            sqlstr << "and suffixType==" << addr->suffix << " ";

        if (addr->direction)
            sqlstr << "and direction==" << addr->direction << " ";

        if (addr->number) 
        {
            sqlstr << "and firstHouseNumber <= '" << addr->number << "' ";
            sqlstr << "and lastHouseNumber >= '" << addr->number << "' ";
        }
        
        sqlstr << "limit 1";

        addr_tuple.first.first = 0.0f;

        char *zErrMsg = 0;
        printf("SQL: %s\n", sqlstr.str().c_str());
        int rc = sqlite3_exec(db, sqlstr.str().c_str(), sqlite_address_cb, 
                              &addr_tuple, &zErrMsg);
        if (rc != SQLITE_OK)
        {
            fprintf(stderr, "SQL error: %s\n", zErrMsg);
            sqlite3_free(zErrMsg);
            
            // we silently fail in this case... maybe it would be better to 
            // just assert?
        }
        
        return addr_tuple.first;
    }

    return pair<float, float>(0.0f, 0.0f);
}
