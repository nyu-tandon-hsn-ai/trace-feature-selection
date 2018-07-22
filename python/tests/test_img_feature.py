import unittest
from ipaddress import IPv4Address
import os

from scapy.all import *
import numpy as np

from img_feature import stringify_protocol, calculate_inter_arri_times, _extract_session_info
from img_feature.extractor import AboveIpLayerHeaderPayloadExtractor, AppLayerLengthExtractor

######################################################################
#  T E S T   C A S E S
######################################################################
# TODO: test more methods
class TestImageFeature(unittest.TestCase):
    """ Test Cases for extracting image features """
    
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

        ##########
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

    def test_stringify_protocol(self):
        """ Test if stringify_protocol() functions well """
        
        # TCP
        self.assertEqual(stringify_protocol(TCP), 'TCP')

        # UDP
        self.assertEqual(stringify_protocol(UDP), 'UDP')

        # IP_stringify_protocol
        with self.assertRaises(AssertionError):
            stringify_protocol(IP)
    
    def test_calculate_inter_arri_times(self):
        """ Test if calculate_inter_arri_times() functions well """

        #########
        # CASE 1
        #########

        # init
        arri_times = [0.2, 0.7, 0.9]

        # generate things
        right_answer = [0.5, 0.2]

        # run tested functions
        inter_arri_times = calculate_inter_arri_times(arri_times)

        self.assertTrue(np.isclose(inter_arri_times, right_answer).all())

        #########
        # CASE 2
        #########

        # init
        arri_times = []

        # generate things
        right_answer = []

        # run tested functions
        inter_arri_times = calculate_inter_arri_times(arri_times)

        self.assertEqual(inter_arri_times, right_answer)

# TODO: test more methods
class TestAboveIPExtractor(unittest.TestCase):
    """ Test class AboveIpLayerHeaderPayloadExtractor """

    @classmethod
    def setUpClass(cls):
        TestAboveIPExtractor.extractor = AboveIpLayerHeaderPayloadExtractor(max_pkts_per_flow=5,trans_layer_payload_len=20)
    
    @classmethod
    def tearDownClass(cls):
        del TestAboveIPExtractor.extractor

    def test_handle_flow_signatures(self):
        """ Test if TestAboveIPExtractor.extractor._handle_flow_signatures() functions well """
        
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
        flow_signatures_prime = TestAboveIPExtractor.extractor._handle_flow_signatures(flow_signatures, pkt_count, max_pkts_per_flow)

        self.assertTrue((flattened_signatures == flow_signatures_prime).all())

        ##########################
        # CASE 2
        # Not enough packet length
        ##########################

        # init things
        flow_signatures = [[1,2],[3,4]]
        pkt_count = 1
        appended = [0] * (AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + TestAboveIPExtractor.extractor._trans_layer_payload_len)
        max_pkts_per_flow = 2

        # generated things
        flattened_signatures = [1,2,3,4] + appended

        # run tested function
        flow_signatures_prime = TestAboveIPExtractor.extractor._handle_flow_signatures(flow_signatures, pkt_count, max_pkts_per_flow)

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

        inter_arri_times = TestAboveIPExtractor.extractor._extract_inter_arrival_time(arri_times, max_pkts_per_flow)

        self.assertTrue((inter_arri_times == right_answer).all())

        ############################
        # CASE 3
        # Less packets than expected
        ############################

        # init things
        arri_times = [0.8, 1.6, 2.5]
        max_pkts_per_flow = 4
        right_answer = [0, 255, 0]

        inter_arri_times = TestAboveIPExtractor.extractor._extract_inter_arrival_time(arri_times, max_pkts_per_flow)

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
                            [0] * (AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + TestAboveIPExtractor.extractor._trans_layer_payload_len - len(pkt_without_tcp_payload) - len(tcp_payload))
        right_answer = [item for item in raw(pkt_without_tcp_payload / Raw(tcp_payload_raw))]

        pkt_signature = TestAboveIPExtractor.extractor._extract_pkt_signature(pkt, TCP)

        self.assertEqual(len(pkt_signature), AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + TestAboveIPExtractor.extractor._trans_layer_payload_len)
        self.assertEqual(pkt_signature, right_answer)

        ############################
        # CASE 2
        # TCP: Enough length
        ############################
        
        # init
        pkt = Ether(type=0x800)/IP(src='127.0.0.1', options=['1','2','3'])/TCP(sport=80, options=['12', '43'])/Raw('12311234233213123231')
        pkt_without_options = IP(src='127.0.0.1')/TCP(sport=80)/Raw('12311234233213123231')
        right_answer = [item for item in raw(pkt_without_options)]

        pkt_signature = TestAboveIPExtractor.extractor._extract_pkt_signature(pkt, TCP)

        self.assertEqual(len(pkt_signature), AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + TestAboveIPExtractor.extractor._trans_layer_payload_len)
        self.assertEqual(pkt_signature, right_answer)

        ############################
        # CASE 3
        # TCP: length excceeds
        ############################
        
        # init
        pkt = Ether(type=0x800)/IP(src='127.0.0.1', options=['1','2','3'])/TCP(sport=80, options=['12', '43'])/Raw('12311234233213123231234')
        pkt_without_options = IP(src='127.0.0.1')/TCP(sport=80)/Raw('12311234233213123231')
        right_answer = [item for item in raw(pkt_without_options)]

        pkt_signature = TestAboveIPExtractor.extractor._extract_pkt_signature(pkt, TCP)

        self.assertEqual(len(pkt_signature), AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + TestAboveIPExtractor.extractor._trans_layer_payload_len)
        self.assertEqual(pkt_signature, right_answer)

        ################################
        # CASE 4
        # UDP: Less length than expected
        ################################
        
        # init
        pkt = Ether(type=0x800)/IP(src='127.0.0.1', options=['1','2','3'])/UDP(sport=80)/Raw('123123')
        pkt_without_udp_payload = IP(src='127.0.0.1')/UDP(sport=80)
        udp_payload_raw = [item for item in raw(Raw('123123'))] + \
                            [0] * (AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + TestAboveIPExtractor.extractor._trans_layer_payload_len - len(pkt_without_udp_payload) - len(Raw('123123')))
        right_answer = [item for item in raw(pkt_without_udp_payload / Raw(udp_payload_raw))]

        pkt_signature = TestAboveIPExtractor.extractor._extract_pkt_signature(pkt, UDP)

        self.assertEqual(len(pkt_signature), AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + TestAboveIPExtractor.extractor._trans_layer_payload_len)
        self.assertEqual(pkt_signature, right_answer)

        ############################
        # CASE 5
        # UDP: Enough length
        ############################
        
        # init
        pkt = Ether(type=0x800)/IP(src='127.0.0.1', options=['1','2','3'])/UDP(sport=80)/Raw('12312311111111111111111111111111')
        pkt_without_options = IP(src='127.0.0.1')/UDP(sport=80)/Raw('12312311111111111111111111111111')
        right_answer = [item for item in raw(pkt_without_options)]

        pkt_signature = TestAboveIPExtractor.extractor._extract_pkt_signature(pkt, UDP)

        self.assertEqual(len(pkt_signature), AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + TestAboveIPExtractor.extractor._trans_layer_payload_len)
        self.assertEqual(pkt_signature, right_answer)

        ############################
        # CASE 6
        # UDP: Enough length
        ############################
        
        # init
        pkt = Ether(type=0x800)/IP(src='127.0.0.1', options=['1','2','3'])/UDP(sport=80)/Raw('1231231111111111111111111111111132131')
        pkt_without_options = IP(src='127.0.0.1')/UDP(sport=80)/Raw('12312311111111111111111111111111')
        right_answer = [item for item in raw(pkt_without_options)]

        pkt_signature = TestAboveIPExtractor.extractor._extract_pkt_signature(pkt, UDP)

        self.assertEqual(len(pkt_signature), AboveIpLayerHeaderPayloadExtractor.IP2TRANS_LAYER_HEADER_LEN + TestAboveIPExtractor.extractor._trans_layer_payload_len)
        self.assertEqual(pkt_signature, right_answer)

# TODO: test more methods
class TestAppLayerLengthExtractor(unittest.TestCase):
    """ Test class AppLayerLengthExtractor """

    @classmethod
    def setUpClass(cls):
        TestAppLayerLengthExtractor.extractor = AppLayerLengthExtractor(trans_layer_payload_len=20)
        TestAppLayerLengthExtractor.test_path = os.path.join('tests', 'test_data', '1_packet.pcap')
    
    @classmethod
    def tearDownClass(cls):
        del TestAppLayerLengthExtractor.extractor
        del TestAppLayerLengthExtractor.test_path

    def test_extract_trans_layer_payload(self):
        """ Test if AppLayerLengthExtractor()._extract_trans_layer_payload() functions well """

        tcp_pkt = Ether(type=0x800)/IP(src='192.168.0.1')/TCP(sport=80)/Raw('This is a test message')
        res = TestAppLayerLengthExtractor.extractor._extract_trans_layer_payload(tcp_pkt, TCP)
        right_answer = [84, 104, 105, 115, 32, 105, 115, 32, 97, 32, 116, 101, 115, 116, 32, 109, 101, 115, 115, 97, 103, 101]
        self.assertEqual(res, right_answer)

        udp_pkt = Ether(type=0x800)/IP(src='192.168.0.1')/UDP(sport=80)/Raw('This is a test message')
        res = TestAppLayerLengthExtractor.extractor._extract_trans_layer_payload(udp_pkt, UDP)
        right_answer = [84, 104, 105, 115, 32, 105, 115, 32, 97, 32, 116, 101, 115, 116, 32, 109, 101, 115, 115, 97, 103, 101]
        self.assertEqual(res, right_answer)

    def test_extract_flow_img(self):
        """ Check extract_flow_img() in AppLayerLengthExtractor functions well """

        # UDP
        res = TestAppLayerLengthExtractor.extractor.extract_flow_img(TestAppLayerLengthExtractor.test_path, UDP)
        right_answer = np.array([[0, 10, 0, 0, 138, 0, 53, 10, 0, 0, 1, 227, 13, 0, 0, 0, 1, 0, 20, 45, 109, 129, 128, 0, 1, 0, 17, 0, 0, 0, 0, 3, 119, 119, 119, 16, 103, 111, 111]])
        self.assertTrue((res == right_answer).all())

        # TCP
        res = TestAppLayerLengthExtractor.extractor.extract_flow_img(TestAppLayerLengthExtractor.test_path, TCP)
        right_answer = np.array([])
        self.assertTrue((res == right_answer).all())
         

######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()