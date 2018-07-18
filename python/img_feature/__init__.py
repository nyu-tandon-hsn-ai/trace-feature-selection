from array import *
from collections import Counter
import os
from copy import deepcopy

import numpy as np
from tqdm import tqdm
from scapy.all import *

from dataset.utils import balance_data, train_test_split

def stringify_protocol(protocol):
    if protocol is TCP:
        return 'TCP'
    elif protocol is UDP:
        return 'UDP'
    else:
        raise AssertionError('Protocol {} unsupported yet'.format(protocol))

def calculate_inter_arri_times(arri_times):
    inter_arri_times = []
    for i in range(1, len(arri_times)):
        inter_arri_times.append(arri_times[i] - arri_times[i - 1])
    return inter_arri_times

def extract(trace_filenames, label_mapper, label_extractor, img_feature_extractor, **kwargs):
    '''
    Extract image features and labels

    Parameters
    ----------
    trace_filenames: [str]
    label_mapper: `label.mapper.LabelMapper`
    label_extractor: `label.extractor.LabelExtractor`
    img_feature_extractor: `img_feature.Extractor`

    Returns
    -------
    dict:{images: `numpy.ndarray`, labels: `numpy.ndarray`}
    '''

    # init things
    imgs, labels = [], []
    trans_flows = {stringify_protocol(TCP):0, stringify_protocol(UDP):0}

    # extract the image and label data of each file and concatenate w/ do stats
    for trace_filename in tqdm(trace_filenames, desc='Processing Trace'):
        # extract base filename
        base_name = os.path.basename(trace_filename).lower()

        # extract label from filename
        label = label_mapper.name2id(label_extractor.extract(base_name, label_mapper.options))

        # necessary assertion
        assert label is not None

        # extract both TCP and UDP flow image
        for trans_layer_type in [TCP, UDP]:
            # calculate
            img = img_feature_extractor.extract_flow_img(trace_filename, trans_layer_type, **kwargs)

            # concatenate
            imgs.extend(img)
            labels.extend([label] * img.shape[0])

            # do stats
            trans_layer_str = stringify_protocol(trans_layer_type)
            trans_flows[trans_layer_str] += img.shape[0]

    # print stats
    print('Raw TCP/UDP distribution', trans_flows)

    # convert to numpy
    imgs, labels = np.array(imgs, dtype=np.int32), np.array(labels, dtype=np.int32)

    # necessary guanratee
    assert imgs.shape[0] == labels.shape[0]

    # generate dataset
    data = {'images':imgs, 'labels':labels}

    return data