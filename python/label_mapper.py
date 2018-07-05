from collections import defaultdict
from copy import deepcopy

class BasicSequentialLabelMapper:
    """ Wrapper for label-related information """

    def __init__(self, name, options):
        self._name=name
        self._options=deepcopy(options)
        self._label_name2label_id=defaultdict()
        self._id_name_mapping(options)

    def _id_name_mapping(self, options):
        for label_id, label_name in enumerate(self._options):
            self._label_name2label_id[label_name]=label_id
    
    def id2name(self, label_id):
        """
            params
                label_id
            return
                a string representing the name of a Label
        """
        if label_id < 0 or label_id >= len(self._options):
            raise AssertionError('Illegal label id {label_id}'.format(label_id=label_id))
        return self._options[label_id]
    
    def name2id(self, label_name):
        """
            params
                label_name
            return
                a number representing the labe id
        """
        if label_name not in self._label_name2label_id.keys():
            raise AssertionError('Unknown label name {label_name}'.format(label_name=label_name))
        return self._label_name2label_id[label_name]
    
    @property
    def name(self):
        return self._name