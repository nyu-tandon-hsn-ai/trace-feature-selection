from utils import assert_lowercase

class LabelExtractor:
    """ Extract label name from specified string """
    

    def _extract_label_name(self, raw_str):
        """
            should be overrided by sub-classes
        """
        raise NotImplementedError()

    def extract_label_name(self, raw_str):
        """
            @params
                raw_str: extract label name from this str
            @return
                label name extracted from this string
            @raise
                AssertionError: if no label name could be extracted from this string
        """
        return self._extract_label_name(raw_str)

class PositionLabelExtractor(LabelExtractor):
    """ Extract label name from specified string by position """

    def __init__(self, pos):
        self._pos=pos

    @property
    def pos(self):
        return self._pos

class KeywordLabelExtractor(LabelExtractor):
    """ Extract label name from specified string using keyword """

    def __init__(self, keyword):
        assert_lowercase(keyword)
        self._keyword=keyword
    
    @property
    def keyword(self):
        return self._keyword