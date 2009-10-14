#include "geoparser.h"
#include "wvtest.h"

using namespace std;


static void test_parser(GeoParser &g, const char *str, int num, 
                        const char *street, const char *region)
{
    Address *a = g.parse_address(str);
    WVPASS(a);
    WVPASSEQ(a->number, num);
    WVPASSEQ(a->street, street);
    WVPASSEQ(a->region, region);
    delete a;
}


WVTEST_MAIN("basic address parsing")
{
    vector<string> region_list; 
    region_list.push_back("Halifax");

    GeoParser g(region_list);
    
    test_parser(g, "442 North Street", 442, "North", "");
}
