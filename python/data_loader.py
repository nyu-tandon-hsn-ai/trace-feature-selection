import os
from ipaddress import IPv4Address

import numpy as np
import gzip

class DataLoader:
    def _load(self, file_path, **kwargs):
        raise NotImplementedError()

    def load(self, file_path, **kwargs):
        if not os.path.exists(file_path):
            raise AssertionError('File {} not exists'.format(file_path))
        return self._load(file_path, **kwargs)

class IdxFileLoader(DataLoader):

    def _read32(self, bytestream):
        dt = np.dtype(np.uint32).newbyteorder('>')
        return np.frombuffer(bytestream.read(4), dtype=dt)[0]

    def _load(self, file_path, **kwargs):
        assert 'gzip_compressed' in kwargs
        gzip_compressed = kwargs['gzip_compressed']
        assert gzip_compressed in [True, False]
        with gzip.open(file_path) if gzip_compressed is True else open(file_path, 'rb') as f:
            magic_numbers=f.read(4)
            assert magic_numbers[0] == 0 and magic_numbers[1] == 0
            data_type=magic_numbers[2]
            if data_type != 8:
                raise AssertionError('Only support for unsigned char now')
            shape=magic_numbers[3]
            num_samples = self._read32(f)
            dimensions = np.array([], dtype=np.int32)
            for _ in range(shape - 1):
                dimensions = np.append(dimensions, self._read32(f))
            buf = f.read(num_samples * np.prod(dimensions, dtype=np.int32))
            data = np.frombuffer(buf, dtype=np.uint8)
            data = data.reshape(np.append(num_samples, dimensions))
            return data


# from github

def extract_images(filename):
  """Extract the images into a 4D uint8 np array [index, y, x, depth]."""
  print('Extracting', filename)
  with gzip.open(filename) as bytestream:
    magic = _read32(bytestream)

    ### kc, changed magic number from 2051 to 2050
    if magic != 2051:
      raise ValueError(
          'Invalid magic number %d in MNIST image file: %s' %
          (magic, filename))
    num_images = _read32(bytestream)
    rows = _read32(bytestream)
    cols = _read32(bytestream)
    buf = bytestream.read(rows * cols * num_images)
    data = np.frombuffer(buf, dtype=np.uint8)
    data = data.reshape(num_images, rows, cols, 1)
    return data

# from test_data_saver.py

# TODO: should be tested, too
# recommended included in utils
def _read(dimensions, stream):
    if len(dimensions) == 0:
        return ord(stream.read(1))
    elif len(dimensions) == 1:
        return [val for val in stream.read(dimensions[0])]
    else:
        res = []
        for _ in range(dimensions[0]):
            res.append(_read(dimensions[1:], stream))
        return res

# TODO: should be tested, too
# recommended included in utils
# refer to gzip etc. for uncompression
def extract(idx_filename):
    """
    Extract information(image/labels) from idx file
    Parameters
    ----------
    idx_filename: str
    Returns
    -------
    list of lists/unsigned char: `np.array`
        image/label with shape designated in idx file
    """
    with open(idx_filename, 'rb') as f:
        magic_numbers=f.read(4)
        assert magic_numbers[0] == 0 and magic_numbers[1] == 0
        if magic_numbers[2] != 8:
            raise AssertionError('Only support for unsigned char now')
        data_type=magic_numbers[2]
        shape=magic_numbers[3]
        num_examples=int.from_bytes(f.read(4), byteorder='big')
        dimensions=[]
        for _ in range(shape-1):
            dimensions.append(int.from_bytes(f.read(4), byteorder='big'))
        data_list=[]
        for _ in range(num_examples):
            each_data_point=_read(dimensions, f)
            data_list.append(each_data_point)
        
    data_list = np.array(data_list)
    return data_type, shape, dimensions, num_examples, data_list

# from idx2images_labels.py

SESSION_BYTE_LEN=13

def _big_endian_bytes2int(byte_data):
    res = 0
    power = 1
    for each_byte_data in byte_data[::-1]:
        res += power * each_byte_data
        power *= 256
    return res

def _read(dimensions, stream):
    if len(dimensions) == 0:
        return ord(stream.read(1))
    elif len(dimensions) == 1:
        return [val for val in stream.read(dimensions[0])]
    else:
        res = []
        for _ in range(dimensions[0]):
            res.append(_read(dimensions[1:], stream))
        return res

def _extract_session_info(byte_data):
    assert len(byte_data) == SESSION_BYTE_LEN
    assert byte_data[0] == 0 or byte_data[0] == 1
    is_tcp = byte_data[0] == 1
    ip0 = str(IPv4Address(_big_endian_bytes2int(byte_data[1:5])))
    port0 = _big_endian_bytes2int(byte_data[5:7])
    ip1 = str(IPv4Address(_big_endian_bytes2int(byte_data[7:11])))
    port1 = _big_endian_bytes2int(byte_data[11:13])
    return {
        'protocol': 'TCP' if is_tcp else 'UDP',
        'ip0': ip0,
        'port0': port0,
        'ip1': ip1,
        'port1': port1,
    }

def extract(idx_filename):
    """
    Extract information(session, image/labels) from idx file

    Parameters
    ----------
    idx_filename: str

    Returns
    -------
    list of 2-element tuples -> [(session_info, actual_pkt_count, image/label)]
        session_info:dict
            'protocol':str, e.g. 'UDP'
            'ip0':str, e.g. '1.2.3.4'
            'port0':int, e.g. 65535
            'ip1':str, e.g. '5.6.7.8'
            'port1':int, e.g. 65534
        actual_pkt_count:int
            number of actual packet of a subflow
        image/label:`np.array`
            with shape designated in idx file
    """
    with open(idx_filename, 'rb') as f:
        magic_numbers=f.read(4)
        print('magic_number', magic_numbers)
        assert magic_numbers[0] == 0 and magic_numbers[1] == 0
        if magic_numbers[2] != 8:
            raise AssertionError('Only support for unsigned char')
        shape=magic_numbers[3]
        print('shape', shape)
        num_examples=int.from_bytes(f.read(4), byteorder='big')
        print('number of examples',num_examples)
        dimensions=[]
        for _ in range(shape-1):
            dimensions.append(int.from_bytes(f.read(4), byteorder='big'))
        print('dimensions', dimensions)
        data_list=[]
        for _ in range(num_examples):
            each_data_point=_read(dimensions, f)
            session_info=_extract_session_info(each_data_point[:SESSION_BYTE_LEN])
            actual_pkt_count = each_data_point[SESSION_BYTE_LEN]
            other_data=each_data_point[SESSION_BYTE_LEN+1:]
            data_list.append((session_info, actual_pkt_count, other_data))
        
    data_list = np.array(data_list)
    return data_list
