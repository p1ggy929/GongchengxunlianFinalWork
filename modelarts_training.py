#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宫颈细胞学AI辅助诊断系统 - ModelArts模型训练脚本
此脚本用于在华为ModelArts平台上训练宫颈细胞学图像分类模型
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

# 设置MindSpore上下文
context.set_context(mode=context.GRAPH_MODE, device_target="Ascend")

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='宫颈细胞学图像分类模型训练')
    parser.add_argument('--data_url', type=str, default='s3://your-obs-bucket/data/', 
                        help='训练数据在OBS上的路径')
    parser.add_argument('--train_url', type=str, default='s3://your-obs-bucket/output/', 
                        help='模型输出在OBS上的路径')
    parser.add_argument('--model_name', type=str, default='resnet50', 
                        choices=['resnet50', 'efficientnet'],
                        help='使用的模型架构')
    parser.add_argument('--batch_size', type=int, default=32, help='批次大小')
    parser.add_argument('--epochs', type=int, default=100, help='训练轮数')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='学习率')
    parser.add_argument('--momentum', type=float, default=0.9, help='动量参数')
    parser.add_argument('--weight_decay', type=float, default=1e-4, help='权重衰减')
    parser.add_argument('--pretrained', type=bool, default=True, help='是否使用预训练权重')
    parser.add_argument('--augmentation', type=bool, default=True, help='是否使用数据增强')
    return parser.parse_args()

# 数据加载和预处理
def create_dataset(data_path, batch_size=32, is_training=True, augmentation=True):
    # 创建数据集
    dataset = ImageFolderDataset(data_path, class_indexing={"normal": 0, "ascus": 1, "lsil": 2, "hsil": 3})
    
    # 定义变换
    transforms_list = []
    
    # 数据增强
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
    
    # 通用变换
    transforms_list.extend([
        T.Rescale(1.0 / 255.0, 0.0),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        T.HWC2CHW()
    ])
    
    # 应用变换
    transform = T.Compose(transforms_list)
    dataset = dataset.map(operations=transform, input_columns="image")
    
    # 批量处理
    dataset = dataset.batch(batch_size, drop_remainder=True)
    
    # 打乱数据（仅训练集）
    if is_training:
        dataset = dataset.shuffle(buffer_size=dataset.get_dataset_size())
    
    return dataset

# 构建ResNet-50模型
class ResNet50(nn.Cell):
    def __init__(self, num_classes=4, pretrained=False):
        super(ResNet50, self).__init__()
        # 使用MindSpore Vision提供的ResNet-50
        from mindvision.classification.models import resnet50
        
        if pretrained:
            # 加载在ImageNet上预训练的权重
            self.model = resnet50(pretrained=True)
            # 修改最后一层以适应我们的分类任务
            in_channels = self.model.fc.in_channels
            self.model.fc = nn.Dense(in_channels, num_classes)
        else:
            # 从头开始训练
            self.model = resnet50(num_classes=num_classes, pretrained=False)
    
    def construct(self, x):
        return self.model(x)

# 构建EfficientNet-B0模型
class EfficientNet(nn.Cell):
    def __init__(self, num_classes=4, pretrained=False):
        super(EfficientNet, self).__init__()
        # 使用MindSpore Vision提供的EfficientNet
        from mindvision.classification.models import efficientnet_b0
        
        if pretrained:
            # 加载在ImageNet上预训练的权重
            self.model = efficientnet_b0(pretrained=True)
            # 修改最后一层
            in_channels = self.model.classifier.out_channels
            self.model.classifier = nn.Dense(in_channels, num_classes)
        else:
            self.model = efficientnet_b0(num_classes=num_classes, pretrained=False)
    
    def construct(self, x):
        return self.model(x)

# 选择模型
def get_model(model_name, num_classes=4, pretrained=False):
    if model_name == 'resnet50':
        return ResNet50(num_classes=num_classes, pretrained=pretrained)
    elif model_name == 'efficientnet':
        return EfficientNet(num_classes=num_classes, pretrained=pretrained)
    else:
        raise ValueError(f"不支持的模型: {model_name}")

# 自定义评估指标
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
        # 计算总体准确率
        total = np.sum(self.confusion_matrix)
        accuracy = np.trace(self.confusion_matrix) / total if total > 0 else 0
        
        # 计算每个类别的灵敏度和特异度
        sensitivity = {}
        specificity = {}
        
        cell_types = ['正常', 'ASC-US', 'LSIL', 'HSIL']
        
        for i in range(self.num_classes):
            # 灵敏度 = TP / (TP + FN)
            tp = self.confusion_matrix[i, i]
            fn = np.sum(self.confusion_matrix[i, :]) - tp
            sensitivity[cell_types[i]] = tp / (tp + fn) if (tp + fn) > 0 else 0
            
            # 特异度 = TN / (TN + FP)
            tn = total - np.sum(self.confusion_matrix[:, i]) - np.sum(self.confusion_matrix[i, :]) + tp
            fp = np.sum(self.confusion_matrix[:, i]) - tp
            specificity[cell_types[i]] = tn / (tn + fp) if (tn + fp) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'sensitivity': sensitivity,
            'specificity': specificity,
            'confusion_matrix': self.confusion_matrix.tolist()
        }

# 主训练函数
def train(args):
    # 创建本地数据目录
    local_data_path = './data'
    local_output_path = './output'
    os.makedirs(local_data_path, exist_ok=True)
    os.makedirs(local_output_path, exist_ok=True)
    
    # 从OBS复制数据到本地（ModelArts环境中需要）
    try:
        import moxing as mox
        print(f"从OBS复制数据: {args.data_url} -> {local_data_path}")
        mox.file.copy_parallel(args.data_url, local_data_path)
    except ImportError:
        print("未检测到moxing库，使用本地数据")
    
    # 加载数据集
    train_data_path = os.path.join(local_data_path, 'train')
    val_data_path = os.path.join(local_data_path, 'val')
    
    print("创建训练数据集...")
    train_dataset = create_dataset(
        train_data_path, 
        batch_size=args.batch_size, 
        is_training=True,
        augmentation=args.augmentation
    )
    
    print("创建验证数据集...")
    val_dataset = create_dataset(
        val_data_path, 
        batch_size=args.batch_size, 
        is_training=False,
        augmentation=False
    )
    
    # 创建模型
    print(f"创建模型: {args.model_name}")
    net = get_model(
        args.model_name, 
        num_classes=4, 
        pretrained=args.pretrained
    )
    
    # 定义损失函数和优化器
    loss_fn = nn.SoftmaxCrossEntropyWithLogits(sparse=True, reduction='mean')
    optimizer = nn.Momentum(
        params=net.trainable_params(),
        learning_rate=args.learning_rate,
        momentum=args.momentum,
        weight_decay=args.weight_decay
    )
    
    # 定义学习率调度器（可选）
    lr_scheduler = nn.cosine_decay_lr(
        min_lr=1e-6,
        max_lr=args.learning_rate,
        total_step=train_dataset.get_dataset_size() * args.epochs,
        step_per_epoch=train_dataset.get_dataset_size()
    )
    
    # 创建检查点配置
    config_ck = CheckpointConfig(
        save_checkpoint_steps=train_dataset.get_dataset_size(),
        keep_checkpoint_max=10
    )
    ckpoint_cb = ModelCheckpoint(
        prefix=f"cervical_cytology_{args.model_name}",
        directory=local_output_path,
        config=config_ck
    )
    
    # 创建模型
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
    
    # 训练模型
    print("开始训练...")
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
    
    # 在验证集上评估模型
    print("在验证集上评估模型...")
    metrics = model.eval(val_dataset, dataset_sink_mode=True)
    
    # 使用自定义指标进一步评估
    custom_metrics = DiagnosticMetrics(num_classes=4)
    for data in val_dataset.create_tuple_iterator():
        images, labels = data
        outputs = model.predict(images)
        custom_metrics.update(outputs, labels)
    
    detailed_metrics = custom_metrics.get_metrics()
    
    # 保存评估结果
    all_metrics = {
        'basic_metrics': metrics,
        'detailed_metrics': detailed_metrics,
        'hyperparameters': vars(args)
    }
    
    with open(os.path.join(local_output_path, 'metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2)
    
    print("评估结果:")
    print(json.dumps(all_metrics, ensure_ascii=False, indent=2))
    
    # 保存最佳模型为MindIR格式（用于部署）
    best_ckpt = os.path.join(local_output_path, f"cervical_cytology_{args.model_name}-{args.epochs}_1.ckpt")
    if os.path.exists(best_ckpt):
        param_dict = load_checkpoint(best_ckpt)
        load_param_into_net(net, param_dict)
        ms.export(net, Tensor(np.zeros([1, 3, 512, 512], np.float32)), file_name=os.path.join(local_output_path, 'cervical_cytology_model'), file_format='MINDIR')
        print("模型已导出为MindIR格式")
    
    # 将结果复制回OBS
    try:
        print(f"将结果复制到OBS: {local_output_path} -> {args.train_url}")
        mox.file.copy_parallel(local_output_path, args.train_url)
    except ImportError:
        print("未检测到moxing库，结果保存在本地")

# 主函数
if __name__ == '__main__':
    args = parse_args()
    print("训练参数:")
    for key, value in vars(args).items():
        print(f"{key}: {value}")
    
    train(args)