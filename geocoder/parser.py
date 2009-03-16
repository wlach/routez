from pyparsing import *

import re
import string

__splitre = re.compile("\W*and|&\W*", re.I)

__suffix_mapping = { "ave": "avenue",
                   "av": "avenue",
                   "aven": "avenue",
                   "avenu": "avenue",
                   "avn": "avenue",
                   "avnue": "avenue",
                   "st": "street",
                   "streets": "street",
                   "strt": "street"
                   }

# number can be any of the forms 123, 21B, or 23 1/2
number = ( Combine(Word(nums) + 
                   Optional(oneOf(list(alphas))+FollowedBy(White()))) + \
            Optional(Optional("-") + "1/2")
         ).setParseAction(keepOriginalText, lambda t:t[0].strip())
numberSuffix = oneOf("st th nd")

# just a basic word of alpha characters, Maple, Main, etc.
name = ~numberSuffix + Word(alphas)

# types of streets - extend as desired
type_ = Combine( oneOf("Street St Boulevard Blvd Lane Ln Road Rd Avenue Ave "
                        "Circle Cir Cove Cv Drive Dr Parkway Pkwy Court Ct",
                        caseless=True) + Optional(".").suppress())

# region
region_ = oneOf("Dartmouth Halifax", caseless=True)

# street name 
streetName = (Combine( Optional(oneOf("N S E W")) + number + 
                        Optional("1/2") + 
                        Optional(numberSuffix), joinString=" ", adjacent=False ) 
              | Combine(OneOrMore(~type_ + ~region_ + name), joinString=" ",adjacent=False) )

# basic street address
streetReference = streetName.setResultsName("name") + Optional(type_.setResultsName("type"))
streetReferenceWithRegion = streetReference + Optional(region_.setResultsName("region"))
direct = number.setResultsName("number") + streetReference
directWithRegion = number.setResultsName("number") + streetReferenceWithRegion
streetAddress = ( directWithRegion.setResultsName("street") | 
                  direct.setResultsName("street") |
                  streetReferenceWithRegion.setResultsName("street") |
                  streetReference.setResultsName("street") )

def __normalize_suffix(addr):
    tmpsuffix = string.lower(addr.suffix)

    if __suffix_mapping.get(tmpsuffix):
        addr.suffix = __suffix_mapping[tmpsuffix]


def parse_address(location_str):
    location_strs = __splitre.split(location_str)

    if len(location_strs) == 1:
        addr = streetAddress.parseString(location_str)
        __normalize_suffix(addr)
        return [ addr ]
    elif len(location_strs) == 2:
        addr1 = streetAddress.parseString(location_strs[0])
        addr2 = streetAddress.parseString(location_strs[1])
        return [ addr1, addr2]
    
