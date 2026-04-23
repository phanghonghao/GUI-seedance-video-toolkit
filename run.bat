@echo off
REM Video Generator Pro - Startup Script
REM 视频生成器专业版启动脚本

echo ========================================
echo Video Generator Pro
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查PyQt6
echo 检查依赖...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo PyQt6未安装，正在安装依赖...
    pip install PyQt6 -i https://pypi.tuna.tsinghua.edu.cn/simple
)

REM 运行程序
echo 启动程序...
python main.py

if errorlevel 1 (
    echo.
    echo 程序异常退出
    pause
)
