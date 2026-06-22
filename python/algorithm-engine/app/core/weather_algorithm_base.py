"""
气象感知算法基类
为全部102种算法提供统一的真实气象数据接入能力

设计思路：
1. 所有算法通过此基类获取 FengWu 真实气象数据
2. 支持模拟数据回退（开发测试环境）
3. 自动将全球气象数据裁剪到任务区域
4. 提供统一的气象代价计算接口
"""
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from loguru import logger


@dataclass
class WeatherContext:
    """气象上下文 - 算法运行时的气象数据容器"""
    # 风场
    u10: Optional[np.ndarray] = None  # 10m U风分量
    v10: Optional[np.ndarray] = None  # 10m V风分量
    wind_speed: Optional[np.ndarray] = None
    wind_direction: Optional[np.ndarray] = None
    
    # 温度/气压
    t2m: Optional[np.ndarray] = None  # 2m温度
    msl: Optional[np.ndarray] = None  # 海平面气压
    
    # 高空变量（可选）
    u_850: Optional[np.ndarray] = None  # 850hPa U风
    v_850: Optional[np.ndarray] = None  # 850hPa V风
    t_850: Optional[np.ndarray] = None  # 850hPa温度
    
    # 衍生场
    turbulence: Optional[np.ndarray] = None  # 湍流强度（估算）
    
    # 元数据
    timestamp: str = ""
    forecast_hour: int = 0
    lat_range: Tuple[float, float] = (0, 0)
    lon_range: Tuple[float, float] = (0, 0)
    resolution: float = 0.25
    source: str = "mock"  # 数据来源: mock/fengwu-v2-real/fengwu-ghr
    
    @property
    def has_real_data(self) -> bool:
        """是否包含真实气象数据"""
        return self.u10 is not None and self.v10 is not None
    
    def get_wind_at(self, lat_idx: int, lon_idx: int) -> Dict[str, float]:
        """获取指定网格点的风场信息"""
        result = {}
        if self.u10 is not None and 0 <= lat_idx < self.u10.shape[0] and 0 <= lon_idx < self.u10.shape[1]:
            result['u10'] = float(self.u10[lat_idx, lon_idx])
            result['v10'] = float(self.v10[lat_idx, lon_idx])
            if self.wind_speed is not None:
                result['wind_speed'] = float(self.wind_speed[lat_idx, lon_idx])
            else:
                result['wind_speed'] = np.sqrt(result['u10']**2 + result['v10']**2)
            if self.wind_direction is not None:
                result['wind_direction'] = float(self.wind_direction[lat_idx, lon_idx])
            else:
                result['wind_direction'] = float(np.degrees(np.arctan2(result['v10'], result['u10'])))
        if self.t2m is not None and 0 <= lat_idx < self.t2m.shape[0] and 0 <= lon_idx < self.t2m.shape[1]:
            result['t2m'] = float(self.t2m[lat_idx, lon_idx])
        if self.msl is not None and 0 <= lat_idx < self.msl.shape[0] and 0 <= lon_idx < self.msl.shape[1]:
            result['msl'] = float(self.msl[lat_idx, lon_idx])
        if self.turbulence is not None and 0 <= lat_idx < self.turbulence.shape[0] and 0 <= lon_idx < self.turbulence.shape[1]:
            result['turbulence'] = float(self.turbulence[lat_idx, lon_idx])
        return result


class WeatherAwareAlgorithmBase(ABC):
    """
    气象感知算法基类
    
    所有102种算法应继承此类以获得真实气象数据接入能力。
    子类只需实现 execute() 方法，气象数据获取由基类统一处理。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.weather_context: Optional[WeatherContext] = None
        self.use_real_weather: bool = self.config.get('use_real_weather', True)
        self.weather_source: str = self.config.get('weather_source', 'fengwu')
        self.fallback_to_mock: bool = self.config.get('fallback_to_mock', True)
        
    def set_weather_context(self, context: WeatherContext):
        """设置气象上下文"""
        self.weather_context = context
        if context.has_real_data:
            logger.info(f"[{self.__class__.__name__}] 已接入真实气象数据: {context.timestamp}, 预报时效={context.forecast_hour}h")
        else:
            logger.warning(f"[{self.__class__.__name__}] 气象上下文无真实数据，将使用模拟数据")
    
    def get_weather_field(self, field_name: str, default: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
        """获取指定气象场"""
        if self.weather_context is None:
            return default
        return getattr(self.weather_context, field_name, default)
    
    def calculate_wind_cost(self, lat_idx: int, lon_idx: int, 
                           flight_direction: Optional[float] = None) -> float:
        """
        计算风阻代价（通用接口）
        
        Args:
            lat_idx, lon_idx: 网格索引
            flight_direction: 飞行方向（度，正北为0）
            
        Returns:
            风阻代价（0-1，越小越好）
        """
        if self.weather_context is None or not self.weather_context.has_real_data:
            return 0.0
            
        wind = self.weather_context.get_wind_at(lat_idx, lon_idx)
        if not wind:
            return 0.0
            
        wind_speed = wind.get('wind_speed', 0)
        max_safe_wind = self.config.get('max_wind_speed', 20.0)
        
        # 超过安全风速，极高代价
        if wind_speed > max_safe_wind:
            return 1.0
            
        # 基础风阻代价
        cost = (wind_speed / max_safe_wind) ** 2
        
        # 如果提供了飞行方向，计算相对风向
        if flight_direction is not None and 'wind_direction' in wind:
            wind_dir = wind['wind_direction']
            relative_angle = abs(flight_direction - wind_dir)
            relative_angle = min(relative_angle, 360 - relative_angle)
            
            # 逆风（180°）代价最高，顺风（0°）代价最低
            headwind_factor = np.cos(np.radians(relative_angle))  # 1=顺风, -1=逆风
            cost *= (1.5 - 0.5 * headwind_factor)  # 逆风时代价放大
            
        return min(cost, 1.0)
    
    def calculate_temperature_cost(self, lat_idx: int, lon_idx: int) -> float:
        """计算温度代价（极端温度警告）"""
        if self.weather_context is None:
            return 0.0
            
        t2m = self.weather_context.t2m
        if t2m is None:
            return 0.0
            
        temp = float(t2m[lat_idx, lon_idx]) if 0 <= lat_idx < t2m.shape[0] and 0 <= lon_idx < t2m.shape[1] else 273.15
        temp_c = temp - 273.15  # 转为摄氏度
        
        # 极端高温/低温警告
        if temp_c > 40 or temp_c < -20:
            return 0.8
        elif temp_c > 35 or temp_c < -10:
            return 0.4
        return 0.0
    
    def is_weather_safe(self, lat_idx: int, lon_idx: int) -> bool:
        """检查指定位置的气象安全性"""
        wind_cost = self.calculate_wind_cost(lat_idx, lon_idx)
        temp_cost = self.calculate_temperature_cost(lat_idx, lon_idx)
        
        # 综合安全判断
        return wind_cost < 0.9 and temp_cost < 0.8
    
    def get_weather_summary(self) -> Dict[str, Any]:
        """获取当前气象数据摘要"""
        if self.weather_context is None:
            return {'status': 'no_data'}
            
        ctx = self.weather_context
        summary = {
            'status': 'real' if ctx.has_real_data else 'mock',
            'timestamp': ctx.timestamp,
            'forecast_hour': ctx.forecast_hour,
            'resolution': ctx.resolution,
            'lat_range': ctx.lat_range,
            'lon_range': ctx.lon_range,
        }
        
        if ctx.has_real_data:
            summary['wind_speed_mean'] = float(np.mean(ctx.wind_speed)) if ctx.wind_speed is not None else None
            summary['wind_speed_max'] = float(np.max(ctx.wind_speed)) if ctx.wind_speed is not None else None
            summary['t2m_mean'] = float(np.mean(ctx.t2m)) if ctx.t2m is not None else None
            
        return summary
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        算法执行入口（子类必须实现）
        
        Args:
            params: 算法参数字典
            
        Returns:
            算法执行结果
        """
        pass
    
    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        统一运行入口（带日志和快照）
        """
        from .experiment_logger import ExperimentLogger
        from .snapshot_manager import SnapshotManager
        
        experiment_id = params.get('experiment_id', f"{self.__class__.__name__}_{int(datetime.now().timestamp())}")
        logger_obj = ExperimentLogger(experiment_id, self.__class__.__name__)
        
        logger_obj.stage_start('execution')
        
        try:
            # 记录气象数据摘要
            weather_summary = self.get_weather_summary()
            logger_obj.info('weather', f"气象数据状态: {weather_summary['status']}", weather_summary)
            
            # 执行算法
            result = self.execute(params)
            
            # 添加气象数据信息到结果
            result['weather_context'] = weather_summary
            result['experiment_id'] = experiment_id
            
            logger_obj.stage_end('execution')
            logger_obj.experiment_end(result.get('metrics'))
            
            return result
            
        except Exception as e:
            logger_obj.error('execution', f"算法执行失败: {str(e)}")
            logger_obj.stage_end('execution')
            raise
