"""
FastAPI 后端主入口
提供测试任务管理 API

Backend main entry point
Provides test task management API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import test

app = FastAPI(
    title="VLM Test API",
    version="2.0.0",
    description="自动化车辆审核工作流后端 API"
)

# ==================== CORS 配置 ====================
# 允许 Streamlit 前端调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 注册路由 ====================
app.include_router(test.router, prefix="/api/test", tags=["test"])

# ==================== 根路径 ====================
@app.get("/")
def root():
    """根路径"""
    return {
        "message": "VLM Test API is running",
        "version": "2.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    """健康检查"""
    return {"status": "ok"}
