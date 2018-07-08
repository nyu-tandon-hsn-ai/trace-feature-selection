import unittest
from array import array

import numpy as np

from data_saver import DataSaver, IdxFileSaver

######################################################################
#  T E S T   C A S E S
######################################################################
class TestDataSaver(unittest.TestCase):
    """ Test Cases for Data Saver class(es) """

    def test_data_saver(self):
        """ Test whether DataSaver class functions well """
        data_saver = DataSaver('test')
        
        self.assertEqual(data_saver.filename_prefix, 'test')
        with self.assertRaises(NotImplementedError):
            data_saver.save(np.array([1,2,3]), 'nothing')
            data_saver.load('nothing')
    
    def test_idx_file_saver(self):
        """ Test whether IdxFileSaver class functions well """
        data_saver = IdxFileSaver('test')
        
        self.assertEqual(data_saver.filename_prefix, 'test')

        self.assertEqual(data_saver._flatten(np.array([1,2,3])), [1,2,3])
        self.assertEqual(data_saver._flatten(np.array([[1,2,3],[4,5,6]])), [1,2,3,4,5,6])

        self.assertEqual(data_saver._generate_idx_header([65535]), [0,0,8,1,0,0,255,255])
        self.assertEqual(data_saver._generate_idx_header([256,65535]), [0,0,8,2,0,0,1,0,0,0,255,255])
        with self.assertRaises(ValueError):
            data_saver._generate_idx_header([0 for _ in range(256)])
        with self.assertRaises(NotImplementedError):
            data_saver._generate_idx_header([1], 10)
        
        self.assertEqual(data_saver._transform2binary(np.array([255 for _ in range(256)])), array('B', [0,0,8,1,0,0,1,0]+[255]*256))
        self.assertEqual(data_saver._transform2binary(np.array([[255 for _ in range(256)] for _ in range(256)])), array('B', [0,0,8,2,0,0,1,0,0,0,1,0]+[255]*256*256))
        #TODO: other function calls
    
######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
