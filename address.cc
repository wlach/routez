#include "address.h"
#include <assert.h>

extern const char *suffix_names[];
extern const Address::TypeSuffix suffix_mapping[];


Address::TypeSuffix get_typesuffix(const std::string &s)
{
    int i = 0;
    while (suffix_names[i]) 
    { 
            printf("%s vs %s\n", s.c_str(), suffix_names[i]);
       if (s == suffix_names[i])
        {
            return suffix_mapping[i];
        }
        
        i++;
    }

    assert(0); // should never happen!

    return Address::STREET;
}
