#!/usr/bin/env python3
"""
贝叶斯同化服务
实现3D-VAR、EnKF和混合方法的贝叶斯同化
"""

import numpy as np
import json
import sys
import os
import logging
from typing import Dict, Tuple, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BayesianAssimilation:
    """
    贝叶斯同化类
    """
    
    def __init__(self, background_error: float = 0.1, observation_error: float = 0.05):
        """
        初始化贝叶斯同化
        :param background_error: 背景场误差
        :param observation_error: 观测误差
        """
        self.background_error = background_error
        self.observation_error = observation_error
    
    def _three_dimensional_var(self, 
                              background: Dict[str, np.ndarray], 
                              observations: Dict[str, np.ndarray]) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
        """
        3D-VAR同化方法
        :param background: 背景场
        :param observations: 观测数据
        :return: 分析场和不确定性
        """
        analysis = {}
        uncertainty = {}
        
        for var in background:
            if var in observations:
                # 确保观测数据与背景场形状一致
                if background[var].shape != observations[var].shape:
                    logger.warning(f"{var} 数据形状不一致，使用背景场")
                    analysis[var] = background[var]
                    uncertainty[var] = np.full_like(background[var], self.background_error ** 2)
                    continue
                
                # 简化的3D-VAR实现
                B = self.background_error ** 2
                R = self.observation_error ** 2
                
                # 增益矩阵
                K = B / (B + R)
                
                # 分析场
                analysis[var] = background[var] + K * (observations[var] - background[var])
                
                # 分析误差方差
                uncertainty[var] = (1 - K) * B
            else:
                analysis[var] = background[var]
                uncertainty[var] = np.full_like(background[var], self.background_error ** 2)
        
        return analysis, uncertainty
    
    def _ensemble_kalman_filter(self, 
                               background: Dict[str, np.ndarray], 
                               observations: Dict[str, np.ndarray]) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
        """
        集合卡尔曼滤波(EnKF)同化方法
        :param background: 背景场
        :param observations: 观测数据
        :return: 分析场和不确定性
        """
        analysis = {}
        uncertainty = {}
        
        # 简化的EnKF实现（使用单个集合成员）
        for var in background:
            if var in observations:
                # 确保观测数据与背景场形状一致
                if background[var].shape != observations[var].shape:
                    logger.warning(f"{var} 数据形状不一致，使用背景场")
                    analysis[var] = background[var]
                    uncertainty[var] = np.full_like(background[var], self.background_error ** 2)
                    continue
                
                # 计算背景场协方差
                B = np.var(background[var])
                R = self.observation_error ** 2
                
                # 增益矩阵
                K = B / (B + R)
                
                # 分析场
                analysis[var] = background[var] + K * (observations[var] - background[var])
                
                # 分析误差方差
                uncertainty[var] = (1 - K) * B
            else:
                analysis[var] = background[var]
                uncertainty[var] = np.full_like(background[var], self.background_error ** 2)
        
        return analysis, uncertainty
    
    def _hybrid_method(self, 
                      background: Dict[str, np.ndarray], 
                      observations: Dict[str, np.ndarray]) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
        """
        混合同化方法（3D-VAR + EnKF）
        :param background: 背景场
        :param observations: 观测数据
        :return: 分析场和不确定性
        """
        # 首先使用3D-VAR
        var_analysis, var_uncertainty = self._three_dimensional_var(background, observations)
        
        # 然后使用EnKF进行进一步优化
        enkf_analysis, enkf_uncertainty = self._ensemble_kalman_filter(var_analysis, observations)
        
        # 加权平均
        analysis = {}
        uncertainty = {}
        for var in background:
            # 3D-VAR权重0.4，EnKF权重0.6
            analysis[var] = 0.4 * var_analysis[var] + 0.6 * enkf_analysis[var]
            uncertainty[var] = 0.4 * var_uncertainty[var] + 0.6 * enkf_uncertainty[var]
        
        return analysis, uncertainty
    
    def assimilate(self, 
                  background: Dict[str, np.ndarray], 
                  observations: Dict[str, np.ndarray], 
                  method: str = 'hybrid') -> Dict:
        """
        执行贝叶斯同化
        :param background: 背景场
        :param observations: 观测数据
        :param method: 同化方法 ('3dvar', 'enkf', 'hybrid')
        :return: 同化结果
        """
        try:
            if method == '3dvar':
                analysis, uncertainty = self._three_dimensional_var(background, observations)
            elif method == 'enkf':
                analysis, uncertainty = self._ensemble_kalman_filter(background, observations)
            elif method == 'hybrid':
                analysis, uncertainty = self._hybrid_method(background, observations)
            else:
                raise ValueError(f"未知的同化方法: {method}")
            
            # 转换为可序列化的格式
            analysis_serializable = {}
            uncertainty_serializable = {}
            
            for var in analysis:
                analysis_serializable[var] = analysis[var].tolist()
                uncertainty_serializable[var] = uncertainty[var].tolist()
            
            logger.info(f"{method} 同化完成")
            return {
                'success': True,
                'data': {
                    'analysis': analysis_serializable,
                    'uncertainty': uncertainty_serializable,
                    'method': method
                }
            }
            
        except Exception as e:
            logger.error(f"同化失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def load_input(file_index):
    """从文件加载JSON输入数据，防止命令注入"""
    if len(sys.argv) <= file_index:
        return {}
    file_path = sys.argv[file_index]
    with open(file_path, 'r') as f:
        return json.load(f)


def main():
    """
    主函数
    """
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': '缺少命令参数'
        }))
        return
    
    command = sys.argv[1]
    
    if command == 'execute':
        # 执行同化
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少输入数据'
            }))
            return
        
        try:
            input_data = load_input(2)
            background = input_data.get('background', {})
            observations = input_data.get('observations', {})
            method = input_data.get('method', 'hybrid')
            
            # 转换为numpy数组
            background_np = {}
            for var, data in background.items():
                background_np[var] = np.array(data)
            
            observations_np = {}
            for var, data in observations.items():
                observations_np[var] = np.array(data)
            
            assimilator = BayesianAssimilation()
            result = assimilator.assimilate(background_np, observations_np, method)
            print(json.dumps(result))
            
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
            
    elif command == 'variance':
        # 获取方差场
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少输入数据'
            }))
            return
        
        try:
            input_data = load_input(2)
            background = input_data.get('background', {})
            observations = input_data.get('observations', {})
            
            # 转换为numpy数组
            background_np = {}
            for var, data in background.items():
                background_np[var] = np.array(data)
            
            observations_np = {}
            for var, data in observations.items():
                observations_np[var] = np.array(data)
            
            assimilator = BayesianAssimilation()
            _, uncertainty = assimilator._hybrid_method(background_np, observations_np)
            
            # 转换为可序列化的格式
            uncertainty_serializable = {}
            for var in uncertainty:
                uncertainty_serializable[var] = uncertainty[var].tolist()
            
            print(json.dumps({
                'success': True,
                'data': uncertainty_serializable
            }))
            
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
            
    elif command == 'batch':
        # 批量处理
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少输入数据'
            }))
            return
        
        try:
            input_data = load_input(2)
            batch_data = input_data.get('batch', [])
            results = []
            
            assimilator = BayesianAssimilation()
            
            for item in batch_data:
                background = item.get('background', {})
                observations = item.get('observations', {})
                method = item.get('method', 'hybrid')
                
                # 转换为numpy数组
                background_np = {}
                for var, data in background.items():
                    background_np[var] = np.array(data)
                
                observations_np = {}
                for var, data in observations.items():
                    observations_np[var] = np.array(data)
                
                result = assimilator.assimilate(background_np, observations_np, method)
                results.append(result)
            
            print(json.dumps({
                'success': True,
                'data': results
            }))
            
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
            
    else:
        print(json.dumps({
            'success': False,
            'error': '未知命令'
        }))

if __name__ == "__main__":
    main()