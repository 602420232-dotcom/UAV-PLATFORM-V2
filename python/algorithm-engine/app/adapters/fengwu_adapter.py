"""
FengWu 气象模型适配器
支持 FengWu v1 (ERA5) 和 v2 (Operational Analysis) 两种模型
数据格式：69x721x1440 (变量x纬度x经度)
"""
import os
import numpy as np
import onnxruntime as ort
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger

# 预加载CUDA DLL（从PyTorch的CUDA库中加载，解决RTX 5070等新GPU兼容性）
def _preload_cuda_dlls():
    """预加载CUDA/cuDNN DLL以支持GPU推理"""
    try:
        import torch
        torch_lib = os.path.join(os.path.dirname(torch.__file__), 'lib')
        if os.path.isdir(torch_lib):
            os.add_dll_directory(torch_lib)
        # onnxruntime 1.21+ 支持 preload_dlls
        if hasattr(ort, 'preload_dlls'):
            ort.preload_dlls()
            logger.info("CUDA DLLs preloaded via onnxruntime.preload_dlls()")
        else:
            logger.info("CUDA DLLs preloaded via os.add_dll_directory()")
    except ImportError:
        logger.debug("PyTorch not available, CUDA preload skipped")

_preload_cuda_dlls()


@dataclass
class FengWuConfig:
    """风乌模型配置"""
    model_path: str              # ONNX模型路径
    data_mean_path: str          # 数据均值路径
    data_std_path: str           # 数据标准差路径
    input_shape: Tuple = (69, 721, 1440)  # 输入形状
    forecast_steps: int = 56     # 预报步数（每步6小时）
    version: str = "v2"          # v1=ERA5, v2=Operational


class FengWuAdapter:
    """风乌气象预报模型适配器"""
    
    # 变量顺序（与论文一致）
    SURFACE_VARS = ['u10', 'v10', 't2m', 'msl']
    PRESSURE_LEVELS = [50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000]
    UPPER_VARS = ['z', 'q', 'u', 'v', 't']
    
    def __init__(self, config: FengWuConfig):
        self.config = config
        self.session = None
        self.data_mean = None
        self.data_std = None
        self._init_model()
        
    def _init_model(self):
        """初始化ONNX运行时"""
        options = ort.SessionOptions()
        options.enable_cpu_mem_arena = False
        options.enable_mem_pattern = False
        options.enable_mem_reuse = False
        options.intra_op_num_threads = 4
        
        cuda_options = {'arena_extend_strategy': 'kSameAsRequested'}
        providers = [
            ('CUDAExecutionProvider', cuda_options),
            'CPUExecutionProvider'
        ]
        
        self.session = ort.InferenceSession(
            self.config.model_path,
            sess_options=options,
            providers=providers
        )
        
        # 加载归一化参数
        self.data_mean = np.load(self.config.data_mean_path)[:, np.newaxis, np.newaxis]
        self.data_std = np.load(self.config.data_std_path)[:, np.newaxis, np.newaxis]
        
        logger.info(f"FengWu {self.config.version} 模型加载完成: {self.config.model_path}")
        
    def normalize(self, data: np.ndarray) -> np.ndarray:
        """数据归一化"""
        return (data - self.data_mean) / self.data_std
        
    def denormalize(self, data: np.ndarray) -> np.ndarray:
        """数据反归一化"""
        return data * self.data_std + self.data_mean
        
    def predict(self, input1: np.ndarray, input2: np.ndarray, 
                steps: Optional[int] = None) -> List[Dict]:
        """
        执行气象预报
        
        Args:
            input1: 第一时刻大气状态 [69, 721, 1440]
            input2: 第二时刻大气状态（6小时后）[69, 721, 1440]
            steps: 预报步数，默认56步（14天）
            
        Returns:
            预报结果列表，每步包含时间戳和各变量场
        """
        steps = steps or self.config.forecast_steps
        
        # 归一化并拼接输入
        input1_norm = self.normalize(input1.astype(np.float32))
        input2_norm = self.normalize(input2.astype(np.float32))
        model_input = np.concatenate((input1_norm, input2_norm), axis=0)[np.newaxis, :, :, :]
        
        results = []
        current_time = datetime.now()
        
        for step in range(steps):
            # ONNX推理
            output = self.session.run(None, {'input': model_input})[0]
            
            # 更新输入：滑动窗口，用后69个变量+新输出
            model_input = np.concatenate((model_input[:, 69:], output[:, :69]), axis=1)
            
            # 反归一化
            forecast = self.denormalize(output[0, :69])
            
            # 计算预报时间（每步6小时）
            forecast_time = current_time + timedelta(hours=6 * (step + 1))
            
            results.append({
                'step': step,
                'forecast_time': forecast_time.isoformat(),
                'lead_time_hours': 6 * (step + 1),
                'data': forecast,
                'variables': self._extract_variables(forecast)
            })
            
            logger.debug(f"FengWu 预报步 {step+1}/{steps} 完成")
            
        return results
        
    def _extract_variables(self, data: np.ndarray) -> Dict:
        """提取各变量场"""
        variables = {}
        
        # 地面变量
        for i, var in enumerate(self.SURFACE_VARS):
            variables[var] = data[i]
            
        # 高空变量
        idx = 4
        for var in self.UPPER_VARS:
            variables[var] = {}
            for level in self.PRESSURE_LEVELS:
                variables[var][f'{level}hPa'] = data[idx]
                idx += 1
                
        return variables
        
    def get_variable_at_level(self, result: Dict, var_name: str, 
                              level: Optional[str] = None) -> np.ndarray:
        """获取指定变量在指定气压层的场"""
        variables = result['variables']
        
        if var_name in self.SURFACE_VARS:
            return variables[var_name]
            
        if level and var_name in variables:
            return variables[var_name].get(level)
            
        raise ValueError(f"变量 {var_name} 或气压层 {level} 不存在")
        
    def get_sichuan_basin_slice(self, result: Dict) -> Dict:
        """
        提取四川盆地区域的数据切片
        四川盆地范围：27-35°N, 102-110°E
        """
        variables = result['variables']
        
        # FengWu全球网格：721x1440 (lat: -90~90, lon: 0~360)
        # lat索引：0=90°N, 360=0°, 720=-90°N
        # lon索引：0=0°, 720=180°E, 1440=360°
        
        lat_start = int((90 - 35) / 180 * 720)  # ~35°N
        lat_end = int((90 - 27) / 180 * 720)    # ~27°N
        lon_start = int(102 / 360 * 1440)       # 102°E
        lon_end = int(110 / 360 * 1440)         # 110°E
        
        basin_data = {}
        for var_name, var_data in variables.items():
            if isinstance(var_data, dict):
                basin_data[var_name] = {}
                for level, data in var_data.items():
                    basin_data[var_name][level] = data[lat_start:lat_end, lon_start:lon_end]
            else:
                basin_data[var_name] = var_data[lat_start:lat_end, lon_start:lon_end]
                
        return {
            'step': result['step'],
            'forecast_time': result['forecast_time'],
            'lead_time_hours': result['lead_time_hours'],
            'lat_range': [35, 27],
            'lon_range': [102, 110],
            'variables': basin_data
        }
