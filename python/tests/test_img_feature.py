from scapy.all import *
import numpy as np
from importlib import reload
import img_feature
from os import listdir
from os.path import isfile, join, isdir

import unittest
import glob
import os
import sys
import filecmp
from functools import partial

######################################################################
#  T E S T   C A S E S
######################################################################
class TestImageFeature(unittest.TestCase):
    """ Test Cases for extracting image features """

    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def test_label_class(self):
        """ Test whether Label class functions well """
        label = img_feature.Label(name='Test', options=['Test1','Test2'])

        self.assertEqual(label.name, 'Test')

        self.assertEqual(label.id2name(0), 'Test1')
        self.assertEqual(label.id2name(1), 'Test2')
        with self.assertRaises(AssertionError):
            label.id2name(2)
        with self.assertRaises(AssertionError):
            label.id2name(-1)

        self.assertEqual(label.name2id('Test1'), 0)
        self.assertEqual(label.name2id('Test2'), 1)
        with self.assertRaises(AssertionError) as err:
            label.name2id('Test3')
    
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