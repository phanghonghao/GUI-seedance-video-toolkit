@echo off
REM Video Generator Pro Build Script
REM 视频生成器专业版构建脚本

echo ========================================
echo Video Generator Pro - Build Script
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

REM 创建虚拟环境（如果不存在）
if not exist "venv" (
    echo [1/4] 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
)

REM 激活虚拟环境
echo [2/4] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo [3/4] 安装依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [错误] 安装依赖失败
    pause
    exit /b 1
)

REM 构建exe
echo [4/4] 构建应用程序...
python setup.py
if errorlevel 1 (
    echo [错误] 构建失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 构建完成！
echo ========================================
echo.
echo 输出文件: release\VideoGeneratorPro.exe
echo.

REM 询问是否运行
set /p RUN="是否立即运行？(Y/N): "
if /i "%RUN%"=="Y" (
    start release\VideoGeneratorPro.exe
)

pause
