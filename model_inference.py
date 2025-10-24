#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宫颈细胞学AI辅助诊断系统 - 模型推理脚本
此脚本用于在ModelArts上部署为RESTful API，处理图像并返回诊断结果
"""

import os
import json
import base64
import numpy as np
import cv2
import mindspore as ms
from mindspore import Tensor, load_checkpoint, load_param_into_net, export
from mindspore import context
from flask import Flask, request, jsonify

# 设置MindSpore上下文
context.set_context(mode=context.GRAPH_MODE, device_target="Ascend")

# 初始化Flask应用
app = Flask(__name__)

# 全局变量存储模型
model = None
cell_types = ['正常', 'ASC-US', 'LSIL', 'HSIL']

# 图像预处理函数
def preprocess_image(image_path=None, image_data=None):
    """
    预处理图像以供模型输入
    支持从文件路径或字节数据加载图像
    """
    try:
        if image_path:
            # 从文件路径加载图像
            image = cv2.imread(image_path)
        elif image_data:
            # 从字节数据加载图像
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            raise ValueError("必须提供图像路径或图像数据")
        
        if image is None:
            raise ValueError("无法读取图像数据")
        
        # 转换为RGB格式
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 调整大小为模型输入尺寸
        image = cv2.resize(image, (512, 512))
        
        # 归一化
        image = image / 255.0
        
        # 标准化
        mean = np.array([0.485, 0.456, 0.406]).reshape((1, 1, 3))
        std = np.array([0.229, 0.224, 0.225]).reshape((1, 1, 3))
        image = (image - mean) / std
        
        # 转换为CHW格式
        image = image.transpose((2, 0, 1))
        
        # 添加批次维度
        image = np.expand_dims(image, axis=0).astype(np.float32)
        
        return Tensor(image)
    except Exception as e:
        raise ValueError(f"图像预处理失败: {str(e)}")

# 加载模型
def load_model(model_path):
    """
    加载训练好的模型
    """
    try:
        # 这里使用的模型类定义需要与训练时一致
        from mindvision.classification.models import resnet50
        
        # 创建模型实例
        net = resnet50(num_classes=4, pretrained=False)
        
        # 加载模型权重
        param_dict = load_checkpoint(model_path)
        load_param_into_net(net, param_dict)
        
        # 设置为推理模式
        net.set_train(False)
        
        return net
    except Exception as e:
        raise ValueError(f"模型加载失败: {str(e)}")

# 获取诊断建议
def get_diagnostic_suggestion(cell_type_index, confidence):
    """
    根据检测到的细胞类型和置信度生成诊断建议
    """
    suggestions = [
        "建议定期复查，未见明显异常细胞。",
        "发现非典型鳞状细胞，意义不明确，建议进行HPV检测和定期随访。",
        "发现低级别鳞状上皮内病变，建议进行阴道镜检查和组织病理学评估。",
        "发现高级别鳞状上皮内病变，建议立即进行阴道镜检查和组织病理学评估。"
    ]
    
    # 如果置信度较低，添加额外提示
    if confidence < 0.7:
        base_suggestion = suggestions[cell_type_index] if cell_type_index < len(suggestions) else "请结合临床情况进行综合评估。"
        return base_suggestion + " [注：AI诊断置信度较低，建议人工复核]"
    else:
        return suggestions[cell_type_index] if cell_type_index < len(suggestions) else "请结合临床情况进行综合评估。"

# 模型推理函数
def predict(model, image_tensor):
    """
    使用模型进行推理并返回结果
    """
    try:
        # 执行推理
        outputs = model(image_tensor)
        
        # 转换为numpy数组
        output_np = outputs.asnumpy()
        
        # 应用softmax获取概率
        probabilities = np.exp(output_np) / np.sum(np.exp(output_np), axis=1, keepdims=True)
        
        # 获取预测类别和置信度
        class_index = np.argmax(probabilities, axis=1)[0]
        confidence = probabilities[0, class_index]
        
        # 获取细胞类型和诊断建议
        cell_type = cell_types[class_index]
        suggestion = get_diagnostic_suggestion(class_index, confidence)
        
        return {
            "cell_type": cell_type,
            "confidence": float(confidence),
            "class_index": int(class_index),
            "probabilities": probabilities.tolist(),
            "suggestion": suggestion
        }
    except Exception as e:
        raise ValueError(f"模型推理失败: {str(e)}")

# 初始化函数 - 在ModelArts部署时会自动调用
def init():
    """
    初始化函数，用于加载模型
    """
    global model
    
    try:
        # 模型路径 - 在ModelArts部署时，模型文件会被放置在特定位置
        # 这里假设模型文件名为'cervical_cytology_model.ckpt'
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cervical_cytology_model.ckpt')
        
        # 如果上述路径不存在，尝试其他常见路径
        if not os.path.exists(model_path):
            model_path = './cervical_cytology_model.ckpt'
        
        if not os.path.exists(model_path):
            model_path = '/model/cervical_cytology_model.ckpt'  # ModelArts标准模型路径
        
        # 加载模型
        model = load_model(model_path)
        print(f"模型加载成功: {model_path}")
        
    except Exception as e:
        print(f"模型初始化失败: {str(e)}")
        raise

# API端点 - 用于ModelArts部署
@app.route('/model/invoke', methods=['POST'])
def invoke_model():
    """
    ModelArts标准推理接口
    """
    try:
        # 获取请求数据
        data = request.get_json()
        instances = data.get('instances', [])
        
        if not instances:
            return jsonify({"predictions": []}), 200
        
        results = []
        
        for instance in instances:
            # 处理base64编码的图像数据
            if 'image' in instance:
                image_data = instance['image']
                
                # 检查是否为base64编码
                if isinstance(image_data, str) and image_data.startswith('data:image/'):
                    # 移除data:image/xxx;base64,前缀
                    image_data = image_data.split(',')[1]
                    # 解码base64数据
                    image_bytes = base64.b64decode(image_data)
                elif isinstance(image_data, str):
                    # 直接解码base64字符串
                    image_bytes = base64.b64decode(image_data)
                else:
                    # 假设已经是字节数据
                    image_bytes = image_data
                
                # 预处理图像
                image_tensor = preprocess_image(image_data=image_bytes)
                
                # 执行推理
                result = predict(model, image_tensor)
                results.append(result)
            
            # 处理图像路径（仅在测试环境下可用）
            elif 'image_path' in instance and os.environ.get('TEST_MODE') == '1':
                image_path = instance['image_path']
                image_tensor = preprocess_image(image_path=image_path)
                result = predict(model, image_tensor)
                results.append(result)
            
            else:
                results.append({"error": "无效的输入格式"})
        
        # 返回推理结果
        return jsonify({"predictions": results}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 简单的健康检查接口
@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口，用于确认服务是否正常运行
    """
    if model is not None:
        return jsonify({"status": "healthy", "model_loaded": True}), 200
    else:
        return jsonify({"status": "unhealthy", "model_loaded": False}), 500

# 自定义推理接口（用于与前端集成）
@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    """
    自定义诊断接口，接受文件上传
    """
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "未上传文件"}), 400
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({"status": "error", "message": "未选择文件"}), 400
        
        # 读取文件内容
        image_bytes = file.read()
        
        # 预处理图像
        image_tensor = preprocess_image(image_data=image_bytes)
        
        # 执行推理
        result = predict(model, image_tensor)
        
        # 返回诊断结果
        return jsonify({
            "status": "success",
            "cell_type": result["cell_type"],
            "confidence": result["confidence"],
            "suggestion": result["suggestion"]
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 主函数
if __name__ == '__main__':
    # 初始化模型
    init()
    
    # 启动Flask应用
    # 在生产环境中，应使用gunicorn等WSGI服务器
    app.run(host='0.0.0.0', port=8080, debug=False)