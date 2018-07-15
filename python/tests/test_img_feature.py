import unittest
from ipaddress import IPv4Address

from scapy.all import *
import numpy as np

from img_feature import _stringify_protocol, _handle_flow_signatures, _extract_inter_arrival_time
from img_feature import _calculate_inter_arri_times, _extract_pkt_signature, _extract_session_info
from img_feature import IP2TCP_HEADER_LEN, PAYLOAD

######################################################################
#  T E S T   C A S E S
######################################################################
class TestImageFeature(unittest.TestCase):
    """ Test Cases for extracting image features """

    def test_stringify_protocol(self):
        """ Test if _stringify_protocol() functions well """
        
        # TCP
        self.assertEqual(_stringify_protocol(TCP), 'TCP')

        # UDP
        self.assertEqual(_stringify_protocol(UDP), 'UDP')

        # IP
        with self.assertRaises(AssertionError):
            _stringify_protocol(IP)
    
    def test_calculate_inter_arri_times(self):
        """ Test if _calculate_inter_arri_times() functions well """

        #########
        # CASE 1
        #########

        # init
        arri_times = [0.2, 0.7, 0.9]

        # generate things
        right_answer = [0.5, 0.2]

        # run tested functions
        inter_arri_times = _calculate_inter_arri_times(arri_times)

        self.assertTrue(np.isclose(inter_arri_times, right_answer).all())

        #########
        # CASE 2
        #########

        # init
        arri_times = []

        # generate things
        right_answer = []

        # run tested functions
        inter_arri_times = _calculate_inter_arri_times(arri_times)

        self.assertEqual(inter_arri_times, right_answer)

    def test_handle_flow_signatures(self):
        """ Test if _handle_flow_signatures() functions well """
        
        #######################
        # CASE 1
        # Enough packet length
        ######################

        # init things
        flow_signatures = [[1,2],[3,4]]
        pkt_count = 2
        max_pkts_per_flow = 2

        # generated things
        flattened_signatures = [1,2,3,4]

        # run tested function
        flow_signatures_prime = _handle_flow_signatures(flow_signatures, pkt_count, max_pkts_per_flow)

        self.assertTrue((flattened_signatures == flow_signatures_prime).all())

        ##########################
        # CASE 2
        # Not enough packet length
        ##########################

        # init things
        flow_signatures = [[1,2],[3,4]]
        pkt_count = 1
        appended = [0] * (IP2TCP_HEADER_LEN + PAYLOAD)
        max_pkts_per_flow = 2

        # generated things
        flattened_signatures = [1,2,3,4] + appended

        # run tested function
        flow_signatures_prime = _handle_flow_signatures(flow_signatures, pkt_count, max_pkts_per_flow)

        self.assertTrue((flattened_signatures == flow_signatures_prime).all())
    
    def test_extract_inter_arrival_time(self):
        """ Test if _extract_inter_arrival_time() functions well """

        #########
        # CASE 1
        # Normal
        #########

        # init things
        arri_times = [0.8, 1.6, 2.5]
        max_pkts_per_flow = 3
        right_answer = [0, 255]

        inter_arri_times = _extract_inter_arrival_time(arri_times, max_pkts_per_flow)

        self.assertTrue((inter_arri_times == right_answer).all())

        ############################
        # CASE 3
        # Less packets than expected
        ############################

        # init things
        arri_times = [0.8, 1.6, 2.5]
        max_pkts_per_flow = 4
        right_answer = [0, 255, 0]

        inter_arri_times = _extract_inter_arrival_time(arri_times, max_pkts_per_flow)

        self.assertTrue((inter_arri_times == right_answer).all())

    #TODO:
    # 1. more adaptive to constants not human hard-coded ...
    # 2. randomly generate test packet not human hard-coded ...
    # 3. break down to several sub test cases?
    def test_extract_pkt_signature(self):
        """ Test if _extract_pkt_signature() functions well """

        ################################
        # CASE 1
        # TCP: Less length than expected
        ################################
        
        # init
        tcp_payload = Raw('123123')
        pkt = Ether(type=0x800)/IP(src='127.0.0.1', options=['1','2','3'])/TCP(sport=80, options=['12', '34'])/tcp_payload
        pkt_without_tcp_payload = IP(src='127.0.0.1')/TCP(sport=80)
        tcp_payload_raw = [item for item in raw(tcp_payload)] + \
                            [0] * (IP2TCP_HEADER_LEN + PAYLOAD - len(pkt_without_tcp_payload) - len(tcp_payload))
        right_answer = [item for item in raw(pkt_without_tcp_payload / Raw(tcp_payload_raw))]

        pkt_signature = _extract_pkt_signature(pkt, TCP)

        self.assertEqual(len(pkt_signature), IP2TCP_HEADER_LEN + PAYLOAD)
        self.assertEqual(pkt_signature, right_answer)

        ############################
        # CASE 2
        # TCP: Enough length
        ############################
        
        # init
        pkt = Ether(type=0x800)/IP(src='127.0.0.1', options=['1','2','3'])/TCP(sport=80, options=['12', '43'])/Raw('12311234233213123231')
        pkt_without_options = IP(src='127.0.0.1')/TCP(sport=80)/Raw('12311234233213123231')
        right_answer = [item for item in raw(pkt_without_options)]

        pkt_signature = _extract_pkt_signature(pkt, TCP)

        self.assertEqual(len(pkt_signature), IP2TCP_HEADER_LEN + PAYLOAD)
        self.assertEqual(pkt_signature, right_answer)

        ############################
        # CASE 3
        # TCP: length excceeds
        ############################
        
        # init
        pkt = Ether(type=0x800)/IP(src='127.0.0.1', options=['1','2','3'])/TCP(sport=80, options=['12', '43'])/Raw('12311234233213123231234')
        pkt_without_options = IP(src='127.0.0.1')/TCP(sport=80)/Raw('12311234233213123231')
        right_answer = [item for item in raw(pkt_without_options)]

        pkt_signature = _extract_pkt_signature(pkt, TCP)

        self.assertEqual(len(pkt_signature), IP2TCP_HEADER_LEN + PAYLOAD)
        self.assertEqual(pkt_signature, right_answer)

        ################################
        # CASE 4
        # UDP: Less length than expected
        ################################
        
        # init
        pkt = Ether(type=0x800)/IP(src='127.0.0.1', options=['1','2','3'])/UDP(sport=80)/Raw('123123')
        pkt_without_udp_payload = IP(src='127.0.0.1')/UDP(sport=80)
        udp_payload_raw = [item for item in raw(Raw('123123'))] + \
                            [0] * (IP2TCP_HEADER_LEN + PAYLOAD - len(pkt_without_udp_payload) - len(Raw('123123')))
        right_answer = [item for item in raw(pkt_without_udp_payload / Raw(udp_payload_raw))]

        pkt_signature = _extract_pkt_signature(pkt, UDP)

        self.assertEqual(len(pkt_signature), IP2TCP_HEADER_LEN + PAYLOAD)
        self.assertEqual(pkt_signature, right_answer)

        ############################
        # CASE 5
        # UDP: Enough length
        ############################
        
        # init
        pkt = Ether(type=0x800)/IP(src='127.0.0.1', options=['1','2','3'])/UDP(sport=80)/Raw('12312311111111111111111111111111')
        pkt_without_options = IP(src='127.0.0.1')/UDP(sport=80)/Raw('12312311111111111111111111111111')
        right_answer = [item for item in raw(pkt_without_options)]

        pkt_signature = _extract_pkt_signature(pkt, UDP)

        self.assertEqual(len(pkt_signature), IP2TCP_HEADER_LEN + PAYLOAD)
        self.assertEqual(pkt_signature, right_answer)

        ############################
        # CASE 6
        # UDP: Enough length
        ############################
        
        # init
        pkt = Ether(type=0x800)/IP(src='127.0.0.1', options=['1','2','3'])/UDP(sport=80)/Raw('1231231111111111111111111111111132131')
        pkt_without_options = IP(src='127.0.0.1')/UDP(sport=80)/Raw('12312311111111111111111111111111')
        right_answer = [item for item in raw(pkt_without_options)]

        pkt_signature = _extract_pkt_signature(pkt, UDP)

        self.assertEqual(len(pkt_signature), IP2TCP_HEADER_LEN + PAYLOAD)
        self.assertEqual(pkt_signature, right_answer)
    
    #TODO:
    # 1. not test special case
    def test_extract_session_info(self):
        """ Test if _extract_session_info() functions well """

        #########
        # CASE 1
        # TCP 
        #########
        tcp_session = 'TCP 192.168.0.1:80 > 127.0.0.1:443'
        right_answer = [1]
        right_answer.extend([item for item in int(IPv4Address('192.168.0.1')).to_bytes(4, byteorder='big')])
        right_answer.append(0)
        right_answer.append(80)
        right_answer.extend([item for item in int(IPv4Address('127.0.0.1')).to_bytes(4, byteorder='big')])
        right_answer.append(1)
        right_answer.append(187)

        self.assertEqual(_extract_session_info(None, tcp_session, TCP), right_answer)

         #########
        # CASE 2
        # UDP
        #########
        udp_session = 'UDP 192.168.0.1:80 > 127.0.0.1:443'
        right_answer = [0]
        right_answer.extend([item for item in int(IPv4Address('192.168.0.1')).to_bytes(4, byteorder='big')])
        right_answer.append(0)
        right_answer.append(80)
        right_answer.extend([item for item in int(IPv4Address('127.0.0.1')).to_bytes(4, byteorder='big')])
        right_answer.append(1)
        right_answer.append(187)

        self.assertEqual(_extract_session_info(None, udp_session, UDP), right_answer)

######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()