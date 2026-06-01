# service_python/src/api/main.py

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
import time
from typing import Optional

from api.core.assimilation_service import AssimilationService
from api.models.request import AssimilationRequest
from api.models.response import AssimilationResponse
from api.utils.validators import validate_grid_consistency
from api.parallel.dask import DaskClusterManager
from api.routes import assimilation, batch

# 结构化日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 全局资源管理
cluster_manager: Optional[DaskClusterManager] = None
assimilation_service: Optional[AssimilationService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global cluster_manager, assimilation_service
    
    # 启动：初始化Dask集群
    logger.info("启动Dask计算集群...")
    cluster_manager = DaskClusterManager(n_workers=4, threads_per_worker=2)
    await cluster_manager.start()
    
    assimilation_service = AssimilationService(cluster_manager)
    # 设置路由中的服务实例
    assimilation.set_assimilation_service(assimilation_service)
    batch.set_assimilation_service(assimilation_service)
    
    yield
    
    # 关闭：清理资源
    logger.info("关闭计算集群...")
    await cluster_manager.stop()

app = FastAPI(
    title="贝叶斯同化计算服务",
    description="WRF气象数据同化与方差场计算",
    version="1.0.0",
    lifespan=lifespan
)

# 中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8088", "http://localhost:8080", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(assimilation.router, prefix="/api/v1/assimilation", tags=["assimilation"])

@app.get("/health")
async def health_check():
    """健康检查（Kubernetes探针）"""
    return {
        "status": "healthy",
        "cluster_status": cluster_manager.status() if cluster_manager else "unknown",
        "queue_size": assimilation_service.queue_size() if assimilation_service else 0
    }

async def persist_result(job_id: str, result):
    """异步持久化到MinIO/S3"""
    # 实现略...
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
