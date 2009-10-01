#ifndef __ADDRESS_H
#define __ADDRESS_H
#include <string>


struct Address 
{
    Address()
    {
        number = 0;
        suffix = Address::UNKNOWN_SUFFIX;
        direction = Address::UNKNOWN_DIRECTION;
    }
    
    std::string street;
    int number;

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
};

Address * parse_address(const std::string &str);

#endif
