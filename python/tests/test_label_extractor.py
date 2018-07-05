import unittest

from label_extractor import KeywordLabelExtractor, PositionLabelExtractor

######################################################################
#  T E S T   C A S E S
######################################################################
class TestLabelMapper(unittest.TestCase):
    """ Test Cases for Label Extractor class(es) """

    def test_keyword_label_extractor(self):
        """ Test whether KeywordLabelMapper class functions well """
        label_extractor = KeywordLabelExtractor(keyword='test')
        
        self.assertEqual(label_extractor.keyword, 'test')

    def test_pos_label_extractor(self):
        """ Test whether PosLabelMapper class functions well """
        label_extractor = PositionLabelExtractor(pos=3)
        
        self.assertEqual(label_extractor.pos, 3)
    
######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()