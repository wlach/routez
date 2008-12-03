#include <math.h>
#include <boost/python.hpp>

inline float radians(float degrees)
{
    return degrees/180.0f*M_PI;
}

inline float degrees(float radians)
{
    return radians*180.0f/M_PI;
}

float distance(float src_lat, float src_lng, float dest_lat, float dest_lng)
{
    if (src_lat == dest_lat && src_lng == dest_lng)
        return 0.0f;

    float theta = src_lng - dest_lng;
    float src_lat_radians = radians(src_lat);
    float dest_lat_radians = radians(dest_lat);
    float dist = sin(src_lat_radians) * sin(dest_lat_radians) + 
                 cos(src_lat_radians) * cos(dest_lat_radians) * 
                 cos(radians(theta));
    dist = acos(dist);
    dist = degrees(dist);
    dist *= (60.0f * 1.1515 * 1.609344 * 1000.0f);
    return dist;
}

BOOST_PYTHON_MODULE(latlng_ext)
{
    using namespace boost::python;
    def("distance", distance);
}
