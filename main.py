import os
import json
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import base64

# 设置日志
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
app = Flask(__name__, static_folder='templates', template_folder='templates')

# 配置上传文件夹
UPLOAD_FOLDER = './uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# 允许的图像扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'tiff'}

# 加载配置文件
def load_config():
    try:
        # 尝试用多种编码读取文件
        encodings = ['utf-8', 'gbk', 'latin-1']
        for encoding in encodings:
            try:
                with open('config.json', 'r', encoding=encoding) as f:
                    config = json.load(f)
                    logger.info(f"成功读取配置文件，使用编码: {encoding}")
                    return config
            except UnicodeDecodeError:
                logger.warning(f"使用编码 {encoding} 读取配置文件失败，尝试下一种编码")
                continue
        
        # 如果所有编码都失败，使用默认配置
        logger.error("无法读取配置文件，使用默认配置")
        return {
            "modelarts_api_url": "https://example.com/modelarts/api/v1/inference",  # ModelArts推理API地址
            "modelarts_api_key": "your_api_key_here",  # ModelArts API密钥
            "upload_folder": "uploads",
            "allowed_extensions": ALLOWED_EXTENSIONS,
            "cell_types": ["正常", "ASC-US", "LSIL", "HSIL"]
        }
    except FileNotFoundError:
        logger.warning("配置文件未找到，使用默认配置")
        return {
            "modelarts_api_url": "https://example.com/modelarts/api/v1/inference",  # ModelArts推理API地址
            "modelarts_api_key": "your_api_key_here",  # ModelArts API密钥
            "upload_folder": "uploads",
            "allowed_extensions": ALLOWED_EXTENSIONS,
            "cell_types": ["正常", "ASC-US", "LSIL", "HSIL"]
        }

config = load_config()

# ??????????
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ??????????
def preprocess_image(image_path):
    try:
        # ??????
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"?????????: {image_path}")
        
        # ????RGB???
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # ??????С?????????磨?????512x512??
        image = cv2.resize(image, (512, 512))
        
        # ?????
        image = image / 255.0
        
        # ?????????????
        image = np.expand_dims(image, axis=0)
        
        return image.tolist()
    except Exception as e:
        logger.error(f"???????????: {str(e)}")
        raise

# ????ModelArts????API
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
            logger.error(f"ModelArts API???????: {response.status_code} - {response.text}")
            raise Exception(f"API???????: {response.status_code}")
    except Exception as e:
        logger.error(f"????ModelArts API?????: {str(e)}")
        raise

# ?????????
def parse_model_result(result):
    try:
        # ???????????????????????
        # ?????????????????????????????????
        predictions = result.get("predictions", [])
        
        if not predictions:
            return {
                "status": "error",
                "message": "δ????????"
            }
        
        # 确定类别名称
        class_names = {
            "normal": "正常",
            "inflammation": "炎症",
            "ascus": "轻度异常",
            "lsil": "中度异常",
            "hsil": "重度异常",
            "scc": "恶性"
        }
        
        prediction = predictions[0]
        
        # 获取预测类别和置信度
        class_index = int(np.argmax(prediction))
        confidence = float(np.max(prediction))
        
        # 获取类别名称映射
        category_map = config.get("cell_types", ["正常", "轻度异常", "中度异常", "重度异常"])
        cell_type = category_map[class_index] if class_index < len(category_map) else "未知"
        
        return {
            "status": "success",
            "cell_type": cell_type,
            "confidence": confidence,
            "suggestion": get_diagnostic_suggestion(cell_type, confidence)
        }
    except Exception as e:
        logger.error(f"????????????: {str(e)}")
        raise

def get_diagnostic_suggestion(category, confidence):
    """
    根据诊断类别生成诊断建议
    """
    try:
        # 映射不同的类别名称到标准名称
        category_map = {
            "正常": "正常",
            "ASC-US": "轻度异常",
            "LSIL": "中度异常",
            "HSIL": "重度异常",
            "ascus": "轻度异常",
            "lsil": "中度异常",
            "hsil": "重度异常",
            "轻度异常": "轻度异常",
            "中度异常": "中度异常",
            "重度异常": "重度异常",
            "恶性": "恶性",
            "scc": "恶性"
        }
        
        # 获取标准类别名称
        standard_category = category_map.get(category, "未知")
        
        suggestions = {
            "正常": "细胞学检查未见明显异常细胞，建议按照常规筛查计划进行定期复查（通常为1-3年一次）。建议保持健康的生活方式，包括均衡饮食、适量运动和避免吸烟等不良习惯。",
            "轻度异常": "发现不典型鳞状细胞(ASC-US)。建议进行高危型HPV检测，如HPV阳性，应转诊阴道镜检查；如HPV阴性，可在12个月后重复细胞学检查或3年后联合筛查。",
            "中度异常": "提示低度鳞状上皮内病变(LSIL)，与HPV感染相关。建议进行阴道镜检查及宫颈组织活检，以排除更高级别病变。对于25岁以下女性，可考虑6个月后复查细胞学及阴道镜。",
            "重度异常": "提示高度鳞状上皮内病变(HSIL)，属于宫颈癌前病变。建议立即进行阴道镜检查及宫颈活检以明确诊断，确诊后通常需要进行宫颈锥切术等治疗，防止进展为宫颈癌。",
            "恶性": "提示可能存在宫颈恶性肿瘤。需立即转诊至妇科肿瘤专科，进行阴道镜下多点活检、宫颈管搔刮等检查明确诊断，并制定个体化治疗方案。",
            "未知": "建议咨询专业医生以获取更详细的诊断和治疗建议。"
        }
        
        base_suggestion = suggestions.get(standard_category, suggestions["未知"])
        
        # 添加置信度相关说明
        if isinstance(confidence, dict):
            max_conf = max(confidence.values()) if confidence else 0
        else:
            max_conf = confidence
        
        # 根据置信度添加额外建议
        if max_conf < 0.5:
            additional = "\n\n【注意】由于诊断置信度较低(" + str(round(max_conf*100)) + "%)，建议进行重复检测或结合其他检查方法以获取更准确的诊断结果。"
        elif max_conf < 0.8:
            additional = "\n\n【提示】诊断结果中等可信(" + str(round(max_conf*100)) + "%)，请结合临床症状和其他检查结果综合判断。"
        else:
            additional = "\n\n【提示】诊断结果高可信度(" + str(round(max_conf*100)) + "%)，但仍需由专业医师进行最终确认。"
            
        return base_suggestion + additional
    except Exception as e:
        logger.error(f"生成诊断建议时出错: {str(e)}")
        return "建议咨询专业医生以获取更详细的诊断和治疗建议。"

# API路由 - 处理图像诊断请求
@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    """
    处理图像诊断请求
    """
    try:
        # 检查请求中是否包含文件
        if 'image' not in request.files:
            return jsonify({"status": "error", "message": "未接收到图像文件"}), 400
        
        file = request.files['image']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({"status": "error", "message": "未选择图像文件"}), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "不支持的文件类型，请上传PNG、JPG、JPEG或GIF格式的图片"}), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # 预处理图像
            logger.info(f"开始预处理图像: {filename}")
            processed_image = preprocess_image(filepath)
            
            # 调用ModelArts API进行推理
            logger.info("调用推理服务进行AI分析")
            model_result = call_modelarts_inference(processed_image)
            
            # 解析结果
            logger.info("解析模型返回结果")
            diagnostic_result = parse_model_result(model_result)
            
            if not diagnostic_result:
                return jsonify({"status": "error", "message": "无法获取有效的诊断结果"}), 500
            
            # 生成诊断建议
            logger.info("生成诊断建议")
            diagnostic_result['suggestion'] = get_diagnostic_suggestion(diagnostic_result.get('cell_type', '未知'), diagnostic_result.get('confidence', 0))
            
            # 添加处理状态信息
            diagnostic_result['status'] = 'success'
            
            # 返回结果
            logger.info("诊断完成，返回结果")
            return jsonify(diagnostic_result)
            
        finally:
            # 删除临时文件
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        logger.error(f"诊断过程中发生错误: {str(e)}")
        return jsonify({"status": "error", "message": f"系统处理时发生错误: {str(e)}，请稍后重试或联系管理员"}), 500

# 添加静态文件路由
@app.route('/<path:path>')
def static_file(path):
    """
    提供静态文件
    """
    return send_from_directory(app.static_folder, path)

# 首页路由
@app.route('/')
def index():
    """
    返回首页
    """
    return render_template('index.html')

# 启动服务器
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)