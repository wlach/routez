#include <sqlite3.h>
#include <utility>
#include <pcrecpp.h>
#include <tr1/memory>

#include "geoparser.h"


class GeoCoder
{
  public:
    GeoCoder(const char *dbname);
    std::pair<float, float> * get_latlng(const char *str);

  private:
    pcrecpp::RE latlng_re;
    std::tr1::shared_ptr<GeoParser> parser;
    sqlite3 *db;
};
