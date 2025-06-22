@echo off
echo ====================================
echo     TypeSage - 启动脚本
echo ====================================
echo.

echo [1/3] 检查环境...
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Conda，请先安装Anaconda或Miniconda
    pause
    exit /b 1
)

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Node.js，请先安装Node.js 18+
    pause
    exit /b 1
)

echo [2/3] 启动后端服务（FastAPI）...
start cmd /k "conda activate py310 && cd /d %cd%\backend && python main.py"

timeout /t 3 /nobreak >nul

echo [3/3] 启动前端服务（Vite）...
start cmd /k "conda deactivate && cd /d %cd%\frontend && npm run dev"

echo.
echo ====================================
echo   服务启动完成！
echo ====================================
echo 前端访问地址: http://localhost:5173
echo 后端API地址: http://localhost:8000
echo 后端文档地址: http://localhost:8000/docs
echo.
echo 请确保 Ollama 正在运行
echo 当前模型已安装: qwen2.5-coder:7b
echo.
pause
