/* This file has been generated with the help of suffix-subst.pl. */
#include "geoparser.h"

#include <stdlib.h>
#include <assert.h>
#include <sstream>

using namespace boost;
using namespace std;


static int placename_cb(void *userdata, int argc, char **argv, char **azColName)
{
    vector<string> *all_placenames = (vector<string> *)userdata;
    
    all_placenames->push_back(argv[0]);

    return 0;
}


GeoParser::GeoParser(sqlite3 *db)
{
    std::string placename_re;
    vector<string> all_placenames;


    char *zErrMsg = 0;
    int rc = sqlite3_exec(db, "select * from placename", placename_cb, 
                          &all_placenames, &zErrMsg);
    if (rc != SQLITE_OK)
    {
        fprintf(stderr, "SQL error: %s\n", zErrMsg);
        sqlite3_free(zErrMsg);
        
        assert(0 && "Couldn't get list of place names!");
    }

    stringstream regex_str;
    regex_str << "(?:([0-9]+)(?:[a-z])?(?: +))?"; // number
    regex_str << "([a-z]+(?: [a-z]+)*?)"; // street name
    regex_str << "(?: +(av|ave|aven|avenu|avenue|avn|avnue|blvd|boul|boulevard|boulv|crecent|cres|crescent|cresent|dr|driv|drive|drives|highway|highwy|hiway|hiwy|hwy|la|lane|lanes|ln|rd|ro|road|rotary|rtry|row|st|street|streets|strt|ter|terr|terrace))?"; // suffix
    regex_str << "(?: +(n|north|ne|northeast|north east|e|east|se|southeast|south east|s|south|sw|southwest|south west|w|west|nw|northwest|north west))?"; // direction
    regex_str << "(?:[, ] *("; // region begin
    for (vector<string>::iterator i = all_placenames.begin(); 
         i != all_placenames.end(); i++)
    {
        if (i != all_placenames.begin())
            regex_str << "|";
        regex_str << (*i);
    }
    regex_str << "))?"; // region end
    printf("regex_str: %s\n", regex_str.str().c_str());

    address_re = new regex(regex_str.str(), regex::icase);
}


static const int NUMBER_INDEX = 1;
static const int STREET_INDEX = 2;
static const int SUFFIX_INDEX = 3;
static const int DIRECTION_INDEX = 4;
static const int REGION_INDEX = 5;

Address * GeoParser::parse_address(const std::string &str)
{    
    cmatch what;
    if (regex_match(str.c_str(), what, (*address_re))) {
        Address *addr = new Address;

        for (int i=1; i<what.size(); i++) {
            if (what[i].second > what[i].first) 
            {
                string s;
                s.assign(what[i].first, what[i].second);
                
                if (i == NUMBER_INDEX)
                    addr->number = atoi(s.c_str());
                else if (i == STREET_INDEX)
                    addr->street = s;
                else if (i == SUFFIX_INDEX) 
                    addr->suffix = Address::get_suffix(s);
                else if (i == DIRECTION_INDEX) 
                    addr->direction = Address::get_direction(s);
                else if (i == REGION_INDEX) 
                    addr->region = s;
            }
        }

        return addr;
    }

    return NULL;
}
