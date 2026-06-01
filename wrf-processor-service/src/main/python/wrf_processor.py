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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WrfProcessor:
    """
    WRF气象数据处理器
    """
    
    def __init__(self, file_path):
        """
        初始化WRF处理器
        :param file_path: WRF输出文件路径
        """
        self.file_path = file_path
        self.dataset = None
        self.variables = {}
    
    def open_dataset(self):
        """
        打开NetCDF4数据集
        """
        try:
            self.dataset = nc.Dataset(self.file_path, 'r')
            logger.info(f"成功打开WRF文件: {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"打开WRF文件失败: {e}")
            return False
    
    def close_dataset(self):
        """
        关闭数据集
        """
        if self.dataset:
            self.dataset.close()
            logger.info("成功关闭WRF文件")
    
    def get_variables(self):
        """
        获取所有变量
        """
        if not self.dataset:
            logger.error("数据集未打开")
            return {}
        
        variables = {}
        for var_name in self.dataset.variables:
            var = self.dataset.variables[var_name]
            variables[var_name] = {
                'shape': var.shape,
                'units': getattr(var, 'units', 'unknown'),
                'long_name': getattr(var, 'long_name', var_name)
            }
        
        self.variables = variables
        return variables
    
    def extract_meteorological_data(self, height=100):
        """
        提取指定高度的气象数据
        :param height: 高度（米）
        :return: 气象数据字典
        """
        if not self.dataset:
            logger.error("数据集未打开")
            return {}
        
        try:
            # 提取基本气象变量
            data = {}
            
            # 提取时间
            if 'Times' in self.dataset.variables:
                times = self.dataset.variables['Times'][:]
                data['times'] = [''.join([chr(c) for c in t]) for t in times]
            
            # 提取风场
            if 'U' in self.dataset.variables and 'V' in self.dataset.variables:
                U = self.dataset.variables['U'][:]
                V = self.dataset.variables['V'][:]
                data['wind_speed'] = np.sqrt(U**2 + V**2).tolist()
                data['wind_direction'] = np.degrees(np.arctan2(V, U)).tolist()
            
            # 提取温度
            if 'T' in self.dataset.variables:
                T = self.dataset.variables['T'][:]
                data['temperature'] = (T + 300).tolist()  # 转换为摄氏度
            
            # 提取湿度
            if 'Q2' in self.dataset.variables:
                Q2 = self.dataset.variables['Q2'][:]
                data['humidity'] = Q2.tolist()
            
            # 提取气压
            if 'PSFC' in self.dataset.variables:
                PSFC = self.dataset.variables['PSFC'][:]
                data['pressure'] = (PSFC / 100).tolist()  # 转换为百帕
            
            logger.info(f"成功提取高度 {height} 米的气象数据")
            return data
            
        except Exception as e:
            logger.error(f"提取气象数据失败: {e}")
            return {}
    
    def get_statistics(self):
        """
        计算数据统计信息
        :return: 统计信息字典
        """
        if not self.dataset:
            logger.error("数据集未打开")
            return {}
        
        stats = {}
        
        # 计算风速统计
        if 'U' in self.dataset.variables and 'V' in self.dataset.variables:
            U = self.dataset.variables['U'][:]
            V = self.dataset.variables['V'][:]
            wind_speed = np.sqrt(U**2 + V**2)
            stats['wind_speed'] = {
                'mean': float(np.mean(wind_speed)),
                'min': float(np.min(wind_speed)),
                'max': float(np.max(wind_speed)),
                'std': float(np.std(wind_speed))
            }
        
        # 计算温度统计
        if 'T' in self.dataset.variables:
            T = self.dataset.variables['T'][:]
            temperature = T + 300  # 转换为摄氏度
            stats['temperature'] = {
                'mean': float(np.mean(temperature)),
                'min': float(np.min(temperature)),
                'max': float(np.max(temperature)),
                'std': float(np.std(temperature))
            }
        
        logger.info("成功计算数据统计信息")
        return stats

def process_wrf_file(file_path, height=100):
    """
    处理WRF文件的主函数
    :param file_path: WRF文件路径
    :param height: 高度（米）
    :return: 处理结果
    """
    processor = WrfProcessor(file_path)
    
    try:
        if not processor.open_dataset():
            return {
                'success': False,
                'error': '无法打开WRF文件'
            }
        
        # 提取气象数据
        meteorological_data = processor.extract_meteorological_data(height)
        
        # 计算统计信息
        statistics = processor.get_statistics()
        
        # 获取变量信息
        variables = processor.get_variables()
        
        return {
            'success': True,
            'data': {
                'meteorological_data': meteorological_data,
                'statistics': statistics,
                'variables': variables
            }
        }
        
    finally:
        processor.close_dataset()

def main():
    """
    主函数
    """
    if len(sys.argv) < 2:
        logger.error("缺少文件路径参数")
        print(json.dumps({
            'success': False,
            'error': '缺少文件路径参数'
        }))
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
    print(json.dumps(result))

if __name__ == "__main__":
    main()