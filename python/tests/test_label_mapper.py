import unittest

from label.mapper import SequentialLabelMapper, BinaryLabelMapper

######################################################################
#  T E S T   C A S E S
######################################################################
class TestLabelMapper(unittest.TestCase):
    """ Test Cases for Label Mapper class(es) """

    def test_seq_label_mapper(self):
        """ Test whether SequentialLabelMapper class functions well """
        test_options=['test1','test2']
        label_mapper = SequentialLabelMapper(options=test_options)

        self.assertEqual(str(label_mapper), '{{{option1}:0, {option2}:1}}'.format(
            option1=test_options[0], option2=test_options[1]))

        self.assertEqual(test_options, label_mapper.options)
        self.assertIsNot(test_options, label_mapper.options)

        self.assertEqual(label_mapper.id2name(0), test_options[0])
        self.assertEqual(label_mapper.id2name(1), test_options[1])
        with self.assertRaises(AssertionError):
            label_mapper.id2name(2)
        with self.assertRaises(AssertionError):
            label_mapper.id2name(-1)

        self.assertEqual(label_mapper.name2id(test_options[0]), 0)
        self.assertEqual(label_mapper.name2id(test_options[1]), 1)
        with self.assertRaises(AssertionError):
            label_mapper.name2id('test3')
    
    def test_bin_label_mapper(self):
        """ Test whether BinaryLabelMapper class functions well """
        positive_option='test'
        label_mapper = BinaryLabelMapper(positive_option=positive_option)

        self.assertEqual(str(label_mapper), '{{{negative_option}:0, {positive_option}:1}}'.format(
            negative_option='non-'+positive_option, positive_option=positive_option))

        self.assertEqual(label_mapper.id2name(0), None)
        self.assertEqual(label_mapper.id2name(1), positive_option)
        with self.assertRaises(AssertionError):
            label_mapper.id2name(2)
        with self.assertRaises(AssertionError):
            label_mapper.id2name(-1)

        self.assertEqual(label_mapper.name2id(None), 0)
        self.assertEqual(label_mapper.name2id(positive_option), 1)
        with self.assertRaises(AssertionError):
            label_mapper.name2id('test-again')
    
######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()