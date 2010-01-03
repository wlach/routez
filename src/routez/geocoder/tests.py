import unittest

import routez.geocoder.parser as geoparser
#import routez.geocoder.geocoder as geocoder

class GeoParserTestCase(unittest.TestCase):

    def check_single(self, str, expected_name, expected_number, 
                     expected_suffix, expected_region):
        addr = geoparser.parse_address(str)
        self.assertEquals(len(addr), 1)
        self.assertEquals(addr[0].name, expected_name)
        self.assertEquals(addr[0].number, expected_number)
        self.assertEquals(addr[0].suffix, expected_suffix)
        self.assertEquals(addr[0].region, expected_region)

    def check_intersection(self, str, 
                           expected_name1, expected_number1, expected_suffix1, 
                           expected_name2, expected_number2, expected_suffix2,
                           expected_region):
        addr = geoparser.parse_address(str)
        self.assertEquals(len(addr), 2)
        self.assertEquals(addr[0].name, expected_name1)
        self.assertEquals(addr[0].number, expected_number1)
        self.assertEquals(addr[0].suffix, expected_suffix1)
        self.assertEquals(addr[0].region, "")
        self.assertEquals(addr[1].name, expected_name2)
        self.assertEquals(addr[1].number, expected_number2)
        self.assertEquals(addr[1].suffix, expected_suffix2)
        self.assertEquals(addr[1].region, expected_region)

    def testSingle(self):
        self.check_single("114 Brentwood", "Brentwood", "114", "", "")
        self.check_single("114 Brentwood Ave", "Brentwood", "114", "avenue", "")
        self.check_single("114 Brentwood Halifax", "Brentwood", "114", "", 
                          "Halifax")
        self.check_single("114 Brentwood Ave Halifax", "Brentwood", "114", 
                          "avenue", "Halifax")
        self.check_single("114 Brentwood, Halifax", "Brentwood", "114", "", 
                          "Halifax")
        self.check_single("114 Brentwood Ave, Halifax", "Brentwood", "114", 
                          "avenue", "Halifax")
        self.check_single("6277 South Street", "South", "6277", 
                          "street", "")
        #self.check_single("3rd Avenue", "3rd", "", "avenue", "")
        self.check_single("Highfield Park Crescent", "Highfield Park", "", 
                          "crescent", "")
        self.check_single("laneroad", "laneroad", "", "", "")
        self.check_single("5000 bland street", "bland", "5000", "street", "")
        self.check_single("victoria road", "victoria", "", "road", "")
        self.check_single("pursell's cove road", "pursells cove", "", "road", "")
        # numbers with letters should be normalized to just numbers
        self.check_single("5000a bland street", "bland", "5000", "street", "")
        # the null case
        self.assertEquals(geoparser.parse_address(""), [])


    def testIntersection(self):
        self.check_intersection("North & Agricola", "North", "", "", 
                                "Agricola", "", "", "")
        self.check_intersection("North &Agricola", "North", "", "", 
                                "Agricola", "", "", "")
        self.check_intersection("North& Agricola", "North", "", "", 
                                "Agricola", "", "", "")
        self.check_intersection("North&Agricola", "North", "", "", 
                                "Agricola", "", "", "")
        self.check_intersection("North and agricola", 
                                "North", "", "",
                                "agricola", "", "", 
                                "")
        self.check_intersection("North and Agricola", "North", "", "", 
                                "Agricola", "", "", "")
        self.check_intersection("North Street and Agricola", 
                                "North", "", "street", 
                                "Agricola", "", "", "")
        self.check_intersection("North Street and Agricola Halifax", 
                                "North", "", "street",
                                "Agricola", "", "", 
                                "Halifax")
        # th was a problem before (th is a street suffix)
        self.check_intersection("Victoria & Thistle",
                                "Victoria", "", "",
                                "Thistle", "", "", "")
        self.check_intersection("victoria & thistle",
                                "victoria", "", "",
                                "thistle", "", "", "")
        # and appears twice
        self.check_intersection("Bland and Duffus",
                                "Bland", "", "",
                                "Duffus", "", "", "")

        # la is a suffix
        self.check_intersection("Albro Lake Road and Wyse Road",
                                "Albro Lake", "", "road",
                                "Wyse", "", "road", "")

        # the null cases
        self.assertEquals(geoparser.parse_address("&"), [])
        self.assertEquals(geoparser.parse_address(" and "), [])
        
# geocoder tests FIXME:
# 110 wyse road (segment where start and end numbers the same)
# North and agricola (first is less than the second, if all lower case)
