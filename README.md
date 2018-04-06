# Tcp Trace Feature Selection
## Goal
Extract TCP feature from raw trace
## Requirement
- A virtual environment with `python 3.6`.*(You could use this [link](https://conda.io/docs/user-guide/tasks/manage-environments.html) to set up a virtual environment)*
- pip *(If you set up a virtual environment using what is mentioned above, you should be free from the problem)*
- tshark 2.4.3 _(detail see [tshark version](./tshark_version.txt))_
## Instructions
1. enter your virtual environment
1. if this is the first time you are using this
    1. run `pip install -r python_requirement.txt` to install required libraries
    1. run `jupyter nbextension enable --py --sys-prefix widgetsnbextension` before using jupyter to install visualization tools in jupyter
1. run `jupyter notebook` to use jupyter notebook
    1. if you are extracting features for **DDoS Detection**, use [extract_ddos_feature.ipynb](./extract_ddos_feature.ipynb)
    1. if you are extracting **packet-based features** for **application type detection**, use [extract_app_pkt_feature.ipynb](./extract_app_pkt_feature.ipynb)
    1. if you are extracting **flow-based features** for **application type detection**, use [extract_app_flow_feature.ipynb](./extract_app_flow_feature.ipynb)
    1. otherwise, feel free to hang around ;)
