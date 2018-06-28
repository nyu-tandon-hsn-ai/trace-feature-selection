import sys
from img_feature import tcp_img, udp_img
from os import listdir
from os.path import isfile, join

if __name__ == '__main__':
    if len(sys.argv) != 3:
        exit(1)
    path = sys.argv[1]
    max_pkts_per_flow = int(sys.argv[2])

    filenames = [join(path,f) for f in listdir(path) if isfile(join(path, f))]
    print(filenames)
    tcp_img(filenames, max_pkts_per_flow=max_pkts_per_flow, train_ratio=0.8, compress=True)

