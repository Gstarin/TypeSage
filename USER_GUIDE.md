# TypeSage 使用指南

## 🚀 快速开始

### 环境要求

- **Python 3.10+**: 用于运行后端FastAPI服务
- **Node.js 18+**: 用于运行前端React应用
- **Ollama**: 用于运行本地大模型
- **Git**: 用于克隆项目（可选）

### 安装步骤

#### 1. 安装Ollama和模型

```bash
# 下载并安装Ollama
# 访问 https://ollama.ai 下载对应操作系统的版本

# 启动Ollama服务
ollama serve

# 安装qwen2.5-coder:7b模型
ollama pull qwen2.5-coder:7b
```

#### 2. 运行项目

**Windows用户：**
```cmd
双击运行 start.bat
```

**Linux/Mac用户：**
```bash
chmod +x start.sh
./start.sh
```

#### 3. 手动启动（可选）

如果自动启动脚本有问题，可以手动启动：

**后端服务：**
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

**前端服务：**
```bash
cd frontend
npm install
npm run dev
```

### 访问地址

- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 📖 功能使用

### 1. 代码分析

1. 访问 http://localhost:5173
2. 点击"开始分析"或导航到"代码分析"页面
3. 在代码编辑器中输入Python代码
4. 配置分析选项：
   - ✅ 启用AI分析：使用大模型进行类型推导
   - ✅ 保存到记忆库：将分析结果保存到数据库
5. 点击"开始分析"按钮
6. 查看分析结果：
   - 未声明变量列表
   - AI类型推导结果
   - 符号表摘要

### 2. 可视化查看

分析完成后，点击"可视化"按钮可以查看：
- **AST可视化**: 抽象语法树结构图
- **符号表**: 详细的符号信息和作用域

### 3. 记忆库管理

在"记忆库"页面可以查看：
- **记忆模式**: 存储的代码模式和类型推断
- **推导历史**: 历史类型推导记录
- **统计信息**: 系统性能指标

## 🔧 高级配置

### 模型配置

如果需要使用其他模型，可以修改 `backend/app/core/llm_client.py`:

```python
llm_client = OllamaClient(
    base_url="http://localhost:11434",  # Ollama服务地址
    model="qwen2.5-coder:7b"            # 模型名称
)
```

### 数据库位置

数据库文件位于: `database/typesage.db`

可以通过SQLite工具直接查看数据库内容。

## 🐛 故障排除

### 常见问题

**1. 分析失败：连接错误**
- 检查Ollama服务是否启动: `ollama serve`
- 检查模型是否安装: `ollama list`
- 确认端口11434未被占用

**2. 前端无法访问后端**
- 检查后端服务是否在8000端口运行
- 检查防火墙设置
- 确认CORS配置正确

**3. 模型响应很慢**
- qwen2.5-coder:7b模型较大，首次运行需要加载时间
- 建议使用GPU加速（如果可用）
- 可以尝试更小的模型版本

**4. 依赖安装失败**
- Python依赖: 确保Python版本正确，考虑使用清华源等镜像
- Node.js依赖: 尝试使用 `npm install --registry https://registry.npmmirror.com`

### 日志查看

- **后端日志**: 查看控制台输出
- **前端日志**: 浏览器开发者工具控制台
- **Ollama日志**: Ollama服务控制台

## 📝 示例代码

以下是一些适合测试的示例代码：

### 示例1：未声明变量
```python
def calculate_area(radius):
    return pi * radius ** 2  # pi未声明

result = calculate_area(5)
print(f"面积: {result}")
```

### 示例2：类型推导
```python
def process_data(items):
    filtered = [x for x in items if x > threshold]  # threshold未声明
    return sum(filtered) / len(filtered)

data = [1, 2, 3, 4, 5]
average = process_data(data)
```

### 示例3：复杂上下文
```python
class DataProcessor:
    def __init__(self):
        self.config = load_config()  # load_config未声明
    
    def analyze(self, dataset):
        results = []
        for item in dataset:
            score = calculate_score(item, self.config)  # calculate_score未声明
            results.append(score)
        return results
```

## 🤝 技术支持

### 项目结构
```
TypeSage/
├── backend/              # FastAPI后端
│   ├── app/
│   │   ├── core/        # 核心分析模块
│   │   ├── routers/     # API路由
│   │   └── database.py  # 数据库操作
│   └── main.py          # 应用入口
├── frontend/            # React前端
│   ├── src/
│   │   ├── components/  # React组件
│   │   ├── pages/       # 页面组件
│   │   └── services/    # API服务
│   └── package.json
├── database/            # SQLite数据库
└── README.md
```

### 开发说明

这是一个编译原理课程的大作业项目，主要特点：

1. **传统编译技术**: AST解析、符号表构建
2. **AI增强**: 大模型驱动的类型推导
3. **半参数化系统**: 记忆库存储和复用
4. **现代技术栈**: React + FastAPI + Ollama

### 联系方式

如有问题或建议，请通过以下方式联系：
- 项目GitHub Issues
- 课程论坛
- 邮件联系 