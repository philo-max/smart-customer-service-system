@echo off
chcp 65001 > nul
echo ======================================================
echo           智能客服系统 (Smart Customer Service)
echo                一键启动脚本 (Windows)
echo ======================================================
echo.

if not exist ".env" (
    echo [警告] 未找到 .env 配置文件，已为您创建模版...
    echo ZHIPU_API_KEY=your_api_key_here > .env
    echo 请先打开项目根目录下的 .env 文件，填入你的 ZHIPU_API_KEY 之后重新启动！
    echo.
    pause
    exit
)

if not exist "venv" (
    echo [错误] 虚拟环境 venv 不存在！
    echo 请在当前目录打开 PowerShell 并执行以下命令创建环境：
    echo   python -m venv venv
    echo   .\venv\Scripts\pip.exe install -r requirements.txt
    echo.
    pause
    exit
)

echo [1/2] 正在激活 Python 虚拟环境...
call .\venv\Scripts\activate.bat

echo [2/2] 正在启动主程序 app.py...
echo.
python app.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 系统运行异常退出了。请检查上方的报错提示！
    echo.
    pause
)
