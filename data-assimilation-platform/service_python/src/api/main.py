# service_python/src/api/main.py

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from api.core.assimilation_service import AssimilationService
from api.parallel.dask import DaskClusterManager
from api.routes import assimilation, batch


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

cluster_manager: Optional[DaskClusterManager] = None
assimilation_service: Optional[AssimilationService] = None


@asynccontextmanager


async def lifespan(app: FastAPI):
    global cluster_manager, assimilation_service
    logger.info("启动Dask计算集群...")
    cluster_manager = DaskClusterManager(n_workers=4, threads_per_worker=2)
    await cluster_manager.start()
    assimilation_service = AssimilationService(cluster_manager)
    assimilation.set_assimilation_service(assimilation_service)
    batch.set_assimilation_service(assimilation_service)
    yield
    logger.info("关闭计算集群...")
    await cluster_manager.stop()


app = FastAPI(
    title="贝叶斯同化计算服务",
    description="WRF气象数据同化与方差场计算",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8088", "http://localhost:8080", "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


app.include_router(
    assimilation.router,
    prefix="/api/v1/assimilation",
    tags=["assimilation"]
)


@app.get("/health")


async def health_check():
    return {
        "status": "healthy",
        "cluster_status": cluster_manager.status() if cluster_manager else "unknown",
        "queue_size": assimilation_service.queue_size() if assimilation_service else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
