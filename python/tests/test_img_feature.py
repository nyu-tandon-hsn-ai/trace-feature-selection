import unittest

from scapy.all import *
import numpy as np

import img_feature

######################################################################
#  T E S T   C A S E S
######################################################################
class TestImageFeature(unittest.TestCase):
    """ Test Cases for extracting image features """

    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def test_normal_run(self):
        """ Test if the program could run without error """
        pass

    def test_idx_img_shape(self):
        """ Test if the shape of the generated idx image file is consistent """
        pass

    def test_idx_label_shape(self):
         """ Test if the shape of the generated idx label file is consistent """
         pass


######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()