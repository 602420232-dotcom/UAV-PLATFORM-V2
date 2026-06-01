"""
边云协同服务 API
提供 REST 接口供其他服务调用
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# 第三方库
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    logging.warning("FastAPI not installed. Running in demo mode.")

# 本地模块
from coordinator import EdgeCloudCoordinator, EdgeTask, TaskType
from federated_learning import FederatedLearning, DroneClient

logger = logging.getLogger(__name__)

# ==================== FastAPI App ====================

if HAS_FASTAPI:
    app = FastAPI(
        title="Edge-Cloud Coordinator API",
        description="边云协同计算框架 API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS配置 - 生产环境必须通过环境变量CORS_ORIGINS限制
    import os
    environment = os.environ.get("ENVIRONMENT", "development")
    cors_origins_str = os.environ.get("CORS_ORIGINS")
    
    if environment == "production":
        if not cors_origins_str:
            raise ValueError(
                "CORS_ORIGINS environment variable must be set in production environment. "
                "Example: CORS_ORIGINS=https://example.com,https://api.example.com"
            )
        cors_origins = cors_origins_str.split(",")
        allow_credentials = True
        logger.info(f"Production CORS configured for origins: {cors_origins}")
    else:
        cors_origins = cors_origins_str.split(",") if cors_origins_str else ["*"]
        allow_credentials = False if cors_origins == ["*"] else True
        if cors_origins == ["*"]:
            logger.warning(
                "CORS is configured to allow all origins (*). "
                "This is acceptable for development but should be restricted in production."
            )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )
    
    # 全局限流器
    coordinator = EdgeCloudCoordinator()
    federated_learning = FederatedLearning(min_clients=2)

# ==================== Pydantic Models ====================

class TaskSubmitRequest(BaseModel):
    """任务提交请求"""
    task_type: str = Field(..., description="任务类型: global_path, local_avoidance, sensor_fusion, model_update, batch_processing")
    priority: int = Field(default=5, ge=1, le=10, description="优先级 1-10")
    data: Dict = Field(default_factory=dict, description="任务数据")
    deadline: float = Field(default=60.0, description="截止时间（秒）")


class TaskSubmitResponse(BaseModel):
    """任务提交响应"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """任务状态查询响应"""
    task_id: str
    task_type: str
    priority: int
    status: str
    result: Optional[Dict] = None


class SystemStatusResponse(BaseModel):
    """系统状态响应"""
    node_id: str
    queue_size: int
    completed_count: int
    cloud_connected: bool
    edge_connected: bool
    buffer_size: int


class FLClientUpdateRequest(BaseModel):
    """联邦学习客户端更新请求"""
    drone_id: str
    weights: Dict[str, List[List[float]]]
    n_samples: int
    metrics: Dict


class FLClientUpdateResponse(BaseModel):
    """联邦学习客户端更新响应"""
    aggregated: bool
    round_id: int
    global_accuracy: Optional[float] = None


class FLStatusResponse(BaseModel):
    """联邦学习状态响应"""
    strategy: str
    min_clients: int
    round_id: int
    clients_this_round: int
    global_accuracy: Optional[float] = None
    total_rounds: int


class FLTrainRequest(BaseModel):
    """联邦学习训练请求"""
    drone_id: str
    epochs: int = 5
    n_samples: int = 100


# ==================== API Routes ====================

if HAS_FASTAPI:
    
    @app.get("/", tags=["Health"])
    async def root():
        """API 根路径"""
        return {
            "service": "Edge-Cloud Coordinator",
            "version": "1.0.0",
            "status": "running"
        }
    
    
    @app.get("/health", tags=["Health"])
    async def health_check():
        """健康检查"""
        return {"status": "healthy"}
    
    
    # ==================== 任务管理 ====================
    
    @app.post("/tasks", response_model=TaskSubmitResponse, tags=["Tasks"])
    async def submit_task(request: TaskSubmitRequest):
        """
        提交任务
        
        根据任务类型自动分配到云端或边缘处理
        """
        try:
            # 转换任务类型
            task_type = TaskType(request.task_type)
            
            # 创建任务
            task = EdgeTask(
                task_id=f"task_{len(coordinator.task_queue) + 1}",
                task_type=task_type,
                priority=request.priority,
                data=request.data,
                deadline=request.deadline
            )
            
            # 提交任务
            task_id = coordinator.submit_task(task)
            
            # 后台处理
            coordinator.process_task(task)
            
            return TaskSubmitResponse(
                task_id=task_id,
                status="submitted",
                message=f"任务已提交到{getattr(task_type, 'value', request.task_type)}队列"
            )
            
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的任务类型")
        except Exception:
            logger.error(f"任务提交失败", exc_info=True)
            raise HTTPException(status_code=500, detail="服务器内部错误")
    
    
    @app.get("/tasks/{task_id}", response_model=TaskStatusResponse, tags=["Tasks"])
    async def get_task_status(task_id: str):
        """查询任务状态"""
        # 查找任务
        for task in coordinator.task_queue:
            if task.task_id == task_id:
                return TaskStatusResponse(
                    task_id=task.task_id,
                    task_type=task.task_type.value,
                    priority=task.priority,
                    status=task.status
                )
        
        # 检查已完成任务
        for task in coordinator.completed_tasks:
            if task.task_id == task_id:
                return TaskStatusResponse(
                    task_id=task.task_id,
                    task_type=task.task_type.value,
                    priority=task.priority,
                    status=task.status,
                    result=task.data.get('result') if task.data else None
                )
        
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    
    @app.delete("/tasks/{task_id}", tags=["Tasks"])
    async def cancel_task(task_id: str):
        """取消任务"""
        for i, task in enumerate(coordinator.task_queue):
            if task.task_id == task_id:
                coordinator.task_queue.pop(i)
                return {"message": f"任务 {task_id} 已取消"}
        
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    
    @app.get("/tasks", response_model=List[TaskStatusResponse], tags=["Tasks"])
    async def list_tasks(
        status: Optional[str] = None,
        limit: int = Field(default=10, le=100)
    ):
        """获取任务列表"""
        tasks = coordinator.task_queue[:limit]
        
        if status == "completed":
            tasks = coordinator.completed_tasks[:limit]
        
        return [
            TaskStatusResponse(
                task_id=task.task_id,
                task_type=task.task_type.value,
                priority=task.priority,
                status=task.status
            )
            for task in tasks
        ]
    
    
    # ==================== 边云协同 ====================
    
    @app.get("/status", response_model=SystemStatusResponse, tags=["Coordinator"])
    async def get_system_status():
        """获取系统状态"""
        return SystemStatusResponse(
            node_id=coordinator.node_id,
            queue_size=len(coordinator.task_queue),
            completed_count=len(coordinator.completed_tasks),
            cloud_connected=True,  # TODO: 实现真实连接检测
            edge_connected=True,
            buffer_size=len(coordinator.offline_buffer)
        )
    
    
    @app.post("/sync", tags=["Coordinator"])
    async def sync_with_cloud():
        """同步云端模型"""
        try:
            coordinator.sync_cloud_models()
            return {"message": "云端同步完成", "models": list(coordinator.cloud_models.keys())}
        except Exception:
            logger.error("云端同步失败", exc_info=True)
            raise HTTPException(status_code=500, detail="服务器内部错误")
    
    
    @app.post("/upload", tags=["Coordinator"])
    async def upload_edge_data(background_tasks: BackgroundTasks):
        """上传边缘数据到云端"""
        def _upload():
            coordinator.upload_edge_data()
        
        background_tasks.add_task(_upload)
        return {"message": "数据上传任务已提交"}
    
    
    @app.get("/models", tags=["Coordinator"])
    async def list_models():
        """列出可用模型"""
        return {
            "cloud_models": list(coordinator.cloud_models.keys()),
            "local_models": list(coordinator.local_models.keys())
        }
    
    
    # ==================== 批量操作 ====================
    
    @app.post("/tasks/batch", tags=["Batch"])
    async def submit_batch_tasks(tasks: List[TaskSubmitRequest]):
        """批量提交任务（上限100个）"""
        if len(tasks) > 100:
            raise HTTPException(status_code=400, detail="批量任务数量不能超过100")
        results = []
        for req in tasks:
            try:
                task_type = TaskType(req.task_type)
                task = EdgeTask(
                    task_id=f"task_{len(coordinator.task_queue) + 1}",
                    task_type=task_type,
                    priority=req.priority,
                    data=req.data,
                    deadline=req.deadline
                )
                task_id = coordinator.submit_task(task)
                results.append({"task_id": task_id, "status": "submitted"})
            except Exception:
                logger.error(f"批量任务 [{req.task_type}] 提交失败", exc_info=True)
                results.append({"error": "任务提交失败"})
        
        return {"results": results}


    # ==================== 联邦学习 ====================

    @app.post("/fl/update", response_model=FLClientUpdateResponse, tags=["Federated Learning"])
    async def fl_client_update(request: FLClientUpdateRequest):
        """接收联邦学习客户端更新"""
        import numpy as np
        np_weights = {k: np.array(v) for k, v in request.weights.items()}
        aggregated = federated_learning.receive_update(
            drone_id=request.drone_id,
            weights=np_weights,
            n_samples=request.n_samples,
            metrics=request.metrics
        )
        global_model = federated_learning.get_global_model()
        return FLClientUpdateResponse(
            aggregated=aggregated,
            round_id=federated_learning.round_id,
            global_accuracy=global_model.accuracy if global_model else None
        )


    @app.get("/fl/status", response_model=FLStatusResponse, tags=["Federated Learning"])
    async def fl_status():
        """获取联邦学习状态"""
        global_model = federated_learning.get_global_model()
        return FLStatusResponse(
            strategy=federated_learning.strategy,
            min_clients=federated_learning.min_clients,
            round_id=federated_learning.round_id,
            clients_this_round=len(federated_learning.client_updates),
            global_accuracy=global_model.accuracy if global_model else None,
            total_rounds=len(federated_learning.round_history)
        )


    @app.get("/fl/history", tags=["Federated Learning"])
    async def fl_history():
        """获取联邦学习历史"""
        return {"rounds": federated_learning.round_history}


    @app.post("/fl/train", tags=["Federated Learning"])
    async def fl_local_train(request: FLTrainRequest):
        """模拟无人机本地训练"""
        global_model = federated_learning.get_global_model()
        if global_model is None:
            from federated_learning import DroneClient
            client = DroneClient(request.drone_id)
            dummy_weights = {"w": np.array([1.0, 2.0, 3.0]), "b": np.array([0.0])}
            updated, n_samples, metrics = client.local_train(dummy_weights, request.epochs)
        else:
            client = DroneClient(request.drone_id)
            updated, n_samples, metrics = client.local_train(global_model.weights, request.epochs)
        aggregated = federated_learning.receive_update(
            drone_id=request.drone_id,
            weights=updated,
            n_samples=n_samples,
            metrics=metrics
        )
        return {"drone_id": request.drone_id, "n_samples": n_samples, "metrics": metrics, "aggregated": aggregated}


# ==================== Main Entry ====================

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """启动 API 服务"""
    if not HAS_FASTAPI:
        logger.info("[Error] FastAPI is required. Install with: pip install fastapi uvicorn")
        return
    
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()

