# data_sources/radar.py
# 雷达数据源处理

import numpy as np
from typing import Optional, List, Dict, Any, Tuple
import h5py
import netCDF4 as nc
import logging


try:
    from .base import DataSourceBase


except ImportError:
    from abc import ABC, abstractmethod
    class DataSourceBase(ABC):
        def __init__(self, config=None):
            self.config = config or {}
            self.data = None
            self.metadata = {}

        @abstractmethod
        def load_data(self, *args, **kwargs):
            pass

logger = logging.getLogger(__name__)


class RadarDataSource(DataSourceBase):
    """
    雷达数据源
    处理雷达观测数据
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.radar_type = self.config.get('radar_type', 'Doppler')
        self.data_format = self.config.get('data_format', 'netcdf')

    def load_data(self, file_path: str, *args, **kwargs) -> bool:
        """
        加载雷达数据

        Args:
            file_path: 数据文件路径

        Returns:
            bool: 加载是否成功
        """
        try:
            if self.data_format == 'netcdf':
                self._load_netcdf(file_path)
            elif self.data_format == 'hdf5':
                self._load_hdf5(file_path)
            else:
                logger.error(f"不支持的数据格式: {self.data_format}")
                return False

            logger.info(f"成功加载雷达数据: {file_path}")
            return True
        except Exception as e:
            logger.error(f"加载雷达数据失败: {e}")
            return False

    def _load_netcdf(self, file_path: str):
        """
        加载NetCDF格式的雷达数据
        """
        with nc.Dataset(file_path, 'r') as ds:
            self.data = {}
            for var_name in ds.variables:
                self.data[var_name] = ds[var_name][:]

            # 提取元数据
            self.metadata['radar'] = getattr(ds, 'radar', self.radar_type)
            self.metadata['site'] = getattr(ds, 'site', 'unknown')
            self.metadata['time'] = getattr(ds, 'time', None)
            self.metadata['range_resolution'] = getattr(ds, 'range_resolution', 'unknown')

    def _load_hdf5(self, file_path: str):
        """
        加载HDF5格式的雷达数据
        """
        with h5py.File(file_path, 'r') as f:
            self.data = {}
            def _extract_data(group, prefix=''):
                for key in group.keys():
                    item = group[key]
                    if isinstance(item, h5py.Group):
                        _extract_data(item, f"{prefix}{key}/")
                    else:
                        self.data[f"{prefix}{key}"] = item[:]

            _extract_data(f)

            # 提取元数据
            self.metadata['radar'] = self.radar_type
            self.metadata['site'] = 'unknown'
            self.metadata['time'] = None
            self.metadata['range_resolution'] = 'unknown'

    def process_data(self) -> Any:
        """
        处理雷达数据

        Returns:
            Any: 处理后的数据
        """
        if not self.validate_data():
            return None

        try:
            # 处理不同类型的雷达数据
            if 'reflectivity' in self.data:
                return self._process_reflectivity_data()
            elif 'velocity' in self.data:
                return self._process_velocity_data()
            else:
                logger.warning("未知的雷达数据类型")
                return self.data
        except Exception as e:
            logger.error(f"处理雷达数据失败: {e}")
            return None

    def _process_reflectivity_data(self) -> Dict[str, Any]:
        """
        处理反射率数据
        """
        # 处理反射率数据
        reflectivity = self.data['reflectivity']
        # 这里可以添加更复杂的处理逻辑，如回波强度转换
        return {'reflectivity': reflectivity}

    def _process_velocity_data(self) -> Dict[str, Any]:
        """
        处理速度数据
        """
        # 处理速度数据
        velocity = self.data['velocity']
        # 这里可以添加更复杂的处理逻辑，如速度退模糊
        return {'velocity': velocity}

    def is_real_data(self) -> bool:
        """
        判断数据是否为真实观测数据（非模拟/测试数据）

        Returns:
            bool: True 为真实数据，False 为模拟数据
        """
        if self.data is None:
            return False
        # 通过元数据判断：如果有真实站点/雷达标识，则为真实数据
        site = self.metadata.get('site', 'unknown')
        radar = self.metadata.get('radar', 'unknown')
        if site != 'unknown' and radar != 'unknown':
            return True
        # 检查配置中是否显式标记为模拟数据
        if self.config.get('mock_data', False):
            return False
        # 默认：如果成功从文件加载了数据，视为真实数据
        return self.data is not None and len(self.data) > 0

    def fetch(self, file_path: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        高级数据获取方法：加载 → 处理 → 返回完整结果

        整合 load_data、process_data 和 get_observations 流程，
        提供统一的数据获取入口和标准化的返回结构。

        Args:
            file_path: 数据文件路径
            **kwargs: 额外参数，支持:
                - apply_qc (bool): 是否应用质量控制，默认 True
                - max_range (float): 最大探测距离 (km)
                - min_snr (float): 最小信噪比 (dB)

        Returns:
            Optional[Dict[str, Any]]: 包含处理后数据的字典，失败返回 None
        """
        try:
            # 1. 加载数据
            if not self.load_data(file_path):
                logger.error(f"雷达数据加载失败: {file_path}")
                return None

            # 2. 处理数据
            processed = self.process_data()
            if processed is None:
                logger.error("雷达数据处理失败")
                return None

            # 3. 提取观测值
            obs_values, obs_locations, obs_errors = self.get_observations()

            # 4. 组装返回结果
            result = {
                'metadata': self.metadata,
                'processed_data': processed,
                'observations': {
                    'values': obs_values,
                    'locations': obs_locations,
                    'errors': obs_errors,
                },
                'is_real_data': self.is_real_data(),
                'data_format': self.data_format,
                'radar_type': self.radar_type,
            }

            # 5. 应用质量控制（如果启用）
            apply_qc = kwargs.get('apply_qc', True)
            if apply_qc and 'reflectivity' in self.data:
                reflectivity = np.array(self.data['reflectivity'])
                # 剔除无效值（通常是 < 0 或 NaN）
                reflectivity = np.where(np.isnan(reflectivity), -999.0, reflectivity)
                result['quality_metrics'] = {
                    'total_gates': int(reflectivity.size),
                    'valid_gates': int(np.sum(reflectivity > -999.0)),
                    'min_reflectivity': float(np.min(reflectivity[reflectivity > -999.0])) if np.any(reflectivity > -999.0) else -999.0,
                    'max_reflectivity': float(np.max(reflectivity)),
                }

            logger.info(f"雷达数据获取成功: {file_path}, 观测数={len(obs_values)}")
            return result

        except Exception as e:
            logger.error(f"雷达数据获取失败: {e}")
            return None

    def get_observations(self) -> Tuple[List[float], List[Tuple[float, float, float]], List[float]]:
        """
        获取观测数据

        Returns:
            Tuple[观测值列表, 观测位置列表, 观测误差列表]
        """
        if not self.validate_data():
            return [], [], []

        try:
            # 提取观测值
            if 'reflectivity' in self.data:
                obs_values = self.data['reflectivity'].flatten().tolist()
            elif 'velocity' in self.data:
                obs_values = self.data['velocity'].flatten().tolist()
            else:
                logger.warning("无法提取观测值")
                return [], [], []

            # 生成观测位置 (这里需要根据实际数据结构调整)
            obs_locations = []
            if 'azimuth' in self.data and 'range' in self.data and 'elevation' in self.data:
                azimuth = self.data['azimuth']
                range_data = self.data['range']
                elevation = self.data['elevation']

                # 雷达站点位置
                radar_lat = self.config.get('radar_lat', 0.0)
                radar_lon = self.config.get('radar_lon', 0.0)
                radar_alt = self.config.get('radar_alt', 0.0)

                for az in azimuth:
                    for r in range_data:
                        for elev in elevation:
                            # 计算雷达回波位置
                            lon = radar_lon  # 简化计算，实际需要球面几何计算
                            lat = radar_lat
                            alt = radar_alt + r * np.sin(np.deg2rad(elev))
                            obs_locations.append((lon, lat, alt))
            else:
                # 生成默认位置
                for i in range(len(obs_values)):
                    obs_locations.append((0.0, 0.0, 0.0))

            # 生成观测误差
            obs_errors = [1.0] * len(obs_values)  # 默认误差

            return obs_values, obs_locations, obs_errors
        except Exception as e:
            logger.error(f"获取观测数据失败: {e}")
            return [], [], []
