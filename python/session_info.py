from scapy.all import *

def extract_session_info(session_str):
    """
    Extract session information from a `scapy`-style session string
    Only for TCP and UDP protocols now

    Parameters
    ----------
    session_str : str
        `scapy`-style session string, e.g. `TCP 131.202.240.87:64345 > 64.12.27.65:443`
    
    Returns
    -------
    session_info : dict
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
    pass