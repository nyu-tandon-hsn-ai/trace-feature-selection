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
        

######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()