"""
数据管道配置 — 成都平原 150km×150km 区域
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class DomainConfig:
    """成都平原计算域"""
    name: str = "chengdu_plain"
    lat_center: float = 30.67   # 成都市中心
    lon_center: float = 104.07
    # 150km × 150km
    width_km: float = 150.0
    height_km: float = 150.0
    # 输入分辨率 (天资/风雷 ≈ 3km)
    coarse_res_km: float = 3.0
    # 输出分辨率 (目标)
    fine_res_km: float = 1.0

    @property
    def coarse_grid(self) -> tuple:
        """粗网格大小 (3km)"""
        return (int(self.height_km / self.coarse_res_km),
                int(self.width_km / self.coarse_res_km))  # (50, 50)

    @property
    def fine_grid(self) -> tuple:
        """细网格大小 (1km)"""
        return (int(self.height_km / self.fine_res_km),
                int(self.width_km / self.fine_res_km))  # (150, 150)


@dataclass
class CMADataConfig:
    """CMA 数据源配置"""
    # 天智系列 — 全球/区域确定性预报
    tianzi_url: str = "https://api.cma.cn/tianzi/v1/forecast"
    tianzi_key: str = ""               # 需要注册获取
    tianzi_params: dict = field(default_factory=lambda: {
        "model": "GRAPES_GFS",  # 全球谱模式
        "resolution": "0.25",  # 0.25° ≈ 25km
        "levels": ["1000", "925", "850", "700", "500"],
        "fcst_hours": [0, 3, 6, 12, 24, 48, 72],
    })

    # 风雷 — 高分辨率区域模式
    fenglei_url: str = "https://api.cma.cn/fenglei/v1/forecast"
    fenglei_key: str = ""
    fenglei_params: dict = field(default_factory=lambda: {
        "model": "GRAPES_MESO",  # 中尺度区域模式
        "resolution": "0.03",  # 3km
        "levels": ["1000", "925", "850", "700", "500", "300"],
        "fcst_hours": [0, 1, 3, 6, 12, 24],
    })

    # GRIB 下载本地缓存
    cache_dir: str = "/data/cma_cache"
    update_interval_min: int = 30


@dataclass
class VariableConfig:
    """气象变量映射"""
    variables: dict = field(default_factory=lambda: {
        # [CMA 变量名, 中文名, 单位]
        "u10":  "10m_u_wind", "v10":  "10m_v_wind",
        "t2m":  "2m_temperature", "rh2m": "2m_relative_humidity",
        "ps":   "surface_pressure", "blh":  "boundary_layer_height",
        "swr":  "shortwave_radiation", "lwr":  "longwave_radiation",
        "hpbl": "pbl_height",
        # 高空层
        "u":  "winds", "v": "winds", "t":  "temperature",
        "q":  "humidity", "w": "vertical_velocity",
    })

    # 地面变量（张量通道顺序）
    surface_channels: List[str] = field(default_factory=lambda: [
        "u10", "v10", "t2m", "rh2m", "ps", "blh"
    ])
    # 3D 变量
    pressure_channels: List[str] = field(default_factory=lambda: [
        "u", "v", "t", "q", "w"
    ])


@dataclass
class ModelConfig:
    """整体配置"""
    domain: DomainConfig = field(default_factory=DomainConfig)
    cma: CMADataConfig = field(default_factory=CMADataConfig)
    vars: VariableConfig = field(default_factory=VariableConfig)

    device: str = "cuda"  # or "cpu"


CONFIG = ModelConfig()
