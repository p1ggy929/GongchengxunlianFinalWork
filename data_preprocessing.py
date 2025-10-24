#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
����ϸ��ѧAI�������ϵͳ - ����Ԥ����ű�
�������ݼ�����ϴ����ǿ�͸�ʽת��
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

# ���������в���
def parse_args():
    parser = argparse.ArgumentParser(description='����ϸ��ѧͼ������Ԥ����')
    parser.add_argument('--input_dir', type=str, required=True, help='��������Ŀ¼')
    parser.add_argument('--output_dir', type=str, required=True, help='�������Ŀ¼')
    parser.add_argument('--image_size', type=int, default=512, help='ͼ���С')
    parser.add_argument('--train_ratio', type=float, default=0.8, help='ѵ��������')
    parser.add_argument('--val_ratio', type=float, default=0.1, help='��֤������')
    parser.add_argument('--test_ratio', type=float, default=0.1, help='���Լ�����')
    parser.add_argument('--augment', action='store_true', help='�Ƿ����������ǿ')
    parser.add_argument('--augment_times', type=int, default=5, help='��ǿ����')
    parser.add_argument('--min_quality', type=int, default=0, help='��Сͼ����������')
    return parser.parse_args()

# ͼ����������
def assess_image_quality(image_path):
    """
    �򵥵�ͼ����������
    ����0-100����������
    """
    try:
        # ��ȡͼ��
        img = cv2.imread(image_path)
        if img is None:
            return 0
        
        # ���������ȣ�������˹���
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        clarity = laplacian.var()
        
        # �������ȷֲ���ֱ��ͼ�����ԣ�
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten() / hist.sum()
        uniformity = -np.sum(hist * np.log(hist + 1e-10))
        
        # �ۺ����֣�0-100��
        clarity_score = min(100, clarity / 10)
        uniformity_score = uniformity * 10
        quality_score = (clarity_score * 0.7 + uniformity_score * 0.3)
        
        return max(0, min(100, quality_score))
    except Exception as e:
        print(f"����ͼ������ʱ���� {image_path}: {e}")
        return 0

# ͼ��Ԥ����
def preprocess_image(image_path, output_path, image_size=512):
    """
    Ԥ������ͼ�񣺵�����С����ʽת����
    """
    try:
        # ��ȡͼ��
        img = cv2.imread(image_path)
        if img is None:
            return False
        
        # ������С
        img = cv2.resize(img, (image_size, image_size))
        
        # ת��ΪRGB��ʽ��OpenCVĬ�϶�ȡΪBGR��
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # ����ͼ��
        cv2.imwrite(output_path, img)
        return True
    except Exception as e:
        print(f"Ԥ����ͼ��ʱ���� {image_path}: {e}")
        return False

# ������ǿ
def augment_image(image_path, output_dir, num_augmentations=5, image_size=512):
    """
    �Ե���ͼ�����������ǿ
    """
    try:
        # ��ȡͼ��
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        # ת��ΪRGB��ʽ
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # ������ǿת��
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
            # Ӧ����ǿ
            augmented = transforms(image=img)
            augmented_img = augmented['image']
            
            # ת����BGR��ʽ
            augmented_img = cv2.cvtColor(augmented_img, cv2.COLOR_RGB2BGR)
            
            # ������ǿ���ͼ��
            output_path = os.path.join(output_dir, f"{name}_aug_{i}{ext}")
            cv2.imwrite(output_path, augmented_img)
            augmented_files.append(output_path)
        
        return augmented_files
    except Exception as e:
        print(f"��ǿͼ��ʱ���� {image_path}: {e}")
        return []

# �������ݼ�Ŀ¼�ṹ
def create_dataset_structure(output_dir):
    """
    ����ѵ������֤�Ͳ��Լ�Ŀ¼�ṹ
    """
    splits = ['train', 'val', 'test']
    classes = ['normal', 'ascus', 'lsil', 'hsil']
    
    for split in splits:
        for cls in classes:
            dir_path = os.path.join(output_dir, split, cls)
            os.makedirs(dir_path, exist_ok=True)

# ��������
def main(args):
    # ���Ŀ¼
    if not os.path.exists(args.input_dir):
        print(f"����Ŀ¼������: {args.input_dir}")
        return
    
    # �������Ŀ¼�ṹ
    create_dataset_structure(args.output_dir)
    
    # ��ȡ�������
    classes = ['normal', 'ascus', 'lsil', 'hsil']
    class_mapping = {}
    
    # ����ÿ�����
    for cls in classes:
        class_dir = os.path.join(args.input_dir, cls)
        if not os.path.exists(class_dir):
            print(f"���Ŀ¼������: {class_dir}")
            continue
        
        # ��ȡ����ͼ���ļ�
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            files = [os.path.join(class_dir, f) for f in os.listdir(class_dir) if f.lower().endswith(ext)]
            image_files.extend(files)
        
        print(f"�ҵ� {cls} ���ͼ�� {len(image_files)} ��")
        
        # ͼ����������
        quality_images = []
        for img_path in tqdm(image_files, desc=f"���� {cls} ͼ������"):
            quality_score = assess_image_quality(img_path)
            if quality_score >= args.min_quality:
                quality_images.append((img_path, quality_score))
        
        print(f"ͨ���������˵� {cls} ͼ��: {len(quality_images)} ��")
        
        # ��������������
        quality_images.sort(key=lambda x: x[1], reverse=True)
        image_paths = [img_path for img_path, _ in quality_images]
        
        # ���ݼ��ָ�
        train_size = int(len(image_paths) * args.train_ratio)
        val_size = int(len(image_paths) * args.val_ratio)
        
        train_images = image_paths[:train_size]
        val_images = image_paths[train_size:train_size+val_size]
        test_images = image_paths[train_size+val_size:]
        
        # ����ѵ����
        print(f"���� {cls} ѵ����: {len(train_images)} ��ͼ��")
        for img_path in tqdm(train_images, desc=f"Ԥ���� {cls} ѵ��ͼ��"):
            base_name = os.path.basename(img_path)
            output_path = os.path.join(args.output_dir, 'train', cls, base_name)
            
            # Ԥ����ͼ��
            if preprocess_image(img_path, output_path, args.image_size):
                # ������ǿ
                if args.augment:
                    augment_dir = os.path.join(args.output_dir, 'train', cls)
                    augment_image(output_path, augment_dir, args.augment_times, args.image_size)
        
        # ������֤��
        print(f"���� {cls} ��֤��: {len(val_images)} ��ͼ��")
        for img_path in tqdm(val_images, desc=f"Ԥ���� {cls} ��֤ͼ��"):
            base_name = os.path.basename(img_path)
            output_path = os.path.join(args.output_dir, 'val', cls, base_name)
            preprocess_image(img_path, output_path, args.image_size)
        
        # ������Լ�
        print(f"���� {cls} ���Լ�: {len(test_images)} ��ͼ��")
        for img_path in tqdm(test_images, desc=f"Ԥ���� {cls} ����ͼ��"):
            base_name = os.path.basename(img_path)
            output_path = os.path.join(args.output_dir, 'test', cls, base_name)
            preprocess_image(img_path, output_path, args.image_size)
    
    # �������ݼ�ͳ����Ϣ
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
    
    # ����ͳ����Ϣ
    with open(os.path.join(args.output_dir, 'dataset_stats.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print("\n���ݼ�ͳ����Ϣ:")
    for split, split_data in stats.items():
        print(f"{split}:")
        total = sum(split_data.values())
        for cls, count in split_data.items():
            print(f"  {cls}: {count}")
        print(f"  �ܼ�: {total}")

# ������
if __name__ == '__main__':
    args = parse_args()
    print("����Ԥ�������:")
    for key, value in vars(args).items():
        print(f"{key}: {value}")
    
    main(args)