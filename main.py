#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宫颈细胞学AI辅助诊断系统 - 主入口文件
"""

import os
import json
import logging
from flask import Flask, request, jsonify, render_template
import requests
import cv2
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 加载配置文件
def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("配置文件未找到，使用默认配置")
        return {
            "modelarts_api_url": "",  # 需要在配置文件中设置
            "modelarts_api_key": "",  # 需要在配置文件中设置
            "upload_folder": "uploads",
            "allowed_extensions": {"png", "jpg", "jpeg", "tiff"}
        }

config = load_config()

# 确保上传文件夹存在
if not os.path.exists(config["upload_folder"]):
    os.makedirs(config["upload_folder"])

# 检查文件扩展名
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config["allowed_extensions"]

# 图像预处理函数
def preprocess_image(image_path):
    try:
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")
        
        # 转换为RGB格式
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 调整大小为模型输入尺寸（示例：512x512）
        image = cv2.resize(image, (512, 512))
        
        # 归一化
        image = image / 255.0
        
        # 转换为模型输入格式
        image = np.expand_dims(image, axis=0)
        
        return image.tolist()
    except Exception as e:
        logger.error(f"图像预处理失败: {str(e)}")
        raise

# 调用ModelArts推理API
def call_modelarts_inference(image_data):
    try:
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": config["modelarts_api_key"]
        }
        
        payload = {
            "instances": image_data
        }
        
        response = requests.post(
            config["modelarts_api_url"],
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"ModelArts API调用失败: {response.status_code} - {response.text}")
            raise Exception(f"API调用失败: {response.status_code}")
    except Exception as e:
        logger.error(f"调用ModelArts API时出错: {str(e)}")
        raise

# 解析模型结果
def parse_model_result(result):
    try:
        # 根据实际模型输出格式解析结果
        # 这里是示例代码，需要根据实际模型输出调整
        predictions = result.get("predictions", [])
        
        if not predictions:
            return {
                "status": "error",
                "message": "未获得预测结果"
            }
        
        # 解析预测类别和置信度
        cell_types = ["正常", "ASC-US", "LSIL", "HSIL"]
        prediction = predictions[0]
        
        # 假设模型返回的是类别的概率分布
        class_index = int(np.argmax(prediction))
        confidence = float(np.max(prediction))
        
        return {
            "status": "success",
            "cell_type": cell_types[class_index],
            "confidence": confidence,
            "suggestion": get_diagnostic_suggestion(class_index, confidence)
        }
    except Exception as e:
        logger.error(f"解析模型结果失败: {str(e)}")
        raise

# 获取诊断建议
def get_diagnostic_suggestion(cell_type_index, confidence):
    suggestions = [
        "建议定期复查，未见明显异常细胞。",
        "发现非典型鳞状细胞，意义不明确，建议进行HPV检测和定期随访。",
        "发现低级别鳞状上皮内病变，建议进行阴道镜检查和组织病理学评估。",
        "发现高级别鳞状上皮内病变，建议立即进行阴道镜检查和组织病理学评估。"
    ]
    
    if cell_type_index < len(suggestions):
        return suggestions[cell_type_index]
    else:
        return "请结合临床情况进行综合评估。"

# API路由 - 上传图像并进行诊断
@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "未上传文件"}), 400
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({"status": "error", "message": "未选择文件"}), 400
        
        # 检查文件类型
        if file and allowed_file(file.filename):
            # 保存文件
            filename = os.path.join(config["upload_folder"], file.filename)
            file.save(filename)
            
            try:
                # 预处理图像
                processed_image = preprocess_image(filename)
                
                # 调用ModelArts API进行推理
                model_result = call_modelarts_inference(processed_image)
                
                # 解析结果
                diagnostic_result = parse_model_result(model_result)
                
                return jsonify(diagnostic_result)
            finally:
                # 可选：处理完成后删除临时文件
                # os.remove(filename)
                pass
        else:
            return jsonify({"status": "error", "message": "不支持的文件类型"}), 400
    
    except Exception as e:
        logger.error(f"诊断过程中出错: {str(e)}")
        return jsonify({"status": "error", "message": f"处理过程中出错: {str(e)}"}), 500

# 页面路由
@app.route('/')
def index():
    return render_template('index.html')

# 启动应用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)