from scapy.all import *
import numpy as np
from importlib import reload
import img_feature
from os import listdir
from os.path import isfile, join, isdir

def test_img(filenames, max_pkts_per_flow, compress=False, label_type='vpn'):
    import img_feature
    reload(img_feature)
    img_feature.img(filenames,
                    max_pkts_per_flow=max_pkts_per_flow,
                    compress=compress,
                    label_type=label_type)

def test_label(filenames, asserted_label):
    for filename in filenames:
        with open(filename,'rb') as f:
            f.read(8)
            new_bytes = f.read(4)
            while len(new_bytes) > 0:
                label = int(new_bytes[0]) * 16 * 16 * 16 + int(new_bytes[1]) * 16 * 16 + int(new_bytes[2]) * 16 + int(new_bytes[3])
                assert label == asserted_label
                new_bytes = f.read(4)

def test_shape(filenames, asserted_shape):
    for filename in filenames:
        with open(filename,'rb') as f:
            f.read(8)
            new_bytes = f.read(4)
            shape = int(new_bytes[0]) * 16 * 16 * 16 + int(new_bytes[1]) * 16 * 16 + int(new_bytes[2]) * 16 + int(new_bytes[3])
            assert shape == asserted_shape

def test_type(path, types):
    assert isdir(path)
    filenames = [f for f in listdir(path) if isfile(join(path, f))]
    for filename in filenames:
        assert any(map(filename.lower().startswith, types))