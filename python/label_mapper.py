from collections import defaultdict
from copy import deepcopy

from utils import assert_lowercase

class LabelMapper:
    """ Deal with the mapping things of labels """

    def __init__(self, options):
        self._options=deepcopy(options)
        assert_lowercase(options)
        self._label_name2label_id=defaultdict()
        self._id_name_mapping()

    def _id_name_mapping(self):
        """
        should be overrided by sub-classes
        """
        raise NotImplementedError()
    
    def _id2name(self, label_id):
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
        return self._id2name(label_id)
    
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

    @property
    def options(self):
        return self._options

class SequentialLabelMapper(LabelMapper):
    """ Mapping the label in a sequential manner """
    
    def __init__(self, options):
        super().__init__(options)

    def _id_name_mapping(self):
        for label_id, label_name in enumerate(self._options):
            self._label_name2label_id[label_name]=label_id
    
    def _id2name(self, label_id):
        if label_id < 0 or label_id >= len(self._options):
            raise AssertionError(
                'Illegal label id {label_id}, should be in range {min_range}-{max_range}'.format(
                    min_range=0,
                    max_range=len(self._options),
                    label_id=label_id))
        return self._options[label_id]

class BinaryLabelMapper(LabelMapper):
    """ Mapping the label in a sequential manner """
    
    def __init__(self, positive_option):
        super().__init__(options=[positive_option])
        assert positive_option==self._positive_option
    
    def _id_name_mapping(self):
        assert 1 == len(self._options)
        self._positive_option=self._options[0]
        self._label_name2label_id[None]=0
        self._label_name2label_id[self._positive_option]=1
    
    def _id2name(self, label_id):
        if label_id not in [0,1]:
            raise AssertionError('Illegal labe id {label_id}, should be in [0,1]'.format(label_id=label_id))
        return None if label_id == 0 else self._positive_option