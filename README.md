# 宫颈细胞学AI辅助诊断系统

基于华为ModelArts平台构建的宫颈细胞学AI辅助诊断系统，能够自动读取宫颈液基细胞学（LBC）图像，检测非典型细胞（ASC-US、LSIL、HSIL），为医师提供诊断参考，提高筛查效率和准确性。

## 功能特点

- **自动细胞检测**：使用深度学习模型自动识别宫颈液基细胞学图像中的异常细胞
- **多类别分类**：能够识别正常细胞、ASC-US（非典型鳞状细胞）、LSIL（低级别鳞状上皮内病变）和HSIL（高级别鳞状上皮内病变）
- **直观的用户界面**：基于Vue.js和Flask的响应式Web界面，支持图像上传、诊断结果展示
- **诊断建议**：根据检测结果提供针对性的医学建议
- **华为全栈技术**：基于ModelArts、MindSpore、OBS等华为云服务构建

## 技术架构

### 后端
- **Flask**：提供RESTful API接口
- **MindSpore**：深度学习框架，用于模型推理
- **OpenCV**：图像处理和预处理
- **华为ModelArts**：模型训练、调参和部署
- **华为OBS**：数据存储

### 前端
- **Vue.js 3**：构建用户界面
- **Bootstrap 5**：响应式布局和UI组件

### 模型
- **ResNet-50/EfficientNet-B0**：用于图像分类
- **在Ascend 910/310处理器上加速**：提升训练和推理性能

## 系统要求

### 开发环境
- Python 3.7+
- Flask 2.3+
- OpenCV 4.8+
- MindSpore 2.0+（可选，用于本地推理）

### 部署环境
- 华为云ModelArts（模型训练）
- 华为云OBS（数据存储）
- 华为云CCE（容器部署，可选）

## 项目结构

```
├── main.py                 # Flask应用主入口
├── config.json             # 配置文件
├── modelarts_training.py   # ModelArts模型训练脚本
├── model_inference.py      # 模型推理服务脚本
├── requirements.txt        # Python依赖包
├── templates/              # HTML模板
│   └── index.html          # 前端主页面
└── uploads/                # 上传文件临时存储目录
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置ModelArts API

编辑`config.json`文件，配置ModelArts推理API相关信息：

```json
{
  "modelarts_api_url": "https://your-modelarts-inference-endpoint",
  "modelarts_api_key": "your-api-key-here",
  "upload_folder": "uploads",
  "allowed_extensions": ["png", "jpg", "jpeg", "tiff"]
}
```

### 3. 启动Web服务

```bash
python main.py
```

服务将在`http://localhost:5000`上运行。

## 在ModelArts上训练模型

1. 将宫颈细胞学图像数据集上传至华为云OBS
2. 在ModelArts平台创建训练作业，选择`modelarts_training.py`作为训练脚本
3. 配置训练参数，如模型类型、批次大小、学习率等
4. 启动训练作业
5. 训练完成后，将模型部署为在线服务

## 在ModelArts上部署模型

1. 在ModelArts模型管理中导入训练好的模型
2. 创建模型服务，选择`model_inference.py`作为推理脚本
3. 配置服务参数，如规格、实例数量等
4. 部署服务并获取API端点
5. 将API端点配置到`config.json`中

## 使用说明

1. 打开Web界面（默认为`http://localhost:5000`）
2. 点击或拖拽图像到上传区域
3. 点击「开始AI诊断」按钮
4. 等待诊断结果显示，包括细胞类型、置信度和诊断建议

## 注意事项

- 本系统仅作为辅助诊断工具，不能替代专业医师的诊断
- 上传的图像应清晰，分辨率建议不低于512x512
- 确保配置的ModelArts API端点和密钥有效
- 在生产环境部署时，建议配置HTTPS和访问控制

## 模型性能指标

- **灵敏度**：98.96%
- **特异度**：89.15%
- **AUC**：≥0.95

*注：实际性能可能因数据质量和模型版本而异*

## 许可证

本项目仅供研究和开发使用，未经授权不得用于商业用途。

## 免责声明

本系统的诊断结果仅供参考，不构成医疗建议。任何医疗决策应基于专业医师的诊断。项目开发者不对因使用本系统而导致的任何后果负责。