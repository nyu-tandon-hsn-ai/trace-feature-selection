import subprocess
import os
import sys
import pandas as pd

def _tshark_extract(tshark_query_str, trace_file_name, trace_feature_file_name, print_err):
    if not os.path.exists(trace_feature_file_name):
        tshark_command = subprocess.Popen(\
            tshark_query_str.\
            format(input=trace_file_name, output=trace_feature_file_name),\
            shell=True,\
            stdout=subprocess.PIPE,\
            stderr=subprocess.PIPE\
        )
        out_data, err_data = tshark_command.communicate()
        out_data, err_data = out_data.decode('utf-8'), err_data.decode('utf-8')
        if out_data == '':
            print('Conversion done',flush=True)
        if print_err:
            if err_data != '':
                print(err_data,file=sys.stderr,flush=True)
            else:
                print('No error',file=sys.stderr,flush=True)
    else:
        print('Packet feature file already exists.')

def _generate_full_addr(protocol, trace_feature_file_name):
    # add source and destination address
    trace_df = pd.read_csv(trace_feature_file_name)
    trace_df['src_addr'] = trace_df['ip.src'] + ":" + trace_df[protocol + '.srcport'].apply(str)
    trace_df['dst_addr'] = trace_df['ip.dst'] + ":" + trace_df[protocol + '.dstport'].apply(str)
    trace_df.to_csv(trace_feature_file_name, index=False)

def _add_tcp_pkt_len(trace_feature_file_name):
    trace_df = pd.read_csv(trace_feature_file_name)
    trace_df['tcp.payload'] = trace_df['tcp.len']
    trace_df['tcp.len'] = trace_df['tcp.len'] + trace_df['tcp.hdr_len']
    trace_df.to_csv(trace_feature_file_name, index=False)

'''
    Generate TCP packet features
'''
def tcp_generate(trace_file_name, trace_feature_file_name, print_err=False):
    _tshark_extract('tshark -r {input} -Y tcp -T fields -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.hdr_len -e tcp.len -e frame.time_relative -e tcp.seq -e tcp.ack -e tcp.flags.ack -e tcp.flags.syn -e tcp.flags.fin -e tcp.stream -Eheader=y -Eseparator=, -Equote=d > {output}', trace_file_name, trace_feature_file_name, print_err)
    _generate_full_addr('tcp', trace_feature_file_name)
    _add_tcp_pkt_len(trace_feature_file_name)

'''
    Generate UDP packet features
'''
def udp_generate(trace_file_name, trace_feature_file_name, print_err=False):
    _tshark_extract('tshark -r {input} -Y udp -T fields -e ip.src -e ip.dst -e udp.srcport -e udp.dstport -e udp.length -e frame.time_relative -e udp.stream -Eheader=y -Eseparator=, -Equote=d > {output}', trace_file_name, trace_feature_file_name, print_err)
    _generate_full_addr('udp', trace_feature_file_name)
    
