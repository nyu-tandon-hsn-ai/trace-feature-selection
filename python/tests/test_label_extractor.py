import unittest

from label_extractor import StartPositionLabelExtractor

######################################################################
#  T E S T   C A S E S
######################################################################
class TestLabelMapper(unittest.TestCase):
    """ Test Cases for Label Extractor class(es) """

    def test_pos_label_extractor(self):
        """ Test whether StartPositionLabelExtractor class functions well """
        label_extractor = StartPositionLabelExtractor(positions=[8,9])
        
        self.assertEqual(label_extractor.positions, [9,8])

        self.assertEqual(label_extractor.contains_label_name('facebook_chat.pcapng', ['audio','chat']), 'chat')
        self.assertEqual(label_extractor.contains_label_name('facebookaudio.pcapng', ['video','audio']), 'audio')
        self.assertEqual(label_extractor.contains_label_name('skype_file.pcapng', ['file','audio']), None)
    
######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()