#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宫颈细胞学AI辅助诊断系统 - 数据预处理脚本
用于数据集的清洗、增强和格式转换
"""

import os
import json
import argparse
import random
import shutil
from tqdm import tqdm
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
import albumentations as A

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='宫颈细胞学图像数据预处理')
    parser.add_argument('--input_dir', type=str, required=True, help='输入数据目录')
    parser.add_argument('--output_dir', type=str, required=True, help='输出数据目录')
    parser.add_argument('--image_size', type=int, default=512, help='图像大小')
    parser.add_argument('--train_ratio', type=float, default=0.8, help='训练集比例')
    parser.add_argument('--val_ratio', type=float, default=0.1, help='验证集比例')
    parser.add_argument('--test_ratio', type=float, default=0.1, help='测试集比例')
    parser.add_argument('--augment', action='store_true', help='是否进行数据增强')
    parser.add_argument('--augment_times', type=int, default=5, help='增强倍数')
    parser.add_argument('--min_quality', type=int, default=0, help='最小图像质量分数')
    return parser.parse_args()

# 图像质量评估
def assess_image_quality(image_path):
    """
    简单的图像质量评估
    返回0-100的质量分数
    """
    try:
        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            return 0
        
        # 计算清晰度（拉普拉斯方差）
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        clarity = laplacian.var()
        
        # 计算亮度分布（直方图均匀性）
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten() / hist.sum()
        uniformity = -np.sum(hist * np.log(hist + 1e-10))
        
        # 综合评分（0-100）
        clarity_score = min(100, clarity / 10)
        uniformity_score = uniformity * 10
        quality_score = (clarity_score * 0.7 + uniformity_score * 0.3)
        
        return max(0, min(100, quality_score))
    except Exception as e:
        print(f"评估图像质量时出错 {image_path}: {e}")
        return 0

# 图像预处理
def preprocess_image(image_path, output_path, image_size=512):
    """
    预处理单张图像：调整大小、格式转换等
    """
    try:
        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            return False
        
        # 调整大小
        img = cv2.resize(img, (image_size, image_size))
        
        # 转换为RGB格式（OpenCV默认读取为BGR）
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 保存图像
        cv2.imwrite(output_path, img)
        return True
    except Exception as e:
        print(f"预处理图像时出错 {image_path}: {e}")
        return False

# 数据增强
def augment_image(image_path, output_dir, num_augmentations=5, image_size=512):
    """
    对单张图像进行数据增强
    """
    try:
        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        # 转换为RGB格式
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 定义增强转换
        transforms = A.Compose([
            A.RandomRotate90(p=0.5),
            A.Flip(p=0.5),
            A.Transpose(p=0.5),
            A.OneOf([
                A.IAAAdditiveGaussianNoise(),
                A.GaussNoise(),
            ], p=0.2),
            A.OneOf([
                A.MotionBlur(p=0.2),
                A.MedianBlur(blur_limit=3, p=0.1),
                A.Blur(blur_limit=3, p=0.1),
            ], p=0.2),
            A.ShiftScaleRotate(shift_limit=0.0625, scale_limit=0.2, rotate_limit=15, p=0.2),
            A.OneOf([
                A.CLAHE(clip_limit=2),
                A.IAASharpen(),
                A.IAAEmboss(),
                A.RandomBrightnessContrast(),
            ], p=0.3),
            A.HueSaturationValue(p=0.3),
            A.Resize(image_size, image_size)
        ])
        
        augmented_files = []
        base_name = os.path.basename(image_path)
        name, ext = os.path.splitext(base_name)
        
        for i in range(num_augmentations):
            # 应用增强
            augmented = transforms(image=img)
            augmented_img = augmented['image']
            
            # 转换回BGR格式
            augmented_img = cv2.cvtColor(augmented_img, cv2.COLOR_RGB2BGR)
            
            # 保存增强后的图像
            output_path = os.path.join(output_dir, f"{name}_aug_{i}{ext}")
            cv2.imwrite(output_path, augmented_img)
            augmented_files.append(output_path)
        
        return augmented_files
    except Exception as e:
        print(f"增强图像时出错 {image_path}: {e}")
        return []

# 创建数据集目录结构
def create_dataset_structure(output_dir):
    """
    创建训练、验证和测试集目录结构
    """
    splits = ['train', 'val', 'test']
    classes = ['normal', 'ascus', 'lsil', 'hsil']
    
    for split in splits:
        for cls in classes:
            dir_path = os.path.join(output_dir, split, cls)
            os.makedirs(dir_path, exist_ok=True)

# 主处理函数
def main(args):
    # 检查目录
    if not os.path.exists(args.input_dir):
        print(f"输入目录不存在: {args.input_dir}")
        return
    
    # 创建输出目录结构
    create_dataset_structure(args.output_dir)
    
    # 获取所有类别
    classes = ['normal', 'ascus', 'lsil', 'hsil']
    class_mapping = {}
    
    # 遍历每个类别
    for cls in classes:
        class_dir = os.path.join(args.input_dir, cls)
        if not os.path.exists(class_dir):
            print(f"类别目录不存在: {class_dir}")
            continue
        
        # 获取所有图像文件
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            files = [os.path.join(class_dir, f) for f in os.listdir(class_dir) if f.lower().endswith(ext)]
            image_files.extend(files)
        
        print(f"找到 {cls} 类别图像 {len(image_files)} 张")
        
        # 图像质量过滤
        quality_images = []
        for img_path in tqdm(image_files, desc=f"评估 {cls} 图像质量"):
            quality_score = assess_image_quality(img_path)
            if quality_score >= args.min_quality:
                quality_images.append((img_path, quality_score))
        
        print(f"通过质量过滤的 {cls} 图像: {len(quality_images)} 张")
        
        # 按质量分数排序
        quality_images.sort(key=lambda x: x[1], reverse=True)
        image_paths = [img_path for img_path, _ in quality_images]
        
        # 数据集分割
        train_size = int(len(image_paths) * args.train_ratio)
        val_size = int(len(image_paths) * args.val_ratio)
        
        train_images = image_paths[:train_size]
        val_images = image_paths[train_size:train_size+val_size]
        test_images = image_paths[train_size+val_size:]
        
        # 处理训练集
        print(f"处理 {cls} 训练集: {len(train_images)} 张图像")
        for img_path in tqdm(train_images, desc=f"预处理 {cls} 训练图像"):
            base_name = os.path.basename(img_path)
            output_path = os.path.join(args.output_dir, 'train', cls, base_name)
            
            # 预处理图像
            if preprocess_image(img_path, output_path, args.image_size):
                # 数据增强
                if args.augment:
                    augment_dir = os.path.join(args.output_dir, 'train', cls)
                    augment_image(output_path, augment_dir, args.augment_times, args.image_size)
        
        # 处理验证集
        print(f"处理 {cls} 验证集: {len(val_images)} 张图像")
        for img_path in tqdm(val_images, desc=f"预处理 {cls} 验证图像"):
            base_name = os.path.basename(img_path)
            output_path = os.path.join(args.output_dir, 'val', cls, base_name)
            preprocess_image(img_path, output_path, args.image_size)
        
        # 处理测试集
        print(f"处理 {cls} 测试集: {len(test_images)} 张图像")
        for img_path in tqdm(test_images, desc=f"预处理 {cls} 测试图像"):
            base_name = os.path.basename(img_path)
            output_path = os.path.join(args.output_dir, 'test', cls, base_name)
            preprocess_image(img_path, output_path, args.image_size)
    
    # 生成数据集统计信息
    stats = {}
    for split in ['train', 'val', 'test']:
        split_stats = {}
        for cls in classes:
            dir_path = os.path.join(args.output_dir, split, cls)
            if os.path.exists(dir_path):
                split_stats[cls] = len(os.listdir(dir_path))
            else:
                split_stats[cls] = 0
        stats[split] = split_stats
    
    # 保存统计信息
    with open(os.path.join(args.output_dir, 'dataset_stats.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print("\n数据集统计信息:")
    for split, split_data in stats.items():
        print(f"{split}:")
        total = sum(split_data.values())
        for cls, count in split_data.items():
            print(f"  {cls}: {count}")
        print(f"  总计: {total}")

# 主函数
if __name__ == '__main__':
    args = parse_args()
    print("数据预处理参数:")
    for key, value in vars(args).items():
        print(f"{key}: {value}")
    
    main(args)