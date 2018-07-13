from functools import reduce

import numpy as np
from nose.tools import nottest

#TODO: just downsampling now
def balance_data(data, all_labels):
    """
    Balance data of different labels

    Parameters
    ----------
    data: dict
        images: `numpy.ndarray`
        labels: `numpy.ndarray`
    all_labels: list[int]

    Returns
    -------
    dict
        images: `numpy.ndarray`
        labels: `numpy.ndarray`
    """

    #TODO
    assert data['images'].shape[0] == data['labels'].shape[0]

    label2imgs = extract_label2imgs(data, all_labels)

    min_label = reduce(lambda x,y:x if label2imgs[x].shape[0] < label2imgs[y].shape[0] else y, all_labels)
    min_label_num = label2imgs[min_label].shape[0]

    downsampled_data = {'images':None, 'labels':np.array([], dtype=np.int32)}
    for label in all_labels:
        label_num = label2imgs[label].shape[0]
        chosen_img_indexes = np.random.choice(label_num, min_label_num, replace=False)
        downsampled_imgs = label2imgs[label][chosen_img_indexes] 
        downsampled_labels = np.array([label for _ in range(downsampled_imgs.shape[0])])
        if downsampled_data['images'] is None:
            downsampled_data['images'] = downsampled_imgs
        else:
            downsampled_data['images'] = np.concatenate((downsampled_data['images'],downsampled_imgs))
        downsampled_data['labels'] = np.append(downsampled_data['labels'], downsampled_labels)
    downsampled_data['images'] = np.array(downsampled_data['images'])
    return downsampled_data

def extract_label2imgs(data, all_labels):
    """
    Check if labels in data are consistent with all_labels

    Parameters
    ----------
    data: dict
        images: `numpy.ndarray`
        labels: `numpy.ndarray`
    all_labels: list[int]
    
    Returns
    -------
    dict
        label:int -> images with that label:`numpy.ndarray`

    Raises
    ------
    AssertionError: if all_labels contains more labels than data or vice versa
    """
    #TODO
    assert data['images'].shape[0] == data['labels'].shape[0]

    label2imgs = {label:[] for label in all_labels}
    for img, label in zip(data['images'], data['labels']):
        if label not in label2imgs:
            raise AssertionError('Data contains labels that are not in all_labels, like {label}'.format(label=label))
        else:
            label2imgs[label].append(img)
    label2imgs = {label:np.array(imgs) for label, imgs in label2imgs.items()}

    for label, imgs in label2imgs.items():
        if imgs.shape[0] == 0:
            raise AssertionError('No data for label {label}'.format(label=label))
    return label2imgs

@nottest
def train_test_split(data, all_labels, train_ratio):
    """
    Split training and testing data based on train_ratio and balance_train

    Parameters
    ----------
    data: dict
        images: `numpy.ndarray`
        labels: `numpy.ndarray`
    all_labels: list[string]
    train_ratio: float
    balance_train: bool
        whether make labels in training data as average as possible

    Returns
    -------
    (train, test)
        train: dict
            images: `numpy.ndarray`
            labels: `numpy.ndarray`
        test: dict
            images: `numpy.ndarray`
            labels: `numpy.ndarray`
    
    Raises
    ------
    AssertionError: if training data point number is less than label number
    AssertionError: when any label has less data points than or equal to training data point number per label
    """
    #TODO
    assert data['images'].shape[0] == data['labels'].shape[0]

    # shuffle
    data = shuffle(data)

    label2imgs = extract_label2imgs(data, all_labels)

    # calculate number of samples used for training
    data_len = data['images'].shape[0] 
    train_num = int(data_len * train_ratio)

    if train_num < len(all_labels):
        raise AssertionError('Training data point number {train_num} is less than label count {label_num}'.format(
            train_num=train_num,
            label_num=len(all_labels)
        ))

    train={'images':np.array([], dtype=np.float32), 'labels':np.array([], dtype=np.int32)}
    test={'images':np.array([], dtype=np.float32), 'labels':np.array([], dtype=np.int32)}

    # calculate things
    each_label_num = train_num // len(all_labels)
    labels_with_one_more = np.random.choice(all_labels, train_num % len(all_labels))

    # balance training data
    for label in all_labels:
        train_num_per_label = each_label_num + 1 if label in labels_with_one_more else each_label_num
        if label2imgs[label].shape[0] <= train_num_per_label:
            raise AssertionError('Label {label} has {label_num} data points, less than or equal to training data point number per label, {train_num_per_label}'.format(
                label=label,
                label_num=label2imgs[label].shape[0],
                train_num_per_label=train_num_per_label
            ))
        train['images'] = np.append(train['images'], label2imgs[label][:train_num_per_label])
        train['labels'] = np.append(train['labels'], [label] * train_num_per_label)

        test['images'] = np.append(test['images'], label2imgs[label][train_num_per_label:])
        test['labels'] = np.append(test['labels'], [label] * (label2imgs[label].shape[0] - train_num_per_label))
    return train, test

def shuffle(data):
    """
    Shuffle data and return new

    Parameters
    ----------
    data: dict
        images: `numpy.ndarray`
        labels: `numpy.ndarray`

    Returns
    -------
    new shuffled data: dict
        images: `numpy.ndarray`
        labels: `numpy.ndarray`
    """
    #TODO
    assert data['images'].shape[0] == data['labels'].shape[0]

    copied_data = {'images': np.copy(data['images']), 'labels': np.copy(data['labels'])}
    copied_data_len = copied_data['images'].shape[0]
    indexes = np.random.permutation(copied_data_len)
    copied_data['images'] = copied_data['images'][indexes]
    copied_data['labels'] = copied_data['labels'][indexes]
    return copied_data