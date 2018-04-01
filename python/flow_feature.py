import numpy as np
import pandas as pd
from tqdm import tqdm

def tcp_generate(raw_trace_df,sampling_rate=1.0,upsampled=False):
    def calculate_two_way_tcp(df):
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
        stat = get_statistical_features(df, df['src_addr'] == addrs[0],'tcp.len','forw_pkt_len')
        stat.update(get_statistical_features(df, df['src_addr'] == addrs[1],'tcp.len','back_pkt_len'))
        return pd.Series(stat)

    trace_df = raw_trace_df
    tcp_flow_df = pd.DataFrame()
    # upsampling
    tcp_flow_df['avg(tcp_pkt_len)'] = trace_df.groupby('tcp.stream')['tcp.len'].mean()
    tcp_flow_df['stddev(tcp_pkt_len)'] = trace_df.groupby('tcp.stream')['tcp.len'].std().fillna(-1)
    tcp_flow_df['min(tcp_pkt_len)'] = trace_df.groupby('tcp.stream')['tcp.len'].min()
    tcp_flow_df['max(tcp_pkt_len)'] = trace_df.groupby('tcp.stream')['tcp.len'].max()
    tcp_flow_df['tot_pkt'] = trace_df.groupby('tcp.stream')['tcp.len'].count()
    tcp_flow_df['tot_byte'] = trace_df.groupby('tcp.stream')['tcp.len'].sum()
    tcp_flow_df['rel_start'] = trace_df.groupby('tcp.stream')['frame.time_relative'].min()
    tcp_flow_df['duration'] = trace_df.groupby('tcp.stream')['frame.time_relative'].max() - tcp_flow_df['rel_start']
    if not upsampled:
        tqdm.pandas(desc='TCP {} samp rate no upsampling'.format(sampling_rate))
    else:
        tcp_flow_df['tot_pkt'] /= sampling_rate
        tcp_flow_df['tot_byte'] /= sampling_rate
        tqdm.pandas(desc='TCP {} samp rate with upsampling'.format(sampling_rate))
    two_way_flow_df = trace_df.groupby('tcp.stream')[['tcp.len','src_addr','dst_addr']].progress_apply(calculate_two_way_tcp)
    tcp_flow_df = pd.concat([tcp_flow_df,two_way_flow_df],axis=1)
    return tcp_flow_df

def sample_trace(raw_trace_df,sampling_rate):
    import time
    return raw_trace_df.sample(frac=sampling_rate, random_state=int(time.time()))

def udp_generate(raw_trace_df,sampling_rate=1.0,upsampled=False):
    def calculate_two_way_tcp(df):
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
        stat = get_statistical_features(df, df['src_addr'] == addrs[0],'udp.length','forw_pkt_len')
        stat.update(get_statistical_features(df, df['src_addr'] == addrs[1],'udp.length','back_pkt_len'))
        return pd.Series(stat)

    trace_df = raw_trace_df
    udp_flow_df = pd.DataFrame()
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