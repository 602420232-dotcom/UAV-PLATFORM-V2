"""
天资/风雷 数据拉取模块
模拟 CMA 开放数据平台接口，支持:
1. HTTP API 拉取（标准 REST）
2. GRIB2 文件下载 + 解析
3. 本地缓存管理
"""
import logging
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import asdict

import requests
import numpy as np
import xarray as xr

from .config import CONFIG

logger = logging.getLogger(__name__)


class CMAFetcher:
    """CMA 数值预报数据拉取器"""

    def __init__(self):
        self.cfg = CONFIG.cma
        self.domain = CONFIG.domain
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "UAV-Weather/1.0"})
        self._ensure_cache()

    def _ensure_cache(self):
        Path(self.cfg.cache_dir).mkdir(parents=True, exist_ok=True)

    # ── 天资拉取 ─────────────────────────────────

    def fetch_tianzi(self, fcst_hour: int = 0) -> Optional[xr.Dataset]:
        """拉取天资全球预报 (GRAPES_GFS, ~25km)"""
        params = {**self.cfg.tianzi_params, "fcst_hour": fcst_hour}
        return self._fetch("tianzi", self.cfg.tianzi_url, params, self.cfg.tianzi_key)

    # ── 风雷拉取 ─────────────────────────────────

    def fetch_fenglei(self, fcst_hour: int = 0) -> Optional[xr.Dataset]:
        """拉取风雷区域预报 (GRAPES_MESO, 3km)"""
        params = {**self.cfg.fenglei_params, "fcst_hour": fcst_hour}
        return self._fetch("fenglei", self.cfg.fenglei_url, params, self.cfg.fenglei_key)

    # ── 内部方法 ─────────────────────────────────

    def _fetch(self, name: str, url: str, params: Dict, api_key: str) -> Optional[xr.Dataset]:
        cache_key = hashlib.md5(f"{name}_{json.dumps(params, sort_keys=True)}".encode()).hexdigest()
        cache_file = Path(self.cfg.cache_dir) / f"{cache_key}.nc"

        # 优先读缓存
        if cache_file.exists() and (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).seconds < self.cfg.update_interval_min * 60:
            logger.info(f"[{name}] 命中缓存: {cache_file}")
            return xr.open_dataset(cache_file)

        # 模拟 API 调用 (后续替换为真实 CMA 接口)
        logger.info(f"[{name}] 拉取 {url} ...")
        try:
            if api_key:
                params["api_key"] = api_key
            # resp = self.session.get(url, params=params, timeout=30)
            # resp.raise_for_status()
            # return self._parse_grib_response(name, resp.content, cache_file)

            # ── 模拟返回 ──
            logger.warning(f"[{name}] 使用模拟数据 (API key 未配置)")
            return self._mock_dataset(name, params)

        except requests.RequestException as e:
            logger.error(f"[{name}] 拉取失败: {e}")
            return None

    # ── GRIB 解析 ─────────────────────────────────

    def _parse_grib_response(self, name: str, data: bytes, cache_file: Path) -> xr.Dataset:
        """解析 GRIB2 二进制 -> xarray Dataset"""
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".grib2")
        tmp.write(data)
        tmp.close()

        try:
            ds = xr.open_dataset(tmp.name, engine="cfgrib",
                                 backend_kwargs={"filter_by_keys": {"typeOfLevel": "surface"}})
            # 裁剪成都平原区域
            ds = self._crop_domain(ds)
            ds.to_netcdf(cache_file)
            logger.info(f"[{name}] 解析完成 -> {cache_file}")
            return ds
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    def _crop_domain(self, ds: xr.Dataset) -> xr.Dataset:
        """裁剪到成都平原"""
        lat_min = self.domain.lat_center - self.domain.height_km / 111.0 / 2
        lat_max = self.domain.lat_center + self.domain.height_km / 111.0 / 2
        lon_min = self.domain.lon_center - self.domain.width_km / (111.0 * np.cos(np.radians(self.domain.lat_center))) / 2
        lon_max = self.domain.lon_center + self.domain.width_km / (111.0 * np.cos(np.radians(self.domain.lat_center))) / 2
        return ds.sel(latitude=slice(lat_min, lat_max),
                      longitude=slice(lon_min, lon_max))

    # ── 模拟数据（无 API key 时用） ────────────────

    def _mock_dataset(self, name: str, params: Dict) -> xr.Dataset:
        """生成模拟预报场用于开发调试"""
        ny, nx = self.domain.coarse_grid
        np.random.seed(42)

        lat = np.linspace(self.domain.lat_center - 0.75, self.domain.lat_center + 0.75, ny)
        lon = np.linspace(self.domain.lon_center - 0.75, self.domain.lon_center + 0.75, nx)
        level = params.get("levels", [850])

        # 模拟 10m 风场 (成都平原真实平均风≈1.5m/s)
        u10 = np.random.normal(1.5, 2.0, (ny, nx))
        v10 = np.random.normal(0.5, 1.5, (ny, nx))
        t2m = np.random.normal(20, 5, (ny, nx)) + 273.15  # K
        rh2m = np.random.normal(70, 15, (ny, nx))
        ps = np.random.normal(1013, 5, (ny, nx))
        blh = np.random.normal(500, 200, (ny, nx))

        coords = {"latitude": lat, "longitude": lon, "isobaricInhPa": level}
        ds = xr.Dataset({
            "u10": (("latitude", "longitude"), u10),
            "v10": (("latitude", "longitude"), v10),
            "t2m": (("latitude", "longitude"), t2m),
            "rh2m": (("latitude", "longitude"), rh2m),
            "ps": (("latitude", "longitude"), ps),
            "blh": (("latitude", "longitude"), blh),
        }, coords=coords)
        ds.attrs["source"] = name
        ds.attrs["forecast_time"] = datetime.now().isoformat()
        return ds


def fetch_latest() -> Dict[str, xr.Dataset]:
    """便捷调用: 拉取全部最新数据"""
    fetcher = CMAFetcher()
    data = {}
    tz = fetcher.fetch_tianzi(0)
    fl = fetcher.fetch_fenglei(0)
    if tz is not None: data["tianzi"] = tz
    if fl is not None: data["fenglei"] = fl
    return data
