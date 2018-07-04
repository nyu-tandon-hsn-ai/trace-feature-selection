import numpy as np
from scapy.all import *
from array import *
import os
from tqdm import tqdm

IP2TCP_HEADER_LEN = 40
PAYLOAD = 20

def _ip2trans_layer_pkt_header2bytes(pkt, trans_layer_type):
    # TODO:
    # temporarily just omit all the options fields
    # MAYBE a better solution: fill the options field with leading/trailing 0s
    pkt[IP].options = []
    if trans_layer_type is TCP:
        pkt[trans_layer_type].options = []

    # remove/pad the payload in transport layer header
    trans_bin_str = raw(pkt[trans_layer_type])
    pkt[IP].remove_payload()
    while len(pkt[IP]) + len(trans_bin_str) < IP2TCP_HEADER_LEN + PAYLOAD:
        trans_bin_str = trans_bin_str + b'\x00'
    trans_bin_str = trans_bin_str[:IP2TCP_HEADER_LEN + PAYLOAD - len(pkt[IP])]

    # convert binary string to bytes
    pkt_header_bin_str = raw(pkt[IP])
    pkt_header_bytes = []
    for byte in pkt_header_bin_str + trans_bin_str:
        pkt_header_bytes.append(byte)
    return pkt_header_bytes

def _calculate_inter_arri_times(arri_times):
    inter_arri_times = []
    for i in range(1, len(arri_times)):
        inter_arri_times.append(arri_times[i] - arri_times[i - 1])
    return inter_arri_times

def _normalize_to(data, from_low=None, from_high=None, to_low=None, to_high=None):
    data = np.array(data)
    if from_low is None and from_high is None:
        from_low = np.min(data)
        from_high = np.max(data)
    data = (data - from_low) / (from_high - from_low)
    # downcast here
    return (data * (to_high - to_low) + to_low).astype(np.int32)

def _layer_feat(filename, trans_layer_type, max_pkts_per_flow):
    # read pcap file
    pcap_file = rdpcap(filename)

    # get all sessions
    sessions = pcap_file.sessions()

    # store all the features
    feat = []
    for session in tqdm(sessions, desc='Session'):
        # it is only until max_pkts_per_flow number of trans_layer_type packets have been captured
        # will we continue to do things
        pkt_count = 0
        headers = []
        arri_times = []
        for pkt in sessions[session]:
            # TODO:
            # Ignore IPv6 for now
            if IP in pkt and trans_layer_type in pkt:
                headers.append(_ip2trans_layer_pkt_header2bytes(pkt, trans_layer_type))
                arri_times.append(pkt.time)
                pkt_count += 1
                if pkt_count == max_pkts_per_flow:
                    break
        if pkt_count < max_pkts_per_flow:
            continue
        elif pkt_count > max_pkts_per_flow:
            raise AssertionError()

        # flatten transport layer packet headers
        headers = np.array(headers)
        row, col = headers.shape
        headers = headers.flatten()
        assert row * col == headers.shape[0]

        # calculate inter arrival times and do normalization
        inter_arri_times = _calculate_inter_arri_times(arri_times)
        if len(inter_arri_times) > 0:
            inter_arri_times = _normalize_to(inter_arri_times, to_low=0, to_high=255)

        # concatenate all the sub-features\
        single_feat = np.append(inter_arri_times, headers)
        feat.append(single_feat)
    return np.array(feat, dtype=np.int32)

def _append2bin_array(bin_array, num):
    '''
    Convert num to hex format and append to bin_array
    '''
    hex_val = hex(num) # number of num in HEX
    while len(hex_val[2:]) < 4:
        hex_val = '0x' + '0' + hex_val[2:]
    bin_array.append(int('0x'+hex_val[2],16))
    bin_array.append(int('0x'+hex_val[3],16))
    bin_array.append(int('0x'+hex_val[4],16))
    bin_array.append(int('0x'+hex_val[5],16))
    return bin_array

def _generate_idx_header(img_shape):
    '''
    Generate idx header with given img_shape
    '''
    header = array('B')
    header.extend([0,0,8,len(img_shape)])

    for shape in img_shape:
        _append2bin_array(header, shape)
    return header

def _save_idx_file(data, filename, compress=True):
    file_obj = open(filename, 'wb')
    data.tofile(file_obj)
    file_obj.close()
    if compress is True:
        os.system('gzip ' + filename)

def _generate_img_file_data(data):
    img_file_data = _generate_idx_header(data.shape)
    for img in tqdm(data, desc='Image'):
        for pixel in img:
            _append2bin_array(img_file_data, pixel)
    return img_file_data

def _generate_label_file_data(labels):
    label_file_data = _generate_idx_header(labels.shape)
    for label in tqdm(labels, desc='Label'):
        _append2bin_array(label_file_data, label)
    return label_file_data

#TODO
def _balance_data(data, all_labels):
    label2img = {label:[] for label in all_labels}
    for img, label in data:
        if label not in label2img:
            raise AssertionError('Data contains labels that are not in all_labels')
        else:
            label2img[label].append(img)
    label2img = {label:np.array(imgs) for label, imgs in label2img.items()}

    for label, imgs in label2img.items():
        if imgs.shape[0] == 0:
            raise AssertionError('No data for label {label}'.format(label=label))

    min_label = reduce(lambda x,y:x if label2img[x].shape[0] < label2img[y].shape[0] else y, all_labels)

    downsampled_data = []
    for label in all_labels:
        downsampled_imgs = label2img[label][np.random.choice(label2img[label].shape[0], label2img[min_label].shape[0], replace=False)] 
        downsampled_labels = np.array([label for _ in range(downsampled_imgs.shape[0])])
        downsampled_data.extend(np.array(list(zip(downsampled_imgs, downsampled_labels))))
    return np.array(downsampled_data)

def _save_data_labels2idx_file(data, filename_prefix, train_ratio, compress):
    # calculate number of samples used for training
    train_num = int(data.shape[0] * train_ratio)

    # unzip
    imgs, labels = list(zip(*data))
    imgs, labels = np.array(imgs), np.array(labels)

    # generate image data for training and testing
    # and save them
    train_img_file_data = _generate_img_file_data(imgs[:train_num])
    test_img_file_data = _generate_img_file_data(imgs[train_num:])
    _save_idx_file(train_img_file_data, filename_prefix+'-train'+'-images-idx{channels}-ubyte'.format(channels=len(imgs.shape)), compress)
    _save_idx_file(test_img_file_data, filename_prefix+'-test'+'-images-idx{channels}-ubyte'.format(channels=len(imgs.shape)), compress)

    # generate labels data for training and testing
    # and save them
    train_labels_file_data = _generate_label_file_data(labels[:train_num])
    test_labels_file_data = _generate_label_file_data(labels[train_num:])
    _save_idx_file(train_labels_file_data, filename_prefix+'-train'+'-labels-idx{channels}-ubyte'.format(channels=len(labels.shape)), compress)
    _save_idx_file(test_labels_file_data, filename_prefix+'-test'+'-labels-idx{channels}-ubyte'.format(channels=len(labels.shape)), compress)

def _generate_img(filenames, filename_prefix, max_pkts_per_flow, train_ratio, compress, label_type='vpn'):
    '''
    Generate idx images
    '''
    img_data = None
    labels = None

    # TODO: refactor
    label_statistics = {}
    label2label_name = {}
    trans_flows = {'TCP':0, 'UDP':0}
    if label_type == 'vpn':
        label_statistics[0] = label_statistics[1] = 0
        label2label_name[0] = 'non-vpn'
        label2label_name[1] = 'vpn'
    elif label_type == 'skype':
        label_statistics[0] = label_statistics[1] = label_statistics[2] = label_statistics[3] = 0
        label2label_name[0] = 'chat'
        label2label_name[1] = 'audio'
        label2label_name[2] = 'video'
        label2label_name[3] = 'file'
    elif label_type == 'facebook':
        sub_categories = ['chat', 'audio', 'video']
        for i in range(len(sub_categories)):
            label_statistics[i] = 0
            label2label_name[i] = sub_categories[i]
    elif label_type == 'non-vpn-app':
        app_types = ['aim', 'email', 'spotify', 'icq', 'sftp', 'scp', 'torrent', 'facebook', 'gmail', 'hangout', 'netflix', 'ftps', 'skype', 'vimeo','tor', 'voipbuster', 'youtube']
        for i in range(len(app_types)):
            label_statistics[i] = 0
            label2label_name[i] = app_types[i]
    else:
        raise AssertionError('Unknwon label type {label_type}'.format(label_type=label_type))

    for trans_layer_type in [TCP, UDP]:
        # for each file, extract features and labels and concatenate into img_data and labels
        trans_layer_str = 'TCP' if trans_layer_type is TCP else 'UDP' if trans_layer_type is UDP else None
        valid_flows = 0
        for filename in tqdm(filenames, desc=trans_layer_str):
            file_img_data = _layer_feat(filename, trans_layer_type, max_pkts_per_flow)
            if img_data is None:
                # no flow
                if file_img_data.shape[0] > 0:
                    img_data = file_img_data
            else:
                # no flow
                if file_img_data.shape[0] > 0:
                    img_data = np.concatenate((img_data, file_img_data))

            label = None
            base_name = os.path.basename(filename)
            
            # TODO: refactor
            if label_type == 'vpn':
                label = 1 if base_name.lower().startswith('vpn') else 0
            elif label_type == 'skype':
                if not base_name.lower().startswith('skype'):
                    raise AssertionError('{filename} not a valid Skype file'.format(filename=filename))

                meta_info = [info.lower() for info in base_name[len('skype'):].split('_') if info is not '']
                this_sub_app_type = meta_info[0]

                # TODO: refactor
                known_types = [(0, 'chat'), (1,'audio'), (2,'video'), (3,'file')]
                # known_types = [(key, label2label_name[key]) for key in label2label_name.keys()]
                for sub_app_label, sub_app_type in known_types:
                    if this_sub_app_type.startswith(sub_app_type):
                        label = sub_app_label
                        break
                
                if label is None:
                    raise AssertionError('Unknown skype sub-category type')
            elif label_type == 'non-vpn-app':
                max_len = None
                temp_label = None
                for app_type_label in label2label_name.keys():
                    app_type = label2label_name[app_type_label]
                    if base_name.lower().startswith(app_type) and (temp_label is None or max_len < len(app_type)):
                        temp_label = app_type_label
                        max_len = len(app_type)
                label = temp_label
            elif label_type == 'facebook':
                sub_categories = ['chat', 'audio', 'video']
                if base_name.startswith('facebook_'):
                    for sub_category_label in label2label_name.keys():
                        if base_name[len('facebook_'):].startswith(label2label_name[sub_category_label]):
                            label = sub_category_label
                            break
                elif base_name.startswith('facebook'):
                     for sub_category_label in label2label_name.keys():
                        if base_name[len('facebook'):].startswith(label2label_name[sub_category_label]):
                            label = sub_category_label
                            break
                else:
                    raise AssertionError('{filename} not a facebook file'.format(filename=filename))
                
                if label is None:
                    raise AssertionError('Unknown facebook category type')
            else:
                raise AssertionError('Unknwon label type {label_type}'.format(label_type=label_type))
            
            assert label is not None

            label_statistics[label] += file_img_data.shape[0]
            valid_flows += file_img_data.shape[0]

            # TODO: refactor with list comprehension
            for _ in range(file_img_data.shape[0]):
                if labels is None:
                    labels = [label]
                else:
                    labels.append(label)
        trans_flows[trans_layer_str] += valid_flows

    print('raw' + str(trans_flows))
    labels = np.array(labels)

    # necessary guanratee
    assert img_data.shape[0] == labels.shape[0]

    # print out statistics
    print('raw ' + label_type + '-> ', end='')
    for key in label_statistics.keys():
        print(str(label2label_name[key]) + ':' + str(label_statistics[key]) + ' ', end='')
    print()

    data = np.array(list(zip(img_data, labels)))

    # balance data
    data = _balance_data(data, label2label_name.keys())

    # reset and do statistics again
    label_statistics = {label:0 for label in label_statistics.keys()}
    for img, label in data:
        label_statistics[label] += 1
    
    # TODO
    # refactor here
    # print out statistics
    print('sampled ' + label_type + '-> ', end='')
    for key in label_statistics.keys():
        print(str(label2label_name[key]) + ':' + str(label_statistics[key]) + ' ', end='')
    print()

    # shuffle
    np.random.shuffle(data)

    _save_data_labels2idx_file(data, filename_prefix, train_ratio, compress)

def img(filenames, max_pkts_per_flow, train_ratio=0.8, compress=False, label_type='vpn'):
    _generate_img(filenames,
                    '{pkts}pkts-subflow-{label_type}'.format(pkts=max_pkts_per_flow, label_type=label_type),
                    max_pkts_per_flow,
                    train_ratio=train_ratio,
                    compress=compress,
                    label_type=label_type)
