#!/bin/bash

echo "===================================="
echo "     TypeSage - 启动脚本"
echo "===================================="
echo

echo "[1/4] 检查环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.10+"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "错误: 未找到Node.js，请先安装Node.js 18+"
    exit 1
fi

echo "[2/4] 安装后端依赖..."
cd backend

if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

echo "激活虚拟环境..."
source venv/bin/activate

echo "安装Python依赖..."
pip install -r requirements.txt

echo "[3/4] 安装前端依赖..."
cd ../frontend
npm install

echo "[4/4] 启动服务..."
echo

echo "启动后端服务 (FastAPI)..."
cd ../backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

sleep 3

echo "启动前端服务 (Vite)..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo
echo "===================================="
echo "   服务启动完成！"
echo "===================================="
echo "前端访问地址: http://localhost:5173"
echo "后端API地址: http://localhost:8000"
echo "后端文档地址: http://localhost:8000/docs"
echo
echo "请确保Ollama服务正在运行并已安装qwen2.5-coder:7b模型"
echo "启动Ollama: ollama serve"
echo "安装模型: ollama pull qwen2.5-coder:7b"
echo
echo "按Ctrl+C停止所有服务"

# 等待中断信号
trap "echo '停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait 