import unittest

from utils import assert_lowercase, assert_all_different, normalize_to

######################################################################
#  T E S T   C A S E S
######################################################################
class TestUtils(unittest.TestCase):
    """ Test Cases for utility functions """

    def test_assert_lowercase(self):
        """ Test the normal functionality of assert_lowercase """
        with self.assertRaises(AssertionError):
            assert_lowercase(['aA', 'bB'])
        self.assertIsNone(assert_lowercase(['ac', 'bd']))
        self.assertIsNone(assert_lowercase(['a-c', 'b-d']))
    
    def test_assert_all_different(self):
        """ Test the normal functionality of assert_all_different """
        non_duplicate_vals=['test1', 'test2']
        self.assertIsNone(assert_all_different(non_duplicate_vals))

        duplicate_vals=['test', 'test', 'test-prime']
        with self.assertRaises(AssertionError):
            assert_all_different(duplicate_vals)
    
    def test_normalize_to(self):
        """ Test if normalize_to() functions well """

        data = [1.0, 3.0, 2.0]
        self.assertTrue((normalize_to(data, 0, 255) == [0, 255, 127]).all())

        data = [1.0]
        self.assertTrue((normalize_to(data, 0, 255) == [0]).all())

    
######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()