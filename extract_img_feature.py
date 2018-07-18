import sys
import time
from os import listdir
from os.path import isfile, join
from collections import Counter
import argparse

import img_feature 
from img_feature.extractor import AboveIpLayerHeaderPayloadExtractor, AppLayerLengthExtractor
from data_saver import IdxFileSaver
from dataset.utils import train_test_split, balance_data
from label.mapper import SequentialLabelMapper, BinaryLabelMapper
from label.extractor import StartPositionLabelExtractor

def _save_data(data_saver, train, test, file_prefix):
    return [data_saver.save(train['images'], file_prefix + '-train-images'),
    data_saver.save(train['labels'], file_prefix + '-train-labels'),
    data_saver.save(test['images'], file_prefix + '-test-images'),
    data_saver.save(test['labels'], file_prefix + '-test-labels')]

# TODO?
def _get_label_mapper(label_type):
    if label_type == 'vpn':
        return BinaryLabelMapper('vpn')
    elif label_type == 'skype':
        return SequentialLabelMapper(['chat', 'audio', 'video', 'file'])
    elif label_type == 'facebook' or label_type == 'hangout':
        return SequentialLabelMapper(['chat', 'audio', 'video'])
    elif label_type == 'non-vpn-app':
        return SequentialLabelMapper(
            ['aim','email', 'spotify', 'icq', 'sftp',
            'scp', 'torrent', 'facebook', 'gmail',
            'hangout', 'netflix', 'ftps', 'skype',
            'vimeo','tor', 'voipbuster', 'youtube'])
    else:
        raise AssertionError('Unknwon label type {label_type}'.format(label_type=label_type))

# TODO?
def _get_label_extractor(label_type):
    if label_type == 'vpn' or label_type == 'non-vpn-app':
        return StartPositionLabelExtractor([0])
    elif label_type == 'skype':
        return StartPositionLabelExtractor([len(label_type+'_')])
    elif label_type == 'facebook':
        return StartPositionLabelExtractor([len(label_type+'_'), len(label_type)])
    elif label_type == 'hangout':
        return StartPositionLabelExtractor([len(label_type+'_'), len(label_type+'s_')])
    else:
        raise AssertionError('Unknwon label type {label_type}'.format(label_type=label_type))

# TODO?
def _get_img_feature_extractor(img_feature_type):
    if img_feature_type == 'ip-above':
        return AboveIpLayerHeaderPayloadExtractor(app_layer_payload_len=20)
    elif img_feature_type == 'payload-len':
        return AppLayerLengthExtractor()
    else:
        raise AssertionError('Unknown image feature type {}'.format(img_feature_type))

def _main():
    # parse arguments
    parser = argparse.ArgumentParser(description = 'Flow Image Feature Preprocessing')
    parser.add_argument('-td', '--trace-dir', help='trace directory')
    parser.add_argument('-m', '--max-pkts-per-flow', help='max packets per flow', type=int, default=10)
    parser.add_argument('-l', '--label-type', help='label type', default='skype')
    parser.add_argument('-s', '--save-path', help='saving path')
    parser.add_argument('-tr', '--train-ratio', help='training dataset ratio', type=float, default=0.8)
    parser.add_argument('-i', '--img-feature-type', help='image feature extractor type')
    args = parser.parse_args()

    trace_dir = args.trace_dir
    label_type = args.label_type
    save_path = args.save_path
    train_ratio = args.train_ratio
    img_feature_type = args.img_feature_type
    max_pkts_per_flow = args.max_pkts_per_flow

    # record start time
    start_time = time.time()

    # init several things
    img_feature_extractor = _get_img_feature_extractor(img_feature_type)
    data_saver = IdxFileSaver(save_path, compress_file=True)
    label_mapper = _get_label_mapper(label_type)
    label_extractor = _get_label_extractor(label_type)
    all_labels = [label_mapper.name2id(label_name) for label_name in label_mapper.options]

    # extract image features
    trace_filenames = [join(trace_dir,f) for f in listdir(trace_dir) if isfile(join(trace_dir, f))]
    data = img_feature.extract(trace_filenames,
                label_mapper=label_mapper,
                label_extractor=label_extractor,
                img_feature_extractor=img_feature_extractor,
                max_pkts_per_flow=max_pkts_per_flow)

    # raw statistics
    print('Raw->', Counter([label_mapper.id2name(label) for label in data['labels']]))

    # balance data among all labels
    data = balance_data(data, all_labels)

    # balanced statistics
    print('After balancing->', Counter([label_mapper.id2name(label) for label in data['labels']]))

    # do train test split and print stats
    train, test = train_test_split(data, all_labels, train_ratio=train_ratio)
    print('Train ratio->', train_ratio)
    print('Train stat->', Counter([label_mapper.id2name(label) for label in train['labels']]))
    print('Test stat->', Counter([label_mapper.id2name(label) for label in test['labels']]))

    # save data
    file_prefix = '{pkts}pkts-subflow-{label_type}'.format(
                        pkts=max_pkts_per_flow,
                        label_type=label_type)
    print('Saved path:', _save_data(data_saver, train, test, file_prefix))

    # total time
    print('Time elapsed : {duration} second(s)'.format(
        duration=time.time() - start_time))

if __name__ == '__main__':
    _main()