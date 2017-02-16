import numpy as np
import os.path as osp
import tempfile

from chainer_cv.wrappers.dataset_wrapper import DatasetWrapper


class CacheDatasetWrapper(DatasetWrapper):
    """This caches outputs from wrapped dataset and reuse them.

    Note that it converts output from wrapped dataset into numpy.ndarray.
    """

    def __init__(self, dataset):
        super(CacheDatasetWrapper, self).__init__(dataset)
        self.initialized = False
        self.cache = None
        self.has_cache = [False] * len(self.dataset)
        self.n_arrays = None

    def get_example(self, i):
        if not self.initialized:
            self._initialize(i)
            self.initialized = True

        if not self.has_cache[i]:
            arrays = self.dataset[i]
            for arr_i, a in enumerate(arrays):
                self.cache[arr_i][i] = np.array(a)
            self.has_cache[i] = True
        return tuple([a_cache[i] for a_cache in self.cache])

    def _initialize(self, i):
        arrays = self.dataset[i]
        self.n_arrays = len(arrays)
        self.cache = [None] * self.n_arrays
        for arr_i, a in enumerate(arrays):
            if not isinstance(np.array(a), np.ndarray):
                raise ValueError(
                    'The dataset wrapped by CacheDatasetWrapper needs to '
                    'return tuple of numpy.ndarray')
            shape = (len(self),) + a.shape
            filename = osp.join(
                tempfile.mkdtemp(), 'cache_{}.data'.format(arr_i))
            self.cache[arr_i] = np.memmap(
                filename, dtype=a.dtype, mode='w+', shape=shape)


if __name__ == '__main__':
    import chainer
    train, test = chainer.datasets.get_mnist()
    cached_dataset = CacheDatasetWrapper(train)
