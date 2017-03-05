import copy
import numpy as np
import os
from skimage.color import gray2rgb
from skimage.io import imread

import chainer
from chainer.dataset import download

from chainercv import utils


root = 'pfnet/chainercv/online_products'
url = 'ftp://cs.stanford.edu/cs/cvgl/Stanford_Online_Products.zip'


def _get_online_products():
    data_root = download.get_dataset_directory(root)
    base_path = os.path.join(data_root, 'Stanford_Online_Products')
    if os.path.exists(base_path):
        # skip downloading
        return base_path

    download_file_path = utils.cached_download(url)
    ext = os.path.splitext(url)[1]
    utils.extractall(download_file_path, data_root, ext)
    return base_path


class OnlineProductsDataset(chainer.dataset.DatasetMixin):

    """Simple class to load data from `Stanford Online Products Dataset`_.

    .. _`Stanford Online Products Dataset`:
        http://cvgl.stanford.edu/projects/lifted_struct

    All returned images are in RGB format.

    Args:
        data_dir (string): Path to the root of the training data. If this is
            ``auto``, this class will automatically download data for you
            under ``$CHAINER_DATASET_ROOT/pfnet/chainercv/online_products``.

    """

    def __init__(self, data_dir='auto'):
        if data_dir == 'auto':
            data_dir = _get_online_products()
        self.data_dir = data_dir

        self.class_ids = []
        self.super_class_ids = []
        self.paths = []
        for mode in ['train', 'test']:
            id_list_file = os.path.join(data_dir, 'Ebay_{}.txt'.format(mode))
            ids_tmp = [id_.strip().split() for id_ in open(id_list_file)][1:]
            self.class_ids += [int(id_[1]) for id_ in ids_tmp]
            self.super_class_ids += [int(id_[2]) for id_ in ids_tmp]
            self.paths += [os.path.join(data_dir, id_[3]) for id_ in ids_tmp]

        self.class_ids_dict = self._list_to_dict(self.class_ids)
        self.super_class_ids_dict = self._list_to_dict(self.super_class_ids)

    def _list_to_dict(self, l):
        dict_ = {}
        for i, v in enumerate(l):
            if v not in dict_:
                dict_[v] = []
            dict_[v].append(i)
        return dict_

    def __len__(self):
        return len(self.paths)

    def get_example(self, i):
        """Returns the i-th example.

        Returns a color image, class_id and super_class_id. The image is in CHW
        format.

        Args:
            i (int): The index of the example.
        Returns:
            i-th example
        """

        class_id = np.array(self.class_ids[i], np.int32)
        super_class_id = np.array(self.super_class_ids[i], np.int32)

        img = imread(self.paths[i])

        if img.ndim == 2:
            img = gray2rgb(img)
        img = img.transpose(2, 0, 1).astype(np.float32)
        return img, class_id, super_class_id

    def get_raw_data(self, i):
        """Returns the i-th example's image and class data in HWC format.

        The color image that is returned is RGB.

        Args:
            i (int): The index of the example.

        Returns:
            i-th example (image, class_id, super_class_id)

        """
        img = imread(self.paths[i])
        class_id = self.class_ids[i]
        super_class_id = self.super_class_ids[i]
        return img, class_id, super_class_id

    def get_ids(self, class_id):
        """Get indices of examples in the given class.

        Args:
            class_id (int): the class id.

        Returns:
            list of indices of examples whose class ids are `class_id`.

        """
        return copy.copy(self.class_ids_dict[class_id])


def get_online_products(data_dir='auto',
                        train_classes=None, test_classes=None):
    """Gets the `Stanford Online Products Dataset`_.

    This method returns train and test split of Online Products Dataset.
    It uses the first 11318 classes for training and remaining 11316 classes
    for testing.

    .. _`Stanford Online Products Dataset`:
        http://cvgl.stanford.edu/projects/lifted_struct

    Args:
        data_dir (string): Path to the root of the training data. If this is
            ``auto``, this class will automatically download data for you
            under ``$CHAINER_DATASET_ROOT/pfnet/chainercv/online_products``.
        train_classes (list of int): The train dataset will contain images
            whose class ids are included in ``train_classes``. If this is
            ``None``, the first 11318 classes are used as done in [Song].
        test_classes (list of int): The test dataset will contain images
            whose class ids are included in ``test_classes``. If this is
            ``None``, the last 11316 classes are used as done in [Song].

    .. [Song] Hyun Oh Song, Yu Xiang, Stefanie Jegelka, Silvio Savarese.
        Deep Metric Learning via Lifted Structured Feature Embedding.
        https://arxiv.org/abs/1511.06452.

    Returns:
        A tuple of two datasets
        :class:`chainercv.datasets.image_retrieval.OnlineProductsDataset` which
        are wrapped by :class:`chainercv.wrappers.KeepSubsetWrapper`.
        The first dataset is for training and the second is for testing.

    """
    if train_classes is None:
        train_classes = range(1, 11319)
    if test_classes is None:
        test_classes = range(11319, 22634 + 1)
    dataset = OnlineProductsDataset(data_dir)

    train_ids = []
    for i in train_classes:
        train_ids += dataset.get_ids(i)
    test_ids = []
    for i in test_classes:
        test_ids += dataset.get_ids(i)

    train_dataset = KeepSubsetWrapper(
        dataset, train_ids, wrapped_func_names=['get_example', 'get_raw_data'])
    test_dataset = KeepSubsetWrapper(
        dataset, test_ids, wrapped_func_names=['get_example', 'get_raw_data'])
    return train_dataset, test_dataset


if __name__ == '__main__':
    train, test = get_online_products()
