import subprocess
import os
import sys

'''
    Generate TCP packet features
'''
def tcp_generate(trace_file_name, trace_feature_file_name, print_err=False):
    if not os.path.exists(trace_feature_file_name):
        tshark_command = subprocess.Popen(\
            'tshark -r {input} -Y tcp -T fields -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.len -e frame.time_relative -e tcp.seq -e tcp.ack -e tcp.flags.ack -e tcp.flags.syn -e tcp.flags.fin -e tcp.stream -Eheader=y -Eseparator=, > {output}'.\
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

'''
    Generate UDP packet features
'''
def udp_generate(trace_file_name, trace_feature_file_name, print_err=False):
    if not os.path.exists(trace_feature_file_name):
        tshark_command = subprocess.Popen(\
            'tshark -r {input} -Y udp -T fields -e ip.src -e ip.dst -e udp.srcport -e udp.dstport -e udp.length -e frame.time_relative -e udp.stream -Eheader=y -Eseparator=, > {output}'.\
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