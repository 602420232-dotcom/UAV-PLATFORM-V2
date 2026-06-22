"""ERA5 再分析数据下载与预处理流水线.

支持从 Copernicus Climate Data Store (CDS) 下载 ERA5 数据，
进行区域裁剪、格式转换、数据验证，并生成 FengWu 模型所需的
输入数据格式 (69 x 721 x 1440)。

依赖::

    pip install cdsapi netCDF4 xarray numpy loguru

使用示例::

    from app.utils.era5_pipeline import ERA5Pipeline

    pipeline = ERA5Pipeline(output_dir="./era5_data")
    pipeline.download(
        variables=["u10", "v10", "t2m", "msl", "sp"],
        start_date="2024-01-01",
        end_date="2024-01-02",
    )
    pipeline.process()
    pipeline.validate()
    pipeline.to_fengwu_format()
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import xarray as xr
from loguru import logger

# ─── 常量定义 ────────────────────────────────────────────────────────────────────

# 四川盆地默认区域范围
DEFAULT_AREA: Dict[str, float] = {
    "north": 35.0,
    "south": 27.0,
    "east": 110.0,
    "west": 102.0,
}

# FengWu 模型输入网格尺寸
FENGWU_HEIGHT_LEVELS: int = 69
FENGWU_LAT_POINTS: int = 721
FENGWU_LON_POINTS: int = 1440

# ERA5 支持的变量及其长名称映射
ERA5_VARIABLES: Dict[str, str] = {
    "u10": "10m_u_component_of_wind",
    "v10": "10m_v_component_of_wind",
    "t2m": "2m_temperature",
    "msl": "mean_sea_level_pressure",
    "sp": "surface_pressure",
    "z500": "geopotential_at_500_hPa",
    "z850": "geopotential_at_850_hPa",
    "z700": "geopotential_at_700_hPa",
    "t500": "temperature_at_500_hPa",
    "t850": "temperature_at_850_hPa",
    "q500": "specific_humidity_at_500_hPa",
    "q850": "specific_humidity_at_850_hPa",
}

# 压力层变量映射（需要指定 pressure_level）
PRESSURE_LEVEL_VARS: List[str] = ["z500", "z850", "z700", "t500", "t850", "q500", "q850"]

# 压力层名称映射
PRESSURE_LEVEL_MAP: Dict[str, Tuple[str, int]] = {
    "z500": ("geopotential", 500),
    "z850": ("geopotential", 850),
    "z700": ("geopotential", 700),
    "t500": ("temperature", 500),
    "t850": ("temperature", 850),
    "q500": ("specific_humidity", 500),
    "q850": ("specific_humidity", 850),
}


class ERA5Pipeline:
    """ERA5 数据下载与预处理流水线.

    Attributes:
        output_dir: 数据输出根目录.
        area: 裁剪区域 (north, south, east, west).
        raw_dir: 原始下载文件存放目录.
        processed_dir: 处理后文件存放目录.
        fengwu_dir: FengWu 格式输出目录.
    """

    def __init__(
        self,
        output_dir: str = "./era5_data",
        area: Optional[Dict[str, float]] = None,
    ) -> None:
        """初始化 ERA5 流水线.

        Args:
            output_dir: 输出根目录.
            area: 区域范围，默认四川盆地.
        """
        self.output_dir = Path(output_dir)
        self.area = area or DEFAULT_AREA
        self.raw_dir = self.output_dir / "raw"
        self.processed_dir = self.output_dir / "processed"
        self.fengwu_dir = self.output_dir / "fengwu"

        # 创建目录结构
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.fengwu_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "ERA5Pipeline 初始化 | output_dir={} | area={}",
            self.output_dir.resolve(),
            self.area,
        )

    # ─── 数据下载 ───────────────────────────────────────────────────────────────

    def download(
        self,
        variables: List[str],
        start_date: str,
        end_date: str,
        pressure_levels: Optional[List[int]] = None,
    ) -> List[Path]:
        """从 CDS 下载 ERA5 数据.

        Args:
            variables: 要下载的变量列表，如 ["u10", "v10", "t2m"].
            start_date: 起始日期，格式 "YYYY-MM-DD".
            end_date: 结束日期，格式 "YYYY-MM-DD".
            pressure_levels: 压力层列表，默认 [500, 700, 850].

        Returns:
            下载的文件路径列表.

        Raises:
            ImportError: cdsapi 未安装.
            ValueError: 日期格式不合法或变量不存在.
        """
        try:
            import cdsapi
        except ImportError:
            raise ImportError(
                "请先安装 cdsapi: pip install cdsapi\n"
                "并配置 ~/.cdsapirc 文件 (参考 https://cds.climate.copernicus.eu/api-how-to)"
            )

        self._validate_dates(start_date, end_date)
        self._validate_variables(variables)

        if pressure_levels is None:
            pressure_levels = [500, 700, 850]

        downloaded_files: List[Path] = []

        # 分离单层变量和压力层变量
        single_level_vars: List[str] = [v for v in variables if v not in PRESSURE_LEVEL_VARS]
        pressure_vars: List[str] = [v for v in variables if v in PRESSURE_LEVEL_VARS]

        # 下载单层数据
        if single_level_vars:
            sl_files = self._download_single_level(
                cdsapi.Client(), single_level_vars, start_date, end_date
            )
            downloaded_files.extend(sl_files)

        # 下载压力层数据
        if pressure_vars:
            pl_files = self._download_pressure_level(
                cdsapi.Client(), pressure_vars, start_date, end_date, pressure_levels
            )
            downloaded_files.extend(pl_files)

        logger.info("下载完成，共 {} 个文件", len(downloaded_files))
        return downloaded_files

    def _download_single_level(
        self,
        client: Any,
        variables: List[str],
        start_date: str,
        end_date: str,
    ) -> List[Path]:
        """下载单层 ERA5 变量."""
        era5_names = [ERA5_VARIABLES[v] for v in variables]
        dates = self._format_date_range(start_date, end_date)

        filename = f"era5_single_{'_'.join(variables)}_{start_date}_{end_date}.nc"
        filepath = self.raw_dir / filename

        logger.info(
            "下载单层变量: {} | 日期: {} -> {} | 文件: {}",
            era5_names,
            start_date,
            end_date,
            filename,
        )

        client.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "variable": era5_names,
                "year": dates["years"],
                "month": dates["months"],
                "day": dates["days"],
                "time": "00:00",
                "area": [
                    self.area["north"],
                    self.area["west"],
                    self.area["south"],
                    self.area["east"],
                ],
                "format": "netcdf",
            },
            str(filepath),
        )

        logger.info("单层变量下载完成: {}", filepath)
        return [filepath]

    def _download_pressure_level(
        self,
        client: Any,
        variables: List[str],
        start_date: str,
        end_date: str,
        pressure_levels: List[int],
    ) -> List[Path]:
        """下载压力层 ERA5 变量."""
        # 按实际 ERA5 变量名和压力层分组
        groups: Dict[str, List[int]] = {}
        for v in variables:
            era5_name, level = PRESSURE_LEVEL_MAP[v]
            if era5_name not in groups:
                groups[era5_name] = []
            if level not in groups[era5_name]:
                groups[era5_name].append(level)

        dates = self._format_date_range(start_date, end_date)
        downloaded: List[Path] = []

        for era5_var, levels in groups.items():
            filename = f"era5_pl_{era5_var}_{'_'.join(str(l) for l in levels)}_{start_date}_{end_date}.nc"
            filepath = self.raw_dir / filename

            logger.info(
                "下载压力层变量: {} @ {}hPa | 日期: {} -> {}",
                era5_var,
                levels,
                start_date,
                end_date,
            )

            client.retrieve(
                "reanalysis-era5-pressure-levels",
                {
                    "product_type": "reanalysis",
                    "variable": era5_var,
                    "pressure_level": levels,
                    "year": dates["years"],
                    "month": dates["months"],
                    "day": dates["days"],
                    "time": "00:00",
                    "area": [
                        self.area["north"],
                        self.area["west"],
                        self.area["south"],
                        self.area["east"],
                    ],
                    "format": "netcdf",
                },
                str(filepath),
            )

            logger.info("压力层变量下载完成: {}", filepath)
            downloaded.append(filepath)

        return downloaded

    # ─── GRIB 转 NetCDF ──────────────────────────────────────────────────────────

    def convert_grib_to_netcdf(self, grib_path: str) -> Path:
        """将 GRIB 文件转换为 NetCDF 格式.

        Args:
            grib_path: GRIB 文件路径.

        Returns:
            转换后的 NetCDF 文件路径.

        Raises:
            FileNotFoundError: GRIB 文件不存在.
            RuntimeError: 转换失败.
        """
        grib = Path(grib_path)
        if not grib.exists():
            raise FileNotFoundError(f"GRIB 文件不存在: {grib_path}")

        output_path = self.raw_dir / grib.with_suffix(".nc").name

        try:
            logger.info("GRIB -> NetCDF 转换: {} -> {}", grib_path, output_path)

            # 使用 xarray + cfgrib 进行转换
            ds = xr.open_dataset(str(grib), engine="cfgrib")
            ds.to_netcdf(str(output_path))
            ds.close()

            logger.info("转换完成: {}", output_path)
            return output_path

        except Exception as exc:
            raise RuntimeError(f"GRIB 转 NetCDF 失败: {exc}") from exc

    # ─── 数据处理 ───────────────────────────────────────────────────────────────

    def process(
        self,
        interpolation_method: str = "linear",
        target_resolution: Optional[float] = None,
    ) -> List[Path]:
        """对原始数据进行预处理.

        包括：合并变量、区域裁剪、插值到统一网格。

        Args:
            interpolation_method: 插值方法 (linear, nearest, cubic).
            target_resolution: 目标空间分辨率（度），None 表示保持原始分辨率.

        Returns:
            处理后的文件路径列表.
        """
        raw_files = list(self.raw_dir.glob("*.nc"))
        if not raw_files:
            logger.warning("未找到原始数据文件，跳过处理")
            return []

        logger.info("开始处理 {} 个原始文件", len(raw_files))

        processed_files: List[Path] = []

        for raw_file in raw_files:
            try:
                ds = xr.open_dataset(str(raw_file))

                # 区域裁剪（如果数据范围大于目标区域）
                ds = self._crop_to_area(ds)

                # 空间插值（如果指定了目标分辨率）
                if target_resolution is not None:
                    ds = self._interpolate_grid(ds, target_resolution, interpolation_method)

                # 填充缺失值
                ds = self._fill_missing_values(ds)

                output_path = self.processed_dir / raw_file.name
                ds.to_netcdf(str(output_path))
                ds.close()

                processed_files.append(output_path)
                logger.info("处理完成: {}", output_path)

            except Exception as exc:
                logger.error("处理文件 {} 失败: {}", raw_file, exc)
                continue

        logger.info("处理完成，共 {} 个文件", len(processed_files))
        return processed_files

    def _crop_to_area(self, ds: xr.Dataset) -> xr.Dataset:
        """裁剪数据到目标区域."""
        lats = ds.coords.get("latitude", ds.coords.get("lat"))
        lons = ds.coords.get("longitude", ds.coords.get("lon"))

        if lats is None or lons is None:
            logger.warning("数据中未找到经纬度坐标，跳过区域裁剪")
            return ds

        lat_name = "latitude" if "latitude" in ds.coords else "lat"
        lon_name = "longitude" if "longitude" in ds.coords else "lon"

        return ds.sel(
            {
                lat_name: slice(self.area["south"], self.area["north"]),
                lon_name: slice(self.area["west"], self.area["east"]),
            }
        )

    def _interpolate_grid(
        self,
        ds: xr.Dataset,
        resolution: float,
        method: str = "linear",
    ) -> xr.Dataset:
        """将数据插值到统一网格."""
        lat_name = "latitude" if "latitude" in ds.coords else "lat"
        lon_name = "longitude" if "longitude" in ds.coords else "lon"

        lat_min = float(ds.coords[lat_name].min())
        lat_max = float(ds.coords[lat_name].max())
        lon_min = float(ds.coords[lon_name].min())
        lon_max = float(ds.coords[lon_name].max())

        new_lat = np.arange(lat_min, lat_max + resolution, resolution)
        new_lon = np.arange(lon_min, lon_max + resolution, resolution)

        return ds.interp(
            {lat_name: new_lat, lon_name: new_lon},
            method=method,
        )

    def _fill_missing_values(self, ds: xr.Dataset) -> xr.Dataset:
        """用邻近值填充缺失数据."""
        return ds.interpolate_na(dim="time", method="nearest").fillna(0)

    # ─── 数据验证 ───────────────────────────────────────────────────────────────

    def validate(self, tolerance_missing: float = 0.01) -> Dict[str, Any]:
        """验证处理后的数据质量.

        检查项:
        - 缺失值比例
        - 数值范围合理性
        - 时间连续性

        Args:
            tolerance_missing: 允许的缺失值比例阈值.

        Returns:
            验证结果字典，包含各项检查的状态和详情.
        """
        processed_files = list(self.processed_dir.glob("*.nc"))
        if not processed_files:
            logger.warning("未找到处理后文件，跳过验证")
            return {"status": "skipped", "reason": "无处理后文件"}

        results: Dict[str, Any] = {
            "status": "pass",
            "files_checked": len(processed_files),
            "checks": {},
        }

        for fpath in processed_files:
            file_results: Dict[str, Any] = {}
            try:
                ds = xr.open_dataset(str(fpath))

                # 缺失值检查
                missing_ratio = self._check_missing_values(ds)
                file_results["missing_ratio"] = missing_ratio
                file_results["missing_check"] = (
                    "pass" if missing_ratio < tolerance_missing else "fail"
                )

                # 数值范围检查
                range_check = self._check_value_ranges(ds)
                file_results["range_check"] = range_check

                # 时间连续性检查
                time_check = self._check_time_continuity(ds)
                file_results["time_check"] = time_check

                ds.close()

                # 汇总文件检查结果
                if file_results["missing_check"] == "fail":
                    results["status"] = "fail"

            except Exception as exc:
                file_results["error"] = str(exc)
                results["status"] = "fail"
                logger.error("验证文件 {} 失败: {}", fpath, exc)

            results["checks"][fpath.name] = file_results

        logger.info("数据验证完成 | 状态: {}", results["status"])
        return results

    def _check_missing_values(self, ds: xr.Dataset) -> float:
        """检查数据集中的缺失值比例."""
        total = 0
        missing = 0
        for var in ds.data_vars:
            arr = ds[var].values
            total += arr.size
            missing += int(np.isnan(arr).sum()) if np.issubdtype(arr.dtype, np.floating) else 0

        ratio = missing / total if total > 0 else 0.0
        logger.debug("缺失值比例: {:.4f}%", ratio * 100)
        return ratio

    def _check_value_ranges(self, ds: xr.Dataset) -> Dict[str, Any]:
        """检查各变量的数值范围是否在合理区间."""
        ranges: Dict[str, Dict[str, Any]] = {}

        # 预定义的合理范围
        reasonable_ranges: Dict[str, Tuple[float, float]] = {
            "u10": (-100, 100),
            "v10": (-100, 100),
            "t2m": (200, 330),
            "msl": (90000, 110000),
            "sp": (50000, 110000),
        }

        for var in ds.data_vars:
            arr = ds[var].values
            if np.issubdtype(arr.dtype, np.floating):
                var_min = float(np.nanmin(arr))
                var_max = float(np.nanmax(arr))
                ranges[var] = {"min": var_min, "max": var_max}

                if var in reasonable_ranges:
                    lo, hi = reasonable_ranges[var]
                    in_range = lo <= var_min and var_max <= hi
                    ranges[var]["expected"] = [lo, hi]
                    ranges[var]["in_range"] = in_range

        return ranges

    def _check_time_continuity(self, ds: xr.Dataset) -> Dict[str, Any]:
        """检查时间维度的连续性."""
        if "time" not in ds.coords:
            return {"status": "skip", "reason": "无时间维度"}

        times = ds.coords["time"].values
        if len(times) < 2:
            return {"status": "skip", "reason": "时间步不足"}

        diffs = np.diff(times.astype("datetime64[h]").astype(np.int64))
        unique_diffs = np.unique(diffs)

        return {
            "status": "pass" if len(unique_diffs) == 1 else "warning",
            "time_steps": len(times),
            "unique_intervals_hours": unique_diffs.tolist(),
        }

    # ─── FengWu 格式转换 ─────────────────────────────────────────────────────────

    def to_fengwu_format(
        self,
        input_files: Optional[List[str]] = None,
        output_name: str = "fengwu_input.nc",
    ) -> Path:
        """生成 FengWu 模型所需的输入数据格式.

        将处理后的数据插值/扩展到 FengWu 模型的标准网格:
        - 69 个高度层
        - 721 个纬度点 (90N ~ 90S, 0.25 度)
        - 1440 个经度点 (0 ~ 359.75E, 0.25 度)

        Args:
            input_files: 输入文件列表，None 则使用 processed_dir 下所有文件.
            output_name: 输出文件名.

        Returns:
            FengWu 格式文件路径.

        Raises:
            FileNotFoundError: 无可用的输入文件.
        """
        if input_files is None:
            files = list(self.processed_dir.glob("*.nc"))
        else:
            files = [Path(f) for f in input_files]

        if not files:
            raise FileNotFoundError("无可用的处理后数据文件")

        logger.info("开始生成 FengWu 格式数据，共 {} 个输入文件", len(files))

        # 合并所有数据集
        datasets = [xr.open_dataset(str(f)) for f in files]
        merged = xr.merge(datasets, compat="no_conflicts")

        # 创建 FengWu 标准网格
        fengwu_lat = np.linspace(90, -90, FENGWU_LAT_POINTS)
        fengwu_lon = np.linspace(0, 360 - 0.25, FENGWU_LON_POINTS)
        fengwu_levels = np.arange(1, FENGWU_HEIGHT_LEVELS + 1)

        # 插值到 FengWu 网格
        lat_name = "latitude" if "latitude" in merged.coords else "lat"
        lon_name = "longitude" if "longitude" in merged.coords else "lon"

        merged = merged.interp(
            {lat_name: fengwu_lat, lon_name: fengwu_lon},
            method="linear",
        )

        # 重命名坐标为 FengWu 期望的名称
        merged = merged.rename({lat_name: "lat", lon_name: "lon"})

        # 如果没有高度层维度，创建虚拟维度
        if "level" not in merged.dims:
            for var in merged.data_vars:
                merged[var] = merged[var].expand_dims(level=fengwu_levels)

        output_path = self.fengwu_dir / output_name
        merged.to_netcdf(str(output_path))

        # 关闭所有数据集
        for ds in datasets:
            ds.close()
        merged.close()

        logger.info(
            "FengWu 格式数据生成完成: {} | shape 预期: ({}, {}, {})",
            output_path,
            FENGWU_HEIGHT_LEVELS,
            FENGWU_LAT_POINTS,
            FENGWU_LON_POINTS,
        )

        return output_path

    # ─── 辅助方法 ───────────────────────────────────────────────────────────────

    @staticmethod
    def _validate_dates(start_date: str, end_date: str) -> None:
        """验证日期格式和范围."""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"日期格式不正确，请使用 YYYY-MM-DD: {exc}") from exc

        if start > end:
            raise ValueError(f"起始日期 ({start_date}) 不能晚于结束日期 ({end_date})")

        if start.year < 1940 or end.year > datetime.now().year + 1:
            raise ValueError("ERA5 数据范围为 1940 年至今")

    @staticmethod
    def _validate_variables(variables: List[str]) -> None:
        """验证变量名称是否在支持列表中."""
        unsupported = [v for v in variables if v not in ERA5_VARIABLES]
        if unsupported:
            raise ValueError(
                f"不支持的变量: {unsupported}\n"
                f"支持的变量: {list(ERA5_VARIABLES.keys())}"
            )

    @staticmethod
    def _format_date_range(start_date: str, end_date: str) -> Dict[str, List[str]]:
        """将日期范围格式化为 CDS API 所需的年/月/日列表."""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        years: List[str] = []
        months: List[str] = []
        days: List[str] = []

        current = start
        while current <= end:
            year_str = str(current.year)
            month_str = f"{current.month:02d}"
            day_str = f"{current.day:02d}"

            if year_str not in years:
                years.append(year_str)
            key = f"{year_str}-{month_str}"
            if key not in months:
                months.append(key)
            if day_str not in days:
                days.append(day_str)

            current += timedelta(days=1)

        return {"years": years, "months": months, "days": days}

    def cleanup(self, keep_raw: bool = False, keep_processed: bool = False) -> None:
        """清理中间文件.

        Args:
            keep_raw: 是否保留原始下载文件.
            keep_processed: 是否保留处理后文件.
        """
        if not keep_raw and self.raw_dir.exists():
            shutil.rmtree(self.raw_dir)
            logger.info("已清理原始数据目录")

        if not keep_processed and self.processed_dir.exists():
            shutil.rmtree(self.processed_dir)
            logger.info("已清理处理后数据目录")


# ─── 使用示例 ────────────────────────────────────────────────────────────────────


def example_usage() -> None:
    """ERA5 流水线使用示例."""
    pipeline = ERA5Pipeline(
        output_dir="./era5_data",
        area={"north": 35.0, "south": 27.0, "east": 110.0, "west": 102.0},
    )

    # 1. 下载数据
    try:
        downloaded = pipeline.download(
            variables=["u10", "v10", "t2m", "msl", "sp", "z500", "z850", "t500", "t850"],
            start_date="2024-01-01",
            end_date="2024-01-02",
        )
        logger.info("下载的文件: {}", downloaded)
    except Exception as exc:
        logger.error("下载失败: {}", exc)
        return

    # 2. 数据处理
    processed = pipeline.process(target_resolution=0.25)
    logger.info("处理后的文件: {}", processed)

    # 3. 数据验证
    validation = pipeline.validate()
    logger.info("验证结果: {}", validation)

    # 4. 生成 FengWu 格式
    fengwu_file = pipeline.to_fengwu_format(output_name="fengwu_input_20240101.nc")
    logger.info("FengWu 输入文件: {}", fengwu_file)


if __name__ == "__main__":
    example_usage()
