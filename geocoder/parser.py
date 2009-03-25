from pyparsing import *

import re
import string

__splitre = re.compile("\W*\ and\ |&\W*", re.I)
numre = re.compile("[0-9]+", re.I)

suffix_mapping = { "ave": "avenue",
                   "av": "avenue",
                   "aven": "avenue",
                   "avenu": "avenue",
                   "avn": "avenue",
                   "avnue": "avenue",
                   "boul": "boulevard",
                   "blvd": "boulevard",
                   "boulv": "boulevard",
                   "crecent": "crescent",
                   "cres": "crescent",
                   "cresent": "crescent",
                   "driv": "drive",
                   "dr": "drive",
                   "drives": "drive",
                   "hwy": "highway",
                   "highwy": "highway",
                   "hiway": "highway",
                   "hiwy": "highway",
                   "la": "lane",
                   "ln": "lane",
                   "lanes": "lane",
                   "rd": "road",
                   "rtry": "rotary",
                   "st": "street",
                   "streets": "street",
                   "strt": "street",
                   "terr": "terrace",
                   "ter": "terrace",
                   }

__all_suffixes = string.join(suffix_mapping.keys() + list(set(suffix_mapping.values())), " ")

# number can be any of the forms 123, 21B, or 23 1/2
number = ( Combine(Word(nums) + 
                   Optional(oneOf(list(alphas))+FollowedBy(White()))) + \
            Optional(Optional("-") + "1/2")
         ).setParseAction(keepOriginalText, lambda t:t[0].strip())

# just a basic word of alpha characters, Maple, Main, etc.
name = Combine( Word(alphas) + Optional(Combine(oneOf("'").suppress() + "s")) )

# suffixs of streets - extend as desired
suffix_ = Combine( White().suppress() + oneOf(__all_suffixes, caseless=True) + 
                   Optional(".").suppress() + FollowedBy(Or([White().suppress(), 
                                                  LineEnd()])))

# region
region_ = Combine( White().suppress() + oneOf("Dartmouth Halifax", 
                                              caseless=True))

# join string
and_ = Or([ Combine( White().suppress() + oneOf("and", caseless=True) + White().suppress()), oneOf("&")])

# street name 
streetName = (Combine( Optional(oneOf("N S E W")) + number + 
                        Optional("1/2"), joinString=" ", adjacent=False )
              | Combine(OneOrMore(~suffix_ + ~region_ + ~and_ + name), joinString=" ",adjacent=False) )

# basic street address
streetReference = streetName.setResultsName("name") + Optional(suffix_.setResultsName("suffix"))
streetReferenceWithRegion = streetReference + Optional(region_.setResultsName("region"))
direct = number.setResultsName("number") + streetReference
directWithRegion = number.setResultsName("number") + streetReferenceWithRegion
streetAddress = ( directWithRegion.setResultsName("street") | 
                  streetReferenceWithRegion.setResultsName("street"))

# intersection
intersection = (streetReferenceWithRegion.setResultsName("street1") + \
                and_ + \
                (streetReferenceWithRegion.setResultsName("street2")))

class Address:
    def __init__(self, addr):
        self.name = addr.name            
        self.number = addr.number
        match = numre.match(self.number)
        if match:
            self.number = match.group(0)
        self.region = addr.region
        self.suffix = string.lower(addr.suffix)
        if suffix_mapping.get(self.suffix):
            self.suffix = suffix_mapping[self.suffix]

def parse_address(location_str):
    # strip out and commas from the string, to make it easier
    # to parse out the region (FIXME: better to do this in the parser?)
    location_str = location_str.replace(",", "")

    location_strs = __splitre.split(location_str)
    
    if len(location_strs) == 1 and location_strs[0]:
        addr = streetAddress.parseString(location_str)
        return [Address(addr)]

    elif len(location_strs) == 2 and location_strs[0] and location_strs[1]:
        inters = intersection.parseString(location_str)
        return [Address(inters.street1), Address(inters.street2)]    
    
    return []
