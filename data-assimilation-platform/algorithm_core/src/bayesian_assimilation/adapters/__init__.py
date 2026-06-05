"""
数据适配器模块
提供数据格式转换、网格处理、文件读写等功能
"""


from .data import (
    DataAdapter,
    WRFDataAdapter,
    ObservationAdapter,
    convert_to_assimilation_format,
    validate_data_format
)


from .grid import (
    GridAdapter,
    interpolate_data,
    resample_data,
    grid_to_points,
    points_to_grid
)


from .io import (
    IOAdapter,
    NetCDFReader,
    HDF5Reader,
    write_netcdf,
    write_hdf5
)


from .uav_adapter import (
    UAVDataAdapter,
    process_uav_data,
    uav_to_standard_format
)


__all__ = [
    # Data adapter
    'DataAdapter',
    'WRFDataAdapter',
    'ObservationAdapter',
    'convert_to_assimilation_format',
    'validate_data_format',

    # Grid adapter
    'GridAdapter',
    'interpolate_data',
    'resample_data',
    'grid_to_points',
    'points_to_grid',

    # IO adapter
    'IOAdapter',
    'NetCDFReader',
    'HDF5Reader',
    'write_netcdf',
    'write_hdf5',

    # UAV adapter
    'UAVDataAdapter',
    'process_uav_data',
    'uav_to_standard_format'
]
