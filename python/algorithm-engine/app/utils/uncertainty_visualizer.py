"""GPR 不确定性可视化工具.

将 GPR 预测的不确定性结果转换为可视化数据格式，
支持不确定性热力图、置信区间可视化和 GeoJSON 输出。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class UncertaintyVisualizer:
    """GPR 不确定性可视化工具.

    将 GPRegressionModel / GPRUncertaintyQuantifier 的预测结果
    转换为前端可直接渲染的可视化数据结构。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.default_grid_size = self.config.get("default_grid_size", 50)

    def generate_heatmap_data(
        self,
        coordinates: list[list[float]],
        uncertainty_values: list[float],
        mean_values: Optional[list[float]] = None,
        grid_size: Optional[int] = None,
    ) -> dict[str, Any]:
        """生成不确定性热力图数据.

        将离散坐标点的不确定性值映射到二维网格，生成前端热力图组件
        可直接消费的数据结构。

        Args:
            coordinates: 坐标点列表，每项为 [lon, lat] 或 [x, y].
            uncertainty_values: 各坐标点对应的不确定性值（标准差）.
            mean_values: 各坐标点对应的预测均值（可选，用于叠加显示）.
            grid_size: 网格分辨率，默认 50.

        Returns:
            热力图数据字典:
                - grid: 二维不确定性网格 (grid_size x grid_size)
                - mean_grid: 二维均值网格（如果提供了 mean_values）
                - x_range: x 坐标范围 [min, max]
                - y_range: y 坐标范围 [min, max]
                - grid_size: 网格尺寸
                - statistics: 不确定性统计信息
        """
        if not coordinates or not uncertainty_values:
            return self._empty_heatmap(grid_size or self.default_grid_size)

        coords = np.asarray(coordinates)
        values = np.asarray(uncertainty_values)
        gs = grid_size or self.default_grid_size

        x_min, x_max = coords[:, 0].min(), coords[:, 0].max()
        y_min, y_max = coords[:, 1].min(), coords[:, 1].max()

        x_range = x_max - x_min + 1e-10
        y_range = y_max - y_min + 1e-10

        grid = np.zeros((gs, gs))
        count = np.zeros((gs, gs))

        for i in range(len(coords)):
            xi = int((coords[i, 0] - x_min) / x_range * (gs - 1))
            yi = int((coords[i, 1] - y_min) / y_range * (gs - 1))
            xi = min(max(xi, 0), gs - 1)
            yi = min(max(yi, 0), gs - 1)
            grid[yi, xi] += values[i]
            count[yi, xi] += 1

        # 对有多个点的网格取平均
        mask = count > 0
        grid[mask] /= count[mask]

        result: dict[str, Any] = {
            "grid": grid.tolist(),
            "x_range": [float(x_min), float(x_max)],
            "y_range": [float(y_min), float(y_max)],
            "grid_size": gs,
            "statistics": {
                "min_uncertainty": float(values.min()),
                "max_uncertainty": float(values.max()),
                "mean_uncertainty": float(values.mean()),
                "high_uncertainty_ratio": float(
                    np.mean(values > np.percentile(values, 75))
                ),
            },
        }

        if mean_values is not None:
            means = np.asarray(mean_values)
            mean_grid = np.zeros((gs, gs))
            mean_count = np.zeros((gs, gs))
            for i in range(len(coords)):
                xi = int((coords[i, 0] - x_min) / x_range * (gs - 1))
                yi = int((coords[i, 1] - y_min) / y_range * (gs - 1))
                xi = min(max(xi, 0), gs - 1)
                yi = min(max(yi, 0), gs - 1)
                mean_grid[yi, xi] += means[i]
                mean_count[yi, xi] += 1
            mask_m = mean_count > 0
            mean_grid[mask_m] /= mean_count[mask_m]
            result["mean_grid"] = mean_grid.tolist()

        logger.info(
            "热力图数据生成完成: grid_size=%d, points=%d",
            gs,
            len(coordinates),
        )
        return result

    def generate_confidence_band_data(
        self,
        x_values: list[float],
        mean_values: list[float],
        std_values: list[float],
        confidence_level: float = 0.95,
    ) -> dict[str, Any]:
        """生成置信区间可视化数据.

        生成用于绘制置信带（confidence band）的数据结构，
        前端可直接用于 ECharts / D3 等图表库。

        Args:
            x_values: x 轴坐标值（如经度、时间等）.
            mean_values: 预测均值.
            std_values: 预测标准差.
            confidence_level: 置信水平，默认 0.95.

        Returns:
            置信带数据字典:
                - x: x 轴坐标
                - mean: 预测均值
                - lower: 置信区间下界
                - upper: 置信区间上界
                - confidence_level: 置信水平
                - band_series: 可直接用于 ECharts 的 series 数据
        """
        z_scores = {0.68: 1.0, 0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_scores.get(confidence_level, 1.96)

        x = np.asarray(x_values)
        mean = np.asarray(mean_values)
        std = np.asarray(std_values)

        lower = mean - z * std
        upper = mean + z * std

        # 生成 ECharts area series 格式
        band_series = {
            "mean_line": [
                [float(x[i]), float(mean[i])] for i in range(len(x))
            ],
            "lower_band": [
                [float(x[i]), float(lower[i])] for i in range(len(x))
            ],
            "upper_band": [
                [float(x[i]), float(upper[i])] for i in range(len(x))
            ],
        }

        return {
            "x": x.tolist(),
            "mean": mean.tolist(),
            "lower": lower.tolist(),
            "upper": upper.tolist(),
            "confidence_level": float(confidence_level),
            "z_score": float(z),
            "band_series": band_series,
            "statistics": {
                "mean_band_width": float(np.mean(upper - lower)),
                "max_band_width": float(np.max(upper - lower)),
                "mean_value_range": [float(mean.min()), float(mean.max())],
            },
        }

    def to_geojson(
        self,
        coordinates: list[list[float]],
        uncertainty_values: list[float],
        mean_values: Optional[list[float]] = None,
        properties: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """将不确定性预测结果转换为 GeoJSON FeatureCollection.

        每个预测点生成一个 GeoJSON Feature，包含不确定性信息作为属性，
        可在 Mapbox / Leaflet / Cesium 等地图库中直接渲染。

        Args:
            coordinates: 坐标点列表，每项为 [lon, lat].
            uncertainty_values: 各点的不确定性值.
            mean_values: 各点的预测均值（可选）.
            properties: 额外的全局属性（可选）.

        Returns:
            GeoJSON FeatureCollection 字典:
                - type: "FeatureCollection"
                - features: Feature 列表，每个 Feature 包含:
                    - geometry: Point 类型
                    - properties: uncertainty, mean, uncertainty_level 等
        """
        features = []
        max_unc = max(uncertainty_values) + 1e-10

        for i, coord in enumerate(coordinates):
            unc_val = uncertainty_values[i]
            # 不确定性等级划分
            if unc_val < max_unc * 0.25:
                level = "low"
            elif unc_val < max_unc * 0.5:
                level = "medium"
            elif unc_val < max_unc * 0.75:
                level = "high"
            else:
                level = "critical"

            feature_props: dict[str, Any] = {
                "uncertainty": float(unc_val),
                "uncertainty_level": level,
                "normalized_uncertainty": float(unc_val / max_unc),
                "index": i,
            }

            if mean_values is not None and i < len(mean_values):
                feature_props["mean"] = float(mean_values[i])

            if properties:
                feature_props.update(properties)

            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(coord[0]), float(coord[1])],
                    },
                    "properties": feature_props,
                }
            )

        geojson: dict[str, Any] = {
            "type": "FeatureCollection",
            "features": features,
        }

        if properties:
            geojson["properties"] = properties

        logger.info(
            "GeoJSON 生成完成: %d 个特征点",
            len(features),
        )
        return geojson

    def generate_uncertainty_contour_data(
        self,
        coordinates: list[list[float]],
        uncertainty_values: list[float],
        levels: Optional[list[float]] = None,
        grid_size: Optional[int] = None,
    ) -> dict[str, Any]:
        """生成不确定性等值线数据.

        将不确定性场离散化到网格后，提取指定等级的等值线坐标，
        用于前端绘制等值线图。

        Args:
            coordinates: 坐标点列表.
            uncertainty_values: 不确定性值.
            levels: 等值线等级列表，默认自动计算 5 级.
            grid_size: 插值网格尺寸.

        Returns:
            等值线数据字典:
                - contours: 等值线列表，每条包含 level 和 coordinates
                - grid_info: 网格信息
        """
        if not coordinates or not uncertainty_values:
            return {"contours": [], "grid_info": {}}

        coords = np.asarray(coordinates)
        values = np.asarray(uncertainty_values)
        gs = grid_size or self.default_grid_size

        # 插值到网格
        from scipy.interpolate import griddata

        x_min, x_max = coords[:, 0].min(), coords[:, 0].max()
        y_min, y_max = coords[:, 1].min(), coords[:, 1].max()

        xi = np.linspace(x_min, x_max, gs)
        yi = np.linspace(y_min, y_max, gs)
        xi_grid, yi_grid = np.meshgrid(xi, yi)

        grid_values = griddata(coords, values, (xi_grid, yi_grid), method="linear")
        # 填充 NaN
        if np.any(np.isnan(grid_values)):
            grid_values = griddata(
                coords, values, (xi_grid, yi_grid), method="nearest"
            )
            grid_values = np.nan_to_num(grid_values, nan=0.0)

        # 计算等值线等级
        if levels is None:
            levels = list(np.linspace(values.min(), values.max(), 6)[1:-1])

        contours = []
        for level in levels:
            # 简化的等值线提取（标记高于/低于阈值的区域边界点）
            mask = grid_values >= level
            boundary_points = []
            for r in range(gs - 1):
                for c in range(gs - 1):
                    # 检查四邻域是否存在阈值交叉
                    neighbors = [
                        mask[r, c],
                        mask[r, c + 1],
                        mask[r + 1, c],
                        mask[r + 1, c + 1],
                    ]
                    if any(neighbors) and not all(neighbors):
                        boundary_points.append(
                            [float(xi[c]), float(yi[r]), float(grid_values[r, c])]
                        )

            contours.append(
                {
                    "level": float(level),
                    "point_count": len(boundary_points),
                    "points": boundary_points[:500],  # 限制点数
                }
            )

        return {
            "contours": contours,
            "grid_info": {
                "x_range": [float(x_min), float(x_max)],
                "y_range": [float(y_min), float(y_max)],
                "grid_size": gs,
                "value_range": [float(values.min()), float(values.max())],
            },
        }

    @staticmethod
    def _empty_heatmap(grid_size: int) -> dict[str, Any]:
        """返回空的热力图数据结构."""
        return {
            "grid": [[0.0] * grid_size for _ in range(grid_size)],
            "x_range": [0.0, 1.0],
            "y_range": [0.0, 1.0],
            "grid_size": grid_size,
            "statistics": {
                "min_uncertainty": 0.0,
                "max_uncertainty": 0.0,
                "mean_uncertainty": 0.0,
                "high_uncertainty_ratio": 0.0,
            },
        }
