import sys
import time
from os import listdir
from os.path import isfile, join

import img_feature

def _main(*args):
    # TODO: parse arguments
    trace_dir = args[0]
    max_pkts_per_flow = int(args[1])
    label_type = args[2]
    save_path = args[3]
    train_ratio = float(args[4])

    # record start time
    start_time = time.time()
    print('{pkt}-pkt-sub-flow start'.format(pkt=max_pkts_per_flow))

    # extract image features
    trace_filenames = [join(trace_dir,f) for f in listdir(trace_dir) if isfile(join(trace_dir, f))]
    img_feature.extract(trace_filenames,
        max_pkts_per_flow=max_pkts_per_flow,
        train_ratio=train_ratio,
        compress=True,
        label_type=label_type)

    # total time
    print('Time elapsed for {pkt}-pkt-sub-flow: {duration} second(s)'.format(
        pkt=max_pkts_per_flow,
        duration=time.time() - start_time))
    # config.max_pkts_per_flow
    # config.train_ratio
    # config.label_mapper
    # config.label_extractor
    # config.data_saver
    # config.obj_name
    # data=_read_data(trace_dir, config)
    # config.data_saver.save(save_path)

if __name__ == '__main__':
    if len(sys.argv) != 6:
        exit(-1)
    _main(*sys.argv[1:])