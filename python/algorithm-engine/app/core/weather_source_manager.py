"""
气象数据源管理器
支持多数据源切换：风乌(FengWu)、风雷(FengLei)、天资(TianZi)、WRF
"""
import os
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class WeatherSourceType(Enum):
    FENGWU = "fengwu"           # 风乌全球预报
    FENGWU_GHR = "fengwu_ghr"   # 风乌高分辨率
    FENGLEI = "fenglei"         # 风雷短临预报
    TIANZI = "tianzi"           # 天资区域AI
    WRF = "wrf"                 # WRF数值模式
    MOCK = "mock"               # 模拟数据（开发测试）


@dataclass
class WeatherSourceConfig:
    """气象数据源配置"""
    source_type: WeatherSourceType
    name: str
    enabled: bool = True
    priority: int = 0           # 优先级（数值越小优先级越高）
    config: Dict = field(default_factory=dict)
    
    # 风乌特定配置
    model_path: Optional[str] = None
    data_mean_path: Optional[str] = None
    data_std_path: Optional[str] = None
    
    # FengWu-GHR 特定配置
    ghr_config_path: Optional[str] = None
    checkpoint_dir: Optional[str] = None
    
    # 通用配置
    forecast_hours: int = 72    # 预报时效（小时）
    resolution: str = "0.25"    # 分辨率（度）


class WeatherSourceManager:
    """气象数据源管理器"""
    
    def __init__(self):
        self.sources: Dict[str, WeatherSourceConfig] = {}
        self.adapters: Dict[str, object] = {}
        self._init_default_sources()
        
    def _init_default_sources(self):
        """初始化默认数据源配置"""
        # 风乌（本地部署）
        fengwu_base = os.environ.get('FENGWU_PATH', 'D:/Developer/FengWu_All/FengWu')
        self.register_source(WeatherSourceConfig(
            source_type=WeatherSourceType.FENGWU,
            name="风乌全球预报",
            priority=1,
            model_path=os.path.join(fengwu_base, 'fengwu_v2.onnx'),
            data_mean_path=os.path.join(fengwu_base, 'data_mean.npy'),
            data_std_path=os.path.join(fengwu_base, 'data_std.npy'),
            forecast_hours=336,  # 14天
            resolution="0.25"
        ))
        
        # 风乌-GHR（本地部署）
        fengwu_ghr_base = os.environ.get('FENGWU_GHR_PATH', 'D:/Developer/FengWu_All/FengWu-GHR')
        self.register_source(WeatherSourceConfig(
            source_type=WeatherSourceType.FENGWU_GHR,
            name="风乌高分辨率",
            priority=2,
            ghr_config_path=os.path.join(fengwu_ghr_base, 'config/fengwu_ghr_cfg_74v_0.25_torch.py'),
            checkpoint_dir=os.path.join(fengwu_ghr_base, 'onnx/meta_model_0.25'),
            forecast_hours=240,  # 10天
            resolution="0.25"
        ))
        
        # 风雷（预留API配置）
        self.register_source(WeatherSourceConfig(
            source_type=WeatherSourceType.FENGLEI,
            name="风雷短临预报",
            enabled=False,  # 默认禁用，等待API
            priority=3,
            config={
                'api_endpoint': os.environ.get('FENGLEI_API_URL', ''),
                'api_key': os.environ.get('FENGLEI_API_KEY', ''),
                'forecast_hours': 3
            },
            resolution="0.01"
        ))
        
        # 天资（预留API配置）
        self.register_source(WeatherSourceConfig(
            source_type=WeatherSourceType.TIANZI,
            name="天资区域AI",
            enabled=False,
            priority=4,
            config={
                'api_endpoint': os.environ.get('TIANZI_API_URL', ''),
                'api_key': os.environ.get('TIANZI_API_KEY', ''),
                'forecast_hours': 12
            },
            resolution="0.01"
        ))
        
        # WRF（本地模式）
        self.register_source(WeatherSourceConfig(
            source_type=WeatherSourceType.WRF,
            name="WRF数值模式",
            enabled=False,
            priority=5,
            config={
                'wrf_path': os.environ.get('WRF_PATH', ''),
                'namelist_path': ''
            },
            resolution="0.03"
        ))
        
        # 模拟数据（开发测试）
        self.register_source(WeatherSourceConfig(
            source_type=WeatherSourceType.MOCK,
            name="模拟数据",
            enabled=True,
            priority=99,
            forecast_hours=72,
            resolution="0.25"
        ))
        
    def register_source(self, config: WeatherSourceConfig):
        """注册数据源"""
        self.sources[config.source_type.value] = config
        logger.info(f"注册气象数据源: {config.name} ({config.source_type.value})")
        
    def get_active_sources(self) -> List[WeatherSourceConfig]:
        """获取启用的数据源（按优先级排序）"""
        return sorted(
            [s for s in self.sources.values() if s.enabled],
            key=lambda x: x.priority
        )
        
    def get_source(self, source_type: str) -> Optional[WeatherSourceConfig]:
        """获取指定数据源配置"""
        return self.sources.get(source_type)
        
    def update_source_config(self, source_type: str, **kwargs):
        """更新数据源配置"""
        if source_type in self.sources:
            for key, value in kwargs.items():
                setattr(self.sources[source_type], key, value)
            logger.info(f"更新数据源配置: {source_type}")
            
    def get_adapter(self, source_type: str):
        """获取或创建数据源适配器"""
        if source_type not in self.adapters:
            config = self.sources.get(source_type)
            if not config:
                raise ValueError(f"未知数据源: {source_type}")
                
            if config.source_type == WeatherSourceType.FENGWU:
                from ..adapters.fengwu_adapter import FengWuAdapter, FengWuConfig
                self.adapters[source_type] = FengWuAdapter(FengWuConfig(
                    model_path=config.model_path,
                    data_mean_path=config.data_mean_path,
                    data_std_path=config.data_std_path
                ))
            elif config.source_type == WeatherSourceType.FENGWU_GHR:
                from ..adapters.fengwu_ghr_adapter import FengWuGHRAdapter, FengWuGHRConfig
                self.adapters[source_type] = FengWuGHRAdapter(FengWuGHRConfig(
                    config_path=config.ghr_config_path,
                    checkpoint_dir=config.checkpoint_dir,
                    save_path=os.environ.get('FENGWU_OUTPUT_PATH', '/tmp/fengwu_output')
                ))
                
        return self.adapters.get(source_type)
        
    def test_connection(self, source_type: str) -> Dict:
        """测试数据源连接"""
        config = self.sources.get(source_type)
        if not config:
            return {'success': False, 'message': f'未知数据源: {source_type}'}
            
        try:
            if config.source_type == WeatherSourceType.FENGWU:
                if not os.path.exists(config.model_path):
                    return {'success': False, 'message': f'模型文件不存在: {config.model_path}'}
                if not os.path.exists(config.data_mean_path):
                    return {'success': False, 'message': f'均值文件不存在: {config.data_mean_path}'}
                return {'success': True, 'message': '风乌模型文件检查通过'}
                
            elif config.source_type == WeatherSourceType.FENGWU_GHR:
                if not os.path.exists(config.ghr_config_path):
                    return {'success': False, 'message': f'配置文件不存在: {config.ghr_config_path}'}
                return {'success': True, 'message': '风乌-GHR配置检查通过'}
                
            elif config.source_type == WeatherSourceType.FENGLEI:
                api_key = config.config.get('api_key')
                if not api_key:
                    return {'success': False, 'message': '风雷API密钥未配置'}
                return {'success': True, 'message': '风雷API配置已设置'}
                
            elif config.source_type == WeatherSourceType.WRF:
                return {'success': False, 'message': 'WRF模式需在远程服务器上运行'}
                
            else:
                return {'success': True, 'message': '模拟数据源可用'}
                
        except Exception as e:
            return {'success': False, 'message': f'测试失败: {str(e)}'}
