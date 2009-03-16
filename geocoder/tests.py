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
        
    def testIntersection(self):
        self.check_intersection("North & Agricola", "North", "", "", 
                                "Agricola", "", "", "")
        self.check_intersection("North and Agricola", "North", "", "", 
                                "Agricola", "", "", "")
        self.check_intersection("North Street and Agricola", 
                                "North", "", "street", 
                                "Agricola", "", "", "")
        self.check_intersection("North Street and Agricola Halifax", 
                                "North", "", "street",
                                "Agricola", "", "", 
                                "Halifax")
