"""
异常值检测算法 (Outlier Detection)
数据管道的第一道过滤器。

检测策略:
  1. 物理范围检查 (温度不能>50°C, 风速不能>50m/s等)
  2. 3σ 统计离群值 (基于滑动窗口)
  3. 空间一致性检查 (相邻格点差异过大)
  4. 时序一致性检查 (相邻时次跳变过大)

所有检测到的异常值会被标记为 NaN，后续管线做插值或丢弃。
"""
import numpy as np
from scipy.ndimage import gaussian_filter
from dataclasses import dataclass, field
from typing import Optional, Tuple, List


@dataclass
class OutlierConfig:
    """异常值检测配置"""
    # 物理范围
    t2m_min: float = 220.0     # K (-53°C)
    t2m_max: float = 330.0     # K (57°C)
    wind_max: float = 50.0     # m/s
    ps_min: float = 50000.0    # Pa
    ps_max: float = 105000.0   # Pa
    rh_range: Tuple[float, float] = (0.0, 100.0)
    blh_min: float = 0.0       # m
    blh_max: float = 3000.0    # m

    # 统计离群
    z_score_threshold: float = 3.5
    window_size: int = 5        # 滑动窗口 (格点)

    # 空间一致性
    spatial_std_factor: float = 4.0  # 超过邻域均值±4σ 标记
    spatial_kernel: int = 3

    # 时序跳变
    temporal_jump_factor: float = 5.0  # 相邻时次差超过 5σ 标记


class OutlierDetector:
    """
    异常值检测器

    用法:
        detector = OutlierDetector()
        cleaned = detector.detect_and_fix(data)
        # 或分步:
        mask = detector.detect(data)
        cleaned = detector.fix(data, mask)
    """

    def __init__(self, config: Optional[OutlierConfig] = None):
        self.config = config or OutlierConfig()
        self.last_mask: Optional[np.ndarray] = None

    # ── 主入口 ─────────────────────────────────

    def detect_and_fix(self, data: np.ndarray,
                       var_names: Optional[List[str]] = None) -> np.ndarray:
        """
        检测 + 修复 一站式

        Args:
            data: (C, H, W) 或 (T, C, H, W)
            var_names: 变量名列表, 用于物理范围检查
        Returns:
            cleaned: 修复后数据
        """
        mask = self.detect(data, var_names)
        return self.fix(data, mask)

    # ── 检测 ─────────────────────────────────

    def detect(self, data: np.ndarray,
               var_names: Optional[List[str]] = None) -> np.ndarray:
        """
        返回异常掩码 True=异常

        Args:
            data: (C, H, W) 或 (T, C, H, W)
        Returns:
            mask: 同 shape, True 表示异常
        """
        is_temporal = data.ndim == 4
        if is_temporal:
            T, C, H, W = data.shape
            data_3d = data.reshape(-1, C, H, W)
        else:
            C, H, W = data.shape
            data_3d = data[None]  # 加伪时间维度

        mask = np.zeros(data_3d.shape, dtype=bool)

        # 1. 物理范围检查
        mask |= self._physical_check(data_3d, var_names)

        # 2. 3σ 统计离群
        mask |= self._statistical_outlier(data_3d)

        # 3. 空间一致性检查
        mask |= self._spatial_consistency(data_3d)

        # 4. 时序一致性检查 (仅当有 T 维度)
        if is_temporal:
            mask |= self._temporal_consistency(data)

        self.last_mask = mask
        return mask

    # ── 修复 (线性插值) ──────────────────────

    def fix(self, data: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """用邻域均值填充异常值"""
        cleaned = data.copy()
        for i in np.argwhere(mask):
            c0, c1, c2, c3 = i
            # 3×3 邻域均值 (忽略自身)
            y0, x0 = max(0, c2 - 1), max(0, c3 - 1)
            y1, x1 = min(data.shape[-2], c2 + 2), min(data.shape[-1], c3 + 2)
            patch = cleaned[c0, c1, y0:y1, x0:x1]
            valid = patch[~mask[c0, c1, y0:y1, x0:x1]]
            if len(valid) > 0:
                cleaned[tuple(i)] = valid.mean()

        # 剩余 NaN 用高斯滤波填补
        nan_mask = np.isnan(cleaned) | np.isinf(cleaned)
        for c in range(cleaned.shape[1]):
            for t in range(cleaned.shape[0]):
                if nan_mask[t, c].any():
                    channel = cleaned[t, c].copy()
                    channel[nan_mask[t, c]] = 0
                    smoothed = gaussian_filter(channel, sigma=2)
                    cleaned[t, c, nan_mask[t, c]] = smoothed[nan_mask[t, c]]

        return cleaned

    # ── 各检测方法 ───────────────────────────

    def _physical_check(self, data: np.ndarray,
                        var_names: Optional[List[str]] = None) -> np.ndarray:
        """物理范围检查"""
        C = data.shape[1]
        mask = np.zeros(data.shape[:2], dtype=bool)

        # 按索引检查 (默认变量顺序: u10, v10, t2m, rh2m, ps, blh, ...)
        checks = [
            (0, -self.config.wind_max, self.config.wind_max),   # u10
            (1, -self.config.wind_max, self.config.wind_max),   # v10
            (2, self.config.t2m_min, self.config.t2m_max),      # t2m
            (3, *self.config.rh_range),                          # rh2m
            (4, self.config.ps_min, self.config.ps_max),         # ps
            (5, self.config.blh_min, self.config.blh_max),       # blh
        ]
        for idx, lo, hi in checks:
            if idx < C:
                mask[:, idx] = (data[:, idx] < lo) | (data[:, idx] > hi)

        # 扩展到完整空间维度
        return mask[:, :, None, None]  # (T, C, 1, 1)

    def _statistical_outlier(self, data: np.ndarray) -> np.ndarray:
        """3σ 统计离群值"""
        T, C, H, W = data.shape
        mask = np.zeros((T, C, H, W), dtype=bool)

        for c in range(C):
            ch = data[:, c]  # (T, H, W)
            median = np.median(ch)
            mad = np.median(np.abs(ch - median))  # 中位数绝对偏差
            threshold = self.config.z_score_threshold * (mad * 1.4826)  # 鲁棒 Z-score
            mask[:, c] = np.abs(ch - median) > threshold

        return mask

    def _spatial_consistency(self, data: np.ndarray) -> np.ndarray:
        """空间一致性: 格点与邻域差异过大"""
        T, C, H, W = data.shape
        mask = np.zeros((T, C, H, W), dtype=bool)

        from scipy.ndimage import uniform_filter
        for c in range(C):
            ch = data[:, c]
            local_mean = uniform_filter(ch, size=(1, self.config.spatial_kernel,
                                                  self.config.spatial_kernel))
            local_std = np.sqrt(
                uniform_filter(ch**2, size=(1, self.config.spatial_kernel,
                                            self.config.spatial_kernel))
                - local_mean**2
            )
            diff = np.abs(ch - local_mean)
            mask[:, c] = diff > self.config.spatial_std_factor * (local_std + 1e-8)

        return mask

    def _temporal_consistency(self, data: np.ndarray) -> np.ndarray:
        """时序一致性: 相邻时次跳变过大"""
        T, C, H, W = data.shape
        mask = np.zeros((T, C, H, W), dtype=bool)

        for t in range(1, T):
            diff = np.abs(data[t] - data[t - 1])
            diff_std = diff.std(axis=(1, 2), keepdims=True) + 1e-8
            mask[t] = diff > self.config.temporal_jump_factor * diff_std

        return mask


# ── 便捷函数 ────────────────────────────────────

def clean_forecast_field(field: np.ndarray) -> np.ndarray:
    """快速清洗单帧预报场"""
    detector = OutlierDetector()
    return detector.detect_and_fix(field)
