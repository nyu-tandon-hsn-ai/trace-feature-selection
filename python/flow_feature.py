import numpy as np
import pandas as pd
from tqdm import tqdm
import functools


def calculate_two_way_communication(len_name, df):
    def get_statistical_features(df, criter, feature_name,name_pred):
        # upsampling
        feature_avg = df[criter][feature_name].mean()
        feature_avg = -1 if pd.isnull(feature_avg) else feature_avg
        feature_min = df[criter][feature_name].min()
        feature_min = -1 if pd.isnull(feature_min) else feature_min
        feature_max = df[criter][feature_name].max()
        feature_max = -1 if pd.isnull(feature_max) else feature_max
        feature_std = df[criter][feature_name].std()
        feature_std = -1 if pd.isnull(feature_std) else feature_std
        feature_sum = df[criter][feature_name].sum()
        feature_sum = -1 if pd.isnull(feature_sum) else feature_sum / sampling_rate if upsampled else feature_sum
        feature_count = df[criter][feature_name].count()
        feature_count = feature_count / sampling_rate if upsampled else feature_count
        return {'avg('+name_pred+')':feature_avg,'std('+name_pred+')':feature_std,'min('+name_pred+')':feature_min,'max('+name_pred+')':feature_max,'count('+name_pred[0:8]+')':feature_count, 'sum('+name_pred+')':feature_sum}
    
    addrs = list(set(np.append(df['src_addr'].unique(), df['dst_addr'].unique())))
    if len(addrs) != 2:
        raise AssertionError()
    stat = get_statistical_features(df, df['src_addr'] == addrs[0],len_name,'forw_pkt_len')
    stat.update(get_statistical_features(df, df['src_addr'] == addrs[1],len_name,'back_pkt_len'))
    stat['fb_ratio'] = stat['count(forw_pkt)'] / stat['count(back_pkt)'] if stat['count(back_pkt)'] > 0 else None
    return pd.Series(stat)

def _tshark_delegate(raw_trace_df, stream_name, len_name, sampling_rate, upsampled, max_count_per_flow):
    trace_df = raw_trace_df
    flow_df = pd.DataFrame()
    # empty flow
    if trace_df.shape[0] == 0:
        return flow_df
    # upsampling
    flow_df['avg(pkt_len)'] = trace_df.groupby(stream_name)[len_name].mean()
    flow_df['stddev(pkt_len)'] = trace_df.groupby(stream_name)[len_name].std().fillna(-1)
    flow_df['min(pkt_len)'] = trace_df.groupby(stream_name)[len_name].min()
    flow_df['max(pkt_len)'] = trace_df.groupby(stream_name)[len_name].max()
    flow_df['tot_pkt'] = trace_df.groupby(stream_name)[len_name].count()
    flow_df['tot_byte'] = trace_df.groupby(stream_name)[len_name].sum()
    flow_df['rel_start'] = trace_df.groupby(stream_name)[len_name].min()
    flow_df['duration'] = trace_df.groupby(stream_name)[len_name].max() - flow_df['rel_start']
    if not upsampled:
        tqdm.pandas(desc='{} samp rate no upsampling'.format(sampling_rate))
    else:
        flow_df['tot_pkt'] /= sampling_rate
        flow_df['tot_byte'] /= sampling_rate
        tqdm.pandas(desc='{} samp rate with upsampling'.format(sampling_rate))
    two_way_flow_df = trace_df.groupby(stream_name)[[len_name,'src_addr','dst_addr']].progress_apply(functools.partial(calculate_two_way_communication, len_name))
    flow_df = pd.concat([flow_df,two_way_flow_df],axis=1)
    return flow_df

def tcp_generate(raw_trace_df,sampling_rate=1.0,upsampled=False, max_count_per_flow=None):
    return _tshark_delegate(raw_trace_df, 'tcp.stream',  'tcp.len', sampling_rate, upsampled, max_count_per_flow)

def sample_trace(raw_trace_df,sampling_rate):
    import time
    return raw_trace_df.sample(frac=sampling_rate, random_state=int(time.time()))

def udp_generate(raw_trace_df,sampling_rate=1.0,upsampled=False):
        
        addrs = list(set(np.append(df['src_addr'].unique(), df['dst_addr'].unique())))
        if len(addrs) == 1:
            addrs.append(addrs[0])
        if len(addrs) != 2:
            print(addrs)
            raise AssertionError()
        stat = get_statistical_features(df, df['src_addr'] == addrs[0],'udp.length','forw_pkt_len')
        stat.update(get_statistical_features(df, df['src_addr'] == addrs[1],'udp.length','back_pkt_len'))
        return pd.Series(stat)

    trace_df = raw_trace_df
    udp_flow_df = pd.DataFrame()
    # empty flow
    if trace_df.shape[0] == 0:
        return udp_flow_df
    # upsampling
    udp_flow_df['avg(udp_pkt_len)'] = trace_df.groupby('udp.stream')['udp.length'].mean()
    udp_flow_df['stddev(udp_pkt_len)'] = trace_df.groupby('udp.stream')['udp.length'].std().fillna(-1)
    udp_flow_df['min(udp_pkt_len)'] = trace_df.groupby('udp.stream')['udp.length'].min()
    udp_flow_df['max(udp_pkt_len)'] = trace_df.groupby('udp.stream')['udp.length'].max()
    udp_flow_df['tot_pkt'] = trace_df.groupby('udp.stream')['udp.length'].count()
    udp_flow_df['tot_byte'] = trace_df.groupby('udp.stream')['udp.length'].sum()
    udp_flow_df['rel_start'] = trace_df.groupby('udp.stream')['frame.time_relative'].min()
    udp_flow_df['duration'] = trace_df.groupby('udp.stream')['frame.time_relative'].max() - udp_flow_df['rel_start']
    if not upsampled:
        tqdm.pandas(desc='UDP {} samp rate no upsampling'.format(sampling_rate))
    else:
        udp_flow_df['tot_pkt'] /= sampling_rate
        udp_flow_df['tot_byte'] /= sampling_rate
        tqdm.pandas(desc='UDP {} samp rate with upsampling'.format(sampling_rate))
    two_way_flow_df = trace_df.groupby('udp.stream')[['udp.length','src_addr','dst_addr']].progress_apply(calculate_two_way_tcp)
    udp_flow_df = pd.concat([udp_flow_df,two_way_flow_df],axis=1)
    return udp_flow_df