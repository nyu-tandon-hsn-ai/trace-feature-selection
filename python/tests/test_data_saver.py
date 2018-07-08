import unittest

from data_saver import DataSaver

######################################################################
#  T E S T   C A S E S
######################################################################
class TestDataSaver(unittest.TestCase):
    """ Test Cases for Data Saver class(es) """

    def test_data_saver(self):
        """ Test whether DataSaver class functions well """
        data_saver = DataSaver()
        
        # TODO
        data_saver.save('nothing')
        data_saver.load('nothing')
    
######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
