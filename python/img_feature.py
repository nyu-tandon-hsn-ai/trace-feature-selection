from array import *
from collections import defaultdict
import os
from collections import Counter

import numpy as np
from tqdm import tqdm
from scapy.all import *

from session_info import extract_session_info
from dataset.utils import balance_data, train_test_split

IP2TCP_HEADER_LEN = 40
PAYLOAD = 20

def _ip2trans_layer_pkt_header2bytes(pkt, trans_layer_type):
    # TODO:
    # temporarily just omit all the options fields
    # MAYBE a better solution: fill the options field with leading/trailing 0s
    pkt[IP].options = []
    if trans_layer_type is TCP:
        pkt[trans_layer_type].options = []

    # remove/pad the payload in transport layer header
    trans_bin_str = raw(pkt[trans_layer_type])
    pkt[IP].remove_payload()
    while len(pkt[IP]) + len(trans_bin_str) < IP2TCP_HEADER_LEN + PAYLOAD:
        trans_bin_str = trans_bin_str + b'\x00'
    trans_bin_str = trans_bin_str[:IP2TCP_HEADER_LEN + PAYLOAD - len(pkt[IP])]

    # convert binary string to bytes
    pkt_header_bin_str = raw(pkt[IP])
    pkt_header_bytes = []
    for byte in pkt_header_bin_str + trans_bin_str:
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
    # TODO?
    if max_pkts_per_flow >= 256:
        raise AssertionError('packet count field exceeded 1 byte long')
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
        # there should be at least one packet in a flow
        if pkt_count <= 0:
            continue
        if pkt_count > max_pkts_per_flow:
            raise AssertionError()

        # extract session info
        if session == 'Other':
            assert len(sessions[session]) > 0
            f_pkt= None
            for pkt in sessions[session]:
                if IP in pkt and trans_layer_type in pkt:
                    f_pkt=pkt
            if f_pkt is None:
                raise AssertionError()
            
            trans_layer_str=None
            if trans_layer_type is TCP:
                trans_layer_str='TCP'
            elif trans_layer_type is UDP:
                trans_layer_str='UDP'
            else:
                raise AssertionError()
            session='{protocol} {ip0}:{port0} > {ip1}:{port1}'.format(
                protocol=trans_layer_str,
                ip0=f_pkt[IP].src,
                ip1=f_pkt[IP].dst,
                port0=f_pkt[trans_layer_type].sport,
                port1=f_pkt[trans_layer_type].dport
            )
        sess_info = extract_session_info(session)
        sess_info_vals=[int(sess_info['is_tcp'])]
        sess_info_vals.extend((sess_info['ip0']).to_bytes(4, byteorder='big'))
        sess_info_vals.extend((sess_info['port0']).to_bytes(2, byteorder='big'))
        sess_info_vals.extend((sess_info['ip1']).to_bytes(4, byteorder='big'))
        sess_info_vals.extend((sess_info['port1']).to_bytes(2, byteorder='big'))

        # flatten transport layer packet headers
        headers = np.array(headers)
        row, col = headers.shape
        headers = headers.flatten()
        assert row * col == headers.shape[0]

        # append 0 to the end of headers and payloads to align
        if pkt_count < max_pkts_per_flow:
            headers=np.append(headers, [0] * ((max_pkts_per_flow-pkt_count) * (IP2TCP_HEADER_LEN + PAYLOAD)))

        # calculate inter arrival times and do normalization
        inter_arri_times = _calculate_inter_arri_times(arri_times)

        # 1. for flow that all packets arrived at almost the same time
        # just let the normalized inter arrival times be 0s
        # 2. for flows that has less than max_per_flow_pkts, just append 0s 
        if len(inter_arri_times) > 0:
            if np.max(inter_arri_times) == np.min(inter_arri_times):
                inter_arri_times = np.array([0] * len(inter_arri_times))
            else:
                inter_arri_times = _normalize_to(inter_arri_times, to_low=0, to_high=255)
        # also deal with flows with 1 packets among other circumstances
        if len(inter_arri_times) < max_pkts_per_flow - 1:
            difference = max_pkts_per_flow - 1 - len(inter_arri_times)
            inter_arri_times = np.append(inter_arri_times,[0] * difference).astype(np.int32)
            

        # TODO
        # refactor with * operator?
        # concatenate all the sub-features
        single_feat = np.append(sess_info_vals, pkt_count)
        single_feat = np.append(single_feat, inter_arri_times)
        single_feat = np.append(single_feat, headers)
        feat.append(single_feat)
    return np.array(feat, dtype=np.int32)

def _extract(trace_filenames, max_pkts_per_flow, label_mapper, label_extractor):
    '''
    Extract image features and labels
    '''
    img_data = None
    labels = []

    # TODO: refactor
    trans_flows = {'TCP':0, 'UDP':0}
    for trans_layer_type in [TCP, UDP]:
        # for each file, extract features and labels and concatenate into img_data and labels
        trans_layer_str = 'TCP' if trans_layer_type is TCP else 'UDP' if trans_layer_type is UDP else None
        valid_flows = 0
        for filename in tqdm(trace_filenames, desc=trans_layer_str):
            file_img_data = _layer_feat(filename, trans_layer_type, max_pkts_per_flow)
            if img_data is None:
                # no flow
                if file_img_data.shape[0] > 0:
                    img_data = file_img_data
            else:
                # no flow
                if file_img_data.shape[0] > 0:
                    img_data = np.concatenate((img_data, file_img_data))

            base_name = os.path.basename(filename).lower()
            label = label_mapper.name2id(label_extractor.extract(base_name, label_mapper.options))
            
            assert label is not None

            valid_flows += file_img_data.shape[0]

            labels.extend([label] * file_img_data.shape[0])

        trans_flows[trans_layer_str] += valid_flows

    # print stats
    print('Raw TCP/UDP distribution', trans_flows)

    labels = np.array(labels)

    # necessary guanratee
    assert img_data.shape[0] == labels.shape[0]

    data = {'images':img_data, 'labels':labels}

    return data

def extract(trace_filenames, max_pkts_per_flow, label_mapper, label_extractor):
    return _extract(trace_filenames, max_pkts_per_flow, label_mapper, label_extractor)