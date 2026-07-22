@echo off
chcp 65001 >nul
echo ========================================
echo   X -> 小红书 自动发布系统
echo ========================================
echo.

REM 优先使用已创建的虚拟环境中的 Python
if exist .venv\Scripts\python.exe (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    set "PIP_EXE=.venv\Scripts\pip.exe"
    set "PLAYWRIGHT_EXE=.venv\Scripts\playwright.exe"
    echo [提示] 检测到已存在虚拟环境，将使用虚拟环境运行。
) else (
    set "PYTHON_EXE=python"
    set "PIP_EXE=pip"
    set "PLAYWRIGHT_EXE=playwright"
)

REM 检查 Python
%PYTHON_EXE% --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查 ffmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [提示] 未找到 ffmpeg，视频转制功能将不可用
    echo 如需视频支持，请安装: https://www.gyan.dev/ffmpeg/builds/
    echo.
)

REM 安装依赖
echo [1/3] 正在安装 Python 依赖...
%PIP_EXE% install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络或手动执行: %PIP_EXE% install -r requirements.txt
    pause
    exit /b 1
)

REM 安装 Playwright 浏览器
echo [2/3] 正在安装 Playwright 浏览器...
%PLAYWRIGHT_EXE% install chromium
if errorlevel 1 (
    echo [警告] Playwright 浏览器安装失败，部分功能可能受限
)

REM 创建必要目录
if not exist data mkdir data
if not exist data\media mkdir data\media
if not exist cookies mkdir cookies
if not exist templates mkdir templates

echo [3/3] 启动服务...
echo.
echo ========================================
echo   服务已启动！
echo   本机访问: http://localhost:8080
echo   手机访问: http://%COMPUTERNAME%:8080
echo   （确保手机和电脑在同一 WiFi 下）
echo ========================================
echo.
echo 按 Ctrl+C 停止服务
echo.

%PYTHON_EXE% app.py
pause
