@echo off

REM �����ű� - ����ϸ��ѧAI�������ϵͳ

cls
echo ====================================================
echo ����ϸ��ѧAI�������ϵͳ - �����������ű�
echo ====================================================

REM ������Ҫ��Ŀ¼
if not exist ".\uploads" mkdir ".\uploads"
if not exist ".\templates" mkdir ".\templates"

echo.
echo [1/3] ��ʼ����ǰ��Ӧ��...

REM ����ǰ��Ŀ¼����װ����
echo ����ǰ��Ŀ¼����װ����...
cd .\frontend 2>nul || (
    echo ����: �Ҳ���ǰ��Ŀ¼����ȷ����Ŀ�ṹ��ȷ��
    pause
    exit /b 1
)

REM ���npm�Ƿ�װ
where npm >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ����: δ�ҵ�npm�����Ȱ�װNode.js��
    pause
    exit /b 1
)

REM ��װ����
echo ���ڰ�װnpm����...
npm install
if %ERRORLEVEL% neq 0 (
    echo ����: ��װnpm����ʧ�ܡ�
    pause
    exit /b 1
)

echo ���ڹ���ǰ��Ӧ��...
npm run build
if %ERRORLEVEL% neq 0 (
    echo ����: ����ǰ��Ӧ��ʧ�ܡ�
    pause
    exit /b 1
)

cd ..

echo.
echo [2/3] ��װPython����...

REM ���Python�Ƿ�װ
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ����: δ�ҵ�Python�����Ȱ�װPython��
    pause
    exit /b 1
)

REM ��װ��Ҫ��Python��
echo ���ڰ�װFlask��OpenCV������...
pip install flask opencv-python numpy requests

echo.
echo [3/3] ����Ӧ��...
echo ����ϸ��ѧAI�������ϵͳ��������...
echo ====================================================
echo ���ʵ�ַ: http://localhost:5000
echo �����������Ӧ��...
pause >nul

REM ����FlaskӦ��
python main.py