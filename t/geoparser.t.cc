#include "geoparser.h"
#include "wvtest.h"

using namespace std;


static bool test_parser(GeoParser &g, const char *str, const char *street, 
                        int num, Address::Direction dir, 
                        Address::Suffix suffix, const char *region)
{
    bool pass = true;

    Address *a = g.parse_address(str);
    pass &= WVPASS(a);
    pass &= WVPASSEQ(a->number, num);
    pass &= WVPASSEQ(a->street, street);
    pass &= WVPASSEQ(a->region, region);
    pass &= WVPASSEQ(a->direction, dir);
    pass &= WVPASSEQ(a->suffix, suffix);
    delete a;
    
    return pass;
}


WVTEST_MAIN("basic address parsing")
{
    vector<string> region_list; 
    region_list.push_back("Halifax");

    GeoParser g(region_list);
    
    WVPASS(test_parser(g, "442 North Street", "North", 442, 
                       Address::UNKNOWN_DIRECTION, Address::STREET, ""));

    WVPASS(test_parser(g, "114 Brentwood", "Brentwood", 114, 
                       Address::UNKNOWN_DIRECTION, Address::UNKNOWN_SUFFIX, ""));
    WVPASS(test_parser(g, "114 Brentwood Ave", "Brentwood", 114, 
                       Address::UNKNOWN_DIRECTION, Address::AVENUE, ""));
    WVPASS(test_parser(g, "114 Brentwood Halifax", "Brentwood", 114, 
                       Address::UNKNOWN_DIRECTION, Address::UNKNOWN_SUFFIX, 
                       "Halifax"));
    WVPASS(test_parser(g, "114 Brentwood Ave Halifax", "Brentwood", 114, 
                       Address::UNKNOWN_DIRECTION, Address::AVENUE, "Halifax"));
    WVPASS(test_parser(g, "114 Brentwood, Halifax", "Brentwood", 114, 
                       Address::UNKNOWN_DIRECTION, Address::UNKNOWN_SUFFIX, "Halifax"));
    WVPASS(test_parser(g, "114 Brentwood Ave, Halifax", "Brentwood", 114, 
                       Address::UNKNOWN_DIRECTION, Address::AVENUE, "Halifax"));
    WVPASS(test_parser(g, "6277 South Street", "South", 6277, 
                       Address::UNKNOWN_DIRECTION, Address::STREET, ""));
    // FIXME: Currently fails
    //WVPASS(test_parser(g, "3rd Avenue", "3rd", 0, Address::UNKNOWN_DIRECTION, 
    //Address::AVENUE, ""));
    WVPASS(test_parser(g, "Highfield Park Crescent", "Highfield Park", 0, 
                       Address::UNKNOWN_DIRECTION, Address::CRESCENT, ""));
    WVPASS(test_parser(g, "laneroad", "laneroad", 0, Address::UNKNOWN_DIRECTION, 
                       Address::UNKNOWN_SUFFIX, ""));
    WVPASS(test_parser(g, "5000 bland street", "bland", 5000, 
                       Address::UNKNOWN_DIRECTION, Address::STREET, ""));
    WVPASS(test_parser(g, "victoria road", "victoria", 0, 
                       Address::UNKNOWN_DIRECTION, Address::ROAD, ""));
    // FIXME: strip punctuation out of user strings
    //    WVPASS(test_parser(g, "pursell's cove road", "pursells cove", "", Address::ROAD, 
    //            "");
    // numbers with letters should be normalized to just numbers
    WVPASS(test_parser(g, "5000a bland street", "bland", 5000, 
                       Address::UNKNOWN_DIRECTION, Address::STREET, ""));
    // the null case
    //self.assertEquals(geoparser.parse_address(""), [])

}
