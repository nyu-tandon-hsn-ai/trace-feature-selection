from array import array

from tqdm import tqdm

class DataSaver:
    """ Save data to other formats """

    def __init__(self, filename_prefix):
        self._filename_prefix=filename_prefix
    
    @property
    def filename_prefix(self):
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
        super().__init__(filename_prefix)
    
    def _flatten(self, data):
        if len(data.shape) == 0:
            return [int(data)]
        else:
            res = []
            for datum in data:
                res.extend(self._flatten(datum))
            return res
    
    def _generate_idx_header(self, data_shape, data_type=8):
        '''
        Generate idx header with given shape
        '''
        if len(data_shape) >= 256:
            raise ValueError('the dimension of data_shape should be in range 0-255, but {dimension} found'.format(dimension=len(data_shape)))
        if data_type != 8:
            raise NotImplementedError('Only support unsigned character type only for now')
        header = [0,0,data_type,len(data_shape)]

        for shape in data_shape:
            header.extend(shape.to_bytes(4, byteorder='big'))
        return header
    
    def _transform2binary(self, data, desc=None):
        bin_data = array('B')
        bin_data.extend(self._generate_idx_header(data.shape))
        for datum in tqdm(data, desc):
            bin_data.extend(self._flatten(datum))
        return bin_data
    
    def _load(self, path):
        # TODO
        pass
    
    def _save(self, data, path):
        # TODO
        pass