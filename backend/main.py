from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analysis, memory
from app.database import init_database
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="TypeSage API",
    description="大模型驱动的语义分析增强API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://localhost:80",
        # 添加您的生产域名
        # "https://your-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_database()
    logging.info("Database initialized successfully")

@app.get("/")
async def root():
    return {"message": "TypeSage API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 