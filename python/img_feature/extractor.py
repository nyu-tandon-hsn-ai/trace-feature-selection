from copy import deepcopy

import numpy as np
from tqdm import tqdm
import scapy
from scapy.all import *

from utils import normalize_to
from session_info import extract_session_info
from img_feature import stringify_protocol, calculate_inter_arri_times

class Extractor:
    def extract_flow_img(self, trace_filename, **kwargs):
        raise NotImplementedError()

class AboveIpLayerHeaderPayloadExtractor(Extractor):

    IP2TRANS_LAYER_HEADER_LEN=40

    def __init__(self, app_layer_payload_len):
        self._app_layer_payload_len = app_layer_payload_len

    def _handle_flow_signatures(self, flow_signatures, pkt_count, max_pkts_per_flow):
        # convert to `numpy.ndarray`
        flow_signatures = np.array(flow_signatures)
        row, col = flow_signatures.shape

        # flatten per packet flow_signatures to 1D flow_signatures
        flow_signatures = flow_signatures.flatten()

        # error-proof
        assert row * col == flow_signatures.shape[0]

        # append 0 to the end of flow_signatures to align
        if pkt_count < max_pkts_per_flow:
            flow_signatures=np.append(flow_signatures, [0] * ((max_pkts_per_flow-pkt_count) * (AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + self._app_layer_payload_len)))
        
        return flow_signatures

    def _extract_inter_arrival_time(self, arri_times, max_pkts_per_flow):
        # calculate inter arrival times
        inter_arri_times = np.array(calculate_inter_arri_times(arri_times))

        # do normalization
        # ATTENTION:
        # 1. for flow that all packets arrived at almost the same time
        # just let the normalized inter arrival times be 0s
        # 2. for flows that has less than max_per_flow_pkts, just append 0s 
        if len(inter_arri_times) > 0:
            if np.max(inter_arri_times) == np.min(inter_arri_times):
                inter_arri_times = np.array([0] * len(inter_arri_times))
            else:
                inter_arri_times = normalize_to(inter_arri_times, to_low=0, to_high=255)

        # also deal with flows with 1 packets among other circumstances
        if len(inter_arri_times) < max_pkts_per_flow - 1:
            difference = max_pkts_per_flow - 1 - len(inter_arri_times)
            inter_arri_times = np.append(inter_arri_times,[0] * difference).astype(np.int32)
        return inter_arri_times

    def _extract_session_info(self, sessions, session, trans_layer_type):
        # Special case
        if session == 'Other':
            # error-proof
            assert len(sessions[session]) > 0

            # extract the first packet we want
            f_pkt= None
            for pkt in sessions[session]:
                if IP in pkt and trans_layer_type in pkt:
                    f_pkt=pkt
            
            # assertion error
            if f_pkt is None:
                raise AssertionError()
            
            # extract five tuples
            trans_layer_str=stringify_protocol(trans_layer_type)
            session='{protocol} {ip0}:{port0} > {ip1}:{port1}'.format(
                protocol=trans_layer_str,
                ip0=f_pkt[IP].src,
                ip1=f_pkt[IP].dst,
                port0=f_pkt[trans_layer_type].sport,
                port1=f_pkt[trans_layer_type].dport
            )

        # extract session info
        sess_info = extract_session_info(session)

        # convert
        return [int(sess_info['is_tcp'])] + \
                list(sess_info['ip0'].to_bytes(4, byteorder='big')) + \
                list(sess_info['port0'].to_bytes(2, byteorder='big')) + \
                list(sess_info['ip1'].to_bytes(4, byteorder='big')) + \
                list(sess_info['port1'].to_bytes(2, byteorder='big'))

    def _extract_pkt_signature(self, pkt, trans_layer_type):
        # copy packet
        pkt = deepcopy(pkt)

        # only consider IP layer and above
        pkt = pkt[IP]

        # TODO:
        # temporarily just omit all the options fields
        # MAYBE a better solution: fill the options field with leading/trailing 0s
        pkt[IP].options = []
        if trans_layer_type is TCP:
            pkt[trans_layer_type].options = []

        # get the transport layer payload
        trans_layer_payload_bin = b'' if isinstance(pkt[trans_layer_type].payload, scapy.packet.NoPayload) else raw(pkt[trans_layer_type].payload)

        # remove the transport layer payload
        pkt[trans_layer_type].remove_payload()
        pkt_without_trans_layer_payload = pkt

        # remove/pad the payload in transport layer header
        if len(pkt_without_trans_layer_payload) + len(trans_layer_payload_bin) < AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + self._app_layer_payload_len:
            trans_layer_payload_bin += b'\x00' * (AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + self._app_layer_payload_len - len(pkt_without_trans_layer_payload) + len(trans_layer_payload_bin))
        trans_layer_payload_bin = trans_layer_payload_bin[:AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + self._app_layer_payload_len - len(pkt_without_trans_layer_payload)]

        # construct new packet
        new_pkt = pkt_without_trans_layer_payload/Raw(trans_layer_payload_bin)

        # return flow signature in bytes
        return [byte for byte in raw(new_pkt)]

    def extract_flow_img(self, trace_filename, trans_layer_type, **kwargs):
        # extract parameters
        max_pkts_per_flow = kwargs['max_pkts_per_flow']

        # due to image definition for now
        if max_pkts_per_flow >= 256:
            raise AssertionError('packet count field exceeded 1 byte long')

        # read pcap file
        pcap_file = rdpcap(trace_filename)

        # get all sessions
        sessions = pcap_file.sessions()

        # store all the features
        imgs = []
        for session in tqdm(sessions, desc=stringify_protocol(trans_layer_type) + ' Session'):

            # it is only until max_pkts_per_flow number of trans_layer_type packets have been captured
            # will we continue to do things
            pkt_count, flow_signatures, arri_times = 0, [], []
            for pkt in tqdm(sessions[session], desc='Current session packets'):

                # Ignore IPv6 for now
                if IP in pkt and trans_layer_type in pkt:

                    # extract flow_signature
                    flow_signatures.append(self._extract_pkt_signature(pkt, trans_layer_type))

                    # extract arrived time
                    arri_times.append(pkt.time)

                    # keep record of packet count
                    pkt_count += 1
                    if pkt_count == max_pkts_per_flow:
                        break

            # there should be at least one packet in a flow
            if pkt_count == 0:
                continue
            
            # error-proof
            if pkt_count > max_pkts_per_flow:
                raise AssertionError()

            # get session inoformation
            session_info = self._extract_session_info(sessions, session, trans_layer_type)

            # handle flow signatures
            flow_signatures = self._handle_flow_signatures(flow_signatures, pkt_count, max_pkts_per_flow)

            # extract inter arrival times
            inter_arri_times = self._extract_inter_arrival_time(arri_times, max_pkts_per_flow)
                
            # concatenate all to form one single image
            img = np.concatenate([session_info, [pkt_count], inter_arri_times, flow_signatures])

            # add to imgs
            imgs.append(img)
        return np.array(imgs, dtype=np.int32)

class AppLayerLengthExtractor(Extractor):
    pass