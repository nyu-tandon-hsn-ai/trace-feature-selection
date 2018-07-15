import unittest
import os
import io

import numpy as np

from data_loader import DataLoader, IdxFileLoader

TEST_IDX_FILE_PATH=os.path.join('.', 'tests', 'test_data', 'test-idx')
TEST_IDX_GZ_FILE_PATH=os.path.join('.', 'tests', 'test_data', 'test-idx.gz')

######################################################################
#  T E S T   C A S E S
######################################################################
class TestDataLoader(unittest.TestCase):
    """ Test Cases for Data Loader class(es) """

    def test_data_loader(self):
        """ Test whether DataLoader class functions well """
        data_saver = DataLoader()

        with self.assertRaises(NotImplementedError):
            data_saver.load(TEST_IDX_FILE_PATH)
    
    def test_idx_file_loader(self):
        """ Test whether IdxFileLoader class functions well """

        # init
        data_loader = IdxFileLoader()
        right_answers = (8, 2, np.array([3]), 1, np.array([[  2, 112, 243]], dtype=np.uint8))
        
        # test _read_bytes
        self.assertEqual(data_loader._read_bytes(io.BytesIO(b'\x10\x20\x30\x40'), 4), 270544960)

        # test read un-zipped idx file
        for program_answer, right_answer in zip(data_loader.load(TEST_IDX_FILE_PATH, gzip_compressed=False), right_answers):
            if isinstance(right_answer, np.ndarray):
                self.assertTrue((program_answer == right_answer).all())
            else:
                self.assertEqual(program_answer, right_answer)

        # test read un-zipped idx file
        for program_answer, right_answer in zip(data_loader.load(TEST_IDX_GZ_FILE_PATH, gzip_compressed=True), right_answers):
            if isinstance(right_answer, np.ndarray):
                self.assertTrue((program_answer == right_answer).all())
            else:
                self.assertEqual(program_answer, right_answer)

######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
