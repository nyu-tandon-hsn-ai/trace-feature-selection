import unittest
from ipaddress import IPv4Address

from session_info import extract_session_info

######################################################################
#  T E S T   C A S E S
######################################################################
class TestSessionInfo(unittest.TestCase):
    """ Test Cases for extracting session information from session string """

    def test_valid_session_str(self):
        """ Generate session information from valid session string """

        # Test TCP session
        session_info = extract_session_info('TCP 131.202.240.87:64345 > 64.12.27.65:443')
        self.assertEqual(session_info['is_tcp'], True)
        self.assertEqual(str(IPv4Address(session_info['ip0'])), '131.202.240.87')
        self.assertEqual(session_info['port0'], 64345)
        self.assertEqual(str(IPv4Address(session_info['ip1'])), '64.12.27.65')
        self.assertEqual(session_info['port1'], 443)

        # Test UDP session
        session_info = extract_session_info('UDP 131.202.240.87:64761 > 224.0.0.252:5355')
        self.assertEqual(session_info['is_tcp'], False)
        self.assertEqual(str(IPv4Address(session_info['ip0'])), '131.202.240.87')
        self.assertEqual(session_info['port0'], 64761)
        self.assertEqual(str(IPv4Address(session_info['ip1'])), '224.0.0.252')
        self.assertEqual(session_info['port1'], 5355)

    def test_invalid_session_str(self):
        """ Generate session information from invalid session string """
        with self.assertRaises(AssertionError):
            extract_session_info('Hello, this is a test message')

    def test_unsupported_protocol(self):
        """ Generate session information from valid session string but unsupported protocols """
        with self.assertRaises(AssertionError):
            extract_session_info('ARP 131.202.240.87 > 131.202.243.254')
    
    def test_bad_field_values(self):
        """ Generate session information from valid session string but with bad values """
        with self.assertRaises(ValueError):
            extract_session_info('TCP 131.202.256.87:64345 > 64.12.27.65:443')
        with self.assertRaises(ValueError):
            extract_session_info('TCP 131.202.253.87:64345 > 258.12.27.65:443')
        
        with self.assertRaises(ValueError):
            extract_session_info('TCP 131.202.256.87:100000 > 64.12.27.65:443')
        with self.assertRaises(ValueError):
            extract_session_info('TCP 131.202.256.87:64345 > 64.12.27.65:100000')

######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()