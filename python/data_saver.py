from array import array
import os, errno

from tqdm import tqdm

class DataSaver:
    """ Save data to other file formats """

    def __init__(self, folder):
        self._folder=folder
    
    @property
    def folder(self):
        return self._folder

    def _save(self, data, filename_prefix):
        raise NotImplementedError()
    
    def save(self, data, filename_prefix):
        """
        Save data to `self.folder` with filename prefix `filename_prefix`

        Parameter
        ---------
        data: `numpy.ndarray`
        filename_prefix: str

        Returns
        -------
        str
            full pathname where the data is saved
        """
        if not os.path.exists(self._folder):
            # make directories
            try:
                os.makedirs(self._folder)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise e
        return self._save(data, filename_prefix)

class IdxFileSaver(DataSaver):
    """ Save data in idx format """

    def __init__(self, folder, compress_file=False):
        super().__init__(folder)
        self._compress_file=compress_file
    
    @property
    def compress_file(self):
        return self._compress_file
    
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
    
    def _add_header_and_convert2bin(self, data, desc=None):
        bin_data = array('B')
        bin_data.extend(self._generate_idx_header(data.shape))
        for datum in tqdm(data, desc):
            bin_data.extend(self._flatten(datum))
        return bin_data
    
    def _save(self, data, filename_prefix):
        # concatenate filename
        filename=filename_prefix+'-idx{channels}-ubyte'.format(channels=len(data.shape))

        # concatenate filename with folder name
        full_pathname=os.path.join(self._folder, filename)

        # convert to idx-format data
        data=self._add_header_and_convert2bin(data, desc=filename_prefix)

        # open file and write data
        with open(full_pathname, 'wb') as f:
            data.tofile(f)

        if self._compress_file is True:
            os.system('gzip ' + full_pathname)
            return full_pathname+'.gz'
        else:
            return full_pathname