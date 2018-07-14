import sys
import time
from os import listdir
from os.path import isfile, join

from img_feature import img

def time_record(func):
    def func_wrapper(*args, **kwargs):
        func(*args, **kwargs)
    return func_wrapper

@time_record
def my_img(*args, **kwargs):
    img(*args, **kwargs)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        exit(-1)
    path = sys.argv[1]
    max_pkts_per_flow = int(sys.argv[2])
    label_type = sys.argv[3]
    start_time = time.time()
    print('{pkt}-pkt-sub-flow start'.format(pkt=max_pkts_per_flow))

    filenames = [join(path,f) for f in listdir(path) if isfile(join(path, f))]
    img(filenames,
        max_pkts_per_flow=max_pkts_per_flow,
        train_ratio=0.5,
        compress=True,
        label_type=label_type)
    print('Time elapsed for {pkt}-pkt-sub-flow: {duration} second(s)'.format(
        pkt=max_pkts_per_flow,
        duration=time.time() - start_time))