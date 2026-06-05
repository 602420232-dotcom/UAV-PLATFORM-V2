"""
文件读写模块
提供NetCDF、HDF5等格式的文件读写功能
"""

import logging
import numpy as np
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class IOAdapter:
    """
    IO适配器基类
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def read(self, file_path: str) -> Dict[str, Any]:
        """
        读取文件

        Args:
            file_path: 文件路径

        Returns:
            读取的数据
        """
        raise NotImplementedError

    def write(self, file_path: str, data: Dict[str, Any]) -> bool:
        """
        写入文件

        Args:
            file_path: 文件路径
            data: 要写入的数据

        Returns:
            是否成功
        """
        raise NotImplementedError


class NetCDFReader(IOAdapter):
    """
    NetCDF文件读取器
    """

    def read(self, file_path: str) -> Dict[str, Any]:
        """
        读取NetCDF文件

        Args:
            file_path: 文件路径

        Returns:
            读取的数据
        """
        try:
            from netCDF4 import Dataset

            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return {}

            data = {}
            with Dataset(file_path, 'r') as nc:
                # 读取所有变量
                for var_name in nc.variables:
                    var = nc.variables[var_name]
                    data[var_name] = var[:]

                # 读取属性
                for attr_name in nc.ncattrs():
                    data[attr_name] = getattr(nc, attr_name)

            logger.info(f"成功读取NetCDF文件: {file_path}")
            return data

        except ImportError:
            logger.error("NetCDF4库未安装，无法读取NetCDF文件")
            logger.info("安装NetCDF4: pip install netCDF4")
            return {}
        except Exception as e:
            logger.error(f"读取NetCDF文件失败: {e}")
            return {}

    def write(self, file_path: str, data: Dict[str, Any]) -> bool:
        """
        写入NetCDF文件

        Args:
            file_path: 文件路径
            data: 要写入的数据

        Returns:
            是否成功
        """
        try:
            from netCDF4 import Dataset

            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with Dataset(file_path, 'w', format='NETCDF4') as nc:
                # 写入属性
                for key, value in data.items():
                    if not isinstance(value, np.ndarray):
                        setattr(nc, key, value)

                # 写入变量
                for key, value in data.items():
                    if isinstance(value, np.ndarray):
                        # 创建维度
                        dims = tuple(f'dim{i}' for i in range(value.ndim))
                        for i, dim in enumerate(dims):
                            if dim not in nc.dimensions:
                                nc.createDimension(dim, value.shape[i])

                        # 创建变量
                        var = nc.createVariable(key, value.dtype, dims)
                        var[:] = value

            logger.info(f"成功写入NetCDF文件: {file_path}")
            return True

        except ImportError:
            logger.error("NetCDF4库未安装，无法写入NetCDF文件")
            return False
        except Exception as e:
            logger.error(f"写入NetCDF文件失败: {e}")
            return False


class HDF5Reader(IOAdapter):
    """
    HDF5文件读取器
    """

    def read(self, file_path: str) -> Dict[str, Any]:
        """
        读取HDF5文件

        Args:
            file_path: 文件路径

        Returns:
            读取的数据
        """
        try:
            import h5py

            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return {}

            data = {}
            with h5py.File(file_path, 'r') as hf:

                def _visit_items(name, obj):
                    if isinstance(obj, h5py.Dataset):
                        data[name] = obj[:]

                hf.visititems(_visit_items)

            logger.info(f"成功读取HDF5文件: {file_path}")
            return data

        except ImportError:
            logger.error("h5py库未安装，无法读取HDF5文件")
            logger.info("安装h5py: pip install h5py")
            return {}
        except Exception as e:
            logger.error(f"读取HDF5文件失败: {e}")
            return {}

    def write(self, file_path: str, data: Dict[str, Any]) -> bool:
        """
        写入HDF5文件

        Args:
            file_path: 文件路径
            data: 要写入的数据

        Returns:
            是否成功
        """
        try:
            import h5py

            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with h5py.File(file_path, 'w') as hf:
                for key, value in data.items():
                    if isinstance(value, np.ndarray):
                        hf.create_dataset(key, data=value)

            logger.info(f"成功写入HDF5文件: {file_path}")
            return True

        except ImportError:
            logger.error("h5py库未安装，无法写入HDF5文件")
            return False
        except Exception as e:
            logger.error(f"写入HDF5文件失败: {e}")
            return False


def write_netcdf(file_path: str, data: Dict[str, Any]) -> bool:
    """
    写入NetCDF文件

    Args:
        file_path: 文件路径
        data: 要写入的数据

    Returns:
        是否成功
    """
    reader = NetCDFReader()
    return reader.write(file_path, data)


def write_hdf5(file_path: str, data: Dict[str, Any]) -> bool:
    """
    写入HDF5文件

    Args:
        file_path: 文件路径
        data: 要写入的数据

    Returns:
        是否成功
    """
    reader = HDF5Reader()
    return reader.write(file_path, data)
