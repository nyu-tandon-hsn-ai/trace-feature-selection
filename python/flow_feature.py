import numpy as np
import pandas as pd
from tqdm import tqdm
import functools

'''
    Is valid IPv4 address
'''
def _is_valid_ipv4(ipaddress_v4):
    import ipaddress
    try:
        ipaddress.IPv4Address(ipaddress_v4)
    except ipaddress.AddressValueError:
        return False
    return True

def extract_packet_tuple(record, protocol):
    return (record['ip.src'], record[protocol + '.srcport'], record['ip.dst'], record[protocol + '.dstport'])

def reverse_pkt_tuple(pkt_tuple):
    return (pkt_tuple[2], pkt_tuple[3], pkt_tuple[0], pkt_tuple[1])

def is_in(record, pcap_statistics, protocol, time_delta_threshold = None):
    pkt_tuple = extract_packet_tuple(record, protocol)
    reversed_pkt_tuple = reverse_pkt_tuple(pkt_tuple)
    if pkt_tuple not in pcap_statistics and reversed_pkt_tuple not in pcap_statistics:
        return False
    else:
        flow_list = pcap_statistics[pkt_tuple] if pkt_tuple in pcap_statistics else pcap_statistics[reversed_pkt_tuple]
        last_flow = flow_list[-1]
        return True if not time_delta_threshold else record['frame.time_relative'] - (last_flow['rel_start'] + last_flow['duration']) <= time_delta_threshold

def extract_useful_info(record, protocol, len_name):
    useful_info = {\
        "src_ip":record['ip.src'],\
        "src_port":record[protocol + '.srcport'],\
        "dst_ip":record['ip.dst'],\
        "dst_port":record[protocol + '.dstport'],\
        "rel_start":record['frame.time_relative'],\
        "duration":0,\
        "pkt_count":1,\
        "pkt_len":record[len_name],\
        "fwd_pkt_count":1,\
        "fwd_pkt_len":record[len_name],\
        "bwd_pkt_count":0,\
        "bwd_pkt_len":0,\
        "inter_arrival_time_summed":0\
    }
    return useful_info

def add_in_statistics(pcap_statistics, packet_tuple, record, protocol, len_name):
    if packet_tuple not in pcap_statistics:
        pcap_statistics[packet_tuple] = []
    pcap_statistics[packet_tuple].append(extract_useful_info(record, protocol, len_name))
    return pcap_statistics

def update_statistics_info(pcap_statistics,pkt_tuple,record,is_forward_stream, protocol, len_name):
    pcap_statistics[pkt_tuple][-1]['inter_arrival_time_summed'] += record['frame.time_relative'] - (pcap_statistics[pkt_tuple][-1]['rel_start'] + pcap_statistics[pkt_tuple][-1]['duration'])
    pcap_statistics[pkt_tuple][-1]['duration'] = max(pcap_statistics[pkt_tuple][-1]['duration'], record['frame.time_relative'] - pcap_statistics[pkt_tuple][-1]['rel_start'])
    pcap_statistics[pkt_tuple][-1]['pkt_count'] += 1
    pcap_statistics[pkt_tuple][-1]['pkt_len'] += record[protocol + len_name]
    if is_forward_stream:
        pcap_statistics[pkt_tuple][-1]['fwd_pkt_count'] += 1
        pcap_statistics[pkt_tuple][-1]['fwd_pkt_len'] += record[len_name]
    else:
        pcap_statistics[pkt_tuple][-1]['bwd_pkt_count'] += 1
        pcap_statistics[pkt_tuple][-1]['bwd_pkt_len'] += record[len_name]
    return pcap_statistics

def update_statistics(pcap_statistics, pkt_tuple, record, protocol, len_name):  
    if pkt_tuple in pcap_statistics:
        return update_statistics_info(pcap_statistics,pkt_tuple,record,True, protocol, len_name)
    else:
        return update_statistics_info(pcap_statistics,reverse_pkt_tuple(pkt_tuple),record, False, protocol, len_name)

def flatten_dict(pcap_statistics):
    result_dict = []
    for _, flow_list in pcap_statistics.items():
        for flow in flow_list:
            result_dict.append(flow)
    return result_dict

# TODO:
# * stddev(pkt_len)
# * trim to 1000 packets/flow
def _track_flow(pcap_df, protocol):
    pcap_statistics = {}
    for _, row in pcap_df.iterrows():
        pkt_tuple = extract_packet_tuple(row, protocol)
        if not is_in(row, pcap_statistics, protocol):
            add_in_statistics(pcap_statistics, pkt_tuple, row, protocol, len_name)
        else:
            update_statistics(pcap_statistics, pkt_tuple, row, protocol, len_name)
    pcap_statistics = flatten_dict(pcap_statistics)
    flow_df = pd.DataFrame(pcap_statistics)
    flow_df['inter_arrival_time'] = flow_df['inter_arrival_time_summed'] / flow_df['pkt_count']
    flow_df['avg(pkt_len)'] = flow_df['pkt_len'] / flow_df['pkt_count']
    return flow_df
    

def _calculate_two_way_communication(len_name, sampling_rate, upsampled, df):
    # one-way statistics
    def get_statistical_features(df, criter, feature_name,name_pred):
        feature_avg = df[criter][feature_name].mean()
        feature_avg = -1 if pd.isnull(feature_avg) else feature_avg
        feature_min = df[criter][feature_name].min()
        feature_min = -1 if pd.isnull(feature_min) else feature_min
        feature_max = df[criter][feature_name].max()
        feature_max = -1 if pd.isnull(feature_max) else feature_max
        feature_std = df[criter][feature_name].std()
        feature_std = -1 if pd.isnull(feature_std) else feature_std
        feature_sum = df[criter][feature_name].sum()
        # upsampling
        feature_sum = -1 if pd.isnull(feature_sum) else feature_sum / sampling_rate if upsampled else feature_sum
        feature_count = df[criter][feature_name].count()
        feature_count = feature_count / sampling_rate if upsampled else feature_count
        return {'avg('+name_pred+')':feature_avg,'std('+name_pred+')':feature_std,'min('+name_pred+')':feature_min,'max('+name_pred+')':feature_max,'count('+name_pred[0:8]+')':feature_count, 'sum('+name_pred+')':feature_sum}
    
    # error check
    addrs = list(set(np.append(df['src_addr'].unique(), df['dst_addr'].unique())))
    if len(addrs) != 2:
        raise AssertionError()
    
    # get forward features
    stat = get_statistical_features(df, df['src_addr'] == addrs[0],len_name,'forw_pkt_len')

    # get backward features
    stat.update(get_statistical_features(df, df['src_addr'] == addrs[1],len_name,'back_pkt_len'))

    # calculate forward/backward packets ratio
    stat['fb_ratio'] = stat['count(forw_pkt)'] / stat['count(back_pkt)'] if stat['count(back_pkt)'] > 0 else None
    return pd.Series(stat)

def _generate_flow_features(raw_trace_df, stream_name, len_name, sampling_rate, upsampled, max_count_per_flow):
    trace_df = raw_trace_df
    flow_df = pd.DataFrame()

    # empty flow at the beginning
    if trace_df.shape[0] == 0:
        return flow_df

    # transform illegal addresses to null
    trace_df['src_addr'] = trace_df.apply(lambda row: None if pd.isnull(row['src_addr']) or not _is_valid_ipv4(row['ip.src']) else row['src_addr'], axis=1)
    trace_df['dst_addr'] = trace_df.apply(lambda row: None if pd.isnull(row['dst_addr']) or not _is_valid_ipv4(row['ip.dst']) else row['dst_addr'], axis=1)

    # filter out all the null addresses
    trace_df = trace_df[trace_df['src_addr'].notnull() & trace_df['dst_addr'].notnull()]

    # empty flow after filter
    if trace_df.shape[0] == 0:
        return flow_df

    # generate flow-based features
    flow_df['avg(pkt_len)'] = trace_df.groupby(stream_name)[len_name].mean()
    flow_df['stddev(pkt_len)'] = trace_df.groupby(stream_name)[len_name].std().fillna(-1)
    flow_df['min(pkt_len)'] = trace_df.groupby(stream_name)[len_name].min()
    flow_df['max(pkt_len)'] = trace_df.groupby(stream_name)[len_name].max()
    flow_df['tot_pkt'] = trace_df.groupby(stream_name)[len_name].count()
    flow_df['tot_byte'] = trace_df.groupby(stream_name)[len_name].sum()
    flow_df['rel_start'] = trace_df.groupby(stream_name)[len_name].min()
    flow_df['duration'] = trace_df.groupby(stream_name)[len_name].max() - flow_df['rel_start']

    # upsampling or not
    if not upsampled:
        tqdm.pandas(desc='{} samp rate no upsampling'.format(sampling_rate))
    else:
        flow_df['tot_pkt'] /= sampling_rate
        flow_df['tot_byte'] /= sampling_rate
        tqdm.pandas(desc='{} samp rate with upsampling'.format(sampling_rate))

    # generate forward and backward flow-based features
    two_way_flow_df = trace_df.groupby(stream_name)[[len_name,'src_addr','dst_addr']].progress_apply(functools.partial(_calculate_two_way_communication, len_name, sampling_rate, upsampled))
    flow_df = pd.concat([flow_df,two_way_flow_df],axis=1)
    return flow_df

def tcp_generate(raw_trace_df,sampling_rate=1.0,upsampled=False, max_count_per_flow=None):
    return _generate_flow_features(raw_trace_df, 'tcp.stream',  'tcp.len', sampling_rate, upsampled, max_count_per_flow)

def sample_trace(raw_trace_df,sampling_rate):
    import time
    return raw_trace_df.sample(frac=sampling_rate, random_state=int(time.time()))

def udp_generate(raw_trace_df,sampling_rate=1.0,upsampled=False, max_count_per_flow=None):
    return _generate_flow_features(raw_trace_df, 'udp.stream',  'udp.length', sampling_rate, upsampled, max_count_per_flow)