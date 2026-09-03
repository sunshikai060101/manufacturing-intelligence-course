"""FastAPI 主应用入口"""
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import init_db
from backend.api import detection, inventory, sensor, stats
from backend.config import BASE_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    init_db()
    print("=" * 60)
    print("智能仓储物料识别与分拣系统 - 后端服务启动")
    print("=" * 60)
    yield
    # 关闭时清理
    print("系统关闭")


app = FastAPI(
    title="智能仓储物料识别与分拣系统 API",
    description="基于机器视觉与多传感器融合的智能仓储物料识别与分拣系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(detection.router)
app.include_router(inventory.router)
app.include_router(sensor.router)
app.include_router(stats.router)


# 前端静态文件服务
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_frontend():
        """服务前端首页"""
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"message": "前端页面未找到"}


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "system": "智能仓储物料识别与分拣系统",
        "version": "1.0.0",
    }


@app.get("/api")
async def api_root():
    """API根路径"""
    return {
        "name": "智能仓储物料识别与分拣系统 API",
        "version": "1.0.0",
        "endpoints": {
            "detection": "/api/detection",
            "inventory": "/api/inventory",
            "sensor": "/api/sensor",
            "stats": "/api/stats",
            "docs": "/docs",
        }
    }
