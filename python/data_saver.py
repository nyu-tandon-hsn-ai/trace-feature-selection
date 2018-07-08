class DataSaver:
    """ Save data to other formats """

    def __init__(self, filename_prefix):
        self._filename_prefix=filename_prefix
    
    @property
    def filename_prefix():
        return self._filename_prefix
    
    def _load(self, path):
        raise NotImplementedError()

    def load(self, path):
        """
        Load data from given path

        Parameter
        ---------
        path: str

        Returns
        -------
        data: `numpy.ndarray`
        """
        return self._load(path)

    def _save(self, data, path):
        raise NotImplementedError()
    
    def save(self, data, path):
        """
        Save data to given path

        Parameter
        ---------
        data: `numpy.ndarray`
        path: str
        """
        self._save(data, path)

class IdxFileSaver(DataSaver):
    """ Save data in idx format """

    def __init__(self, filename_prefix):
        super.__init__(filename_prefix)
    
    def _load(self, path):
        # TODO
        pass
    
    def _save(self, data, path):
        # TODO
        pass