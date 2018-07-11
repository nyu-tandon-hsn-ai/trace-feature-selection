import unittest

from label.extractor import StartPositionLabelExtractor

######################################################################
#  T E S T   C A S E S
######################################################################
class TestLabelMapper(unittest.TestCase):
    """ Test Cases for Label Extractor class(es) """

    def test_pos_label_extractor(self):
        """ Test whether StartPositionLabelExtractor class functions well """
        test_positions=[len('facebook'),len('facebook_')]
        label_extractor = StartPositionLabelExtractor(positions=test_positions)
        
        self.assertIsNot(label_extractor.positions, test_positions)
        
        self.assertEqual(label_extractor.positions, sorted(test_positions, reverse=True))

        self.assertEqual(label_extractor.contains_label_name('facebook_chat.pcapng', ['audio','chat']), 'chat')
        self.assertEqual(label_extractor.contains_label_name('facebookaudio.pcapng', ['video','audio']), 'audio')
        self.assertEqual(label_extractor.contains_label_name('skype_file.pcapng', ['file','audio']), None)
    
######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()