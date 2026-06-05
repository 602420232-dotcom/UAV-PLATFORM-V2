# data_sources/ground_station.py
# 地面站数据源处理

from typing import Optional, List, Dict, Any, Tuple
import csv
import json
import logging


try:
    from .base import DataSourceBase  # type: ignore[assignment]


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


class GroundStationDataSource(DataSourceBase):
    """
    地面站数据源
    处理地面观测数据
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.station_type = self.config.get('station_type', 'meteorological')
        self.data_format = self.config.get('data_format', 'csv')

    def load_data(self, file_path: str, *args, **kwargs) -> bool:
        """
        加载地面站数据

        Args:
            file_path: 数据文件路径

        Returns:
            bool: 加载是否成功
        """
        try:
            if self.data_format == 'csv':
                self._load_csv(file_path)
            elif self.data_format == 'json':
                self._load_json(file_path)
            else:
                logger.error(f"不支持的数据格式: {self.data_format}")
                return False

            logger.info(f"成功加载地面站数据: {file_path}")
            return True
        except Exception as e:
            logger.error(f"加载地面站数据失败: {e}")
            return False

    def _load_csv(self, file_path: str):
        """
        加载CSV格式的地面站数据
        """
        self.data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 转换数据类型
                processed_row = {}
                for key, value in row.items():
                    try:
                        processed_row[key] = float(value)
                    except ValueError:
                        processed_row[key] = value
                self.data.append(processed_row)

        # 提取元数据
        if self.data:
            self.metadata['station_id'] = self.data[0].get('station_id', 'unknown')
            self.metadata['station_name'] = self.data[0].get('station_name', 'unknown')
            self.metadata['data_format'] = 'csv'

    def _load_json(self, file_path: str):
        """
        加载JSON格式的地面站数据
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        # 提取元数据
        if isinstance(self.data, dict):
            self.metadata['station_id'] = self.data.get('station_id', 'unknown')
            self.metadata['station_name'] = self.data.get('station_name', 'unknown')
            self.metadata['data_format'] = 'json'
        elif isinstance(self.data, list) and self.data:
            self.metadata['station_id'] = self.data[0].get('station_id', 'unknown')
            self.metadata['station_name'] = self.data[0].get('station_name', 'unknown')
            self.metadata['data_format'] = 'json'

    def process_data(self) -> Any:
        """
        处理地面站数据

        Returns:
            Any: 处理后的数据
        """
        if not self.validate_data():  # type: ignore[attr-defined]
            return None

        try:
            # 处理不同类型的地面站数据
            if self.station_type == 'meteorological':
                return self._process_meteorological_data()
            elif self.station_type == 'air_quality':
                return self._process_air_quality_data()
            else:
                logger.warning("未知的地面站类型")
                return self.data
        except Exception as e:
            logger.error(f"处理地面站数据失败: {e}")
            return None

    def _process_meteorological_data(self) -> Dict[str, Any]:
        """
        处理气象地面站数据
        """
        # 处理气象数据
        processed_data = {
            'temperature': [],
            'humidity': [],
            'pressure': [],
            'wind_speed': [],
            'wind_direction': [],
            'timestamp': []
        }

        for record in self.data:
            if isinstance(record, dict):
                processed_data['temperature'].append(record.get('temperature', 0.0))
                processed_data['humidity'].append(record.get('humidity', 0.0))
                processed_data['pressure'].append(record.get('pressure', 0.0))
                processed_data['wind_speed'].append(record.get('wind_speed', 0.0))
                processed_data['wind_direction'].append(record.get('wind_direction', 0.0))
                processed_data['timestamp'].append(record.get('timestamp', ''))

        return processed_data

    def _process_air_quality_data(self) -> Dict[str, Any]:
        """
        处理空气质量地面站数据
        """
        # 处理空气质量数据
        processed_data = {
            'pm25': [],
            'pm10': [],
            'so2': [],
            'no2': [],
            'o3': [],
            'co': [],
            'timestamp': []
        }

        for record in self.data:
            if isinstance(record, dict):
                processed_data['pm25'].append(record.get('pm25', 0.0))
                processed_data['pm10'].append(record.get('pm10', 0.0))
                processed_data['so2'].append(record.get('so2', 0.0))
                processed_data['no2'].append(record.get('no2', 0.0))
                processed_data['o3'].append(record.get('o3', 0.0))
                processed_data['co'].append(record.get('co', 0.0))
                processed_data['timestamp'].append(record.get('timestamp', ''))

        return processed_data

    def is_real_data(self) -> bool:
        """
        判断数据是否为真实观测数据（非模拟/测试数据）

        Returns:
            bool: True 为真实数据，False 为模拟数据
        """
        if self.data is None:
            return False
        # 通过元数据判断：有站点标识且非 'unknown' 则为真实数据
        station_id = self.metadata.get('station_id', 'unknown')
        if station_id != 'unknown':
            return True
        # 检查配置中是否显式标记为模拟数据
        if self.config.get('mock_data', False):
            return False
        # 默认：成功从文件加载且包含有效数据，视为真实数据
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
                - max_stations (int): 最大站点数限制
                - data_types (list): 需要提取的数据类型列表

        Returns:
            Optional[Dict[str, Any]]: 包含处理后数据的字典，失败返回 None
        """
        try:
            # 1. 加载数据
            if not self.load_data(file_path):
                logger.error(f"地面站数据加载失败: {file_path}")
                return None

            # 2. 处理数据
            processed = self.process_data()
            if processed is None:
                logger.error("地面站数据处理失败")
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
                'station_type': self.station_type,
                'record_count': len(self.data) if self.data else 0,
            }

            # 5. 应用质量控制（如果启用）
            apply_qc = kwargs.get('apply_qc', True)
            if apply_qc and isinstance(processed, dict):
                # 统计各字段有效观测数
                quality_metrics = {}
                for key, values in processed.items():
                    if isinstance(values, list):
                        valid = sum(1 for v in values if v is not None and v != '')
                        quality_metrics[f'{key}_valid'] = valid
                        quality_metrics[f'{key}_total'] = len(values)
                result['quality_metrics'] = quality_metrics

            logger.info(
                f"地面站数据获取成功: {file_path}, "
                f"站点={self.metadata.get('station_id', 'unknown')}, "
                f"记录数={len(obs_values)}"
            )
            return result

        except Exception as e:
            logger.error(f"地面站数据获取失败: {e}")
            return None

    def get_observations(self) -> Tuple[List[float], List[Tuple[float, float, float]], List[float]]:
        """
        获取观测数据

        Returns:
            Tuple[观测值列表, 观测位置列表, 观测误差列表]
        """
        if not self.validate_data():  # type: ignore[attr-defined]
            return [], [], []

        try:
            obs_values = []
            obs_locations = []
            obs_errors = []

            for record in self.data:
                if isinstance(record, dict):
                    # 提取观测值
                    if 'temperature' in record:
                        obs_values.append(record['temperature'])
                    elif 'pm25' in record:
                        obs_values.append(record['pm25'])
                    else:
                        continue

                    # 提取观测位置
                    lat = record.get('latitude', 0.0)
                    lon = record.get('longitude', 0.0)
                    alt = record.get('altitude', 0.0)
                    obs_locations.append((lon, lat, alt))

                    # 生成观测误差
                    obs_errors.append(0.2)  # 默认误差

            return obs_values, obs_locations, obs_errors
        except Exception as e:
            logger.error(f"获取观测数据失败: {e}")
            return [], [], []
