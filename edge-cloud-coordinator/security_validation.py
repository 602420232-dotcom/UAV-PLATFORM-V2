"""
Coordinator API 安全验证模块

提供输入消毒、路径保护等安全功能。
"""

import re
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)


def sanitize_task_id(task_id: str) -> str:
    """
    消毒任务 ID，移除危险字符。
    只允许字母数字、连字符和下划线。
    """
    sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '', task_id)
    return sanitized if sanitized else 'invalid_id'


def validate_coordinates(coord: Tuple[float, float], max_range: float = 1000.0) -> bool:
    """
    验证坐标值在合理范围内。
    """
    return (isinstance(coord, (tuple, list)) and
            len(coord) == 2 and
            isinstance(coord[0], (int, float)) and
            isinstance(coord[1], (int, float)) and
            abs(coord[0]) <= max_range and
            abs(coord[1]) <= max_range)


def validate_task_data(task_type: str, data: Dict) -> bool:
    """
    根据任务类型验证数据字段。
    """
    if task_type in ('global_path', 'local_avoidance'):
        start = data.get('start')
        goal = data.get('goal')
        if start and not validate_coordinates(tuple(start)):
            return False
        if goal and not validate_coordinates(tuple(goal)):
            return False
    return True


def safe_get(data: Dict, key: str, default=None) -> Any:
    """安全获取字典值，避免注入。"""
    value = data.get(key, default)
    if isinstance(value, str) and len(value) > 5000:
        return value[:5000]
    return value
