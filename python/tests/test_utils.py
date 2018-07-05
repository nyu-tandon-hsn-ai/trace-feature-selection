import unittest

from utils import assert_lowercase

######################################################################
#  T E S T   C A S E S
######################################################################
class TestUtils(unittest.TestCase):
    """ Test Cases for utility functions """

    def test_assert_lowercase(self):
        """ Test the normal functionality of assert_lowercase """
        with self.assertRaises(AssertionError):
            assert_lowercase(['aA', 'bB'])
        self.assertEqual(assert_lowercase(['ac', 'bd']), None)
        self.assertEqual(assert_lowercase(['a-c', 'b-d']), None)
    
######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()