#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
����ϸ��ѧAI�������ϵͳ - ModelArtsģ��ѵ���ű�
�˽ű������ڻ�ΪModelArtsƽ̨��ѵ������ϸ��ѧͼ�����ģ��
"""

import os
import json
import argparse
import numpy as np
import mindspore as ms
from mindspore import nn, Tensor, context
from mindspore.train import Model, Trainer, CheckpointConfig, ModelCheckpoint
from mindspore.train.callback import LossMonitor, TimeMonitor
from mindspore.dataset import ImageFolderDataset, transforms as T
from mindspore import load_checkpoint, load_param_into_net

# ����MindSpore������
context.set_context(mode=context.GRAPH_MODE, device_target="Ascend")

# ���������в���
def parse_args():
    parser = argparse.ArgumentParser(description='����ϸ��ѧͼ�����ģ��ѵ��')
    parser.add_argument('--data_url', type=str, default='s3://your-obs-bucket/data/', 
                        help='ѵ��������OBS�ϵ�·��')
    parser.add_argument('--train_url', type=str, default='s3://your-obs-bucket/output/', 
                        help='ģ�������OBS�ϵ�·��')
    parser.add_argument('--model_name', type=str, default='resnet50', 
                        choices=['resnet50', 'efficientnet'],
                        help='ʹ�õ�ģ�ͼܹ�')
    parser.add_argument('--batch_size', type=int, default=32, help='���δ�С')
    parser.add_argument('--epochs', type=int, default=100, help='ѵ������')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='ѧϰ��')
    parser.add_argument('--momentum', type=float, default=0.9, help='��������')
    parser.add_argument('--weight_decay', type=float, default=1e-4, help='Ȩ��˥��')
    parser.add_argument('--pretrained', type=bool, default=True, help='�Ƿ�ʹ��Ԥѵ��Ȩ��')
    parser.add_argument('--augmentation', type=bool, default=True, help='�Ƿ�ʹ��������ǿ')
    return parser.parse_args()

# ���ݼ��غ�Ԥ����
def create_dataset(data_path, batch_size=32, is_training=True, augmentation=True):
    # �������ݼ�
    dataset = ImageFolderDataset(data_path, class_indexing={"normal": 0, "ascus": 1, "lsil": 2, "hsil": 3})
    
    # ����任
    transforms_list = []
    
    # ������ǿ
    if is_training and augmentation:
        transforms_list.extend([
            T.RandomCropDecodeResize(size=(512, 512), scale=(0.8, 1.0)),
            T.RandomHorizontalFlip(prob=0.5),
            T.RandomVerticalFlip(prob=0.5),
            T.RandomRotation(degrees=10),
            T.RandomColorAdjust(brightness=0.2, contrast=0.2, saturation=0.2),
        ])
    else:
        transforms_list.append(T.Resize((512, 512)))
    
    # ͨ�ñ任
    transforms_list.extend([
        T.Rescale(1.0 / 255.0, 0.0),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        T.HWC2CHW()
    ])
    
    # Ӧ�ñ任
    transform = T.Compose(transforms_list)
    dataset = dataset.map(operations=transform, input_columns="image")
    
    # ��������
    dataset = dataset.batch(batch_size, drop_remainder=True)
    
    # �������ݣ���ѵ������
    if is_training:
        dataset = dataset.shuffle(buffer_size=dataset.get_dataset_size())
    
    return dataset

# ����ResNet-50ģ��
class ResNet50(nn.Cell):
    def __init__(self, num_classes=4, pretrained=False):
        super(ResNet50, self).__init__()
        # ʹ��MindSpore Vision�ṩ��ResNet-50
        from mindvision.classification.models import resnet50
        
        if pretrained:
            # ������ImageNet��Ԥѵ����Ȩ��
            self.model = resnet50(pretrained=True)
            # �޸����һ������Ӧ���ǵķ�������
            in_channels = self.model.fc.in_channels
            self.model.fc = nn.Dense(in_channels, num_classes)
        else:
            # ��ͷ��ʼѵ��
            self.model = resnet50(num_classes=num_classes, pretrained=False)
    
    def construct(self, x):
        return self.model(x)

# ����EfficientNet-B0ģ��
class EfficientNet(nn.Cell):
    def __init__(self, num_classes=4, pretrained=False):
        super(EfficientNet, self).__init__()
        # ʹ��MindSpore Vision�ṩ��EfficientNet
        from mindvision.classification.models import efficientnet_b0
        
        if pretrained:
            # ������ImageNet��Ԥѵ����Ȩ��
            self.model = efficientnet_b0(pretrained=True)
            # �޸����һ��
            in_channels = self.model.classifier.out_channels
            self.model.classifier = nn.Dense(in_channels, num_classes)
        else:
            self.model = efficientnet_b0(num_classes=num_classes, pretrained=False)
    
    def construct(self, x):
        return self.model(x)

# ѡ��ģ��
def get_model(model_name, num_classes=4, pretrained=False):
    if model_name == 'resnet50':
        return ResNet50(num_classes=num_classes, pretrained=pretrained)
    elif model_name == 'efficientnet':
        return EfficientNet(num_classes=num_classes, pretrained=pretrained)
    else:
        raise ValueError(f"��֧�ֵ�ģ��: {model_name}")

# �Զ�������ָ��
class DiagnosticMetrics:
    def __init__(self, num_classes=4):
        self.num_classes = num_classes
        self.confusion_matrix = np.zeros((num_classes, num_classes))
    
    def clear(self):
        self.confusion_matrix = np.zeros((self.num_classes, self.num_classes))
    
    def update(self, y_pred, y_true):
        y_pred = np.argmax(y_pred.asnumpy(), axis=1)
        y_true = y_true.asnumpy()
        
        for i in range(len(y_true)):
            self.confusion_matrix[y_true[i]][y_pred[i]] += 1
    
    def get_metrics(self):
        # ��������׼ȷ��
        total = np.sum(self.confusion_matrix)
        accuracy = np.trace(self.confusion_matrix) / total if total > 0 else 0
        
        # ����ÿ�����������Ⱥ������
        sensitivity = {}
        specificity = {}
        
        cell_types = ['����', 'ASC-US', 'LSIL', 'HSIL']
        
        for i in range(self.num_classes):
            # ������ = TP / (TP + FN)
            tp = self.confusion_matrix[i, i]
            fn = np.sum(self.confusion_matrix[i, :]) - tp
            sensitivity[cell_types[i]] = tp / (tp + fn) if (tp + fn) > 0 else 0
            
            # ����� = TN / (TN + FP)
            tn = total - np.sum(self.confusion_matrix[:, i]) - np.sum(self.confusion_matrix[i, :]) + tp
            fp = np.sum(self.confusion_matrix[:, i]) - tp
            specificity[cell_types[i]] = tn / (tn + fp) if (tn + fp) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'sensitivity': sensitivity,
            'specificity': specificity,
            'confusion_matrix': self.confusion_matrix.tolist()
        }

# ��ѵ������
def train(args):
    # ������������Ŀ¼
    local_data_path = './data'
    local_output_path = './output'
    os.makedirs(local_data_path, exist_ok=True)
    os.makedirs(local_output_path, exist_ok=True)
    
    # ��OBS�������ݵ����أ�ModelArts��������Ҫ��
    try:
        import moxing as mox
        print(f"��OBS��������: {args.data_url} -> {local_data_path}")
        mox.file.copy_parallel(args.data_url, local_data_path)
    except ImportError:
        print("δ��⵽moxing�⣬ʹ�ñ�������")
    
    # �������ݼ�
    train_data_path = os.path.join(local_data_path, 'train')
    val_data_path = os.path.join(local_data_path, 'val')
    
    print("����ѵ�����ݼ�...")
    train_dataset = create_dataset(
        train_data_path, 
        batch_size=args.batch_size, 
        is_training=True,
        augmentation=args.augmentation
    )
    
    print("������֤���ݼ�...")
    val_dataset = create_dataset(
        val_data_path, 
        batch_size=args.batch_size, 
        is_training=False,
        augmentation=False
    )
    
    # ����ģ��
    print(f"����ģ��: {args.model_name}")
    net = get_model(
        args.model_name, 
        num_classes=4, 
        pretrained=args.pretrained
    )
    
    # ������ʧ�������Ż���
    loss_fn = nn.SoftmaxCrossEntropyWithLogits(sparse=True, reduction='mean')
    optimizer = nn.Momentum(
        params=net.trainable_params(),
        learning_rate=args.learning_rate,
        momentum=args.momentum,
        weight_decay=args.weight_decay
    )
    
    # ����ѧϰ�ʵ���������ѡ��
    lr_scheduler = nn.cosine_decay_lr(
        min_lr=1e-6,
        max_lr=args.learning_rate,
        total_step=train_dataset.get_dataset_size() * args.epochs,
        step_per_epoch=train_dataset.get_dataset_size()
    )
    
    # ������������
    config_ck = CheckpointConfig(
        save_checkpoint_steps=train_dataset.get_dataset_size(),
        keep_checkpoint_max=10
    )
    ckpoint_cb = ModelCheckpoint(
        prefix=f"cervical_cytology_{args.model_name}",
        directory=local_output_path,
        config=config_ck
    )
    
    # ����ģ��
    model = Model(
        net,
        loss_fn=loss_fn,
        optimizer=optimizer,
        metrics={
            'accuracy': nn.Accuracy(),
            'precision': nn.Precision(),
            'recall': nn.Recall()
        }
    )
    
    # ѵ��ģ��
    print("��ʼѵ��...")
    model.train(
        args.epochs,
        train_dataset,
        callbacks=[
            LossMonitor(),
            TimeMonitor(),
            ckpoint_cb
        ],
        dataset_sink_mode=True
    )
    
    # ����֤��������ģ��
    print("����֤��������ģ��...")
    metrics = model.eval(val_dataset, dataset_sink_mode=True)
    
    # ʹ���Զ���ָ���һ������
    custom_metrics = DiagnosticMetrics(num_classes=4)
    for data in val_dataset.create_tuple_iterator():
        images, labels = data
        outputs = model.predict(images)
        custom_metrics.update(outputs, labels)
    
    detailed_metrics = custom_metrics.get_metrics()
    
    # �����������
    all_metrics = {
        'basic_metrics': metrics,
        'detailed_metrics': detailed_metrics,
        'hyperparameters': vars(args)
    }
    
    with open(os.path.join(local_output_path, 'metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2)
    
    print("�������:")
    print(json.dumps(all_metrics, ensure_ascii=False, indent=2))
    
    # �������ģ��ΪMindIR��ʽ�����ڲ���
    best_ckpt = os.path.join(local_output_path, f"cervical_cytology_{args.model_name}-{args.epochs}_1.ckpt")
    if os.path.exists(best_ckpt):
        param_dict = load_checkpoint(best_ckpt)
        load_param_into_net(net, param_dict)
        ms.export(net, Tensor(np.zeros([1, 3, 512, 512], np.float32)), file_name=os.path.join(local_output_path, 'cervical_cytology_model'), file_format='MINDIR')
        print("ģ���ѵ���ΪMindIR��ʽ")
    
    # ��������ƻ�OBS
    try:
        print(f"��������Ƶ�OBS: {local_output_path} -> {args.train_url}")
        mox.file.copy_parallel(local_output_path, args.train_url)
    except ImportError:
        print("δ��⵽moxing�⣬��������ڱ���")

# ������
if __name__ == '__main__':
    args = parse_args()
    print("ѵ������:")
    for key, value in vars(args).items():
        print(f"{key}: {value}")
    
    train(args)