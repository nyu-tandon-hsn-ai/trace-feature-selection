import sys
from img_feature import img
from os import listdir
from os.path import isfile, join

if __name__ == '__main__':
    if len(sys.argv) != 4:
        exit(1)
    path = sys.argv[1]
    max_pkts_per_flow = int(sys.argv[2])
    label_type = sys.argv[3]

    filenames = [join(path,f) for f in listdir(path) if isfile(join(path, f))]
    img(filenames, max_pkts_per_flow=max_pkts_per_flow, train_ratio=0.8, compress=True, label_type=label_type)

