# TypeSage - 大模型驱动的语义分析增强

## 项目简介

TypeSage是一个编译原理大作业项目，在传统类型检查基础上，引入大模型解决复杂上下文推导问题。

## 主要功能

- **Python类型推导**: 基于代码上下文和大模型推理进行类型推导
- **代码类型标注**: 自动为代码添加类型标注
- **语法树可视化**: 展示Python代码的抽象语法树(AST)
- **符号表可视化**: 显示符号表的构建过程和结果
- **半参数化系统**: 将模型推理结果存入记忆库供后续复用

## 技术栈

### 前端
- React 18
- TypeScript
- Tailwind CSS
- Vite
- Recharts (图表库)
- Monaco Editor (代码编辑器)

### 后端
- FastAPI
- Python 3.10
- SQLite3
- Ollama (qwen2.5-coder:7b)
- AST分析

## 项目结构

```
TypeSage/
├── frontend/          # React前端应用
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── backend/           # FastAPI后端服务
│   ├── app/
│   ├── requirements.txt
│   └── main.py
├── database/          # SQLite数据库文件
└── README.md
```

## 安装和运行

### 前置条件
- Node.js 18+
- Python 3.10
- Ollama (需要安装qwen2.5-coder:7b模型)

### 后端设置
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 前端设置
```bash
cd frontend
npm install
npm run dev
```

### Ollama设置
```bash
# 安装并启动ollama
ollama pull qwen2.5-coder:7b
ollama serve
```

## 使用说明

1. 启动后端服务(FastAPI)
2. 启动前端开发服务器
3. 确保Ollama服务正在运行
4. 在浏览器中访问 http://localhost:5173
5. 在代码编辑器中输入Python代码
6. 点击"分析代码"按钮查看类型推导结果、AST和符号表

## 核心特性

### 大模型驱动的类型推导
- 利用qwen2.5-coder:7b模型分析代码上下文
- 对未声明变量进行智能类型推测
- 与传统符号表分析结果对比验证

### 记忆库系统
- 将推理结果存储到SQLite数据库
- 支持历史查询和复用
- 提高后续分析效率

## 开发者

编译原理大作业项目 