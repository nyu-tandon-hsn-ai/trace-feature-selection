import numpy as np
import pandas as pd
from tqdm import tqdm
import functools

def extract_stream_id(record, protocol):
    return record[protocol + '.stream']

def is_in(record, pcap_statistics, protocol):
    return extract_stream_id(record, protocol) in pcap_statistics

def extract_useful_info(record):
    useful_info = {\
        'pkt_lens':[record['frame.len']],\
        'arri_times':[record['frame.time_relative']]\
    }
    return useful_info

def add_in_statistics(pcap_statistics, row, protocol):
    stream_id = extract_stream_id(row, protocol)
    pcap_statistics[stream_id] = extract_useful_info(row)
    return pcap_statistics

def update_statistics(pcap_statistics, row, protocol):
    stream_id = extract_stream_id(row, protocol)
    pcap_statistics[stream_id]['pkt_lens'].append(row['frame.len'])
    pcap_statistics[stream_id]['arri_times'].append(row['frame.time_relative'])
    return pcap_statistics

def generate_graph(record):
    channel1 = record['pkt_lens'][:-1]
    channel2 = []
    for i in range(1, len(record['arri_times'])):
        channel2.append(record['arri_times'][i] - record['arri_times'][i - 1])
    return np.array([channel1, channel2]).T

def save_graph(graph, filename):
    np.save(filename, graph)

INDEX = 0
UNACCEPTED_PKTS = 0
def _track_flow(pcap_df, protocol, max_pkts_to_see=10, filename_prefix=None):
    def helper(pcap_statistics, row):
        if not is_in(row, pcap_statistics, protocol):
            add_in_statistics(pcap_statistics, row, protocol)
        else:
            stream_id = extract_stream_id(row, protocol)
            # flow packets not exceeds max_pkts_to_see
            if len(pcap_statistics[stream_id]['pkt_lens']) < max_pkts_to_see:
                update_statistics(pcap_statistics, row, protocol)
                if len(pcap_statistics[stream_id]['pkt_lens']) == max_pkts_to_see:
                    global INDEX
                    graph = generate_graph(pcap_statistics[stream_id])
                    save_graph(graph, filename_prefix + str(INDEX) + '.npy')
                    print(filename_prefix + str(INDEX) + '.npy')
                    INDEX += 1
            else:
                global UNACCEPTED_PKTS
                UNACCEPTED_PKTS += 1
    global INDEX
    global UNACCEPTED_PKTS
    INDEX = 0
    UNACCEPTED_PKTS = 0
    pcap_statistics = {}
    tqdm.pandas(desc='{protocol} flow, flow byte limit->{flow_byte_limit}'.format(protocol=protocol, flow_byte_limit=max_pkts_to_see))
    pcap_df.progress_apply(functools.partial(helper, pcap_statistics), axis=1)
    undealt_pkts = 0
    for _, record in pcap_statistics.items():
        if len(record['pkt_lens']) != max_pkts_to_see:
            undealt_pkts += len(record['pkt_lens'])
    print('pkts undealt in total', undealt_pkts)
    print('unaccepted pkts in total', UNACCEPTED_PKTS)
    total = INDEX * max_pkts_to_see + undealt_pkts + UNACCEPTED_PKTS
    print('pkts in total', total)
    assert total == pcap_df.shape[0]

def tcp_generate(raw_trace_df, max_pkts_to_see=10, label=None):
    return _track_flow(raw_trace_df, 'tcp', max_pkts_to_see=max_pkts_to_see, filename_prefix=label)

def udp_generate(raw_trace_df, max_pkts_to_see=10, label=None):
    return _track_flow(raw_trace_df, 'udp', max_pkts_to_see=max_pkts_to_see, filename_prefix=label)