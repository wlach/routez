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
        self.assertEquals(addr[0].type, expected_suffix)
        self.assertEquals(addr[0].region, expected_region)

    def check_intersection(self, str, 
                           expected_name1, expected_number1, expected_suffix1, 
                           expected_name2, expected_number2, expected_suffix2):
        addr = geoparser.parse_address(str)
        self.assertEquals(len(addr), 2)
        self.assertEquals(addr[0].name, expected_name1)
        self.assertEquals(addr[0].number, expected_number1)
        self.assertEquals(addr[0].type, expected_suffix1)
        self.assertEquals(addr[1].name, expected_name2)
        self.assertEquals(addr[1].number, expected_number2)
        self.assertEquals(addr[1].type, expected_suffix2)

    def testSingle(self):
        self.check_single("114 Brentwood", "Brentwood", "114", "", "")
        self.check_single("114 Brentwood Ave", "Brentwood", "114", "Ave", "")
        self.check_single("114 Brentwood Halifax", "Brentwood", "114", "", 
                          "Halifax")
        self.check_single("114 Brentwood Ave Halifax", "Brentwood", "114", 
                          "Ave", "Halifax")
        
    def testIntersection(self):
        self.check_intersection("North & Agricola", "North", "", "", 
                                "Agricola", "", "")
