@echo off

REM �������ű� - ����ϸ��ѧAI�������ϵͳ

echo ====================================================
echo ��������ϸ��ѧAI�������ϵͳ��˷���
echo ====================================================

REM ������Ҫ��Ŀ¼
if not exist ".\uploads" mkdir ".\uploads"
if not exist ".\templates" mkdir ".\templates"

REM ���Python�Ƿ�װ
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ����: δ�ҵ�Python�����Ȱ�װPython��
    pause
    exit /b 1
)

REM ��װ��Ҫ��Python��
echo ���ڰ�װ����...
pip install flask opencv-python numpy requests

echo.
echo ����Flask����...
echo ���ʵ�ַ: http://localhost:5000
echo ��Ctrl+Cֹͣ����...

python main.py