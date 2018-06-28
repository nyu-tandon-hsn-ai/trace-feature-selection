import numpy as np
from scapy.all import *
from array import *
import os
from tqdm import tqdm

def _ip2trans_layer_pkt_header2bytes(pkt, trans_layer_type):
    # if IP not in pkt:
    #     print("A packet without IP field:" + repr(pkt))
    #     raise AssertionError()

    # remove the packet information after transport layer header
    pkt[trans_layer_type].remove_payload()

    # TODO:
    # temporarily just omit all the options fields
    # MAYBE a better solution: fill the options field with leading/trailing 0s
    pkt[IP].options = []
    if trans_layer_type is TCP:
        pkt[trans_layer_type].options = []

    # convert binary string to bytes
    pkt_header_bin_str = raw(pkt[IP])
    pkt_header_bytes = []
    for byte in pkt_header_bin_str:
        pkt_header_bytes.append(byte)
    return pkt_header_bytes

def _calculate_inter_arri_times(arri_times):
    inter_arri_times = []
    for i in range(1, len(arri_times)):
        inter_arri_times.append(arri_times[i] - arri_times[i - 1])
    return inter_arri_times

def _normalize_to(data, from_low=None, from_high=None, to_low=None, to_high=None):
    data = np.array(data)
    if from_low is None and from_high is None:
        from_low = np.min(data)
        from_high = np.max(data)
    data = (data - from_low) / (from_high - from_low)
    # downcast here
    return (data * (to_high - to_low) + to_low).astype(np.int32)

def _layer_feat(filename, trans_layer_type, max_pkts_per_flow):
    # read pcap file
    pcap_file = rdpcap(filename)

    # get all sessions
    sessions = pcap_file.sessions()

    # store all the features
    feat = []
    for session in tqdm(sessions, desc='Session'):
        # it is only until max_pkts_per_flow number of trans_layer_type packets have been captured
        # will we continue to do things
        pkt_count = 0
        headers = []
        arri_times = []
        for pkt in sessions[session]:
            # TODO:
            # Ignore IPv6 for now
            if IP in pkt and trans_layer_type in pkt:
                headers.append(_ip2trans_layer_pkt_header2bytes(pkt, trans_layer_type))
                arri_times.append(pkt.time)
                pkt_count += 1
                if pkt_count == max_pkts_per_flow:
                    break
        if pkt_count < max_pkts_per_flow:
            continue
        elif pkt_count > max_pkts_per_flow:
            raise AssertionError()

        # flatten transport layer packet headers
        headers = np.array(headers)
        row, col = headers.shape
        headers = headers.flatten()
        assert row * col == headers.shape[0]

        # calculate inter arrival times and do normalization
        inter_arri_times = _calculate_inter_arri_times(arri_times)
        inter_arri_times = _normalize_to(inter_arri_times, to_low=0, to_high=255)

        # add inter arrival time
        feat.append(np.append(inter_arri_times, headers))
    return np.array(feat)

def _append2bin_array(bin_array, num):
    '''
    Convert num to hex format and append to bin_array
    '''
    hex_val = "{0:#0{1}x}".format(num,6) # number of img in HEX
    hex_val = '0x' + hex_val[2:].zfill(8)
    bin_array.append(int('0x'+hex_val[2:][0:2],16))
    bin_array.append(int('0x'+hex_val[2:][2:4],16))
    bin_array.append(int('0x'+hex_val[2:][4:6],16))
    bin_array.append(int('0x'+hex_val[2:][6:8],16))
    return bin_array

def _generate_idx_header(img_shape):
    '''
    Generate idx header with given img_shape
    '''
    header = array('B')
    header.extend([0,0,8,len(img_shape)])

    for shape in img_shape:
        _append2bin_array(header, shape)
    return header

def _save_idx_file(data, filename, compress=True):
    file_obj = open(filename, 'wb')
    data.tofile(file_obj)
    file_obj.close()
    if compress is True:
        os.system('gzip ' + filename)

def _generate_img_file_data(data):
    img_file_data = _generate_idx_header(data.shape)
    for img in tqdm(data, desc='Image'):
        for pixel in img:
            _append2bin_array(img_file_data, pixel)
    return img_file_data

def _generate_label_file_data(labels):
    label_file_data = _generate_idx_header(labels.shape)
    for label in tqdm(labels, desc='Label'):
        _append2bin_array(label_file_data, label)
    return label_file_data

def _save_data_labels2idx_file(data, filename_prefix, train_ratio, compress):
    # shuffle
    np.random.shuffle(data)

    # calculate number of samples used for training
    train_num = int(data.shape[0] * train_ratio)

    # unzip
    imgs, labels = list(zip(*data))
    imgs, labels = np.array(imgs), np.array(labels)

    print('image shape', imgs.shape)
    print('labels', labels.shape)

    # generate image data for training and testing
    # and save them
    train_img_file_data = _generate_img_file_data(imgs[:train_num])
    test_img_file_data = _generate_img_file_data(imgs[train_num:])
    _save_idx_file(train_img_file_data, filename_prefix+'-train'+'-images-idx{channels}-ubyte'.format(channels=len(imgs.shape)), compress)
    _save_idx_file(test_img_file_data, filename_prefix+'-test'+'-images-idx{channels}-ubyte'.format(channels=len(imgs.shape)), compress)

    # generate labels data for training and testing
    # and save them
    train_labels_file_data = _generate_label_file_data(labels[:train_num])
    test_labels_file_data = _generate_label_file_data(labels[train_num:])
    _save_idx_file(train_labels_file_data, filename_prefix+'-train'+'-labels-idx{channels}-ubyte'.format(channels=len(labels.shape)), compress)
    _save_idx_file(test_labels_file_data, filename_prefix+'-test'+'-labels-idx{channels}-ubyte'.format(channels=len(labels.shape)), compress)

def _generate_img(trans_layer_type, filenames, filename_prefix, max_pkts_per_flow, train_ratio, compress):
    '''
    Generate idx images
    '''
    img_data = None
    labels = None
    
    # for each file, extract features and labels and concatenate into img_data and labels
    trans_layer_str = 'TCP' if trans_layer_type is TCP else 'UDP' if trans_layer_type is UDP else None
    for filename in tqdm(filenames, desc=trans_layer_str):
        file_img_data = _layer_feat(filename, trans_layer_type, max_pkts_per_flow)
        if img_data is None:
            # no flow
            if file_img_data.shape[0] > 0:
                img_data = file_img_data
        else:
            # no flow
            if file_img_data.shape[0] > 0:
                img_data = np.concatenate((img_data, file_img_data))

        # 1 for vpn and 0 for non-vpn
        label = 1 if filename.lower().startswith('vpn') else 0
        for _ in range(file_img_data.shape[0]):
            if labels is None:
                labels = [label]
            else:
                labels.append(label)
        print('{filename} {trans_layer}: {data_points}'.format(filename=filename, trans_layer=trans_layer_str, data_points=file_img_data.shape[0]))
    labels = np.array(labels)

    # necessary guanratee
    assert img_data.shape[0] == labels.shape[0]

    data = np.array(list(zip(img_data, labels)))
    _save_data_labels2idx_file(data, filename_prefix, train_ratio, compress)

def tcp_img(filenames, max_pkts_per_flow, train_ratio=0.8, compress=False):
    return _generate_img(TCP, filenames, 'tcp-{pkts}pkts'.format(pkts=max_pkts_per_flow), max_pkts_per_flow, train_ratio=train_ratio, compress=compress)

def udp_img(filenames, max_pkts_per_flow, train_ratio=0.8, compress=False):
    return _generate_img(UDP, filenames, 'udp', max_pkts_per_flow, train_ratio=train_ratio, compress=compress)