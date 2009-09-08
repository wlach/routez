#ifndef __ADDRESS_H
#define __ADDRESS_H
#include <string>

struct Address 
{
    std::string street;
    int number;

    enum TypeSuffix {
        AVENUE = 0,
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
    };

    TypeSuffix suffix;
};

Address::TypeSuffix get_typesuffix(const std::string &s);

#endif
