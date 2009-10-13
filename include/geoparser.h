#include "address.h"

#include <boost/regex.hpp>
#include <vector>
#include <sqlite3.h>


class GeoParser
{
  public:
    //GeoParser(const char *dbname);
    GeoParser(sqlite3 *db);
    GeoParser(const std::vector<std::string> &region_names);

    Address * parse_address(const std::string &str);


  private:
    boost::regex * address_re;
};
