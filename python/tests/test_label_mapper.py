import unittest

from label_mapper import SequentialLabelMapper

######################################################################
#  T E S T   C A S E S
######################################################################
class TestLabelMapper(unittest.TestCase):
    """ Test Cases for Label Mapper class(es) """

    def test_seq_label_mapper(self):
        """ Test whether SequentialLabelMapper class functions well """
        label_mapper = SequentialLabelMapper(options=['test1','test2'])

        self.assertEqual(label_mapper.id2name(0), 'test1')
        self.assertEqual(label_mapper.id2name(1), 'test2')
        with self.assertRaises(AssertionError):
            label_mapper.id2name(2)
        with self.assertRaises(AssertionError):
            label_mapper.id2name(-1)

        self.assertEqual(label_mapper.name2id('test1'), 0)
        self.assertEqual(label_mapper.name2id('test2'), 1)
        with self.assertRaises(AssertionError) as err:
            label_mapper.name2id('test3')
    
######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()