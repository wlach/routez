from pyparsing import *

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

# street name 
streetName = (Combine( Optional(oneOf("N S E W")) + number + 
                        Optional("1/2") + 
                        Optional(numberSuffix), joinString=" ", adjacent=False ) 
                | Combine(OneOrMore(~type_ + name), joinString=" ",adjacent=False) )

# basic street address
streetReference = streetName.setResultsName("name") + Optional(type_).setResultsName("type")
direct = number.setResultsName("number") + streetReference
streetAddress = ( direct.setResultsName("street") | 
                  streetReference.setResultsName("street") )

