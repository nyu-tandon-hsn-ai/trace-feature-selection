from collections import defaultdict
from copy import deepcopy

from utils import assert_lowercase

class LabelMapper:
    """ Deal with the mapping things of labels """

    def __init__(self, options):
        self._options=deepcopy(options)
        assert_lowercase(options)
        self._label_name2label_id=defaultdict()
        self._id_name_mapping(options)

    def _id_name_mapping(self, options):
        """
        should be overrided by sub-classes
        """
        raise NotImplementedError()
    
    def id2name(self, label_id):
        """
            @params
                label_id
            @return
                a string representing the name of a Label
        """
        if label_id < 0 or label_id >= len(self._options):
            raise AssertionError('Illegal label id {label_id}'.format(label_id=label_id))
        return self._options[label_id]
    
    def name2id(self, label_name):
        """
            @params
                label_name
            @return
                a number representing the labe id
        """
        if label_name not in self._label_name2label_id.keys():
            raise AssertionError('Unknown label name {label_name}'.format(label_name=label_name))
        return self._label_name2label_id[label_name]

class SequentialLabelMapper(LabelMapper):
    """ Mapping the label in a sequential manner """
    
    def __init__(self, options):
        super().__init__(options)

    def _id_name_mapping(self, options):
        for label_id, label_name in enumerate(self._options):
            self._label_name2label_id[label_name]=label_id

class BinaryLabelMapper(SequentialLabelMapper):
    """ Mapping the label in a sequential manner """
    
    def __init__(self, positive_option):
        super().__init__(options=[None, positive_option])