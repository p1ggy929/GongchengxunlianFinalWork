@echo off

REM 简单启动脚本 - 宫颈细胞学AI辅助诊断系统

echo ====================================================
echo 启动宫颈细胞学AI辅助诊断系统后端服务
echo ====================================================

REM 创建必要的目录
if not exist ".\uploads" mkdir ".\uploads"
if not exist ".\templates" mkdir ".\templates"

REM 检查Python是否安装
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到Python，请先安装Python。
    pause
    exit /b 1
)

REM 安装必要的Python包
echo 正在安装依赖...
pip install flask opencv-python numpy requests

echo.
echo 启动Flask服务...
echo 访问地址: http://localhost:5000
echo 按Ctrl+C停止服务...

python main.py