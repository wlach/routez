#include <sqlite3.h>
#include <utility>
#include <boost/regex.hpp>
#include <boost/shared_ptr.hpp>

#include "geoparser.h"


class GeoCoder
{
  public:
    GeoCoder(const char *dbname);
    std::pair<float, float> get_latlng(const char *str);

  private:
    boost::shared_ptr<boost::regex> latlng_re;
    boost::shared_ptr<GeoParser> parser;
    sqlite3 *db;
};
