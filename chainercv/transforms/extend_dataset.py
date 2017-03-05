import os
import shelve
import tempfile


def extend(dataset, transform, method_name='__getitem__'):
    method = getattr(dataset, method_name)

    def _extended(self, i):
        in_data = method(self, i)
        return transform(in_data)
    setattr(dataset, method_name, _extended)


def extend_cache(dataset, transform, method_name='__getitem__'):
    filename = os.path.join(tempfile.mkdtemp(), 'chainercv.db')
    cache = shelve.open(filename, protocol=2)

    method = getattr(dataset, method_name)

    def _extended(self, i):
        key = str(i)
        if key not in cache:
            in_data = method(self, i)
            cache[key] = transform(in_data)
        return cache[key]
    setattr(dataset, method_name, _extended)


if __name__ == '__main__':
    from chainercv.datasets import VOCSemanticSegmentationDataset
    from chainercv.transforms.random_crop_transform import random_crop
    dataset = VOCSemanticSegmentationDataset()

    def transform(in_data):
        return random_crop(in_data, (None, 256, 256))

    extend(dataset, transform)
    img, label = dataset.get_example(0)
