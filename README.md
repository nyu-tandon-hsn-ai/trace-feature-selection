# Trace Feature Selection
## Goal
Extract features from raw trace
## Requirement
- A virtual environment with `python 3.6`.*(You could use this [link](https://conda.io/docs/user-guide/tasks/manage-environments.html) to set up a virtual environment)*
- pip *(If you set up a virtual environment using what is mentioned above, you should be free from the problem)*
- tshark 2.4.3 _(detail see [tshark version](./tshark_version.txt))_
## Instructions
1. enter your virtual environment
1. if this is the first time you are using this
    1. run `pip install -r requirements.txt` to install required libraries
    1. run `jupyter nbextension enable --py --sys-prefix widgetsnbextension` before using jupyter to install visualization tools in jupyter
1. extract features
    - run `jupyter notebook` to use jupyter notebook
        - if you are extracting features for **DDoS Detection**, use [extract_ddos_feature.ipynb](./extract_ddos_feature.ipynb)
        - if you are extracting **packet-based features** for **application type detection**, use [extract_app_pkt_feature.ipynb](./extract_app_pkt_feature.ipynb)
        - if you are extracting **flow-based features** for **application type detection**, use [extract_app_flow_feature.ipynb](./extract_app_flow_feature.ipynb)
    - extract flow image features
        1. set environment variables for `PYTHONPATH`
            ```shell
            export PYTHONPATH=$(pwd)/python:$PYTHONPATH
            ```
        2. extract image features
            - extract above IP layer, IP w/ transport layer (only for TCP or UDP) header with fixed-length transport layer payload.
                ```shell
                python3 extract_img_feature.py -td ${YOUR_TRACE_DIR} -l ${YOUR_LABEL_TYPE} -m ${MAX_PKTS_PER_FLOW} -s ${SAVING_PATH} -tr ${TRAINING_RATIO} -i ip-above
                ```
                e.g. 
                ```shell
                python3 extract_img_feature.py -td data/unb-vpn-app/pcap-trace/vpn-test/ -l vpn -m 10 -s vpn-test/ -tr 0.8 -i ip-above
                ```
            - extract fixed-length transport layer payload
                ```shell
                python3 extract_img_feature.py -td ${YOUR_TRACE_DIR} -l ${YOUR_LABEL_TYPE} -s ${SAVING_PATH} -tr ${TRAINING_RATIO} -i payload-len
                ```
                e.g.
                ```shell
                python3 extract_img_feature.py -td data/unb-vpn-app/pcap-trace/vpn-test/ -l vpn -s vpn-test/ -tr 0.8 -i payload-len
                ```
            - APPENDIX: label type contains the following for now
                * vpn
                * non-vpn-app
                * skype
                * hangout
                * facebook
