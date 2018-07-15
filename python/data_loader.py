import os
from ipaddress import IPv4Address
import gzip

import numpy as np

class DataLoader:
    """ Load data """
    def _load(self, file_path, **kwargs):
        """ Should be overriden by sub-classes """
        raise NotImplementedError()

    def load(self, file_path, **kwargs):
        if not os.path.exists(file_path):
            raise AssertionError('File {} not exists'.format(file_path))
        return self._load(file_path, **kwargs)

class IdxFileLoader(DataLoader):
    """ Load idx format data """

    def _read_bytes(self, byte_stream, num_byte):
        """ read n bytes from byte stream into a big endian integer """
        dt = np.dtype(np.uint32).newbyteorder('>')
        return np.frombuffer(byte_stream.read(num_byte), dtype=dt)[0]

    def _load(self, file_path, **kwargs):
        # need this fileld
        assert 'gzip_compressed' in kwargs
        gzip_compressed = kwargs['gzip_compressed']
        assert gzip_compressed in [True, False]

        # according to the value of gzip_compressed, utilize different stream
        with gzip.open(file_path) if gzip_compressed is True else open(file_path, 'rb') as f:
            # read magic number and do assertion
            magic_numbers=f.read(4)
            assert magic_numbers[0] == 0 and magic_numbers[1] == 0
            data_type=magic_numbers[2]
            if data_type != 8:
                raise AssertionError('Only support for unsigned char now')

            # extract shape
            shape=magic_numbers[3]

            # extract number of samples
            num_samples = self._read_bytes(f, 4)

            # extract dimensions
            dimensions = np.array([], dtype=np.int32)
            for _ in range(shape - 1):
                dimensions = np.append(dimensions, self._read_bytes(f, 4))
            
            # read data
            buf = f.read(num_samples * np.prod(dimensions, dtype=np.int32))

            # assert this is the end of data
            assert f.read() == b''

            # read from buffer
            data = np.frombuffer(buf, dtype=np.uint8)

            # assert enough data are read
            assert len(data.shape) == 1 and data.shape[0] == num_samples * np.prod(dimensions, dtype=np.int32)

            # reshape data
            data = data.reshape(np.append(num_samples, dimensions))
            return data_type, shape, dimensions, num_samples, data
