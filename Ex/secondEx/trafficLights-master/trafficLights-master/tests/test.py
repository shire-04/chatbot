from hawksoft import trafficLights

import unittest
class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        #print ("this setupclass() method only called once.\n")
        pass
    @classmethod
    def tearDownClass(cls):
        #print ("this teardownclass() method only called once too.\n")
        pass
    def setUp(self):
        #print ("do something before test : prepare environment.\n")
        pass
    def tearDown(self):
        #print ("do something after test : clean up.\n")
        pass
        
    def test_start(self):
        trafficLights.main()

if __name__ == '__main__':
    unittest.main(verbosity=1)