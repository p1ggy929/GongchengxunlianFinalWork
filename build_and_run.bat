@echo off

REM 构建脚本 - 宫颈细胞学AI辅助诊断系统

cls
echo ====================================================
echo 宫颈细胞学AI辅助诊断系统 - 构建与启动脚本
echo ====================================================

REM 创建必要的目录
if not exist ".\uploads" mkdir ".\uploads"
if not exist ".\templates" mkdir ".\templates"

echo.
echo [1/3] 开始构建前端应用...

REM 进入前端目录并安装依赖
echo 进入前端目录并安装依赖...
cd .\frontend 2>nul || (
    echo 错误: 找不到前端目录，请确保项目结构正确。
    pause
    exit /b 1
)

REM 检查npm是否安装
where npm >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到npm，请先安装Node.js。
    pause
    exit /b 1
)

REM 安装依赖
echo 正在安装npm依赖...
npm install
if %ERRORLEVEL% neq 0 (
    echo 错误: 安装npm依赖失败。
    pause
    exit /b 1
)

echo 正在构建前端应用...
npm run build
if %ERRORLEVEL% neq 0 (
    echo 错误: 构建前端应用失败。
    pause
    exit /b 1
)

cd ..

echo.
echo [2/3] 安装Python依赖...

REM 检查Python是否安装
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到Python，请先安装Python。
    pause
    exit /b 1
)

REM 安装必要的Python包
echo 正在安装Flask、OpenCV等依赖...
pip install flask opencv-python numpy requests

echo.
echo [3/3] 启动应用...
echo 宫颈细胞学AI辅助诊断系统正在启动...
echo ====================================================
echo 访问地址: http://localhost:5000
echo 按任意键启动应用...
pause >nul

REM 启动Flask应用
python main.py