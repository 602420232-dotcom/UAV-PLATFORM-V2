#!/usr/bin/env python3
"""
WRF气象数据处理服务
负责解析WRF输出的NetCDF4文件，提取低空气象参数
"""

import netCDF4 as nc
import numpy as np
import pandas as pd
import json
import sys
import os
import logging
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WrfProcessor:
    """WRF气象数据处理器"""

    def __init__(self, file_path: str):
        """
        Initialize WRF processor.

        Args:
            file_path: Path to the WRF output NetCDF4 file.
        """
        self.file_path = file_path
        self.dataset = None
        self.variables = {}
        self._lock = threading.Lock()
        self._open_count = 0

    def open_dataset(self) -> bool:
        """Open the NetCDF4 dataset thread-safely."""
        with self._lock:
            if self._open_count > 0:
                self._open_count += 1
                return True
            try:
                self.dataset = nc.Dataset(self.file_path, 'r')
                self._open_count = 1
                logger.info(f"成功打开WRF文件: {self.file_path}")
                return True
            except Exception as e:
                logger.error(f"打开WRF文件失败: {e}")
                self.dataset = None
                return False

    def close_dataset(self) -> None:
        """Close the dataset thread-safely."""
        with self._lock:
            if self._open_count <= 0:
                return
            self._open_count -= 1
            if self._open_count > 0:
                return
            if self.dataset is not None:
                try:
                    self.dataset.close()
                    logger.info("成功关闭WRF文件")
                except Exception as e:
                    logger.warning(f"关闭WRF文件异常: {e}")
                finally:
                    self.dataset = None

    def get_variables(self) -> dict:
        """
        Get all variable metadata from the dataset.

        Returns:
            Dict mapping variable names to their shape, units, and long_name.
        """
        with self._lock:
            if not self.dataset:
                logger.error("数据集未打开")
                return {}

            variables = {}
            for var_name in self.dataset.variables:
                var = self.dataset.variables[var_name]
                variables[var_name] = {
                    'shape': var.shape,
                    'units': getattr(var, 'units', 'unknown'),
                    'long_name': getattr(var, 'long_name', var_name),
                }

            self.variables = variables
            return variables

    def extract_meteorological_data_chunked(
        self, height: int = 100, chunk_size: int = 10
    ) -> dict:
        """
        Extract meteorological data in time chunks to limit memory usage.

        For large WRF files with many time steps, this method reads
        one chunk of time steps at a time instead of loading all data at once.

        Args:
            height: Target height in meters (default: 100).
            chunk_size: Number of time steps per chunk (default: 10).

        Returns:
            Dict containing meteorological data arrays, or empty dict on failure.
        """
        with self._lock:
            if not self.dataset:
                logger.error("数据集未打开")
                return {}

            try:
                n_times = len(self.dataset.dimensions.get('Time', ()))
                if n_times == 0:
                    logger.warning("数据集无时间维度")
                    return {}

                data: dict = {}
                data['wind_speed'] = []
                data['wind_direction'] = []
                data['temperature'] = []
                data['humidity'] = []
                data['pressure'] = []

                for start in range(0, n_times, chunk_size):
                    end = min(start + chunk_size, n_times)
                    logger.info(
                        f"分块读取: 时间步 [{start}:{end}] / {n_times}"
                    )

                    if 'U' in self.dataset.variables and 'V' in self.dataset.variables:
                        U_chunk = self.dataset.variables['U'][start:end]
                        V_chunk = self.dataset.variables['V'][start:end]
                        data['wind_speed'].extend(
                            np.sqrt(U_chunk**2 + V_chunk**2).tolist()
                        )
                        data['wind_direction'].extend(
                            np.degrees(np.arctan2(V_chunk, U_chunk)).tolist()
                        )

                    if 'T' in self.dataset.variables:
                        T_chunk = self.dataset.variables['T'][start:end]
                        data['temperature'].extend((T_chunk + 300).tolist())

                    if 'Q2' in self.dataset.variables:
                        Q2_chunk = self.dataset.variables['Q2'][start:end]
                        data['humidity'].extend(Q2_chunk.tolist())

                    if 'PSFC' in self.dataset.variables:
                        PSFC_chunk = self.dataset.variables['PSFC'][start:end]
                        data['pressure'].extend((PSFC_chunk / 100).tolist())

                if 'Times' in self.dataset.variables:
                    times = self.dataset.variables['Times'][:]
                    data['times'] = [
                        ''.join(chr(c) for c in t) for t in times
                    ]

                logger.info(
                    f"分块提取完成: {n_times} 时间步, {chunk_size} 步/块"
                )
                return data

            except Exception as e:
                logger.error(f"分块提取气象数据失败: {e}")
                return {}

    def extract_meteorological_data(self, height: int = 100) -> dict:
        """
        Extract meteorological data at a given height level.

        Args:
            height: Target height in meters (default: 100).

        Returns:
            Dict containing wind_speed, wind_direction, temperature,
            humidity, pressure arrays, or empty dict on failure.
        """
        with self._lock:
            if not self.dataset:
                logger.error("数据集未打开")
                return {}

            try:
                data = {}

                if 'Times' in self.dataset.variables:
                    times = self.dataset.variables['Times'][:]
                    data['times'] = [''.join(chr(c) for c in t) for t in times]

                if 'U' in self.dataset.variables and 'V' in self.dataset.variables:
                    U = self.dataset.variables['U'][:]
                    V = self.dataset.variables['V'][:]
                    data['wind_speed'] = np.sqrt(U**2 + V**2).tolist()
                    data['wind_direction'] = np.degrees(np.arctan2(V, U)).tolist()

                if 'T' in self.dataset.variables:
                    T = self.dataset.variables['T'][:]
                    data['temperature'] = (T + 300).tolist()

                if 'Q2' in self.dataset.variables:
                    Q2 = self.dataset.variables['Q2'][:]
                    data['humidity'] = Q2.tolist()

                if 'PSFC' in self.dataset.variables:
                    PSFC = self.dataset.variables['PSFC'][:]
                    data['pressure'] = (PSFC / 100).tolist()

                logger.info(f"成功提取高度 {height} 米的气象数据")
                return data

            except Exception as e:
                logger.error(f"提取气象数据失败: {e}")
                return {}

    def get_statistics(self) -> dict:
        """
        Calculate statistical summary of weather variables.

        Returns:
            Dict with 'wind_speed' and 'temperature' stats, each containing
            mean, min, max, and standard deviation.
        """
        with self._lock:
            if not self.dataset:
                logger.error("数据集未打开")
                return {}

            stats = {}

            if 'U' in self.dataset.variables and 'V' in self.dataset.variables:
                U = self.dataset.variables['U'][:]
                V = self.dataset.variables['V'][:]
                wind_speed = np.sqrt(U**2 + V**2)
                stats['wind_speed'] = {
                    'mean': float(np.mean(wind_speed)),
                    'min': float(np.min(wind_speed)),
                    'max': float(np.max(wind_speed)),
                    'std': float(np.std(wind_speed)),
                }

            if 'T' in self.dataset.variables:
                T = self.dataset.variables['T'][:]
                temperature = T + 300
                stats['temperature'] = {
                    'mean': float(np.mean(temperature)),
                    'min': float(np.min(temperature)),
                    'max': float(np.max(temperature)),
                    'std': float(np.std(temperature)),
                }

            logger.info("成功计算数据统计信息")
            return stats


def process_wrf_file(file_path: str, height: int = 100) -> dict:
    """
    Process a WRF NetCDF4 file and extract meteorological data.

    Args:
        file_path: Path to the WRF output file.
        height: Target height in meters.

    Returns:
        Dict with 'success' (bool) and either 'data' or 'error' key.
    """
    processor = WrfProcessor(file_path)

    try:
        if not processor.open_dataset():
            return {'success': False, 'error': '无法打开WRF文件'}

        meteorological_data = processor.extract_meteorological_data(height)
        statistics = processor.get_statistics()
        variables = processor.get_variables()

        return {
            'success': True,
            'data': {
                'meteorological_data': meteorological_data,
                'statistics': statistics,
                'variables': variables,
            },
        }

    finally:
        processor.close_dataset()


def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) < 2:
        logger.error("缺少文件路径参数")
        logger.info(json.dumps({'success': False, 'error': '缺少文件路径参数'}))
        return

    file_path = sys.argv[1]
    height = 100

    if len(sys.argv) > 2:
        try:
            height = int(sys.argv[2])
        except ValueError:
            logger.warning("高度参数无效，使用默认值100米")

    logger.info(f"开始处理WRF文件: {file_path}, 高度: {height}米")
    result = process_wrf_file(file_path, height)
    logger.info(f"WRF文件处理完成: {file_path}")
    logger.info(json.dumps(result))


if __name__ == "__main__":
    main()
