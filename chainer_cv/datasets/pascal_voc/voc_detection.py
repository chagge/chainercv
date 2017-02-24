import glob
import numpy as np
import os.path as osp
from skimage.io import imread
import xml.etree.ElementTree as ET

import chainer

import voc_utils


class VOCDetectionDataset(chainer.dataset.DatasetMixin):

    """Dataset class for the detection task of Pascal VOC2012.

    The index corresponds to each bounding box

    Args:
        data_dir (string): Path to the root of the training data. If this is
            'auto', this class will automatically download data for you
            under ``$CHAINER_DATASET_ROOT/yuyu2172/chainer-cv/pascal_voc``.
        use_difficult (bool)
        bgr (bool): If true, method `get_example` will return an image in BGR
            format.

    """

    labels = voc_utils.pascal_voc_labels

    def __init__(self, data_dir='auto', mode='train', use_difficult=False,
                 bgr=True):
        if data_dir == 'auto':
            data_dir = voc_utils.get_pascal_voc()

        if mode not in ['train', 'trainval', 'val']:
            raise ValueError(
                'please pick mode from \'train\', \'trainval\', \'val\'')

        id_list_file = osp.join(
            data_dir, 'ImageSets/Main/{0}.txt'.format(mode))

        self.ids = [id_.strip() for id_ in open(id_list_file)]

        self.data_dir = data_dir
        self.use_difficult = use_difficult

        self.objects = self._collect_objects(
            self.data_dir, self.ids, self.use_difficult)
        self.keys = self.objects.keys()
        self.bgr = bgr

    def _collect_objects(self, data_dir, ids, use_difficult):
        objects = {}
        anno_dir = osp.join(data_dir, 'Annotations')
        for fn in glob.glob('{}/*.xml'.format(anno_dir)):
            tree = ET.parse(fn)
            filename = tree.find('filename').text
            img_id = osp.splitext(filename)[0]
            # skip annotation that is not included in ids
            if img_id not in ids:
                continue

            datums = []
            for obj in tree.findall('object'):
                # when in not using difficult mode, and the object is
                # difficult, skipt it.
                if not use_difficult and int(obj.find('difficult').text) == 1:
                    continue

                bbox_ = obj.find('bndbox')  # bndbox is the key used by raw VOC
                bbox = [int(bbox_.find('xmin').text),
                        int(bbox_.find('ymin').text),
                        int(bbox_.find('xmax').text),
                        int(bbox_.find('ymax').text)]
                # make pixel indexes 0-based
                bbox = [float(b - 1) for b in bbox]

                datum = {
                    'filename': filename,
                    'name': obj.find('name').text.lower().strip(),
                    'pose': obj.find('pose').text.lower().strip(),
                    'truncated': int(obj.find('truncated').text),
                    'difficult': int(obj.find('difficult').text),
                    'bbox': bbox,
                }
                datums.append(datum)
            objects[img_id] = datums
        return objects

    def __len__(self):
        return len(self.objects)

    def get_example(self, i):
        """Returns the i-th example.

        Returns a color image and bounding boxes. The image is in CHW format.
        If `self.bgr` is True, the image is in BGR. If not, it is in RGB.

        The boundig boxes are a
        collection of length 5 arrays. Each array contains values
        organized as (x_min, y_min, x_max, y_max, label_id).
        The number of bounding box is equal to the number of objects
        int the image.

        Args:
            i (int): The index of the example.

        Returns:
            tuple of an image and bounding boxes
        """
        if i >= len(self):
            raise IndexError('index is too large')
        img, bboxes = self.get_raw_data(i)

        if self.bgr:
            img = img[:, :, ::-1]
        img = img.transpose(2, 0, 1).astype(np.float32)
        return img, bboxes

    def get_raw_data(self, i):
        """Returns the i-th example

        This returns a color image and bounding boxes.
        The color image has shape (H, W, 3).

        The color image that is returned is in RGB. The boundig boxes are a
        collection of length 5 arrays. Each array contains values
        organized as (x_min, y_min, x_max, y_max, label_id).
        The number of bounding box is equal to the number of objects
        int the image.

        Args:
            i (int): The index of the example.

        Returns:
            i-th example (image, bbox)

        """
        # Load a bbox and its category
        objects = self.objects[self.keys[i]]
        bboxes = []
        for obj in objects:
            bbox = obj['bbox']
            name = obj['name']
            label_id = self.labels.index(name)
            bbox = np.asarray([bbox[0], bbox[1], bbox[2], bbox[3], label_id],
                              dtype=np.float32)
            bboxes.append(bbox)
        bboxes = np.stack(bboxes)

        # Load a image
        img_file = osp.join(self.data_dir, 'JPEGImages', obj['filename'])
        img = imread(img_file)  # RGB
        return img, bboxes


if __name__ == '__main__':
    dataset = VOCDetectionDataset()
    img, bboxes = dataset.get_example(0)
