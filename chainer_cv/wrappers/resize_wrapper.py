import collections
import numpy as np
import skimage.transform

from chainer.utils import type_check

from chainer_cv.wrappers.dataset_wrapper import DatasetWrapper


class ResizeWrapper(DatasetWrapper):

    """Resize image to match a certain size.

    Args:
        dataset: a chainer.dataset.DatasetMixin to be wrapped.
        output_shape: the size of output image after padding. This needs to be
            in HWC format.
        resize_idx (int or list of ints): this wrapper will resize output of
            wrapped dataset's get_example whose index is in `resize_idx`.

    """

    def __init__(self, dataset, output_shape, resize_idx):
        super(ResizeWrapper, self).__init__(dataset)
        if len(output_shape) != 3:
            raise ValueError('output_shape needs to be of length 3')
        self.output_shape = output_shape
        if not isinstance(resize_idx, collections.Iterable):
            resize_idx = (resize_idx,)
        self.resize_idx = resize_idx

    def check_type_get_example(self, in_types):
        for idx in self.resize_idx:
            in_type = in_types[idx]
            type_check.expect(
                in_type.dtype.kind == 'f',
                in_type.ndim == 3
            )

    def get_example(self, i):
        """Returns the i-th example.

        All returned images are in CHW format.

        Args:
            i (int): The index of the example.

        Returns:
            i-th example.

        """
        in_data = self.dataset[i]
        out_data = list(in_data)
        for idx in self.resize_idx:
            img = in_data[idx]
            img = np.transpose(img, (1, 2, 0))
            scale = np.max(np.abs(img))
            out_img = skimage.transform.resize(
                img / scale, self.output_shape)
            out_data[idx] = out_img.transpose(2, 0, 1) * scale
        return tuple(out_data)


if __name__ == '__main__':
    from chainer_cv.datasets import get_online_products
    train, test = get_online_products()
    dataset = ResizeWrapper(train, (128, 128, 3), 0)
    img = dataset.get_example(0)[0]
    img = img.transpose(1, 2, 0).astype(np.uint8)
    # you can visualize img with matplotlib
