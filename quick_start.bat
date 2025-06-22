@echo off
chcp 65001 >nul
echo ===========================================
echo        TypeSage 快速启动脚本
echo ===========================================
echo.

echo [1/2] 检查Ollama服务状态...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo 警告: Ollama服务未运行，请先启动Ollama
    echo 运行命令: ollama serve
    echo.
)

echo [2/2] 启动服务...
echo.
echo 启动后端服务（端口: 8000）...
start "TypeSage-Backend" cmd /k "conda activate py310 && cd /d %~dp0backend && python main.py"

timeout /t 5 /nobreak >nul

echo 启动前端服务（端口: 5173）...
start "TypeSage-Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ===========================================
echo              服务启动完成
echo ===========================================
echo 前端地址: http://localhost:5173
echo 后端地址: http://localhost:8000
echo 后端文档: http://localhost:8000/docs
echo.
echo 请确保 Ollama 正在运行并安装了 qwen2.5-coder:7b 模型
echo 启动Ollama: ollama serve
echo 安装模型: ollama pull qwen2.5-coder:7b
echo.
pause 