import sys
import time
from os import listdir
from os.path import isfile, join

from img_feature import img

if __name__ == '__main__':
    if len(sys.argv) != 4:
        exit(1)
    tot_start_time = time.time()
    path = sys.argv[1]
    pkts=list(map(int,sys.argv[2].split(',')))
    label_type = sys.argv[3]

    filenames = [join(path,f) for f in listdir(path) if isfile(join(path, f))]
    for max_pkts_per_flow in pkts:
        start_time = time.time()
        img(filenames, max_pkts_per_flow=max_pkts_per_flow, train_ratio=0.8, compress=True, label_type=label_type)
        print('Time elapsed for {pkt}-pkt-sub-flow: {duration} second(s)'.format(pkt=max_pkts_per_flow, duration=time.time() - start_time))
    print('Total time: {duration} second(s)'.format(duration=time.time() - tot_start_time))