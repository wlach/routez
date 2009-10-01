#include <sqlite3.h>
#include <utility>


class GeoCoder
{
  public:
    GeoCoder(const char *dbname);
    std::pair<float, float> get_latlng(const char *str);

  private:
    sqlite3 *db;
};
