#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
����ϸ��ѧAI�������ϵͳ - ģ������ű�
�˽ű�������ModelArts�ϲ���ΪRESTful API������ͼ�񲢷�����Ͻ��
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

# ����MindSpore������
context.set_context(mode=context.GRAPH_MODE, device_target="Ascend")

# ��ʼ��FlaskӦ��
app = Flask(__name__)

# ȫ�ֱ����洢ģ��
model = None
cell_types = ['����', 'ASC-US', 'LSIL', 'HSIL']

# ͼ��Ԥ������
def preprocess_image(image_path=None, image_data=None):
    """
    Ԥ����ͼ���Թ�ģ������
    ֧�ִ��ļ�·�����ֽ����ݼ���ͼ��
    """
    try:
        if image_path:
            # ���ļ�·������ͼ��
            image = cv2.imread(image_path)
        elif image_data:
            # ���ֽ����ݼ���ͼ��
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            raise ValueError("�����ṩͼ��·����ͼ������")
        
        if image is None:
            raise ValueError("�޷���ȡͼ������")
        
        # ת��ΪRGB��ʽ
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # ������СΪģ������ߴ�
        image = cv2.resize(image, (512, 512))
        
        # ��һ��
        image = image / 255.0
        
        # ��׼��
        mean = np.array([0.485, 0.456, 0.406]).reshape((1, 1, 3))
        std = np.array([0.229, 0.224, 0.225]).reshape((1, 1, 3))
        image = (image - mean) / std
        
        # ת��ΪCHW��ʽ
        image = image.transpose((2, 0, 1))
        
        # �������ά��
        image = np.expand_dims(image, axis=0).astype(np.float32)
        
        return Tensor(image)
    except Exception as e:
        raise ValueError(f"ͼ��Ԥ����ʧ��: {str(e)}")

# ����ģ��
def load_model(model_path):
    """
    ����ѵ���õ�ģ��
    """
    try:
        # ����ʹ�õ�ģ���ඨ����Ҫ��ѵ��ʱһ��
        from mindvision.classification.models import resnet50
        
        # ����ģ��ʵ��
        net = resnet50(num_classes=4, pretrained=False)
        
        # ����ģ��Ȩ��
        param_dict = load_checkpoint(model_path)
        load_param_into_net(net, param_dict)
        
        # ����Ϊ����ģʽ
        net.set_train(False)
        
        return net
    except Exception as e:
        raise ValueError(f"ģ�ͼ���ʧ��: {str(e)}")

# ��ȡ��Ͻ���
def get_diagnostic_suggestion(cell_type_index, confidence):
    """
    ���ݼ�⵽��ϸ�����ͺ����Ŷ�������Ͻ���
    """
    suggestions = [
        "���鶨�ڸ��飬δ�������쳣ϸ����",
        "���ַǵ�����״ϸ�������岻��ȷ���������HPV���Ͷ�����á�",
        "���ֵͼ�����״��Ƥ�ڲ��䣬�������������������֯����ѧ������",
        "���ָ߼�����״��Ƥ�ڲ��䣬������������������������֯����ѧ������"
    ]
    
    # ������ŶȽϵͣ���Ӷ�����ʾ
    if confidence < 0.7:
        base_suggestion = suggestions[cell_type_index] if cell_type_index < len(suggestions) else "�����ٴ���������ۺ�������"
        return base_suggestion + " [ע��AI������ŶȽϵͣ������˹�����]"
    else:
        return suggestions[cell_type_index] if cell_type_index < len(suggestions) else "�����ٴ���������ۺ�������"

# ģ��������
def predict(model, image_tensor):
    """
    ʹ��ģ�ͽ����������ؽ��
    """
    try:
        # ִ������
        outputs = model(image_tensor)
        
        # ת��Ϊnumpy����
        output_np = outputs.asnumpy()
        
        # Ӧ��softmax��ȡ����
        probabilities = np.exp(output_np) / np.sum(np.exp(output_np), axis=1, keepdims=True)
        
        # ��ȡԤ���������Ŷ�
        class_index = np.argmax(probabilities, axis=1)[0]
        confidence = probabilities[0, class_index]
        
        # ��ȡϸ�����ͺ���Ͻ���
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
        raise ValueError(f"ģ������ʧ��: {str(e)}")

# ��ʼ������ - ��ModelArts����ʱ���Զ�����
def init():
    """
    ��ʼ�����������ڼ���ģ��
    """
    global model
    
    try:
        # ģ��·�� - ��ModelArts����ʱ��ģ���ļ��ᱻ�������ض�λ��
        # �������ģ���ļ���Ϊ'cervical_cytology_model.ckpt'
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cervical_cytology_model.ckpt')
        
        # �������·�������ڣ�������������·��
        if not os.path.exists(model_path):
            model_path = './cervical_cytology_model.ckpt'
        
        if not os.path.exists(model_path):
            model_path = '/model/cervical_cytology_model.ckpt'  # ModelArts��׼ģ��·��
        
        # ����ģ��
        model = load_model(model_path)
        print(f"ģ�ͼ��سɹ�: {model_path}")
        
    except Exception as e:
        print(f"ģ�ͳ�ʼ��ʧ��: {str(e)}")
        raise

# API�˵� - ����ModelArts����
@app.route('/model/invoke', methods=['POST'])
def invoke_model():
    """
    ModelArts��׼����ӿ�
    """
    try:
        # ��ȡ��������
        data = request.get_json()
        instances = data.get('instances', [])
        
        if not instances:
            return jsonify({"predictions": []}), 200
        
        results = []
        
        for instance in instances:
            # ����base64�����ͼ������
            if 'image' in instance:
                image_data = instance['image']
                
                # ����Ƿ�Ϊbase64����
                if isinstance(image_data, str) and image_data.startswith('data:image/'):
                    # �Ƴ�data:image/xxx;base64,ǰ׺
                    image_data = image_data.split(',')[1]
                    # ����base64����
                    image_bytes = base64.b64decode(image_data)
                elif isinstance(image_data, str):
                    # ֱ�ӽ���base64�ַ���
                    image_bytes = base64.b64decode(image_data)
                else:
                    # �����Ѿ����ֽ�����
                    image_bytes = image_data
                
                # Ԥ����ͼ��
                image_tensor = preprocess_image(image_data=image_bytes)
                
                # ִ������
                result = predict(model, image_tensor)
                results.append(result)
            
            # ����ͼ��·�������ڲ��Ի����¿��ã�
            elif 'image_path' in instance and os.environ.get('TEST_MODE') == '1':
                image_path = instance['image_path']
                image_tensor = preprocess_image(image_path=image_path)
                result = predict(model, image_tensor)
                results.append(result)
            
            else:
                results.append({"error": "��Ч�������ʽ"})
        
        # ����������
        return jsonify({"predictions": results}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# �򵥵Ľ������ӿ�
@app.route('/health', methods=['GET'])
def health_check():
    """
    �������ӿڣ�����ȷ�Ϸ����Ƿ���������
    """
    if model is not None:
        return jsonify({"status": "healthy", "model_loaded": True}), 200
    else:
        return jsonify({"status": "unhealthy", "model_loaded": False}), 500

# �Զ�������ӿڣ�������ǰ�˼��ɣ�
@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    """
    �Զ�����Ͻӿڣ������ļ��ϴ�
    """
    try:
        # ����Ƿ����ļ��ϴ�
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "δ�ϴ��ļ�"}), 400
        
        file = request.files['file']
        
        # ����ļ���
        if file.filename == '':
            return jsonify({"status": "error", "message": "δѡ���ļ�"}), 400
        
        # ��ȡ�ļ�����
        image_bytes = file.read()
        
        # Ԥ����ͼ��
        image_tensor = preprocess_image(image_data=image_bytes)
        
        # ִ������
        result = predict(model, image_tensor)
        
        # ������Ͻ��
        return jsonify({
            "status": "success",
            "cell_type": result["cell_type"],
            "confidence": result["confidence"],
            "suggestion": result["suggestion"]
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ������
if __name__ == '__main__':
    # ��ʼ��ģ��
    init()
    
    # ����FlaskӦ��
    # �����������У�Ӧʹ��gunicorn��WSGI������
    app.run(host='0.0.0.0', port=8080, debug=False)