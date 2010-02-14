#ifndef __ADDRESS_H
#define __ADDRESS_H
#include <string>


struct Address 
{
    Address()
    {
        number = 0;
        cross_street = NULL;
        suffix = Address::UNKNOWN_SUFFIX;
        direction = Address::UNKNOWN_DIRECTION;        
    }
    
    ~Address() 
    {
        delete cross_street;
    }

    int number;
    std::string street;
    std::string region;

    Address *cross_street;

    bool is_intersection() { return cross_street; }

    enum Suffix {
        UNKNOWN_SUFFIX = 0,
        AVENUE,
        BOULEVARD,
        CRESCENT,
        DRIVE,
        HIGHWAY,
        LANE,
        ROAD,
        ROTARY,
        ROW,
        STREET,
        TERRACE,
    } suffix;

    static Suffix get_suffix(const std::string &str);

    enum Direction {
        UNKNOWN_DIRECTION = 0,
        NORTH, 
        NORTHEAST, 
        EAST,
        SOUTHEAST,
        SOUTH,
        SOUTHWEST,
        WEST,
        NORTHWEST,
    } direction;

    static Direction get_direction(const std::string &str);
};

#endif
