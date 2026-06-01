"""
边缘云协调器熔断器模块
Edge-Cloud Coordinator Circuit Breaker Module

提供HTTP和WebSocket调用的熔断器保护
"""

import pybreaker
import logging
from functools import wraps
from typing import Callable, Any, Optional
import time

# 配置日志
logger = logging.getLogger(__name__)


class CircuitBreakerConfig:
    """熔断器配置"""
    
    # HTTP 服务熔断器配置
    HTTP_SERVICE_CB = {
        'fail_max': 5,              # 失败5次后打开熔断器
        'reset_timeout': 60,        # 60秒后尝试半开
        'exclude': [Exception],     # 排除的异常类型
    }
    
    # WebSocket 连接熔断器配置
    WEBSOCKET_CB = {
        'fail_max': 3,              # WebSocket更敏感，失败3次
        'reset_timeout': 30,        # 30秒后尝试恢复
        'exclude': [],              # 不过滤任何异常
    }
    
    # 联邦学习熔断器配置
    FEDERATED_LEARNING_CB = {
        'fail_max': 4,
        'reset_timeout': 45,
        'exclude': [Exception],
    }


# 创建熔断器实例
http_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=CircuitBreakerConfig.HTTP_SERVICE_CB['fail_max'],
    reset_timeout=CircuitBreakerConfig.HTTP_SERVICE_CB['reset_timeout'],
    exclude=CircuitBreakerConfig.HTTP_SERVICE_CB['exclude']
)

websocket_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=CircuitBreakerConfig.WEBSOCKET_CB['fail_max'],
    reset_timeout=CircuitBreakerConfig.WEBSOCKET_CB['reset_timeout'],
    exclude=CircuitBreakerConfig.WEBSOCKET_CB['exclude']
)

federated_learning_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=CircuitBreakerConfig.FEDERATED_LEARNING_CB['fail_max'],
    reset_timeout=CircuitBreakerConfig.FEDERATED_LEARNING_CB['reset_timeout'],
    exclude=CircuitBreakerConfig.FEDERATED_LEARNING_CB['exclude']
)


class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""
    pass


class CircuitBreakerService:
    """熔断器服务封装"""
    
    def __init__(self):
        self.http_breaker = http_circuit_breaker
        self.websocket_breaker = websocket_circuit_breaker
        self.federated_breaker = federated_learning_circuit_breaker
        
        # 状态回调
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """设置熔断器状态回调"""
        
        def on_circuit_open(breaker):
            logger.warning(f"Circuit breaker OPENED: {breaker.name}")
        
        def on_circuit_half_open(breaker):
            logger.info(f"Circuit breaker HALF-OPEN: {breaker.name}")
        
        def on_circuit_closed(breaker):
            logger.info(f"Circuit breaker CLOSED: {breaker.name}")
        
        # 为所有熔断器添加回调
        for breaker in [self.http_breaker, self.websocket_breaker, self.federated_breaker]:
            breaker.add_eventListener(
                pybreaker.CircuitBreakerListener.EVENT_CLOSED,
                lambda e, b=breaker: on_circuit_closed(b)
            )
            breaker.add_eventListener(
                pybreaker.CircuitBreakerListener.EVENT_OPEN,
                lambda e, b=breaker: on_circuit_open(b)
            )
            breaker.add_eventListener(
                pybreaker.CircuitBreakerListener.EVENT_HALF_OPEN,
                lambda e, b=breaker: on_circuit_half_open(b)
            )
    
    def call_http_service(
        self, 
        func: Callable, 
        fallback: Optional[Callable] = None,
        *args, 
        **kwargs
    ) -> Any:
        """
        使用熔断器调用HTTP服务
        
        Args:
            func: 要调用的函数
            fallback: 降级函数
            *args, **kwargs: 函数参数
        
        Returns:
            函数返回值或降级函数返回值
        """
        try:
            return self.http_breaker.call(func, *args, **kwargs)
        except pybreaker.CircuitBreakerError:
            logger.warning(f"HTTP Circuit breaker is OPEN, using fallback")
            if fallback:
                return fallback(*args, **kwargs)
            raise CircuitBreakerOpenError("HTTP service circuit breaker is open")
    
    def call_websocket(
        self, 
        func: Callable, 
        fallback: Optional[Callable] = None,
        *args, 
        **kwargs
    ) -> Any:
        """
        使用熔断器调用WebSocket
        
        Args:
            func: 要调用的函数
            fallback: 降级函数
            *args, **kwargs: 函数参数
        
        Returns:
            函数返回值或降级函数返回值
        """
        try:
            return self.websocket_breaker.call(func, *args, **kwargs)
        except pybreaker.CircuitBreakerError:
            logger.warning(f"WebSocket Circuit breaker is OPEN, using fallback")
            if fallback:
                return fallback(*args, **kwargs)
            raise CircuitBreakerOpenError("WebSocket circuit breaker is open")
    
    def call_federated_learning(
        self, 
        func: Callable, 
        fallback: Optional[Callable] = None,
        *args, 
        **kwargs
    ) -> Any:
        """
        使用熔断器调用联邦学习
        
        Args:
            func: 要调用的函数
            fallback: 降级函数
            *args, **kwargs: 函数参数
        
        Returns:
            函数返回值或降级函数返回值
        """
        try:
            return self.federated_breaker.call(func, *args, **kwargs)
        except pybreaker.CircuitBreakerError:
            logger.warning(f"Federated Learning Circuit breaker is OPEN, using fallback")
            if fallback:
                return fallback(*args, **kwargs)
            raise CircuitBreakerOpenError("Federated learning circuit breaker is open")
    
    def get_status(self) -> dict:
        """获取熔断器状态"""
        return {
            'http': {
                'state': self.http_breaker.current_state.name,
                'failures': self.http_breaker.failures,
                'successes': self.http_breaker.successes,
            },
            'websocket': {
                'state': self.websocket_breaker.current_state.name,
                'failures': self.websocket_breaker.failures,
                'successes': self.websocket_breaker.successes,
            },
            'federated_learning': {
                'state': self.federated_breaker.current_state.name,
                'failures': self.federated_breaker.failures,
                'successes': self.federated_breaker.successes,
            }
        }


# 全局熔断器服务实例
cb_service = CircuitBreakerService()


def circuit_breaker(breaker_type: str = 'http'):
    """
    熔断器装饰器
    
    Args:
        breaker_type: 熔断器类型 ('http', 'websocket', 'federated')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 根据类型选择熔断器
            if breaker_type == 'http':
                breaker = http_circuit_breaker
            elif breaker_type == 'websocket':
                breaker = websocket_circuit_breaker
            elif breaker_type == 'federated':
                breaker = federated_learning_circuit_breaker
            else:
                raise ValueError(f"Unknown breaker type: {breaker_type}")
            
            try:
                return breaker.call(func, *args, **kwargs)
            except pybreaker.CircuitBreakerError:
                logger.warning(f"Circuit breaker {breaker_type} is OPEN for {func.__name__}")
                raise
        
        return wrapper
    return decorator


def with_circuit_breaker(breaker_name: str, fallback: Optional[Callable] = None):
    """
    使用指定名称的熔断器
    
    Args:
        breaker_name: 熔断器名称
        fallback: 降级函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 根据名称选择熔断器
            if 'http' in breaker_name:
                breaker = http_circuit_breaker
            elif 'websocket' in breaker_name:
                breaker = websocket_circuit_breaker
            elif 'federated' in breaker_name:
                breaker = federated_learning_circuit_breaker
            else:
                breaker = http_circuit_breaker
            
            try:
                return breaker.call(func, *args, **kwargs)
            except pybreaker.CircuitBreakerError:
                logger.warning(f"Circuit breaker {breaker_name} is OPEN")
                if fallback:
                    return fallback(*args, **kwargs)
                raise
        
        return wrapper
    return decorator


# 示例使用

# 示例1: 使用装饰器
@circuit_breaker(breaker_type='http')
def call_external_api(url: str) -> dict:
    """调用外部API"""
    import requests
    response = requests.get(url)
    return response.json()


# 示例2: 使用服务类
def call_websocket_endpoint(endpoint: str, message: dict) -> dict:
    """调用WebSocket端点"""
    # WebSocket调用逻辑
    return {'status': 'sent', 'endpoint': endpoint}


def websocket_fallback(endpoint: str, message: dict) -> dict:
    """WebSocket降级函数"""
    logger.warning(f"Using fallback for WebSocket: {endpoint}")
    return {'status': 'fallback', 'message': 'Service temporarily unavailable'}


# 示例3: 使用服务类
def demo_service_usage():
    """演示服务使用"""
    service = CircuitBreakerService()
    
    # 调用HTTP服务
    try:
        result = service.call_http_service(
            call_external_api,
            fallback=lambda url: {'error': 'service unavailable'},
            url='http://example.com/api'
        )
        print(f"Result: {result}")
    except CircuitBreakerOpenError as e:
        print(f"Circuit breaker is open: {e}")
    
    # 调用WebSocket
    try:
        result = service.call_websocket(
            call_websocket_endpoint,
            fallback=websocket_fallback,
            endpoint='/ws/data',
            message={'type': 'update'}
        )
        print(f"WebSocket result: {result}")
    except CircuitBreakerOpenError as e:
        print(f"WebSocket circuit breaker is open: {e}")
    
    # 获取状态
    status = service.get_status()
    print(f"Circuit breaker status: {status}")


if __name__ == '__main__':
    # 运行演示
    demo_service_usage()
