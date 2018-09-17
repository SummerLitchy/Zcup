from mxnet import nd, image
import numpy as np
import os


from mxnet.gluon.model_zoo import vision
from mxnet.gluon import nn
import logging


def load_image(img_path, long_side_length):
    x = image.imread(img_path)
    x = image.resize_short(x, long_side_length)
    x, _ = image.center_crop(x, (448, 448))
    x = x.astype('float32')
    x = x / 255
    x = image.color_normalize(x,
                              mean=nd.array([0.485, 0.456, 0.406]),
                              std=nd.array([0.229, 0.224, 0.225]))
    x = x.reshape((1, 3, 448, 448))

    return x


def get_image_feature(img_path):
    img_net = vision.inception_v3(pretrained=True)
    img = load_image(img_path, 448)

    feature = img_net.features(img)
    logging.debug("feature shape is %s", feature.shape)
    feature = feature.reshape(-1)

    return feature


def get_processed_state(mode=None):
    tmp_path = 'tmp/'
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    file_list = os.listdir(tmp_path)
    idx = 0

    best_filename = None
    pre_str = mode

    for f in file_list:
        filename = f
        f = f.split('.')
        if len(f) != 2:
            continue
        if f[1] == 'npy':
            f = f[0].split('-')

            if f[0] == pre_str and len(f) == 2 and int(f[1]) > idx:
                idx = int(f[1])
                best_filename = 'tmp/' + filename

    print(mode, 'feature idx start from', idx)

    return idx, best_filename


data_path = {'train': './../data/train_img/',
             'val': './../data/train_img/',
             'test': './../data/test_img/'}


def output_image_feature(mode=None, val_cut_idx=0):
    image_feature = []

    if os.path.exists(mode+'_image.npy'):
        print(mode+'_image.npy exists, skip')
        return
    file_list = os.listdir(data_path[mode])
    file_list.sort()

    print('curremt mode is', mode, 'file length', len(file_list))
    processed_img_num, processed_img_filename = get_processed_state(mode)
    cur_img_idx = -1
    if processed_img_num != 0:
        image_feature = np.load(processed_img_filename).tolist()
    elif mode == 'val':  # start from beginning
        processed_img_num = val_cut_idx

    for filename in file_list:
        cur_img_idx += 1
        if cur_img_idx < processed_img_num:
            continue

        if cur_img_idx >= val_cut_idx and mode == 'train':
            break

        f = filename.split('.')
        if len(f) == 1 or f[1] != 'jpg':
            continue
        feature = get_image_feature(data_path[mode] + filename).asnumpy()
        image_feature.append(feature)

        if (cur_img_idx+1) % 100 == 0:
            print('100 of %s image is processed' % mode)
        if (cur_img_idx+1) % 1000 == 0:
            tmp_nd = np.vstack(image_feature)

            np.save('tmp/' + mode + '-' + str(cur_img_idx) + '.npy', tmp_nd)

    assert len(image_feature) != 0
    image_feature_nd = np.vstack(image_feature)
    print('check final shape', image_feature_nd.shape)

    np.save(mode + '_image.npy', image_feature_nd)

    # output feature to file
    # feature shape (2048, )


output_image_feature(mode='train', val_cut_idx=3000)
output_image_feature(mode='val', val_cut_idx=3000)
output_image_feature(mode='test')