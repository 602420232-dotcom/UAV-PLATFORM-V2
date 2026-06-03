"""
时空配准算法

问题:
  天资 (0.25° ≈ 25km) 和 风雷 (3km) 分辨率不同,
  而且发布时间不同步。

解决:
  空间配准: 重采样到统一网格 + DEM 地形校正
  时间配准: 多源预报的异步时间对齐 + 线性插值
"""
import numpy as np
from scipy.ndimage import zoom, gaussian_filter
from dataclasses import dataclass, field
from typing import Optional, Tuple, List
from datetime import datetime, timedelta


@dataclass
class SpatiotemporalConfig:
    """配准配置"""
    target_resolution_km: float = 3.0       # 统一到 3km 网格
    target_grid: Tuple[int, int] = (50, 50) # 成都平原粗网格
    max_time_diff_min: int = 60             # 最大时间差 (超过此值不配准)
    interpolation_order: int = 1            # 插值阶数 (1=线性)
    terrain_correction: bool = True         # 是否做地形校正


class SpatiotemporalRegistrator:
    """
    时空配准器

    用法:
        registrator = SpatiotemporalRegistrator()
        registered = registrator.register(tianzi_data, fenglei_data)
    """

    def __init__(self, config: Optional[SpatiotemporalConfig] = None):
        self.config = config or SpatiotemporalConfig()

    # ── 主入口 ─────────────────────────────────

    def register(self, sources: List[dict]) -> np.ndarray:
        """
        多源数据配准

        Args:
            sources: [{"name": "tianzi", "data": np.ndarray(C, H, W),
                        "resolution_km": 25, "timestamp": datetime},
                       {"name": "fenglei", ...}]

        Returns:
            registered: (C, Ht, Wt) 统一网格的融合场
        """
        Ht, Wt = self.config.target_grid
        C = sources[0]["data"].shape[0]
        combined = np.zeros((C, Ht, Wt))
        weights = np.zeros((C, Ht, Wt))

        for source in sources:
            # 空间配准
            resampled = self._spatial_resample(
                source["data"],
                source["resolution_km"],
                (Ht, Wt)
            )

            # 时间偏差权重 (越新权重越大)
            time_weight = self._time_weight(source.get("timestamp"))

            # DEM 地形校正
            if self.config.terrain_correction:
                resampled = self._terrain_correct(resampled)

            # 加权叠加
            combined += resampled * time_weight
            weights += time_weight

        return combined / np.maximum(weights, 1e-8)

    # ── 空间配准 ─────────────────────────────

    def _spatial_resample(self, data: np.ndarray,
                          src_res_km: float,
                          target_shape: Tuple[int, int]) -> np.ndarray:
        """重采样到目标分辨率"""
        C, Hs, Ws = data.shape
        Ht, Wt = target_shape

        if src_res_km == self.config.target_resolution_km:
            return data

        # 缩放因子
        sy = Ht / Hs * (src_res_km / self.config.target_resolution_km)
        sx = Wt / Ws * (src_res_km / self.config.target_resolution_km)

        resampled = np.zeros((C, Ht, Wt))
        for c in range(C):
            resampled[c] = zoom(data[c], (sy, sx), order=self.config.interpolation_order)

        return resampled

    def _terrain_correct(self, field: np.ndarray) -> np.ndarray:
        """地形校正: 温度/气压随高度修正"""
        # 简化修正: 温度每100m 降 0.65°C
        dem = self._load_dem(field.shape[1], field.shape[2])
        dem_norm = (dem - dem.mean()) / 100.0  # 100m 为单位

        corrected = field.copy()
        if field.shape[0] > 2:  # t2m 通道 (索引2)
            corrected[2] -= dem_norm * 0.65  # K
        if field.shape[0] > 4:  # ps 通道 (索引4)
            corrected[4] -= dem_norm * 12.0  # Pa/100m

        return corrected

    @staticmethod
    def _load_dem(H: int, W: int) -> np.ndarray:
        """加载 DEM (简化版)"""
        from scipy.ndimage import zoom
        base = np.fromfunction(lambda i, j: 500 + 400 * (1 - i / 50) - 200 * (j / 50), (50, 50))
        return zoom(base, (H / 50, W / 50), order=1)

    def register_pair(self, coarse: np.ndarray, fine: np.ndarray,
                      coarse_res_km: float = 25.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        配准一对粗/细网格

        Returns:
            coarse_reg: (C, 50, 50)
            fine_reg: (C, 150, 150)
        """
        coarse_reg = self._spatial_resample(coarse, coarse_res_km, (50, 50))
        if self.config.terrain_correction:
            coarse_reg = self._terrain_correct(coarse_reg)
        return coarse_reg, fine

    # ── 时间配准 ─────────────────────────────

    def _time_weight(self, timestamp: Optional[datetime]) -> float:
        """计算时间衰减权重"""
        if timestamp is None:
            return 1.0
        age = (datetime.now() - timestamp).total_seconds() / 60
        if age > self.config.max_time_diff_min:
            return 0.0
        # 线性衰减: 最新的权重 1.0, 最新的衰减到 0.1
        return max(0.1, 1.0 - age / self.config.max_time_diff_min)

    def synchronize_timestamps(self, sources: List[dict],
                               target_time: datetime) -> List[np.ndarray]:
        """
        时间同步: 将所有源插值到同一时刻

        Args:
            sources: [{"data": ..., "timestamp": ...}, ...]
            target_time: 目标时刻

        Returns:
            sync_data: [np.ndarray, ...]
        """
        synced = []
        for src in sources:
            if src["timestamp"] == target_time:
                synced.append(src["data"])
            else:
                # 线性时间插值 (简化: 直接用最接近的数据)
                time_diff = abs((src["timestamp"] - target_time).total_seconds())
                if time_diff < self.config.max_time_diff_min * 60:
                    synced.append(src["data"])
                else:
                    synced.append(np.zeros_like(src["data"]))
        return synced
