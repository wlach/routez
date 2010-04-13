#include "address.h"

#include <pcrecpp.h>
#include <vector>
#include <sqlite3.h>


class GeoParser
{
  public:
    //GeoParser(const char *dbname);
    GeoParser(sqlite3 *db);
    GeoParser(const std::vector<std::string> &region_names);
    ~GeoParser();

    Address * parse_address(const std::string &str);

  private:
    pcrecpp::RE *address_re;
    pcrecpp::RE *intersection_re;
};
