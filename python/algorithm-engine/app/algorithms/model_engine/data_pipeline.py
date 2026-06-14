"""数据管道模块 — 统一数据处理流水线.

支持5种处理模式：质量控制、垂直插值、水平重网格化、时间聚合和
格式转换。通过统一的管道接口实现数据预处理链路的标准化管理。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class DataPipeline:
    """统一数据管道模块.

    提供标准化的数据处理接口，支持5种处理模式:
    1. quality_control — 质量控制（异常值检测、缺失值处理、范围检查）
    2. vertical_interpolation — 垂直插值（气压/高度层间插值）
    3. horizontal_regrid — 水平重网格化（网格分辨率转换）
    4. temporal_aggregation — 时间聚合（时间序列降采样/统计）
    5. format_conversion — 格式转换（数据结构/编码转换）
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.stage_names = {
            1: "quality_control",
            2: "vertical_interpolation",
            3: "horizontal_regrid",
            4: "temporal_aggregation",
            5: "format_conversion",
        }

    def process(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行数据管道处理.

        Args:
            params: 处理参数字典，包含:
                - input_data: 输入数据 (numpy数组或字典)
                - pipeline_stage: 管道阶段 (1-5)
                  1=质量控制, 2=垂直插值, 3=水平重网格化,
                  4=时间聚合, 5=格式转换
                - config: 阶段特定配置 (可选)

        Returns:
            包含处理结果的字典:
                - output_data: 处理后数据
                - quality_report: 质量报告
                - processing_stats: 处理统计
        """
        np.random.seed(42)

        input_data = params.get("input_data", None)
        pipeline_stage = params.get("pipeline_stage", 1)
        config = params.get("config", {})

        stage_name = self.stage_names.get(pipeline_stage, "unknown")
        logger.info(
            "开始数据处理: 阶段=%d (%s)",
            pipeline_stage,
            stage_name,
        )

        if pipeline_stage == 1:
            output_data, quality_report = self._quality_control(
                input_data,
                config,
            )
        elif pipeline_stage == 2:
            output_data, quality_report = self._vertical_interpolation(
                input_data,
                config,
            )
        elif pipeline_stage == 3:
            output_data, quality_report = self._horizontal_regrid(
                input_data,
                config,
            )
        elif pipeline_stage == 4:
            output_data, quality_report = self._temporal_aggregation(
                input_data,
                config,
            )
        elif pipeline_stage == 5:
            output_data, quality_report = self._format_conversion(
                input_data,
                config,
            )
        else:
            logger.warning("未知管道阶段 %d，返回原始数据", pipeline_stage)
            output_data = input_data
            quality_report = {"status": "unknown_stage", "warnings": []}

        processing_stats = self._compute_processing_stats(
            input_data,
            output_data,
            pipeline_stage,
        )

        logger.info(
            "数据处理完成: 阶段=%s, 输出形状=%s",
            stage_name,
            str(np.asarray(output_data).shape) if output_data is not None else "N/A",
        )

        return {
            "output_data": output_data,
            "quality_report": quality_report,
            "processing_stats": processing_stats,
        }

    def _quality_control(
        self,
        input_data: Any,
        config: dict[str, Any],
    ) -> tuple[Any, dict[str, Any]]:
        """阶段1: 质量控制.

        执行异常值检测、缺失值处理和范围检查。
        """
        data = np.asarray(input_data, dtype=float) if input_data is not None else np.zeros((10, 10))
        total_elements = data.size

        valid_range = config.get("valid_range", (-1e6, 1e6))
        missing_value = config.get("missing_value", -9999.0)
        outlier_std_threshold = config.get("outlier_std_threshold", 3.0)

        warnings: list[str] = []

        data_clean = data.copy()

        missing_mask = np.isclose(data_clean, missing_value, atol=1e-6)
        nan_mask = np.isnan(data_clean)
        inf_mask = np.isinf(data_clean)

        total_missing = int(np.sum(missing_mask))
        total_nan = int(np.sum(nan_mask))
        total_inf = int(np.sum(inf_mask))

        if total_missing > 0:
            warnings.append(f"检测到缺失值标记: {total_missing}个")
        if total_nan > 0:
            warnings.append(f"检测到NaN值: {total_nan}个")
        if total_inf > 0:
            warnings.append(f"检测到Inf值: {total_inf}个")

        invalid_mask = missing_mask | nan_mask | inf_mask
        data_clean[invalid_mask] = np.nan

        range_mask = (data_clean < valid_range[0]) | (data_clean > valid_range[1])
        out_of_range = int(np.sum(range_mask & ~np.isnan(data_clean)))
        if out_of_range > 0:
            warnings.append(f"超出有效范围的值: {out_of_range}个")
            data_clean[range_mask] = np.nan

        finite_vals = data_clean[np.isfinite(data_clean)]
        if len(finite_vals) > 0:
            mean_val = float(np.mean(finite_vals))
            std_val = float(np.std(finite_vals))
            outlier_mask = np.abs(data_clean - mean_val) > outlier_std_threshold * std_val
            outlier_mask = outlier_mask & np.isfinite(data_clean)
            n_outliers = int(np.sum(outlier_mask))
            if n_outliers > 0:
                warnings.append(f"统计异常值 (>{outlier_std_threshold}sigma): {n_outliers}个")
                data_clean[outlier_mask] = np.nan

        fill_method = config.get("fill_method", "linear")
        if np.any(np.isnan(data_clean)):
            data_clean = self._fill_missing(data_clean, fill_method)

        quality_report = {
            "stage": "quality_control",
            "status": "passed" if not warnings else "passed_with_warnings",
            "total_elements": total_elements,
            "missing_count": total_missing,
            "nan_count": total_nan,
            "inf_count": total_inf,
            "out_of_range_count": out_of_range,
            "valid_range": list(valid_range),
            "warnings": warnings,
            "fill_method": fill_method,
        }

        return data_clean.tolist(), quality_report

    def _vertical_interpolation(
        self,
        input_data: Any,
        config: dict[str, Any],
    ) -> tuple[Any, dict[str, Any]]:
        """阶段2: 垂直插值.

        在不同气压/高度层之间进行插值，支持线性和对数插值。
        """
        data = (
            np.asarray(input_data, dtype=float)
            if input_data is not None
            else np.zeros((10, 50, 50))
        )

        if data.ndim < 3:
            data = np.expand_dims(data, axis=0)

        n_levels, grid_h, grid_w = data.shape
        warnings: list[str] = []

        source_levels = config.get("source_levels", None)
        target_levels = config.get("target_levels", None)
        method = config.get("interpolation_method", "linear")

        if source_levels is None:
            source_levels = np.linspace(1000, 100, n_levels)
        else:
            source_levels = np.asarray(source_levels, dtype=float)

        if target_levels is None:
            target_levels = np.linspace(
                float(source_levels.min()),
                float(source_levels.max()),
                n_levels,
            )
        else:
            target_levels = np.asarray(target_levels, dtype=float)

        output = np.zeros((len(target_levels), grid_h, grid_w))
        for i in range(grid_h):
            for j in range(grid_w):
                column = data[:, i, j]
                if method == "log":
                    log_src = np.log(np.maximum(np.abs(source_levels), 1e-10))
                    log_tgt = np.log(np.maximum(np.abs(target_levels), 1e-10))
                    output[:, i, j] = np.interp(log_tgt, log_src, column)
                else:
                    output[:, i, j] = np.interp(target_levels, source_levels, column)

        nan_count = int(np.sum(np.isnan(output)))
        if nan_count > 0:
            warnings.append(f"插值产生NaN值: {nan_count}个")

        quality_report = {
            "stage": "vertical_interpolation",
            "status": "passed" if not warnings else "passed_with_warnings",
            "source_levels": source_levels.tolist(),
            "target_levels": target_levels.tolist(),
            "method": method,
            "input_levels": n_levels,
            "output_levels": len(target_levels),
            "warnings": warnings,
        }

        return output.tolist(), quality_report

    def _horizontal_regrid(
        self,
        input_data: Any,
        config: dict[str, Any],
    ) -> tuple[Any, dict[str, Any]]:
        """阶段3: 水平重网格化.

        将数据从源网格分辨率转换到目标网格分辨率。
        """
        data = np.asarray(input_data, dtype=float) if input_data is not None else np.zeros((50, 50))

        if data.ndim < 2:
            data = np.expand_dims(data, axis=0)
            data = np.expand_dims(data, axis=0)

        warnings: list[str] = []

        target_resolution = config.get("target_resolution", None)
        method = config.get("regrid_method", "bilinear")

        src_h, src_w = data.shape[-2], data.shape[-1]

        if target_resolution is not None:
            scale_h = target_resolution / src_h
            scale_w = target_resolution / src_w
        else:
            scale = config.get("scale_factor", 2.0)
            scale_h = scale
            scale_w = scale

        if data.ndim == 2:
            output = self._resize_2d(data, int(src_h * scale_h), int(src_w * scale_w), method)
        else:
            n_channels = data.shape[0]
            output_list = []
            for c in range(n_channels):
                resized = self._resize_2d(
                    data[c],
                    int(src_h * scale_h),
                    int(src_w * scale_w),
                    method,
                )
                output_list.append(resized)
            output = np.stack(output_list, axis=0)

        quality_report = {
            "stage": "horizontal_regrid",
            "status": "passed" if not warnings else "passed_with_warnings",
            "input_shape": list(data.shape),
            "output_shape": list(output.shape),
            "method": method,
            "scale_h": float(scale_h),
            "scale_w": float(scale_w),
            "warnings": warnings,
        }

        return output.tolist(), quality_report

    def _temporal_aggregation(
        self,
        input_data: Any,
        config: dict[str, Any],
    ) -> tuple[Any, dict[str, Any]]:
        """阶段4: 时间聚合.

        对时间序列数据进行降采样和统计聚合。
        """
        data = (
            np.asarray(input_data, dtype=float)
            if input_data is not None
            else np.zeros((24, 50, 50))
        )

        if data.ndim < 3:
            data = np.expand_dims(data, axis=0)

        warnings: list[str] = []

        aggregation_method = config.get("aggregation_method", "mean")
        window_size = config.get("window_size", 3)
        stride = config.get("stride", window_size)

        n_time = data.shape[0]
        if n_time < window_size:
            warnings.append(
                f"时间步数({n_time})小于窗口大小({window_size})，使用全部数据",
            )
            window_size = n_time

        n_windows = max(1, (n_time - window_size) // stride + 1)
        spatial_shape = data.shape[1:]

        output = np.zeros((n_windows,) + spatial_shape)
        for i in range(n_windows):
            start = i * stride
            end = start + window_size
            window = data[start:end]

            if aggregation_method == "mean":
                output[i] = np.mean(window, axis=0)
            elif aggregation_method == "sum":
                output[i] = np.sum(window, axis=0)
            elif aggregation_method == "max":
                output[i] = np.max(window, axis=0)
            elif aggregation_method == "min":
                output[i] = np.min(window, axis=0)
            elif aggregation_method == "std":
                output[i] = np.std(window, axis=0)
            elif aggregation_method == "median":
                output[i] = np.median(window, axis=0)
            else:
                output[i] = np.mean(window, axis=0)

        quality_report = {
            "stage": "temporal_aggregation",
            "status": "passed" if not warnings else "passed_with_warnings",
            "input_time_steps": n_time,
            "output_time_steps": n_windows,
            "window_size": window_size,
            "stride": stride,
            "method": aggregation_method,
            "warnings": warnings,
        }

        return output.tolist(), quality_report

    def _format_conversion(
        self,
        input_data: Any,
        config: dict[str, Any],
    ) -> tuple[Any, dict[str, Any]]:
        """阶段5: 格式转换.

        执行数据结构转换、归一化、编码转换等操作。
        """
        data = np.asarray(input_data, dtype=float) if input_data is not None else np.zeros((10, 10))
        warnings: list[str] = []

        conversion_type = config.get("conversion_type", "normalize")
        target_dtype = config.get("target_dtype", "float32")

        if conversion_type == "normalize":
            min_val = config.get("min_val", float(np.min(data)))
            max_val = config.get("max_val", float(np.max(data)))
            range_val = max_val - min_val
            if abs(range_val) < 1e-10:
                warnings.append("数据范围接近零，归一化可能不准确")
                output = np.zeros_like(data)
            else:
                output = (data - min_val) / range_val

            quality_report = {
                "stage": "format_conversion",
                "status": "passed" if not warnings else "passed_with_warnings",
                "conversion_type": conversion_type,
                "min_val": float(min_val),
                "max_val": float(max_val),
                "warnings": warnings,
            }

        elif conversion_type == "standardize":
            mean_val = float(np.mean(data))
            std_val = float(np.std(data))
            if abs(std_val) < 1e-10:
                warnings.append("标准差接近零，标准化可能不准确")
                output = np.zeros_like(data)
            else:
                output = (data - mean_val) / std_val

            quality_report = {
                "stage": "format_conversion",
                "status": "passed" if not warnings else "passed_with_warnings",
                "conversion_type": conversion_type,
                "mean": mean_val,
                "std": std_val,
                "warnings": warnings,
            }

        elif conversion_type == "transpose":
            output = data.T
            quality_report = {
                "stage": "format_conversion",
                "status": "passed",
                "conversion_type": conversion_type,
                "input_shape": list(data.shape),
                "output_shape": list(output.shape),
                "warnings": warnings,
            }

        else:
            output = data
            quality_report = {
                "stage": "format_conversion",
                "status": "passed",
                "conversion_type": conversion_type,
                "warnings": warnings,
            }

        if target_dtype == "float32":
            output = output.astype(np.float32)
        elif target_dtype == "float64":
            output = output.astype(np.float64)
        elif target_dtype == "int32":
            output = output.astype(np.int32)

        return output.tolist(), quality_report

    def _fill_missing(
        self,
        data: np.ndarray,
        method: str,
    ) -> np.ndarray:
        """填充缺失值."""
        if method == "zero":
            return np.nan_to_num(data, nan=0.0)

        if method == "mean":
            mean_val = np.nanmean(data)
            return np.nan_to_num(data, nan=float(mean_val))

        if method == "nearest":
            return self._nearest_fill(data)

        return self._linear_fill(data)

    def _linear_fill(self, data: np.ndarray) -> np.ndarray:
        """线性插值填充缺失值."""
        result = data.copy()
        if result.ndim == 1:
            nans = np.isnan(result)
            if np.any(nans):
                valid = np.where(~nans)[0]
                if len(valid) > 0:
                    result[nans] = np.interp(
                        np.where(nans)[0],
                        valid,
                        result[valid],
                    )
        else:
            flat = result.flatten()
            nans = np.isnan(flat)
            if np.any(nans):
                valid = np.where(~nans)[0]
                if len(valid) > 0:
                    flat[nans] = np.interp(
                        np.where(nans)[0],
                        valid,
                        flat[valid],
                    )
                result = flat.reshape(result.shape)
        return result

    def _nearest_fill(self, data: np.ndarray) -> np.ndarray:
        """最近邻填充缺失值."""
        result = data.copy()
        nans = np.isnan(result)
        if not np.any(nans):
            return result

        flat = result.flatten()
        nan_indices = np.where(np.isnan(flat))[0]
        valid_indices = np.where(~np.isnan(flat))[0]

        if len(valid_indices) == 0:
            return np.zeros_like(result)

        for idx in nan_indices:
            distances = np.abs(valid_indices - idx)
            nearest = valid_indices[np.argmin(distances)]
            flat[idx] = flat[nearest]

        return flat.reshape(result.shape)

    def _resize_2d(
        self,
        data: np.ndarray,
        target_h: int,
        target_w: int,
        method: str,
    ) -> np.ndarray:
        """2D数组缩放."""
        src_h, src_w = data.shape

        if method == "nearest":
            row_indices = np.clip(
                (np.arange(target_h) * src_h / target_h).astype(int),
                0,
                src_h - 1,
            )
            col_indices = np.clip(
                (np.arange(target_w) * src_w / target_w).astype(int),
                0,
                src_w - 1,
            )
            return data[np.ix_(row_indices, col_indices)]

        y_src = np.linspace(0, src_h - 1, target_h)
        x_src = np.linspace(0, src_w - 1, target_w)

        y0 = np.clip(np.floor(y_src).astype(int), 0, src_h - 2)
        y1 = y0 + 1
        x0 = np.clip(np.floor(x_src).astype(int), 0, src_w - 2)
        x1 = x0 + 1

        wy = (y_src - y0).reshape(-1, 1)
        wx = (x_src - x0).reshape(1, -1)

        output = (
            data[np.ix_(y0, x0)] * (1 - wy) * (1 - wx)
            + data[np.ix_(y1, x0)] * wy * (1 - wx)
            + data[np.ix_(y0, x1)] * (1 - wy) * wx
            + data[np.ix_(y1, x1)] * wy * wx
        )
        return output

    def _compute_processing_stats(
        self,
        input_data: Any,
        output_data: Any,
        pipeline_stage: int,
    ) -> dict[str, Any]:
        """计算处理统计信息."""
        stats: dict[str, Any] = {
            "pipeline_stage": pipeline_stage,
            "stage_name": self.stage_names.get(pipeline_stage, "unknown"),
        }

        if input_data is not None:
            input_arr = np.asarray(input_data)
            stats["input_shape"] = list(input_arr.shape)
            stats["input_dtype"] = str(input_arr.dtype)
            stats["input_min"] = float(np.min(input_arr))
            stats["input_max"] = float(np.max(input_arr))
            stats["input_mean"] = float(np.mean(input_arr))

        if output_data is not None:
            output_arr = np.asarray(output_data)
            stats["output_shape"] = list(output_arr.shape)
            stats["output_dtype"] = str(output_arr.dtype)
            stats["output_min"] = float(np.min(output_arr))
            stats["output_max"] = float(np.max(output_arr))
            stats["output_mean"] = float(np.mean(output_arr))

        return stats
