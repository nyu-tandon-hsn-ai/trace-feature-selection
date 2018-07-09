import unittest
from array import array
import os
import shutil

import numpy as np

from data_saver import DataSaver, IdxFileSaver

DATA_SAVER_TEST_DIR=os.path.join('.', 'tests', 'test_data', 'test_idx_file_saver')

def _read(dimensions, stream):
    if len(dimensions) == 0:
        return ord(stream.read(1))
    elif len(dimensions) == 1:
        return [val for val in stream.read(dimensions[0])]
    else:
        res = []
        for _ in range(dimensions[0]):
            res.append(_read(dimensions[1:], stream))
        return res

def extract(idx_filename):
    """
    Extract information(image/labels) from idx file
    Parameters
    ----------
    idx_filename: str
    Returns
    -------
    list of lists/unsigned char: `numpy.array`
        image/label with shape designated in idx file
    """
    with open(idx_filename, 'rb') as f:
        magic_numbers=f.read(4)
        assert magic_numbers[0] == 0 and magic_numbers[1] == 0
        if magic_numbers[2] != 8:
            raise AssertionError('Only support for unsigned char now')
        data_type=magic_numbers[2]
        shape=magic_numbers[3]
        num_examples=int.from_bytes(f.read(4), byteorder='big')
        dimensions=[]
        for _ in range(shape-1):
            dimensions.append(int.from_bytes(f.read(4), byteorder='big'))
        data_list=[]
        for _ in range(num_examples):
            each_data_point=_read(dimensions, f)
            data_list.append(each_data_point)
        
    data_list = np.array(data_list)
    return data_type, shape, dimensions, num_examples, data_list

######################################################################
#  T E S T   C A S E S
######################################################################
class TestDataSaver(unittest.TestCase):
    """ Test Cases for Data Saver class(es) """

    def _delete_data_dirs(self):
        if os.path.exists(DATA_SAVER_TEST_DIR):
            shutil.rmtree(DATA_SAVER_TEST_DIR)

    def setUp(self):
        self._delete_data_dirs()

    def tearDown(self):
        self._delete_data_dirs()

    def test_data_saver(self):
        """ Test whether DataSaver class functions well """
        data_saver = DataSaver(DATA_SAVER_TEST_DIR)
        
        self.assertEqual(data_saver.folder, DATA_SAVER_TEST_DIR)
        with self.assertRaises(NotImplementedError):
            data_saver.save(np.array([1,2,3]), 'nothing')
            data_saver.load('nothing')
    
    def test_idx_file_saver(self):
        """ Test whether IdxFileSaver class functions well """
        data_saver = IdxFileSaver(DATA_SAVER_TEST_DIR)
        
        self.assertEqual(data_saver.folder, os.path.join('.', 'tests', 'test_data', 'test_idx_file_saver'))

        self.assertEqual(data_saver._flatten(np.array([1,2,3])), [1,2,3])
        self.assertEqual(data_saver._flatten(np.array([[1,2,3],[4,5,6]])), [1,2,3,4,5,6])

        self.assertEqual(data_saver._generate_idx_header([65535]), [0,0,8,1,0,0,255,255])
        self.assertEqual(data_saver._generate_idx_header([256,65535]), [0,0,8,2,0,0,1,0,0,0,255,255])
        with self.assertRaises(ValueError):
            data_saver._generate_idx_header([0 for _ in range(256)])
        with self.assertRaises(NotImplementedError):
            data_saver._generate_idx_header([1], 10)
        
        test1d=[255 for _ in range(256)]
        test2d=[[255 for _ in range(258)] for _ in range(256)]
        self.assertEqual(data_saver._add_header_and_convert2bin(np.array(test1d)), array('B', [0,0,8,1,0,0,1,0]+[255]*256))
        self.assertEqual(data_saver._add_header_and_convert2bin(np.array(test2d)), array('B', [0,0,8,2,0,0,1,0,0,0,1,2]+[255]*256*258))

        saving_pathname=data_saver.save(np.array(test1d), filename_prefix='test1d')
        data_type, shape, dimensions, num_examples, data_list=extract(saving_pathname)
        self.assertEqual(data_type, 8)
        self.assertEqual(shape, 1)
        self.assertEqual(dimensions, [])
        self.assertEqual(num_examples, len(test1d))
        self.assertTrue((data_list == test1d).all())

        self._delete_data_dirs()

        saving_pathname=data_saver.save(np.array(test2d), filename_prefix='test2d')
        data_type, shape, dimensions, num_examples, data_list=extract(saving_pathname)
        self.assertEqual(data_type, 8)
        self.assertEqual(shape, 2)
        self.assertEqual(dimensions, [len(test2d[0])])
        self.assertEqual(num_examples, len(test2d))
        self.assertTrue((data_list == test2d).all())
    
######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
