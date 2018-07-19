import os
from copy import deepcopy
import multiprocessing
from itertools import product
from functools import partial

import numpy as np
from scapy.all import *
from tqdm import tqdm

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

def extract_flow_img_from_single_trace_file(img_feature_extractor, label_mapper, label_extractor,
                trace_filename, trans_layer_type):
    # extract base filename
    base_name = os.path.basename(trace_filename).lower()

    # extract label from filename
    label = label_mapper.name2id(label_extractor.extract(base_name, label_mapper.options))

    # necessary assertion
    assert label is not None

    # calculate
    images = img_feature_extractor.extract_flow_img(trace_filename, trans_layer_type)

    return images, np.repeat(label, images.shape[0]), stringify_protocol(trans_layer_type)

def extract(trace_filenames, label_mapper, label_extractor, img_feature_extractor, parallel=False):
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
    images, labels = np.array([], dtype=np.int32), np.array([], np.int32)
    trans_flows = {stringify_protocol(TCP):0, stringify_protocol(UDP):0}

    # init parallel arguments
    parallel_args = [(item[0], item[1]) for item in product(trace_filenames, [TCP, UDP])]

    if parallel is True:
        # get number of cpus available to job
        # NOW just a fixed number as the memory would explode otherwise
        # try:
        #     ncpus = int(os.environ["SLURM_JOB_CPUS_PER_NODE"])
        # except KeyError:
        #     ncpus = multiprocessing.cpu_count()
        ncpus = 4

        # create pool of ncpus workers
        p = multiprocessing.Pool(ncpus)

        # mapping phase: apply work function in parallel
        res = p.starmap(partial(extract_flow_img_from_single_trace_file,
                                img_feature_extractor,
                                label_mapper,
                                label_extractor), parallel_args)
    else:
        res = []
        for trace_filename, trans_layer_type in tqdm(parallel_args, desc='Sequential'):
            res.append(extract_flow_img_from_single_trace_file(
                                img_feature_extractor,
                                label_mapper,
                                label_extractor,
                                trace_filename,
                                trans_layer_type))

    # reduce phase: concatenate, do stats
    for single_tracefile_images, single_tracefile_labels, trans_layer_name in res:
        images = np.concatenate([images, single_tracefile_images]) if images.size > 0 and single_tracefile_images.size > 0 else \
                        single_tracefile_images if single_tracefile_images.size > 0 else images
        labels = np.concatenate([labels, single_tracefile_labels]) if labels.size > 0 and single_tracefile_labels.size > 0 else \
                        single_tracefile_labels if single_tracefile_labels.size > 0 else labels
    
        # do stats
        trans_flows[trans_layer_name] += single_tracefile_labels.shape[0]

    # print stats
    print('Raw TCP/UDP distribution', trans_flows)

    # necessary guanratee
    assert images.shape[0] == labels.shape[0]

    # generate dataset
    data = {'images':images, 'labels':labels}

    return data