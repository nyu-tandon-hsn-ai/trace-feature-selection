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
            new_bytes = f.read(1)
            while len(new_bytes) > 0:
                label = int(new_bytes[0])
                assert label == asserted_label
                new_bytes = f.read(1)

def get_label_stat(filename):
    with open(filename,'rb') as f:
        f.read(4)
        new_bytes = f.read(4)
        n = int(new_bytes[0]) * 256 * 256 * 256 + int(new_bytes[1]) * 256 * 256 + int(new_bytes[2]) * 256 + int(new_bytes[3])
        label_stat={}
        new_bytes = f.read(1)
        for _ in range(n):
            label = int(new_bytes[0])
            if label in label_stat:
                label_stat[label] += 1
            else:
                label_stat[label] = 1
            new_bytes = f.read(1)
    return label_stat

def test_shape(filenames, asserted_shape):
    for filename in filenames:
        with open(filename,'rb') as f:
            f.read(8)
            new_bytes = f.read(4)
            shape = int(new_bytes[0]) * 256 * 256 * 256 + int(new_bytes[1]) * 256 * 256 + int(new_bytes[2]) * 256 + int(new_bytes[3])
            assert shape == asserted_shape

def test_type(path, types):
    assert isdir(path)
    filenames = [f for f in listdir(path) if isfile(join(path, f))]
    for filename in filenames:
        assert any(map(filename.lower().startswith, types))