from copy import deepcopy

import numpy as np
from tqdm import tqdm
import scapy
from scapy.all import *

from utils import normalize_to
from img_feature import stringify_protocol, calculate_inter_arri_times, _extract_session_info

class Extractor:

    @property
    def desc(self):
        return self._extract_description()

    def _extract_description(self):
        raise NotImplementedError()

    def extract_flow_img(self, trace_filename):
        raise NotImplementedError()

class AboveIpLayerHeaderPayloadExtractor(Extractor):

    IP2TRANS_LAYER_HEADER_LEN=40

    def __init__(self, max_pkts_per_flow, trans_layer_payload_len):
        # due to image definition for now
        if max_pkts_per_flow >= 256:
            raise AssertionError('packet count field exceeded 1 byte long')
        self._max_pkts_per_flow = max_pkts_per_flow
        self._trans_layer_payload_len = trans_layer_payload_len

    def _extract_description(self):
        return '{}-pkts-subflow'.format(self._max_pkts_per_flow)

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
            flow_signatures=np.append(flow_signatures, [0] * ((max_pkts_per_flow-pkt_count) * (AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + self._trans_layer_payload_len)))
        
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
        if len(pkt_without_trans_layer_payload) + len(trans_layer_payload_bin) < AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + self._trans_layer_payload_len:
            trans_layer_payload_bin += b'\x00' * (AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + self._trans_layer_payload_len - len(pkt_without_trans_layer_payload) + len(trans_layer_payload_bin))
        trans_layer_payload_bin = trans_layer_payload_bin[:AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + self._trans_layer_payload_len - len(pkt_without_trans_layer_payload)]

        # construct new packet
        new_pkt = pkt_without_trans_layer_payload/Raw(trans_layer_payload_bin)

        # return flow signature in bytes
        return [byte for byte in raw(new_pkt)]

    def extract_flow_img(self, trace_filename, trans_layer_type):
        max_pkts_per_flow = self._max_pkts_per_flow

        # read pcap file
        pcap_file = rdpcap(trace_filename)

        # get all sessions
        sessions = pcap_file.sessions()

        # store all the features
        imgs = []
        for session in tqdm(sessions, desc=trace_filename.split('.')[-2][-5:]+stringify_protocol(trans_layer_type) + ' Session'):

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
            session_info = _extract_session_info(sessions, session, trans_layer_type)

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
    
    def __init__(self, trans_layer_payload_len):
        if trans_layer_payload_len >= 65536:
            raise AssertionError('Only support less than 65536 bytes')
        self._trans_layer_payload_len = trans_layer_payload_len
    
    def _extract_description(self):
        return '{}-byte-payload-per-flow'.format(self._trans_layer_payload_len)
    
    def _extract_trans_layer_payload(self, pkt, trans_layer_type):
        return [] if isinstance(pkt[trans_layer_type].payload, scapy.packet.NoPayload) else \
                [item for item in raw(pkt[trans_layer_type].payload)]
    
    def extract_flow_img(self, trace_filename, trans_layer_type):
        # read pcap file
        pcap_file = rdpcap(trace_filename)

        # get all sessions
        sessions = pcap_file.sessions()

        # store all the features
        imgs = []
        for session in tqdm(sessions, desc=trace_filename.split('.')[-2][-5:]+stringify_protocol(trans_layer_type) + ' Session'):

            # it is only until max_pkts_per_flow number of trans_layer_type packets have been captured
            # will we continue to do things
            flow_signatures = []

            byte_count, pkt_count = 0, 0

            for pkt in tqdm(sessions[session], desc='Current session packets'):

                # Ignore IPv6 for now
                if IP in pkt and trans_layer_type in pkt:
                    # transport layer payload
                    trans_layer_payload = self._extract_trans_layer_payload(pkt, trans_layer_type)

                    # count byte_count
                    if byte_count + len(trans_layer_payload) > self._trans_layer_payload_len:
                        trans_layer_payload = trans_layer_payload[\
                            :-(byte_count + len(trans_layer_payload) - self._trans_layer_payload_len)]
                        byte_count = self._trans_layer_payload_len
                    else:
                        byte_count += len(trans_layer_payload)

                    # increment pkt_count
                    pkt_count += 1

                    # extract flow_signature
                    flow_signatures.extend(trans_layer_payload)
                    if byte_count == self._trans_layer_payload_len:
                        break

            # there should be at least one byte of payload in a flow
            if byte_count == 0:
                continue
            
            # error-proof
            if byte_count > self._trans_layer_payload_len:
                raise AssertionError()
            
            # padding
            if len(flow_signatures) < self._trans_layer_payload_len:
                flow_signatures += [0] * (self._trans_layer_payload_len - len(flow_signatures))
            
            # get session inoformation
            session_info = _extract_session_info(sessions, session, trans_layer_type)
            
            # generate images
            img = np.concatenate([session_info, [item for item in pkt_count.to_bytes(2, byteorder='big')], [item for item in byte_count.to_bytes(2, byteorder='big')], flow_signatures])

            # add to imgs
            imgs.append(img)
        return np.array(imgs, dtype=np.int32)
