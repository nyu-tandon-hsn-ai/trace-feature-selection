import unittest

import numpy as np

from dataset.utils import balance_data, extract_label2imgs, train_test_split, shuffle

######################################################################
#  T E S T   C A S E S
######################################################################
class TestDataset(unittest.TestCase):
    """ Test Cases for dataset """

    def test_shuffle(self):
        """ Test dataset shuffle """
        images = [1,2,3]
        labels = [4,5,6]
        img2label = {}
        for image, label in zip(images, labels):
            img2label[image] = label
        data = {'images': np.array(images), 'labels': np.array(labels)}
        test_times = 3

        for _ in range(test_times):
            shuffled_data = shuffle(data)

            self.assertIsNot(data, shuffled_data)
            self.assertEqual(shuffled_data['images'].shape[0], data['images'].shape[0])
            self.assertEqual(shuffled_data['labels'].shape[0], data['labels'].shape[0])

            for key in img2label.keys():
                self.assertIn(key, shuffled_data['images'])
                index = np.where(shuffled_data['images'] == key)[0][0]
                val = shuffled_data['labels'][index]
                self.assertEqual(img2label[key], val)
    def test_extract_label2imgs(self):
        """ Test dataset extract_label2imgs """
        images = [1,2,3]
        labels = [4,4,6]
        all_labels = [4,6]
        self_label2imgs = {}
        for image, label in zip(images, labels):
            if label not in self_label2imgs:
                self_label2imgs[label] = [image]
            else:
                self_label2imgs[label].append(image)
        data = {'images': np.array(images), 'labels': np.array(labels)}

        label2imgs = extract_label2imgs(data, all_labels)
        self.assertEqual(set(label2imgs.keys()), set(labels))
        for label in set(labels):
            label2imgs[label].sort()
            self_label2imgs[label].sort()
            self.assertTrue((self_label2imgs[label] == label2imgs[label]).all())

######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()