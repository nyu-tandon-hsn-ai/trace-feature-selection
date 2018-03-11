import unittest
import glob
import os
import sys, io
import packet_feature
from contextlib import redirect_stdout, redirect_stderr

ONE_PKT_PCAP = 'test_data/1_packet.pcap'
ONE_PKT_CSV = 'test_data/1_packet.csv'

######################################################################
#  T E S T   C A S E S
######################################################################
class TestPacketFeature(unittest.TestCase):
    """ Test Cases for extracting packet features """

    def setUp(self):
        pass
    
    def tearDown(self):
        for f in glob.glob('test_data/*.csv'):
            os.remove(f)
    
    @staticmethod
    def _capture_stdout_stderr(func, times=1, *args):
        # redirect sys.stdout to a buffer
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            for i in range(times):
                func(*args)

        out_data, err_data = out.getvalue(), err.getvalue()

        # close streams
        out.close()
        err.close()

        # return value
        return out_data, err_data

    def test_tshark_create_file(self):
        """ Create feature from a pcap file with 1 packet and assert that it exists """
        out_data, err_data = TestPacketFeature._capture_stdout_stderr(packet_feature.tshark, 1, ONE_PKT_PCAP,ONE_PKT_CSV)

        # checkout something has been printed
        self.assertTrue(out_data == '\n')
        self.assertTrue(err_data == '')
        self.assertTrue(os.path.exists(ONE_PKT_CSV))

    def test_tshark_output(self):
        """ If print_err is set, something gets printed on screen """
        out_data, err_data = TestPacketFeature._capture_stdout_stderr(packet_feature.tshark, 1, ONE_PKT_PCAP,ONE_PKT_CSV, True)

        # checkout something has been printed
        self.assertTrue(out_data == '\n')
        self.assertTrue(err_data == 'No error\n')
    
    def test_tshark_create_file_twice(self):
        """ Create feature from a pcap file with 1 packet twice and assert that it exists and stdout should be something """
        # redirect sys.stdout to a buffer
        out_data, err_data = TestPacketFeature._capture_stdout_stderr(packet_feature.tshark, 2, ONE_PKT_PCAP,ONE_PKT_CSV)

        # checkout something has been printed
        self.assertTrue(out_data == '\nFeature file already exists.\n')
        self.assertTrue(err_data == '')
        self.assertTrue(os.path.exists(ONE_PKT_CSV))


######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
    # suite = unittest.TestLoader().loadTestsFromTestCase(TestPets)
    # unittest.TextTestRunner(verbosity=2).run(suite)