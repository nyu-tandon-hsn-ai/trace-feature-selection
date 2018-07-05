import unittest
import glob
import os
import sys, io
import filecmp
import packet_feature
from contextlib import redirect_stdout, redirect_stderr
from functools import partial

ONE_PKT_PCAP = os.path.join('tests','test_data','1_packet_tcp.pcapng')
GENERATED_ONE_PKT_CSV = os.path.join('tests','test_data','temp_1_packet_tcp.csv')
ONE_PKT_CSV = os.path.join('tests','test_data','1_packet_tcp.csv')
IS_CLUSTER=os.getenv('IS_CLUSTER', 'False') == 'True'

######################################################################
#  T E S T   C A S E S
######################################################################
class TestPacketFeature(unittest.TestCase):
    """ Test Cases for extracting packet features """

    def setUp(self):
        if os.path.exists(GENERATED_ONE_PKT_CSV):
            os.remove(GENERATED_ONE_PKT_CSV)
    
    def tearDown(self):
        if os.path.exists(GENERATED_ONE_PKT_CSV):
            os.remove(GENERATED_ONE_PKT_CSV)
    
    @staticmethod
    def _capture_stdout_stderr(func, times=1, *args):
        # redirect sys.stdout to a buffer
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            for _ in range(times):
                func(*args)

        out_data, err_data = out.getvalue(), err.getvalue()

        # close streams
        out.close()
        err.close()

        # return value
        return out_data, err_data

    def test_create_csv(self):
        """ Create feature from a pcap file with 1 packet and assert that it exists """
        out_data, err_data = TestPacketFeature._capture_stdout_stderr(partial(packet_feature.tcp_generate, is_cluster=IS_CLUSTER), 1, ONE_PKT_PCAP,GENERATED_ONE_PKT_CSV)

        # check something
        import pandas as pd
        test_csv=pd.read_csv(GENERATED_ONE_PKT_CSV)
        real_csv=pd.read_csv(ONE_PKT_CSV)
        print(test_csv)
        print(real_csv)
        self.assertTrue(filecmp.cmp(GENERATED_ONE_PKT_CSV, ONE_PKT_CSV,shallow=False))
        self.assertTrue(out_data == 'Conversion done\n')
        self.assertTrue(err_data == '')
        self.assertTrue(os.path.exists(GENERATED_ONE_PKT_CSV))

    def test_stderr_output(self):
        """ If print_err is set, something gets printed on screen """
        out_data, err_data = TestPacketFeature._capture_stdout_stderr(partial(packet_feature.tcp_generate, is_cluster=IS_CLUSTER), 1, ONE_PKT_PCAP,GENERATED_ONE_PKT_CSV, True)

        # check something
        self.assertTrue(filecmp.cmp(GENERATED_ONE_PKT_CSV, ONE_PKT_CSV,shallow=False))
        self.assertTrue(out_data == 'Conversion done\n')
        self.assertTrue(err_data == 'No error\n')
    
    def test_create_csv_file_twice(self):
        """ Create feature from a pcap file with 1 packet twice and assert that it exists and stdout should be something """
        # redirect sys.stdout to a buffer
        out_data, err_data = TestPacketFeature._capture_stdout_stderr(partial(packet_feature.tcp_generate, is_cluster=IS_CLUSTER), 2, ONE_PKT_PCAP,GENERATED_ONE_PKT_CSV)

        # check something
        self.assertTrue(filecmp.cmp(GENERATED_ONE_PKT_CSV, ONE_PKT_CSV,shallow=False))
        self.assertTrue(out_data == 'Conversion done\nConversion done\n')
        self.assertTrue(err_data == '')
        self.assertTrue(os.path.exists(GENERATED_ONE_PKT_CSV))


######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
    # suite = unittest.TestLoader().loadTestsFromTestCase(TestPets)
    # unittest.TextTestRunner(verbosity=2).run(suite)