"""
边缘云协调器熔断器 REST API
Edge-Cloud Coordinator Circuit Breaker REST API

提供熔断器状态的HTTP接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from circuit_breaker import cb_service, CircuitBreakerOpenError
import logging

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/api/circuit-breaker", tags=["Circuit Breaker"])


class FallbackRequest(BaseModel):
    """降级请求"""
    endpoint: str
    fallback_type: str = "websocket"


class CircuitBreakerResponse(BaseModel):
    """熔断器响应"""
    success: bool
    status: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


@router.get("/status", response_model=CircuitBreakerResponse)
async def get_status():
    """
    获取所有熔断器状态

    Returns:
        所有熔断器的当前状态
    """
    try:
        status = cb_service.get_status()
        return CircuitBreakerResponse(
            success=True,
            status=status,
            message="Circuit breaker status retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get circuit breaker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{breaker_name}", response_model=CircuitBreakerResponse)
async def get_breaker_status(breaker_name: str):
    """
    获取指定熔断器状态

    Args:
        breaker_name: 熔断器名称 (http, websocket, federated)

    Returns:
        熔断器状态
    """
    try:
        status = cb_service.get_status()

        if breaker_name not in status:
            raise HTTPException(
                status_code=404,
                detail=f"Circuit breaker '{breaker_name}' not found"
            )

        return CircuitBreakerResponse(
            success=True,
            status=status[breaker_name],
            message=f"Circuit breaker '{breaker_name}' status retrieved"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get breaker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trip/{breaker_name}", response_model=CircuitBreakerResponse)
async def trip_breaker(breaker_name: str):
    """
    手动触发熔断

    Args:
        breaker_name: 熔断器名称

    Returns:
        操作结果
    """
    try:
        # 选择熔断器
        if breaker_name == 'http':
            breaker = cb_service.http_breaker
        elif breaker_name == 'websocket':
            breaker = cb_service.websocket_breaker
        elif breaker_name == 'federated':
            breaker = cb_service.federated_breaker
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown circuit breaker: {breaker_name}"
            )

        # 手动打开熔断器
        breaker.open()

        logger.warning(f"Circuit breaker '{breaker_name}' manually tripped")

        return CircuitBreakerResponse(
            success=True,
            message=f"Circuit breaker '{breaker_name}' has been tripped"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trip breaker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset/{breaker_name}", response_model=CircuitBreakerResponse)
async def reset_breaker(breaker_name: str):
    """
    手动重置熔断器

    Args:
        breaker_name: 熔断器名称

    Returns:
        操作结果
    """
    try:
        # 选择熔断器
        if breaker_name == 'http':
            breaker = cb_service.http_breaker
        elif breaker_name == 'websocket':
            breaker = cb_service.websocket_breaker
        elif breaker_name == 'federated':
            breaker = cb_service.federated_breaker
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown circuit breaker: {breaker_name}"
            )

        # 手动重置熔断器
        breaker.close()

        logger.info(f"Circuit breaker '{breaker_name}' has been reset")

        return CircuitBreakerResponse(
            success=True,
            message=f"Circuit breaker '{breaker_name}' has been reset"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset breaker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=CircuitBreakerResponse)
async def health_check():
    """
    健康检查

    Returns:
        健康状态
    """
    try:
        status = cb_service.get_status()

        # 检查所有熔断器
        all_healthy = all(
            s['state'] == 'CLOSED'
            for s in status.values()
        )

        return CircuitBreakerResponse(
            success=True,
            status=status,
            message="Healthy" if all_healthy else "Degraded"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return CircuitBreakerResponse(
            success=False,
            message=f"Unhealthy: {str(e)}"
        )


# 示例: 使用熔断器的端点


@router.post("/call-with-fallback")
async def call_with_fallback(request: FallbackRequest):
    """
    使用熔断器调用服务

    Args:
        request: 请求参数

    Returns:
        调用结果或降级结果
    """
    try:
        if request.fallback_type == 'websocket':
            result = cb_service.call_websocket(
                lambda: {"status": "called", "endpoint": request.endpoint},
                fallback=lambda: {"status": "fallback", "message": "Service unavailable"}
            )
        else:
            result = cb_service.call_http_service(
                lambda: {"status": "called", "endpoint": request.endpoint},
                fallback=lambda: {"status": "fallback", "message": "Service unavailable"}
            )

        return {
            "success": True,
            "result": result,
            "used_fallback": "fallback" in str(result.get('status', ''))
        }
    except CircuitBreakerOpenError as e:
        return {
            "success": False,
            "result": {"status": "fallback", "message": str(e)},
            "used_fallback": True
        }
    except Exception as e:
        logger.error(f"Call failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 使用示例


if __name__ == "__main__":
    import uvicorn

    # 创建FastAPI应用
    from fastapi import FastAPI
    app = FastAPI(title="Circuit Breaker API")

    # 注册路由
    app.include_router(router)

    # 启动服务器
    uvicorn.run(app, host="0.0.0.0", port=8000)
