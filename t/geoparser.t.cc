#include "geoparser.h"
#include "wvtest.h"

using namespace std;


static bool test_parser_address(GeoParser &g, const char *str, const char *street, 
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
    
    WVPASS(test_parser_address(g, "442 North Street", "North", 442, 
                       Address::UNKNOWN_DIRECTION, Address::STREET, ""));

    WVPASS(test_parser_address(g, "114 Brentwood", "Brentwood", 114, 
                       Address::UNKNOWN_DIRECTION, Address::UNKNOWN_SUFFIX, ""));
    WVPASS(test_parser_address(g, "114 Brentwood Ave", "Brentwood", 114, 
                       Address::UNKNOWN_DIRECTION, Address::AVENUE, ""));
    WVPASS(test_parser_address(g, "114 Brentwood Halifax", "Brentwood", 114, 
                       Address::UNKNOWN_DIRECTION, Address::UNKNOWN_SUFFIX, 
                       "Halifax"));
    WVPASS(test_parser_address(g, "114 Brentwood Ave Halifax", "Brentwood", 114, 
                       Address::UNKNOWN_DIRECTION, Address::AVENUE, "Halifax"));
    WVPASS(test_parser_address(g, "114 Brentwood, Halifax", "Brentwood", 114, 
                       Address::UNKNOWN_DIRECTION, Address::UNKNOWN_SUFFIX, "Halifax"));
    WVPASS(test_parser_address(g, "114 Brentwood Ave, Halifax", "Brentwood", 114, 
                       Address::UNKNOWN_DIRECTION, Address::AVENUE, "Halifax"));
    WVPASS(test_parser_address(g, "6277 South Street", "South", 6277, 
                       Address::UNKNOWN_DIRECTION, Address::STREET, ""));
    WVPASS(test_parser_address(g, "Highfield Park Crescent", "Highfield Park", 0, 
                       Address::UNKNOWN_DIRECTION, Address::CRESCENT, ""));
    WVPASS(test_parser_address(g, "laneroad", "laneroad", 0, Address::UNKNOWN_DIRECTION, 
                       Address::UNKNOWN_SUFFIX, ""));
    WVPASS(test_parser_address(g, "5000 bland street", "bland", 5000, 
                       Address::UNKNOWN_DIRECTION, Address::STREET, ""));
    WVPASS(test_parser_address(g, "victoria road", "victoria", 0, 
                       Address::UNKNOWN_DIRECTION, Address::ROAD, ""));

    // street names that start with numbers
    WVPASS(test_parser_address(g, "3rd Avenue", "3rd", 0, Address::UNKNOWN_DIRECTION, 
                               Address::AVENUE, ""));
    WVPASS(test_parser_address(g, "5th street, halifax", "5th", 0, Address::UNKNOWN_DIRECTION, 
                               Address::STREET, "halifax"));
    //WVPASS(test_parser_address(g, "55 avenue, halifax", "55", 0, Address::UNKNOWN_DIRECTION, 
    //                           Address::AVENUE, "halifax"));

    // FIXME: strip punctuation out of user strings
    //    WVPASS(test_parser_address(g, "pursell's cove road", "pursells cove", "", Address::ROAD, 
    //            "");
    // numbers with letters should be normalized to just numbers
    WVPASS(test_parser_address(g, "5000a bland street", "bland", 5000, 
                       Address::UNKNOWN_DIRECTION, Address::STREET, ""));
    // the null case
    //self.assertEquals(geoparser.parse_address(""), [])

}


static bool test_parser_intersection(GeoParser &g, const char *str, 
                                     const char *street1, 
                                     Address::Direction dir1, 
                                     Address::Suffix suffix1, 
                                     const char *street2, 
                                     Address::Direction dir2, 
                                     Address::Suffix suffix2, 
                                     const char *region)
{
    bool pass = true;

    Address *a = g.parse_address(str);
    pass &= WVPASS(a);
    pass &= WVPASSEQ(a->street, street1);
    pass &= WVPASSEQ(a->direction, dir1);
    pass &= WVPASSEQ(a->suffix, suffix1);

    pass &= WVPASS(a->cross_street);
    pass &= WVPASSEQ(a->cross_street->street, street2);
    pass &= WVPASSEQ(a->cross_street->direction, dir2);
    pass &= WVPASSEQ(a->cross_street->suffix, suffix2);

    pass &= WVPASSEQ(a->region, region);

    delete a;
    
    return pass;
}


WVTEST_MAIN("intersection parsing") 
{
    vector<string> region_list; 
    region_list.push_back("Halifax");
    GeoParser g(region_list);

    WVPASS(test_parser_intersection(g, "North & Agricola", "North", 
                                    Address::UNKNOWN_DIRECTION, Address::UNKNOWN_SUFFIX, 
                                    "Agricola", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX, ""));
    WVPASS(test_parser_intersection(g, "North &Agricola", "North", 
                                    Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX, 
                                    "Agricola", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX, ""));
    WVPASS(test_parser_intersection(g, "North& Agricola", "North",
                                    Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX,
                                    "Agricola", Address::UNKNOWN_DIRECTION,
                                    Address::UNKNOWN_SUFFIX, ""));
    WVPASS(test_parser_intersection(g, "North&Agricola", "North", 
                                    Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX, 
                                    "Agricola", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX, ""));
    WVPASS(test_parser_intersection(g, "North and agricola", 
                                    "North", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX,
                                    "agricola", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX, 
                                    ""));
    WVPASS(test_parser_intersection(g, "North and Agricola", "North", 
                                    Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX, 
                                    "Agricola", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX, ""));
    WVPASS(test_parser_intersection(g, "North Street and Agricola", 
                                    "North", Address::UNKNOWN_DIRECTION, 
                                    Address::STREET, 
                                    "Agricola", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX, ""));
    WVPASS(test_parser_intersection(g, "North Street and Agricola Halifax", 
                                    "North", Address::UNKNOWN_DIRECTION, 
                                    Address::STREET,
                                    "Agricola", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX, 
                                    "Halifax"));
    // th was a problem before (th is a street suffix));
    WVPASS(test_parser_intersection(g, "Victoria & Thistle",
                                    "Victoria", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX,
                                    "Thistle", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX, ""));
    WVPASS(test_parser_intersection(g, "victoria & thistle",
                                    "victoria", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX,
                                    "thistle", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX, ""));
    // and appears twice
    WVPASS(test_parser_intersection(g, "Bland and Duffus",
                                    "Bland", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX,
                                    "Duffus", Address::UNKNOWN_DIRECTION, 
                                    Address::UNKNOWN_SUFFIX, ""));
    
    // la is a suffix
    WVPASS(test_parser_intersection(g, "Albro Lake Road and Wyse Road",
                                    "Albro Lake", Address::UNKNOWN_DIRECTION, 
                                    Address::ROAD,
                                    "Wyse", Address::UNKNOWN_DIRECTION, 
                                    Address::ROAD, ""));

    // the null cases
    //self.assertEquals(geoparser.parse_address("&"), [])
    //self.assertEquals(geoparser.parse_address(" and "), [])
}
