import unittest

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

        #TODO: other function calls
    
######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
