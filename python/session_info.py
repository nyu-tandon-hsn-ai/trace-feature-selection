from scapy.all import *
from ipaddress import IPv4Address

def extract_session_info(session_str):
    """
    Extract session information from a `scapy`-style session string
    Only for TCP and UDP protocols and IPv4 address now

    Parameters
    ----------
    session_str : str
        `scapy`-style session string, e.g. `TCP 131.202.240.87:64345 > 64.12.27.65:443`
    
    Returns
    -------
    :type dict
        contains the following structure
        {
            `is_tcp` : bool,
            `ip0` : int,
            `port0` : int,
            `ip1` : int,
            `port1` : int
        }
    
    Raises
    ------
    AssertionError : when not a valid `scapy`-style session string
    AssertionError : when neither TCP nor UDP protocol
    ValueError : when any field value is broken
    """
    sess_group=session_str.split()
    if len(sess_group) != 4 or sess_group[2] != '>':
        raise AssertionError('Not a valid scapy-style session string, e.g. UDP 1.2.3.4:5 > 5.6.7.8:9, found {string}'.format(string=session_str))

    if sess_group[0] != 'TCP' and sess_group[0] != 'UDP':
        raise AssertionError('Unsupported protocol type, only for TCP or UDP now but {protocol} was found'.format(protocol=sess_group[0]))
    
    protocol=sess_group[0]
    ip_ports=[sess_group[1], sess_group[3]]
    ips=[]
    ports=[]
    for index, ip_port in enumerate(ip_ports):
        if len(ip_port.split(':')) != 2:
            raise AssertionError('Should be in format "$IPv4Address{index}:$PORT{index}" but {string} was found'.format(index=index, string=ip_port))
        
        ips.append(int(IPv4Address(ip_port.split(':')[0])))
        ports.append(int(ip_port.split(':')[1]))
    
    session_info={'is_tcp':protocol=='TCP'}
    for index, ip in enumerate(ips):
        session_info['ip{index}'.format(index=index)]=ip
    for index, port in enumerate(ports):
        session_info['port{index}'.format(index=index)]=port
    return session_info