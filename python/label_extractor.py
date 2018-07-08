from copy import deepcopy

import numpy as np

class LabelExtractor:
    """ Extract label name from specified string """

    def _contains_label_name(self, raw_str, label_names):
        """
            should be overrided by sub-classes
        """
        raise NotImplementedError()

    def contains_label_name(self, raw_str, label_names):
        """
            @params
                raw_str: extract label name from this str
            @return
                label name extracted from this string or
                None if no such label in this string
        """
        return self._contains_label_name(raw_str, label_names)

class StartPositionLabelExtractor(LabelExtractor):
    """ Extract label name from specified string by position """

    def __init__(self, positions):
        super().__init__()
        self._positions=deepcopy(positions)
        self._positions.sort(reverse=True)

    @property
    def positions(self):
        return self._positions
    
    def _contains_label_name(self, raw_str, label_names):
        res=[False for _ in range(len(label_names))]
        lower_str=raw_str.lower()
        for position in self._positions:
            for i, label_name in enumerate(label_names):
                res[i]=res[i] or lower_str[position:].startswith(label_name)
            if any(res):
                return label_names[np.argmax(res)]
        return None