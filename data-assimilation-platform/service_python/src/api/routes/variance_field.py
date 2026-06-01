from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional, List
import logging
import numpy as np
import sys
import os

router = APIRouter(prefix="/variance", tags=["variance"])

try:
    ALGORITHM_CORE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        'algorithm_core', 'src'
    )
    if os.path.exists(ALGORITHM_CORE_PATH) and ALGORITHM_CORE_PATH not in sys.path:
        sys.path.insert(0, ALGORITHM_CORE_PATH)
    
    from bayesian_assimilation.models.variance_field_optimizer import (
        VarianceFieldOptimizer, 
        AdaptiveVarianceField
    )
    from bayesian_assimilation.utils.config import BaseConfig
    ALGORITHM_CORE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"algorithm_core模块导入失败: {e}")
    ALGORITHM_CORE_AVAILABLE = False
    VarianceFieldOptimizer = None
    AdaptiveVarianceField = None
    BaseConfig = None

logger = logging.getLogger(__name__)

variance_optimizer_instance: Optional[VarianceFieldOptimizer] = None
adaptive_optimizer_instance: Optional[AdaptiveVarianceField] = None


def get_optimizer_instance(config: Optional[Dict[str, Any]] = None) -> VarianceFieldOptimizer:
    """获取或创建方差场优化器实例"""
    global variance_optimizer_instance
    
    if variance_optimizer_instance is None:
        if ALGORITHM_CORE_AVAILABLE and BaseConfig:
            base_config = BaseConfig(config) if config else None
            variance_optimizer_instance = VarianceFieldOptimizer(config=base_config, use_sparse=True)
        else:
            variance_optimizer_instance = VarianceFieldOptimizer(use_sparse=True)
    
    return variance_optimizer_instance


def get_adaptive_optimizer_instance(config: Optional[Dict[str, Any]] = None) -> AdaptiveVarianceField:
    """获取或创建自适应方差场优化器实例"""
    global adaptive_optimizer_instance
    
    if adaptive_optimizer_instance is None:
        if ALGORITHM_CORE_AVAILABLE and BaseConfig:
            base_config = BaseConfig(config) if config else None
            adaptive_optimizer_instance = AdaptiveVarianceField(config=base_config)
        else:
            adaptive_optimizer_instance = AdaptiveVarianceField()
    
    return adaptive_optimizer_instance


@router.post("/compute")
async def compute_variance(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算方差场
    
    支持功能:
    - 参数优化
    - 交叉验证
    - 自适应方差场
    """
    try:
        if not ALGORITHM_CORE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="algorithm_core模块不可用，请检查安装"
            )
        
        background = request.get("background")
        observations = request.get("observations")
        obs_locations = request.get("obs_locations")
        use_adaptive = request.get("use_adaptive", False)
        use_cv = request.get("use_cv", False)
        n_folds = request.get("n_folds", 5)
        method = request.get("method", "L-BFGS-B")
        verbose = request.get("verbose", 0)
        
        if background is None:
            raise HTTPException(status_code=400, detail="缺少 background 参数")
        if observations is None:
            raise HTTPException(status_code=400, detail="缺少 observations 参数")
        if obs_locations is None:
            raise HTTPException(status_code=400, detail="缺少 obs_locations 参数")
        
        bg_array = np.array(background)
        obs_array = np.array(observations)
        loc_array = np.array(obs_locations)
        
        if bg_array.ndim not in [2, 3]:
            raise HTTPException(
                status_code=400, 
                detail=f"background维度错误，需要2D或3D数组，当前: {bg_array.ndim}D"
            )
        
        if use_adaptive:
            optimizer = get_adaptive_optimizer_instance(request.get("config"))
            result = optimizer.optimize(
                background=bg_array,
                observations=obs_array,
                obs_locations=loc_array,
                method=method,
                verbose=verbose
            )
        elif use_cv:
            optimizer = get_optimizer_instance(request.get("config"))
            result = optimizer.optimize_with_cv(
                background=bg_array,
                observations=obs_array,
                obs_locations=loc_array,
                n_folds=n_folds,
                method=method,
                verbose=verbose
            )
        else:
            optimizer = get_optimizer_instance(request.get("config"))
            result = optimizer.optimize(
                background=bg_array,
                observations=obs_array,
                obs_locations=loc_array,
                method=method,
                verbose=verbose
            )
        
        shape = bg_array.shape
        variance_field = optimizer.get_variance_field(shape)
        
        return {
            "status": "success",
            "variance_field": variance_field.tolist(),
            "best_params": result.get("best_params"),
            "best_score": float(result.get("best_score", 0)),
            "optimization_history": result.get("history", [])[-10:],
            "shape": list(shape),
            "method": method,
            "use_adaptive": use_adaptive,
            "use_cv": use_cv
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"方差场计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"方差场计算失败: {str(e)}")


@router.post("/variance-matrix")
async def get_variance_matrix(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取稀疏方差矩阵
    
    用于同化计算中的协方差矩阵构建
    """
    try:
        if not ALGORITHM_CORE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="algorithm_core模块不可用"
            )
        
        shape = request.get("shape")
        if shape is None:
            raise HTTPException(status_code=400, detail="缺少 shape 参数")
        
        if len(shape) != 3:
            raise HTTPException(
                status_code=400,
                detail="shape需要3个维度 [nx, ny, nz]"
            )
        
        optimizer = get_optimizer_instance(request.get("config"))
        sparse_var = optimizer.get_sparse_variance_matrix(tuple(shape))
        
        return {
            "status": "success",
            "variance_matrix": {
                "format": "sparse",
                "shape": list(sparse_var.shape),
                "nnz": sparse_var.nnz,
                "density": float(sparse_var.nnz / (sparse_var.shape[0] * sparse_var.shape[1])),
                "data": sparse_var.data.tolist(),
                "indices": sparse_var.indices.tolist(),
                "indptr": sparse_var.indptr.tolist()
            },
            "best_params": optimizer.get_best_params()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取方差矩阵失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adaptive")
async def adaptive_variance(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    自适应方差场调整
    
    根据同化质量动态调整方差参数
    """
    try:
        if not ALGORITHM_CORE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="algorithm_core模块不可用"
            )
        
        analysis = request.get("analysis")
        background = request.get("background")
        observations = request.get("observations")
        obs_locations = request.get("obs_locations")
        adaptation_rate = request.get("adaptation_rate")
        
        if not all([analysis, background, observations, obs_locations]):
            raise HTTPException(
                status_code=400,
                detail="缺少必要参数: analysis, background, observations, obs_locations"
            )
        
        analysis_array = np.array(analysis)
        background_array = np.array(background)
        observations_array = np.array(observations)
        obs_locations_array = np.array(obs_locations)
        
        optimizer = get_adaptive_optimizer_instance(request.get("config"))
        
        if adaptation_rate is not None:
            optimizer.set_adaptation_rate(adaptation_rate)
        
        optimizer.adapt(
            analysis=analysis_array,
            background=background_array,
            observations=observations_array,
            obs_locations=obs_locations_array
        )
        
        return {
            "status": "success",
            "background_error_scale": float(optimizer.background_error_scale),
            "observation_error_scale": float(optimizer.observation_error_scale),
            "correlation_length_scale": float(optimizer.correlation_length_scale),
            "last_score": float(optimizer.last_incremental_score) if optimizer.last_incremental_score else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"自适应调整失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/params")
async def get_params() -> Dict[str, Any]:
    """获取当前优化器参数"""
    try:
        if not ALGORITHM_CORE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="algorithm_core模块不可用"
            )
        
        optimizer = get_optimizer_instance()
        
        return {
            "status": "success",
            "current_params": {
                "background_error_scale": float(optimizer.background_error_scale),
                "observation_error_scale": float(optimizer.observation_error_scale),
                "correlation_length_scale": float(optimizer.correlation_length_scale),
                "regularization": float(optimizer.regularization)
            },
            "best_params": optimizer.get_best_params(),
            "best_score": float(optimizer.best_score) if optimizer.best_score != float('inf') else None,
            "n_jobs": optimizer.n_jobs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取参数失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/params")
async def set_params(request: Dict[str, Any]) -> Dict[str, Any]:
    """设置优化器参数"""
    try:
        if not ALGORITHM_CORE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="algorithm_core模块不可用"
            )
        
        optimizer = get_optimizer_instance()
        
        if "background_error_scale" in request:
            optimizer.background_error_scale = float(request["background_error_scale"])
        if "observation_error_scale" in request:
            optimizer.observation_error_scale = float(request["observation_error_scale"])
        if "correlation_length_scale" in request:
            optimizer.correlation_length_scale = float(request["correlation_length_scale"])
        if "regularization" in request:
            optimizer.regularization = float(request["regularization"])
        if "n_jobs" in request:
            optimizer.set_parallel_jobs(int(request["n_jobs"]))
        
        return {
            "status": "success",
            "message": "参数更新成功",
            "current_params": {
                "background_error_scale": float(optimizer.background_error_scale),
                "observation_error_scale": float(optimizer.observation_error_scale),
                "correlation_length_scale": float(optimizer.correlation_length_scale),
                "regularization": float(optimizer.regularization),
                "n_jobs": optimizer.n_jobs
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置参数失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_optimizer() -> Dict[str, Any]:
    """重置优化器"""
    try:
        if not ALGORITHM_CORE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="algorithm_core模块不可用"
            )
        
        global variance_optimizer_instance, adaptive_optimizer_instance
        
        if variance_optimizer_instance:
            variance_optimizer_instance.reset()
        
        if adaptive_optimizer_instance:
            adaptive_optimizer_instance.reset()
        
        return {
            "status": "success",
            "message": "优化器已重置"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置优化器失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """获取方差场服务状态"""
    return {
        "status": "success",
        "algorithm_core_available": ALGORITHM_CORE_AVAILABLE,
        "has_optimizer_instance": variance_optimizer_instance is not None,
        "has_adaptive_instance": adaptive_optimizer_instance is not None,
        "version": "1.0.0"
    }
