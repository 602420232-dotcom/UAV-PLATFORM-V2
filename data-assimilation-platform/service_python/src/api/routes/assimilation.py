# service_python/src/api/routes/assimilation.py

from fastapi import APIRouter, BackgroundTasks
from api.models.request import AssimilationRequest, SelfImproveRequest
from api.models.response import AssimilationResponse
from api.core.assimilation_service import AssimilationService
from api.utils.validators import validate_grid_consistency, validate_observation_locations
from api.middleware.error_handler import AppException
import time
import logging
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局服务实例
assimilation_service = None


def set_assimilation_service(service: AssimilationService):
    """设置同化服务实例"""
    global assimilation_service
    assimilation_service = service


@router.post("/compute", response_model=AssimilationResponse)
async def compute_assimilation(
    request: AssimilationRequest,
    background_tasks: BackgroundTasks


):
    """
    执行贝叶斯同化计算

    - 支持3DVAR/EnKF/4DVAR算法
    - 自动并行处理大网格
    - 异步持久化结果
    """
    start_time = time.time()

    if not assimilation_service:
        raise AppException(status_code=503, message="服务未初始化")

    validate_grid_consistency(request.background_field, request.observations)
    if request.obs_locations:
        validate_observation_locations(request.obs_locations, request.observations)

    request_dict = {
        "job_id": request.job_id,
        "background_field": request.background_field,
        "observations": request.observations,
        "obs_locations": request.obs_locations,
        "config": request.config,
        "allow_degraded": request.allow_degraded,
        "algorithm": request.algorithm
    }

    try:
        result = await assimilation_service.compute(request_dict)
    except ValueError as e:
        logger.warning(f"参数错误: {e}")
        raise AppException(status_code=400, message=f"参数错误: {str(e)}")
    except RuntimeError as e:
        logger.error(f"运行时错误: {e}")
        raise AppException(status_code=500, message=f"算法执行失败: {str(e)}")
    except Exception as e:
        logger.error(f"同化计算失败: {type(e).__name__}: {e}", exc_info=True)
        raise AppException(status_code=500, message="同化计算失败")

    background_tasks.add_task(persist_result, job_id=request.job_id, result=result)

    elapsed = time.time() - start_time
    logger.info(f"同化计算完成，Job: {request.job_id}, 耗时: {elapsed:.2f}s")

    return AssimilationResponse(
        job_id=request.job_id,
        status="SUCCESS",
        analysis_field=result.analysis.tolist(),
        variance_field=result.variance.tolist(),
        computation_time=elapsed,
        timestamp=time.time(),
        message="同化计算成功"
    )


@router.post("/self-improve")
async def self_improve_model(request: SelfImproveRequest):
    """
    自迭代改进模型
    """
    if not assimilation_service:
        raise AppException(status_code=503, message="服务未初始化")

    if not request.job_id:
        raise AppException(status_code=400, message="job_id不能为空")

    if not request.X or len(request.X) == 0:
        raise AppException(status_code=400, message="输入数据X不能为空")

    if not request.y or len(request.y) == 0:
        raise AppException(status_code=400, message="目标数据y不能为空")

    try:
        result = await assimilation_service.self_improve(
            job_id=request.job_id,
            X=np.array(request.X),
            y=np.array(request.y),
            epochs=request.epochs,
            batch_size=request.batch_size
        )
    except ValueError as e:
        logger.warning(f"参数错误: {e}")
        raise AppException(status_code=400, message=f"参数错误: {str(e)}")
    except RuntimeError as e:
        logger.error(f"训练失败: {e}")
        raise AppException(status_code=500, message=f"模型训练失败: {str(e)}")
    except Exception as e:
        logger.error(f"自迭代改进失败: {type(e).__name__}: {e}", exc_info=True)
        raise AppException(status_code=500, message="自迭代改进失败")

    logger.info(f"模型自迭代改进完成，Job: {request.job_id}")

    return {
        "status": "SUCCESS",
        "job_id": request.job_id,
        "result": result,
        "timestamp": time.time()
    }


@router.get("/model-performance/{job_id}")
async def get_model_performance(job_id: str):
    """
    获取模型性能

    - 支持增强贝叶斯同化器的性能查询
    - 返回训练历史和最佳分数
    """
    if not assimilation_service:
        raise AppException(status_code=503, message="服务未初始化")

    if not job_id:
        raise AppException(status_code=400, message="job_id不能为空")

    try:
        performance = assimilation_service.get_model_performance(job_id)
    except ValueError as e:
        logger.warning(f"性能查询参数错误: {e}")
        raise AppException(status_code=400, message=f"参数错误: {str(e)}")
    except KeyError as e:
        logger.warning(f"模型不存在: {e}")
        raise AppException(status_code=404, message=f"模型不存在: {str(e)}")
    except Exception as e:
        logger.error(f"获取模型性能失败: {type(e).__name__}: {e}", exc_info=True)
        raise AppException(status_code=500, message="获取模型性能失败")

    logger.info(f"获取模型性能完成，Job: {job_id}")

    return {
        "status": "SUCCESS",
        "job_id": job_id,
        "performance": performance,
        "timestamp": time.time()
    }


async def persist_result(job_id: str, result):
    """异步持久化结果"""
    logger.info(f"持久化结果，JobID: {job_id}")
