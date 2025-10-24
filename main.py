#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
����ϸ��ѧAI�������ϵͳ - ������ļ�
"""

import os
import json
import logging
from flask import Flask, request, jsonify, render_template
import requests
import cv2
import numpy as np

# ������־
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ����FlaskӦ��
app = Flask(__name__)

# ���������ļ�
def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("�����ļ�δ�ҵ���ʹ��Ĭ������")
        return {
            "modelarts_api_url": "",  # ��Ҫ�������ļ�������
            "modelarts_api_key": "",  # ��Ҫ�������ļ�������
            "upload_folder": "uploads",
            "allowed_extensions": {"png", "jpg", "jpeg", "tiff"}
        }

config = load_config()

# ȷ���ϴ��ļ��д���
if not os.path.exists(config["upload_folder"]):
    os.makedirs(config["upload_folder"])

# ����ļ���չ��
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config["allowed_extensions"]

# ͼ��Ԥ������
def preprocess_image(image_path):
    try:
        # ��ȡͼ��
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"�޷���ȡͼ��: {image_path}")
        
        # ת��ΪRGB��ʽ
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # ������СΪģ������ߴ磨ʾ����512x512��
        image = cv2.resize(image, (512, 512))
        
        # ��һ��
        image = image / 255.0
        
        # ת��Ϊģ�������ʽ
        image = np.expand_dims(image, axis=0)
        
        return image.tolist()
    except Exception as e:
        logger.error(f"ͼ��Ԥ����ʧ��: {str(e)}")
        raise

# ����ModelArts����API
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
            logger.error(f"ModelArts API����ʧ��: {response.status_code} - {response.text}")
            raise Exception(f"API����ʧ��: {response.status_code}")
    except Exception as e:
        logger.error(f"����ModelArts APIʱ����: {str(e)}")
        raise

# ����ģ�ͽ��
def parse_model_result(result):
    try:
        # ����ʵ��ģ�������ʽ�������
        # ������ʾ�����룬��Ҫ����ʵ��ģ���������
        predictions = result.get("predictions", [])
        
        if not predictions:
            return {
                "status": "error",
                "message": "δ���Ԥ����"
            }
        
        # ����Ԥ���������Ŷ�
        cell_types = ["����", "ASC-US", "LSIL", "HSIL"]
        prediction = predictions[0]
        
        # ����ģ�ͷ��ص������ĸ��ʷֲ�
        class_index = int(np.argmax(prediction))
        confidence = float(np.max(prediction))
        
        return {
            "status": "success",
            "cell_type": cell_types[class_index],
            "confidence": confidence,
            "suggestion": get_diagnostic_suggestion(class_index, confidence)
        }
    except Exception as e:
        logger.error(f"����ģ�ͽ��ʧ��: {str(e)}")
        raise

# ��ȡ��Ͻ���
def get_diagnostic_suggestion(cell_type_index, confidence):
    suggestions = [
        "���鶨�ڸ��飬δ�������쳣ϸ����",
        "���ַǵ�����״ϸ�������岻��ȷ���������HPV���Ͷ�����á�",
        "���ֵͼ�����״��Ƥ�ڲ��䣬�������������������֯����ѧ������",
        "���ָ߼�����״��Ƥ�ڲ��䣬������������������������֯����ѧ������"
    ]
    
    if cell_type_index < len(suggestions):
        return suggestions[cell_type_index]
    else:
        return "�����ٴ���������ۺ�������"

# API·�� - �ϴ�ͼ�񲢽������
@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    try:
        # ����Ƿ����ļ��ϴ�
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "δ�ϴ��ļ�"}), 400
        
        file = request.files['file']
        
        # ����ļ���
        if file.filename == '':
            return jsonify({"status": "error", "message": "δѡ���ļ�"}), 400
        
        # ����ļ�����
        if file and allowed_file(file.filename):
            # �����ļ�
            filename = os.path.join(config["upload_folder"], file.filename)
            file.save(filename)
            
            try:
                # Ԥ����ͼ��
                processed_image = preprocess_image(filename)
                
                # ����ModelArts API��������
                model_result = call_modelarts_inference(processed_image)
                
                # �������
                diagnostic_result = parse_model_result(model_result)
                
                return jsonify(diagnostic_result)
            finally:
                # ��ѡ��������ɺ�ɾ����ʱ�ļ�
                # os.remove(filename)
                pass
        else:
            return jsonify({"status": "error", "message": "��֧�ֵ��ļ�����"}), 400
    
    except Exception as e:
        logger.error(f"��Ϲ����г���: {str(e)}")
        return jsonify({"status": "error", "message": f"��������г���: {str(e)}"}), 500

# ҳ��·��
@app.route('/')
def index():
    return render_template('index.html')

# ����Ӧ��
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)