import fire
import os.path as osp

import chainer
from chainer import training
from chainer.training import extensions

from chainercv.datasets import get_online_products
from chainercv.extensions import EmbedImages
from chainercv.extensions import MeasureKRetrieval
from chainercv.wrappers import CropWrapper
from chainercv.wrappers import ResizeWrapper
from chainercv.wrappers import SubtractWrapper

from deep_metric_triplet_loss import TripletLossEmbedding
from deep_metric_triplet_loss import TripletLossIterator
from deep_metric_triplet_loss import TripletLossUpdater


def main(gpu=-1, batch_size=120, epochs=20000, resume='',
         lr=1e-10, out='result'):
    train_data, test_data = get_online_products(
        test_classes=range(20000, 20040))
    wrappers = [lambda d: SubtractWrapper(d, value=122.5),
                lambda d: ResizeWrapper(d, [0], (256, 256, 3))]
    for wrapper in wrappers:
        train_data = wrapper(train_data)
        test_data = wrapper(test_data)

    train_data = CropWrapper(train_data, [0], (3, 224, 224))
    test_data = CropWrapper(test_data, [0], (3, 224, 224), (0, 16, 16))

    model = TripletLossEmbedding(embed_size=128)

    if gpu != -1:
        model.to_gpu(gpu)
        chainer.cuda.get_device(gpu).use()

    # optimizer = O.Adam(alpha=1e-9)
    optimizer = chainer.optimizers.MomentumSGD(lr=lr, momentum=0.99)
    optimizer.setup(model)

    # optimizer.add_hook(chainer.optimizer.WeightDecay(rate=0.0005))

    train_iter = TripletLossIterator(train_data, batch_size,
                                     repeat=True)
    test_iter = chainer.iterators.SerialIterator(
        test_data, batch_size, repeat=False, shuffle=False)

    updater = TripletLossUpdater(train_iter, optimizer, device=gpu)
    trainer = training.Trainer(updater, (epochs, 'epoch'), out=out)

    val_interval = 1, 'epoch'
    log_interval = 100, 'iteration'

    # reporter related
    trainer.extend(extensions.LogReport(trigger=log_interval))
    trainer.extend(extensions.PrintReport(
        ['epoch', 'main/time',
         'main/loss', 'validation/main/loss']),
        trigger=log_interval)
    trainer.extend(extensions.ProgressBar(update_interval=10))
    trainer.extend(
        EmbedImages(test_iter, model, filename='embed.npy'),
        trigger=val_interval, invoke_before_training=True)
    trainer.extend(
        MeasureKRetrieval(test_iter, features_file='embed.npy',
                          ks=[1, 10, 100]),
        trigger=val_interval, invoke_before_training=True)

    # training visualization
    trainer.extend(
        extensions.PlotReport(
            ['main/loss', 'validation/main/loss', 'main/recall@1',
             'main/recall@10', 'main/recall@100'],
            trigger=log_interval, file_name='loss.png')
    )
    trainer.extend(extensions.dump_graph('main/loss'))

    if resume:
        chainer.serializers.load_npz(osp.expanduser(resume), trainer)

    trainer.run()


if __name__ == '__main__':
    fire.Fire(main)
