# Type annotations added: 2026-05-08 13:22:43
from typing import Dict, List, Any, Optional, Callable, Tuple

"""Real-world case example (simplified version)
Demonstrates how to process WRF meteorological data and perform Bayesian assimilation
"""

import os

# 去除 TensorFlow/oneDNN 的输出日志
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import numpy as np
import logging
import sys
import json
from datetime import datetime

# 添加 src 目录到路径
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

# 直接导入所需模块，避免触发包的 __init__.py
from bayesian_assimilation.core.assimilator import BayesianAssimilator # type: ignore
from bayesian_assimilation.utils.config import AssimilationConfig # type: ignore

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


class MeteorologicalQualityControl:
    """气象数据质量控制模块"""
    
    @staticmethod
    def validate_wind_speed(wind_speed):
        """验证风速数据"""
        min_wind = 0.0
        max_wind = 83.3  # 300 km/h，台风级风速上限
        
        # 检查异常值
        mask = (wind_speed < min_wind) | (wind_speed > max_wind)
        if np.any(mask):
            count = np.sum(mask)
            logger.warning(f"发现 {count} 个无效风速值，已裁剪到有效范围")
            wind_speed = np.clip(wind_speed, min_wind, max_wind)
        
        return wind_speed
    
    @staticmethod
    def validate_temperature(temperature):
        """验证温度数据"""
        min_temp = 200.0  # 约 -73°C
        max_temp = 330.0  # 约 57°C
        
        mask = (temperature < min_temp) | (temperature > max_temp)
        if np.any(mask):
            count = np.sum(mask)
            logger.warning(f"发现 {count} 个无效温度值，已裁剪到有效范围")
            temperature = np.clip(temperature, min_temp, max_temp)
        
        return temperature
    
    @staticmethod
    def validate_humidity(humidity: str):
        """验证湿度数据"""
        min_humidity = 0.0
        max_humidity = 100.0
        
        mask = (humidity < min_humidity) | (humidity > max_humidity)
        if np.any(mask):
            count = np.sum(mask)
            logger.warning(f"发现 {count} 个无效湿度值，已裁剪到有效范围")
            humidity = np.clip(humidity, min_humidity, max_humidity)
        
        return humidity
    
    @staticmethod
    def detect_outliers(data: Dict[str, Any], threshold=3.0: Any):
        """检测异常值"""
        mean = np.mean(data)
        std = np.std(data)
        outliers = np.abs(data - mean) > threshold * std
        return outliers
    
    @staticmethod
    def check_wind_gradient(wind_speed, max_gradient=5.0):
        """检查风速梯度，检测不合理的风速突变"""
        if wind_speed.ndim != 3:
            return wind_speed
        
        # 计算水平梯度
        gradient_x = np.abs(np.diff(wind_speed, axis=0))
        gradient_y = np.abs(np.diff(wind_speed, axis=1))
        
        # 计算垂直梯度
        gradient_z = np.abs(np.diff(wind_speed, axis=2))
        
        # 检查梯度是否超过阈值
        max_gradient_x = gradient_x.max()
        max_gradient_y = gradient_y.max()
        max_gradient_z = gradient_z.max()
        
        if max_gradient_x > max_gradient or max_gradient_y > max_gradient or max_gradient_z > max_gradient:
            logger.warning(f"风速梯度超过阈值: x={max_gradient_x:.2f}, y={max_gradient_y:.2f}, z={max_gradient_z:.2f} m/s")
            
            # 平滑处理
            from scipy.ndimage import gaussian_filter
            wind_speed = gaussian_filter(wind_speed, sigma=1.0)
            wind_speed = MeteorologicalQualityControl.validate_wind_speed(wind_speed)
        
        return wind_speed
    
    @staticmethod
    def check_time_consistency(time_series_data: float, max_change=10.0: Any):
        """检查时间一致性，确保气象数据随时间合理变化"""
        if len(time_series_data) < 2:
            return time_series_data
        
        for i in range(1, len(time_series_data)):
            current_data = time_series_data[i]['wind_speed']
            previous_data = time_series_data[i-1]['wind_speed']
            
            # 计算时间变化
            time_change = np.abs(current_data - previous_data)
            max_time_change = time_change.max()
            
            if max_time_change > max_change:
                logger.warning(f"检测到时间不一致: 最大变化 {max_time_change:.2f} m/s 超过阈值 {max_change:.2f} m/s")
                
                # 平滑处理
                time_series_data[i]['wind_speed'] = 0.7 * current_data + 0.3 * previous_data
                time_series_data[i]['wind_speed'] = MeteorologicalQualityControl.validate_wind_speed(time_series_data[i]['wind_speed'])
        
        return time_series_data
    
    @staticmethod
    def quality_control_observations(observations, obs_types):
        """质量控制观测数据"""
        validated_obs = []
        valid_mask = []
        
        for i, (obs, obs_type) in enumerate(zip(observations, obs_types)):
            if obs_type == 'wind_speed':
                # 风速质量控制
                if 0 <= obs <= 83.3:
                    validated_obs.append(obs)
                    valid_mask.append(True)
                else:
                    logger.warning(f"无效风速观测值: {obs} m/s，已丢弃")
                    valid_mask.append(False)
            elif obs_type == 'temperature':
                # 温度质量控制（转换为K）
                if 200 <= obs <= 330:
                    validated_obs.append(obs)
                    valid_mask.append(True)
                else:
                    logger.warning(f"无效温度观测值: {obs} K，已丢弃")
                    valid_mask.append(False)
            elif obs_type == 'humidity':
                # 湿度质量控制
                if 0 <= obs <= 100:
                    validated_obs.append(obs)
                    valid_mask.append(True)
                else:
                    logger.warning(f"无效湿度观测值: {obs} %，已丢弃")
                    valid_mask.append(False)
            else:
                validated_obs.append(obs)
                valid_mask.append(True)
        
        return np.array(validated_obs), np.array(valid_mask)


class MeteorologicalRiskAssessment:
    """气象风险评估模块"""
    
    @staticmethod
    def assess_wind_risk(wind_speed):
        """评估风速风险"""
        # 风速风险等级（m/s）
        thresholds = {
            'low': 10.8,      # 6级风
            'moderate': 17.2,  # 8级风
            'high': 24.5,     # 10级风
            'extreme': 32.7   # 12级风
        }
        
        risk_levels = np.zeros_like(wind_speed, dtype=int)
        risk_levels[wind_speed > thresholds['extreme']] = 4
        risk_levels[(wind_speed > thresholds['high']) & (wind_speed <= thresholds['extreme'])] = 3
        risk_levels[(wind_speed > thresholds['moderate']) & (wind_speed <= thresholds['high'])] = 2
        risk_levels[(wind_speed > thresholds['low']) & (wind_speed <= thresholds['moderate'])] = 1
        
        return risk_levels
    
    @staticmethod
    def assess_turbulence_risk(wind_speed, variance):
        """评估湍流风险"""
        # 基于风速和方差的湍流风险评估
        turbulence_index = wind_speed * np.sqrt(variance)
        
        thresholds = {
            'low': 5,      # 低湍流
            'moderate': 15, # 中等湍流
            'high': 25,    # 高湍流
            'extreme': 35   # 极端湍流
        }
        
        risk_levels = np.zeros_like(turbulence_index, dtype=int)
        risk_levels[turbulence_index > thresholds['extreme']] = 4
        risk_levels[(turbulence_index > thresholds['high']) & (turbulence_index <= thresholds['extreme'])] = 3
        risk_levels[(turbulence_index > thresholds['moderate']) & (turbulence_index <= thresholds['high'])] = 2
        risk_levels[(turbulence_index > thresholds['low']) & (turbulence_index <= thresholds['moderate'])] = 1
        
        return risk_levels
    
    @staticmethod
    def assess_shear_risk(vertical_shear):
        """评估垂直风切变风险"""
        # 垂直风切变风险等级（m/s/km）
        thresholds = {
            'low': 2.0,      # 低切变
            'moderate': 4.0,  # 中等切变
            'high': 6.0,     # 高切变
            'extreme': 8.0   # 极端切变
        }
        
        risk_levels = np.zeros_like(vertical_shear, dtype=int)
        risk_levels[vertical_shear > thresholds['extreme']] = 4
        risk_levels[(vertical_shear > thresholds['high']) & (vertical_shear <= thresholds['extreme'])] = 3
        risk_levels[(vertical_shear > thresholds['moderate']) & (vertical_shear <= thresholds['high'])] = 2
        risk_levels[(vertical_shear > thresholds['low']) & (vertical_shear <= thresholds['moderate'])] = 1
        
        return risk_levels
    
    @staticmethod
    def composite_risk_assessment(analysis, variance, wind_speed=None):
        """综合风险评估"""
        if wind_speed is None:
            wind_speed = analysis
        
        # 评估风速风险
        wind_risk = MeteorologicalRiskAssessment.assess_wind_risk(wind_speed)
        
        # 评估湍流风险
        turbulence_risk = MeteorologicalRiskAssessment.assess_turbulence_risk(wind_speed, variance)
        
        # 综合风险（加权平均）
        composite_risk = (0.6 * wind_risk + 0.4 * turbulence_risk).astype(int)
        
        return {
            'wind_risk': wind_risk,
            'turbulence_risk': turbulence_risk,
            'composite_risk': composite_risk
        }


def calculate_vertical_shear(wind_field):
    """计算垂直风切变"""
    # 检查维度
    if wind_field.ndim != 3:
        raise ValueError("Wind field must be 3D (x, y, z)")
    
    # 计算垂直方向的梯度
    vertical_shear = np.zeros_like(wind_field)
    
    # 计算层间风速差
    for z in range(1, wind_field.shape[2]):
        # 计算当前层与上一层的风速差
        shear = np.abs(wind_field[:, :, z] - wind_field[:, :, z-1])
        vertical_shear[:, :, z] = shear
    
    # 第一层设为0
    vertical_shear[:, :, 0] = 0
    
    return vertical_shear


def enhanced_risk_assessment(analysis, variance):
    """增强版风险评估，增加更多气象因素考量"""
    # 风速风险
    wind_risk = MeteorologicalRiskAssessment.assess_wind_risk(analysis)
    
    # 湍流风险
    turbulence_risk = MeteorologicalRiskAssessment.assess_turbulence_risk(analysis, variance)
    
    # 垂直风切变风险
    vertical_shear = calculate_vertical_shear(analysis)
    shear_risk = MeteorologicalRiskAssessment.assess_shear_risk(vertical_shear)
    
    # 综合风险（加权平均）
    composite_risk = (0.5 * wind_risk + 0.3 * turbulence_risk + 0.2 * shear_risk).astype(int)
    
    return {
        'wind_risk': wind_risk,
        'turbulence_risk': turbulence_risk,
        'shear_risk': shear_risk,
        'composite_risk': composite_risk
    }


class TimeSeriesAnalyzer:
    """时间序列分析模块"""
    
    @staticmethod
    def generate_time_series_data(domain_size: int, n_time_steps=6: float):
        """生成时间序列数据"""
        time_series = []
        
        for t in range(n_time_steps):
            # 生成随时间变化的风速场
            nx, ny, nz = 50, 50, 10
            x = np.linspace(0, domain_size[0], nx)
            y = np.linspace(0, domain_size[1], ny)
            z = np.linspace(0, domain_size[2], nz)
            
            xx, yy, zz = np.meshgrid(x, y, z, indexing='ij')
            
            # 随时间变化的风速模式 - 更真实的时间演变
            time_factor = np.sin(2*np.pi*t/12)  # 12小时周期
            # 添加趋势成分
            trend = 0.1 * t
            # 天气系统移动
            system_center_x = domain_size[0] / 2 + 500 * np.sin(2*np.pi*t/24)
            system_center_y = domain_size[1] / 2 + 500 * np.cos(2*np.pi*t/24)
            
            # 计算距离天气系统中心的距离
            distance = np.sqrt((xx - system_center_x)**2 + (yy - system_center_y)**2)
            
            # 基于距离的风速分布
            u_wind = 5.0 + trend + 2.0 * time_factor * np.sin(2*np.pi*xx/1000) * np.cos(2*np.pi*yy/1000)
            v_wind = 3.0 + trend + 1.5 * time_factor * np.cos(2*np.pi*xx/800) * np.sin(2*np.pi*yy/1200)
            # 天气系统中心附近风速增强
            system_effect = 3.0 * np.exp(-(distance/1000)**2)
            u_wind += system_effect
            v_wind += system_effect
            
            wind_speed = np.sqrt(u_wind**2 + v_wind**2)
            
            # 添加一些随机变化
            wind_speed += 0.5 * np.random.randn(nx, ny, nz)
            wind_speed = np.clip(wind_speed, 0, 83.3)
            
            time_series.append({
                'time_step': t,
                'wind_speed': wind_speed,
                'time_factor': time_factor,
                'trend': trend,
                'system_center': (system_center_x, system_center_y)
            })
        
        # 时间一致性检查
        time_series = MeteorologicalQualityControl.check_time_consistency(time_series)
        
        return time_series
    
    @staticmethod
    def analyze_risk_trend(risk_time_series: float):
        """分析风险趋势"""
        trend_data = []
        for i, risk_data in enumerate(risk_time_series):
            trend_data.append({
                'time_step': i,
                'mean_risk': float(np.mean(risk_data['composite_risk'])),
                'max_risk': int(np.max(risk_data['composite_risk'])),
                'high_risk_area': float(np.sum(risk_data['composite_risk'] >= 3) / risk_data['composite_risk'].size * 100),
                'risk_std': float(np.std(risk_data['composite_risk'])),
                'moderate_risk_area': float(np.sum((risk_data['composite_risk'] >= 2) & (risk_data['composite_risk'] < 3)) / risk_data['composite_risk'].size * 100)
            })
        return trend_data
    
    @staticmethod
    def detect_risk_anomalies(trend_data, threshold=2.0):
        """检测风险异常"""
        mean_risks = [item['mean_risk'] for item in trend_data]
        mean = np.mean(mean_risks)
        std = np.std(mean_risks)
        
        anomalies = []
        for i, item in enumerate(trend_data):
            if abs(item['mean_risk'] - mean) > threshold * std:
                anomalies.append({
                    'time_step': i,
                    'mean_risk': item['mean_risk'],
                    'deviation': abs(item['mean_risk'] - mean),
                    'threshold': threshold * std
                })
        return anomalies
    
    @staticmethod
    def predict_risk_trend(trend_data, n_steps=2):
        """预测风险趋势"""
        if len(trend_data) < 3:
            return []
        
        mean_risks = [item['mean_risk'] for item in trend_data]
        
        # 简单线性预测
        x = np.arange(len(mean_risks))
        coefficients = np.polyfit(x, mean_risks, 1)
        polynomial = np.poly1d(coefficients)
        
        predictions = []
        for i in range(n_steps):
            next_step = len(mean_risks) + i
            predicted_risk = float(polynomial(next_step))
            predictions.append({
                'time_step': next_step,
                'predicted_mean_risk': max(0, min(4, predicted_risk))  # 限制在0-4范围内
            })
        
        return predictions


def check_netcdf_available():
    """检查NetCDF是否可用"""
    try:
        from netCDF4 import Dataset
        logger.info("NetCDF4可用，可以读取WRF数据")
        return True
    except ImportError:
        logger.info("NetCDF4未安装，无法读取WRF数据")
        logger.info("安装NetCDF4: pip install netCDF4")
        return False


def load_wrf_data_mock(file_path=None):
    """加载WRF气象数据（模拟数据）"""
    logger.info("="*60)
    logger.info("加载WRF气象数据（模拟数据）")
    logger.info("="*60)

    if file_path and os.path.exists(file_path):
        try:
            from netCDF4 import Dataset
            nc_data = Dataset(file_path, 'r')
            logger.info(f"成功读取WRF文件: {file_path}")
            logger.info(f"维度: {nc_data.dimensions.keys()}")
            logger.info(f"变量: {nc_data.variables.keys()}")

            times = nc_data.variables['XTIME'][:] if 'XTIME' in nc_data.variables else None
            lats = nc_data.variables['XLAT'][:] if 'XLAT' in nc_data.variables else None
            lons = nc_data.variables['XLONG'][:] if 'XLONG' in nc_data.variables else None
            u_wind = nc_data.variables['U'][:] if 'U' in nc_data.variables else None
            v_wind = nc_data.variables['V'][:] if 'V' in nc_data.variables else None
            temperature = nc_data.variables['T'][:] if 'T' in nc_data.variables else None

            nc_data.close()

            return {
                'times': times, 'lats': lats, 'lons': lons,
                'u_wind': u_wind, 'v_wind': v_wind, 'temperature': temperature
            }
        except Exception as e:
            logger.error(f"读取WRF文件失败: {e}")

    logger.info("使用模拟数据演示真实案例流程")

    nx, ny, nz = 50, 50, 10
    domain_size = (5000, 5000, 1000)

    x = np.linspace(0, domain_size[0], nx)
    y = np.linspace(0, domain_size[1], ny)
    z = np.linspace(0, domain_size[2], nz)

    xx, yy, zz = np.meshgrid(x, y, z, indexing='ij')

    u_wind = 5.0 + 2.0 * np.sin(2*np.pi*xx/1000) * np.cos(2*np.pi*yy/1000)
    v_wind = 3.0 + 1.5 * np.cos(2*np.pi*xx/800) * np.sin(2*np.pi*yy/1200)
    temperature = 288.15 - 0.0065 * zz + 2.0 * np.random.randn(nx, ny, nz)

    wind_speed = np.sqrt(u_wind**2 + v_wind**2)
    
    # 质量控制
    wind_speed = MeteorologicalQualityControl.validate_wind_speed(wind_speed)
    temperature = MeteorologicalQualityControl.validate_temperature(temperature)

    logger.info(f"模拟WRF数据加载完成")
    logger.info(f"网格: {nx}x{ny}x{nz}")
    logger.info(f"风速范围: [{wind_speed.min():.2f}, {wind_speed.max():.2f}] m/s")
    logger.info(f"温度范围: [{temperature.min():.2f}, {temperature.max():.2f}] K")

    return {
        'xx': xx, 'yy': yy, 'zz': zz,
        'u_wind': u_wind, 'v_wind': v_wind,
        'wind_speed': wind_speed, 'temperature': temperature,
        'domain_size': domain_size
    }


def process_observation_data(obs_file=None):
    """处理观测数据"""
    logger.info("\n" + "="*60)
    logger.info("处理气象站观测数据（模拟数据）")
    logger.info("="*60)

    if obs_file and os.path.exists(obs_file):
        try:
            import pandas as pd
            obs_data = pd.read_csv(obs_file)
            logger.info(f"成功读取观测文件: {obs_file}")
            logger.info(f"观测数据形状: {obs_data.shape}")
            return obs_data
        except Exception as e:
            logger.error(f"读取观测文件失败: {e}")

    np.random.seed(42)
    n_stations = 20
    domain_size = (5000, 5000, 1000)

    observations = []
    obs_locations = []
    obs_types = []

    for i in range(n_stations):
        obs_x = np.random.uniform(0, domain_size[0])
        obs_y = np.random.uniform(0, domain_size[1])
        obs_z = np.random.uniform(50, 200)

        wind_speed_true = 5.0 + 2.0 * np.sin(2*np.pi*obs_x/1000) * np.cos(2*np.pi*obs_y/1000)
        wind_speed_obs = wind_speed_true + np.random.normal(0, 0.5)

        observations.append(wind_speed_obs)
        obs_locations.append([obs_x, obs_y, obs_z])
        obs_types.append('wind_speed')

        temp_true = 288.15 - 0.0065 * obs_z
        temp_obs = temp_true + np.random.normal(0, 1.0)
        observations.append(temp_obs)
        obs_locations.append([obs_x, obs_y, obs_z])
        obs_types.append('temperature')

        # 添加湿度数据
        humidity_true = 60.0 - 0.05 * obs_z + 10.0 * np.sin(2*np.pi*obs_x/2000)
        humidity_obs = humidity_true + np.random.normal(0, 5.0)
        observations.append(humidity_obs)
        obs_locations.append([obs_x, obs_y, obs_z])
        obs_types.append('humidity')

    # 质量控制
    observations = np.array(observations)
    obs_locations = np.array(obs_locations)
    obs_types = np.array(obs_types)
    
    # 质量控制观测数据
    validated_obs, valid_mask = MeteorologicalQualityControl.quality_control_observations(observations, obs_types)
    
    # 过滤无效观测
    if len(validated_obs) < len(observations):
        logger.info(f"已过滤 {len(observations) - len(validated_obs)} 个无效观测值")
        obs_locations = obs_locations[valid_mask]
        obs_types = obs_types[valid_mask]
    else:
        validated_obs = observations

    logger.info(f"模拟观测数据加载完成")
    logger.info(f"站点数量: {n_stations}")
    logger.info(f"总观测数: {len(validated_obs)}")
    logger.info(f"观测类型: {set(obs_types)}")
    logger.info(f"观测值范围: [{validated_obs.min():.2f}, {validated_obs.max():.2f}]")

    return {
        'observations': validated_obs,
        'obs_locations': obs_locations,
        'obs_types': obs_types,
        'n_stations': n_stations
    }


def run_assimilation(background_data, observation_data):
    """运行贝叶斯同化"""
    logger.info("\n" + "="*60)
    logger.info("正在运行贝叶斯同化")
    logger.info("="*60)

    domain_size = background_data.get('domain_size', (5000, 5000, 1000))

    config = AssimilationConfig(
        domain_size=domain_size,
        target_resolution=100.0,
        background_error_scale=1.5,
        observation_error_scale=0.8
    )

    assimilator = BayesianAssimilator(config)
    assimilator.initialize_grid(domain_size)

    background = background_data.get('wind_speed')
    if background is None:
        background = np.random.randn(51, 51, 11) * 2 + 5

    # 背景场质量控制
    background = MeteorologicalQualityControl.validate_wind_speed(background)

    observations = observation_data['observations']
    obs_locations = observation_data['obs_locations']
    obs_types = observation_data.get('obs_types', [])

    # 只使用风速观测数据，排除温度数据
    if len(obs_types) == len(observations):
        wind_mask = np.array(obs_types) == 'wind_speed'
        if np.any(wind_mask):
            observations = observations[wind_mask]
            obs_locations = obs_locations[wind_mask]
            logger.info(f"已过滤温度观测值，仅使用 {len(observations)} 个风速观测值")

    try:
        analysis, variance = assimilator.assimilate_3dvar(
            background, observations, obs_locations
        )

        # 数据合理性检查和异常值处理
        analysis = MeteorologicalQualityControl.validate_wind_speed(analysis)
        
        # 风速梯度检查
        analysis = MeteorologicalQualityControl.check_wind_gradient(analysis)
        
        # 进一步的合理性检查
        max_analysis_value = analysis.max()
        min_analysis_value = analysis.min()
        
        logger.info(f"同化完成")
        logger.info(f"分析场形状: {analysis.shape}")
        logger.info(f"分析场范围: [{min_analysis_value:.2f}, {max_analysis_value:.2f}] m/s")
        logger.info(f"方差范围: [{variance.min():.4f}, {variance.max():.4f}]")
        
        # 检查每一层的风速范围
        n_layers = analysis.shape[2]
        for i in range(n_layers):
            layer_max = analysis[:, :, i].max()
            layer_min = analysis[:, :, i].min()
            if layer_max > 83.3 or layer_min < 0:
                logger.warning(f"第 {i} 层: 风速范围 [{layer_min:.2f}, {layer_max:.2f}] m/s 超出有效范围")

        variance_fine = assimilator.interpolate_to_path_grid(target_resolution=50.0)
        logger.info(f"降尺度后方差场形状: {variance_fine.shape}")

        return {
            'success': True,
            'analysis': analysis,
            'variance': variance,
            'variance_fine': variance_fine
        }

    except Exception as e:
        logger.error(f"同化失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False}


def generate_risk_heatmap(analysis, variance):
    """生成风险热力图"""
    logger.info("\n" + "="*60)
    logger.info("正在生成气象风险热力图")
    logger.info("="*60)

    # 增强版风险评估
    risk_assessment = enhanced_risk_assessment(analysis, variance)
    
    # 传统基于方差的风险评估
    risk_threshold = variance.mean() + 2 * variance.std()
    high_risk_mask = variance > risk_threshold

    n_high_risk = np.sum(high_risk_mask)
    total_points = variance.size
    risk_percentage = n_high_risk / total_points * 100

    # 基于综合风险的评估
    composite_high_risk = risk_assessment['composite_risk'] >= 3
    composite_risk_percentage = np.sum(composite_high_risk) / total_points * 100

    logger.info(f"传统风险评估:")
    logger.info(f"  高风险区域: {n_high_risk} 个点 ({risk_percentage:.2f}%)")
    logger.info(f"  风险阈值: {risk_threshold:.4f}")
    logger.info(f"  方差范围: [{variance.min():.4f}, {variance.max():.4f}]")
    
    logger.info(f"\n增强型综合风险评估:")
    logger.info(f"  高风险区域: {np.sum(composite_high_risk)} 个点 ({composite_risk_percentage:.2f}%)")
    logger.info(f"  最大风险等级: {np.max(risk_assessment['composite_risk'])}")
    
    # 计算垂直风切变统计
    vertical_shear = calculate_vertical_shear(analysis)
    logger.info(f"\n垂直风切变分析:")
    logger.info(f"  切变范围: [{vertical_shear.min():.2f}, {vertical_shear.max():.2f}] m/s")
    logger.info(f"  平均切变: {vertical_shear.mean():.2f} m/s")
    
    risk_zones = []
    if composite_risk_percentage > 20:
        risk_zones.append("高风险：高风险区域比例较高，建议重新规划路线")
    elif composite_risk_percentage > 10:
        risk_zones.append("中等风险：中等风险区域，需要关注")
    else:
        risk_zones.append("低风险：整体风险可控")

    for zone in risk_zones:
        logger.info(f"  {zone}")

    return {
        'risk_threshold': risk_threshold,
        'high_risk_mask': high_risk_mask,
        'risk_percentage': risk_percentage,
        'composite_risk': risk_assessment['composite_risk'],
        'wind_risk': risk_assessment['wind_risk'],
        'turbulence_risk': risk_assessment['turbulence_risk'],
        'shear_risk': risk_assessment['shear_risk'],
        'composite_risk_percentage': composite_risk_percentage,
        'risk_zones': risk_zones,
        'vertical_shear': vertical_shear
    }


def save_results(background_data, observation_data, assimilation_result, risk_result, output_dir, time_series_data=None):
    """保存结果到文件"""
    logger.info("\n" + "="*60)
    logger.info("正在保存结果")
    logger.info("="*60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    summary_data = {
        'timestamp': timestamp,
        'data_config': {
            'domain_size': list(background_data.get('domain_size', (5000, 5000, 1000))),
            'background_shape': list(background_data.get('wind_speed', np.array([])).shape) if background_data.get('wind_speed') is not None else None,
            'n_observations': len(observation_data['observations']),
            'n_stations': observation_data['n_stations']
        },
        'assimilation_result': {
            'analysis_shape': list(assimilation_result['analysis'].shape),
            'analysis_range': [float(assimilation_result['analysis'].min()), float(assimilation_result['analysis'].max())],
            'variance_range': [float(assimilation_result['variance'].min()), float(assimilation_result['variance'].max())]
        },
        'risk_analysis': {
            'risk_threshold': float(risk_result['risk_threshold']),
            'risk_percentage': float(risk_result['risk_percentage']),
            'composite_risk_percentage': float(risk_result['composite_risk_percentage']),
            'high_risk_points': int(np.sum(risk_result['high_risk_mask'])),
            'max_composite_risk': int(np.max(risk_result['composite_risk'])),
            'risk_zones': risk_result['risk_zones']
        }
    }

    summary_path = os.path.join(output_dir, f'assimilation_summary_{timestamp}.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    logger.info(f"摘要已保存: {summary_path}")

    analysis_path = os.path.join(output_dir, f'analysis_field_{timestamp}.npy')
    np.save(analysis_path, assimilation_result['analysis'])
    logger.info(f"分析场已保存: {analysis_path}")

    variance_path = os.path.join(output_dir, f'variance_field_{timestamp}.npy')
    np.save(variance_path, assimilation_result['variance'])
    logger.info(f"方差场已保存: {variance_path}")

    obs_data = {
        'observations': observation_data['observations'].tolist(),
        'obs_locations': observation_data['obs_locations'].tolist(),
        'obs_types': observation_data['obs_types'].tolist()
    }
    obs_path = os.path.join(output_dir, f'observation_data_{timestamp}.json')
    with open(obs_path, 'w', encoding='utf-8') as f:
        json.dump(obs_data, f, indent=2)
    logger.info(f"观测数据已保存: {obs_path}")

    if HAS_MATPLOTLIB and plt is not None:
        try:
            # 风险热力图
            fig, axes = plt.subplots(3, 3, figsize=(18, 15))

            mid_z = assimilation_result['analysis'].shape[2] // 2

            # 分析场
            im1 = axes[0, 0].imshow(assimilation_result['analysis'][:, :, mid_z], cmap='viridis', origin='lower')
            axes[0, 0].set_title('分析场 (中间层)', fontsize=12, fontweight='bold')
            axes[0, 0].set_xlabel('X', fontsize=10)
            axes[0, 0].set_ylabel('Y', fontsize=10)
            plt.colorbar(im1, ax=axes[0, 0], label='风速 (m/s)')

            # 方差场
            im2 = axes[0, 1].imshow(assimilation_result['variance'][:, :, mid_z], cmap='hot', origin='lower')
            axes[0, 1].set_title('方差场 (中间层)', fontsize=12, fontweight='bold')
            axes[0, 1].set_xlabel('X', fontsize=10)
            axes[0, 1].set_ylabel('Y', fontsize=10)
            plt.colorbar(im2, ax=axes[0, 1], label='方差')

            # 垂直风切变
            im3 = axes[0, 2].imshow(risk_result.get('vertical_shear', np.zeros_like(assimilation_result['analysis']))[:, :, mid_z], cmap='coolwarm', origin='lower')
            axes[0, 2].set_title('垂直风切变', fontsize=12, fontweight='bold')
            axes[0, 2].set_xlabel('X', fontsize=10)
            axes[0, 2].set_ylabel('Y', fontsize=10)
            plt.colorbar(im3, ax=axes[0, 2], label='切变 (m/s)')

            # 传统高风险区域
            im4 = axes[1, 0].imshow(risk_result['high_risk_mask'][:, :, mid_z].astype(int), cmap='Reds', origin='lower')
            axes[1, 0].set_title('传统高风险区域', fontsize=12, fontweight='bold')
            axes[1, 0].set_xlabel('X', fontsize=10)
            axes[1, 0].set_ylabel('Y', fontsize=10)
            plt.colorbar(im4, ax=axes[1, 0], label='风险')

            # 综合风险
            im5 = axes[1, 1].imshow(risk_result['composite_risk'][:, :, mid_z], cmap='RdYlGn_r', origin='lower', vmin=0, vmax=4)
            axes[1, 1].set_title('综合风险 (0-4)', fontsize=12, fontweight='bold')
            axes[1, 1].set_xlabel('X', fontsize=10)
            axes[1, 1].set_ylabel('Y', fontsize=10)
            plt.colorbar(im5, ax=axes[1, 1], label='风险等级')

            # 风速风险
            im6 = axes[1, 2].imshow(risk_result['wind_risk'][:, :, mid_z], cmap='RdYlGn_r', origin='lower', vmin=0, vmax=4)
            axes[1, 2].set_title('风速风险 (0-4)', fontsize=12, fontweight='bold')
            axes[1, 2].set_xlabel('X', fontsize=10)
            axes[1, 2].set_ylabel('Y', fontsize=10)
            plt.colorbar(im6, ax=axes[1, 2], label='风险等级')

            # 湍流风险
            im7 = axes[2, 0].imshow(risk_result['turbulence_risk'][:, :, mid_z], cmap='RdYlGn_r', origin='lower', vmin=0, vmax=4)
            axes[2, 0].set_title('湍流风险 (0-4)', fontsize=12, fontweight='bold')
            axes[2, 0].set_xlabel('X', fontsize=10)
            axes[2, 0].set_ylabel('Y', fontsize=10)
            plt.colorbar(im7, ax=axes[2, 0], label='风险等级')

            # 垂直风切变风险
            im8 = axes[2, 1].imshow(risk_result['shear_risk'][:, :, mid_z], cmap='RdYlGn_r', origin='lower', vmin=0, vmax=4)
            axes[2, 1].set_title('垂直风切变风险 (0-4)', fontsize=12, fontweight='bold')
            axes[2, 1].set_xlabel('X', fontsize=10)
            axes[2, 1].set_ylabel('Y', fontsize=10)
            plt.colorbar(im8, ax=axes[2, 1], label='风险等级')

            # 空面板
            axes[2, 2].axis('off')

            plt.tight_layout()

            fig_path = os.path.join(output_dir, f'risk_heatmap_{timestamp}.png')
            plt.savefig(fig_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"风险热力图已保存: {fig_path}")

            # 时间序列分析图
            if time_series_data:
                # 分离实际数据和预测数据
                actual_data = [item for item in time_series_data if 'predicted' not in item or not item['predicted']]
                predicted_data = [item for item in time_series_data if 'predicted' in item and item['predicted']]
                
                fig2, axes2 = plt.subplots(3, 1, figsize=(12, 12))
                
                # 实际数据
                actual_time_steps = [item['time_step'] for item in actual_data]
                actual_mean_risks = [item['mean_risk'] for item in actual_data]
                actual_max_risks = [item['max_risk'] for item in actual_data]
                actual_high_risk_areas = [item['high_risk_area'] for item in actual_data]
                actual_moderate_risk_areas = [item.get('moderate_risk_area', 0) for item in actual_data]
                
                # 预测数据
                predicted_time_steps = [item['time_step'] for item in predicted_data]
                predicted_mean_risks = [item['mean_risk'] for item in predicted_data]
                
                # 风险水平趋势
                axes2[0].plot(actual_time_steps, actual_mean_risks, 'b-o', label='平均风险 (实际)', linewidth=2)
                axes2[0].plot(actual_time_steps, actual_max_risks, 'r-s', label='最大风险 (实际)', linewidth=2)
                if predicted_data:
                    axes2[0].plot(predicted_time_steps, predicted_mean_risks, 'b--o', label='平均风险 (预测)', linewidth=2, alpha=0.7)
                axes2[0].set_title('风险水平随时间变化趋势', fontsize=12, fontweight='bold')
                axes2[0].set_xlabel('时间步', fontsize=10)
                axes2[0].set_ylabel('风险等级', fontsize=10)
                axes2[0].legend()
                axes2[0].grid(True, alpha=0.3)
                
                # 风险区域百分比
                axes2[1].plot(actual_time_steps, actual_high_risk_areas, 'g-^', label='高风险区域 (%)', linewidth=2)
                axes2[1].plot(actual_time_steps, actual_moderate_risk_areas, 'y-^', label='中等风险区域 (%)', linewidth=2)
                axes2[1].set_title('风险区域百分比随时间变化', fontsize=12, fontweight='bold')
                axes2[1].set_xlabel('时间步', fontsize=10)
                axes2[1].set_ylabel('百分比 (%)', fontsize=10)
                axes2[1].legend()
                axes2[1].grid(True, alpha=0.3)
                
                # 风险标准差
                if 'risk_std' in actual_data[0]:
                    actual_risk_std = [item['risk_std'] for item in actual_data]
                    axes2[2].plot(actual_time_steps, actual_risk_std, 'purple', marker='*', label='风险标准差', linewidth=2)
                    axes2[2].set_title('风险变异性随时间变化', fontsize=12, fontweight='bold')
                    axes2[2].set_xlabel('时间步', fontsize=10)
                    axes2[2].set_ylabel('标准差', fontsize=10)
                    axes2[2].legend()
                    axes2[2].grid(True, alpha=0.3)
                
                plt.tight_layout()
                time_series_path = os.path.join(output_dir, f'risk_time_series_{timestamp}.png')
                plt.savefig(time_series_path, dpi=150, bbox_inches='tight')
                plt.close(fig2)
                logger.info(f"风险时间序列图已保存: {time_series_path}")

        except Exception as e:
            logger.error(f"保存图像失败: {e}")

    logger.info(f"所有结果已保存到: {output_dir}")

    return {
        'summary_path': summary_path,
        'analysis_path': analysis_path,
        'variance_path': variance_path,
        'obs_path': obs_path
    }


def main():
    """主函数"""
    logger.info("="*60)
    logger.info("WRF数据真实案例贝叶斯同化演示")
    logger.info("="*60)

    check_netcdf_available()

    wrf_data = load_wrf_data_mock()
    obs_data = process_observation_data()

    assimilation_result = run_assimilation(wrf_data, obs_data)

    if assimilation_result['success']:
        risk_result = generate_risk_heatmap(
            assimilation_result['analysis'],
            assimilation_result['variance']
        )

        # 生成时间序列数据并分析
        time_series = TimeSeriesAnalyzer.generate_time_series_data(wrf_data['domain_size'], n_time_steps=12)  # 增加时间步长
        risk_time_series = []
        
        for time_data in time_series:
            # 生成更合理的方差场
            variance = np.random.randn(*time_data['wind_speed'].shape) * 0.5 + 1.0
            # 方差与风速相关
            variance = np.abs(variance) * (0.1 * time_data['wind_speed'] + 0.5)
            
            time_risk = MeteorologicalRiskAssessment.composite_risk_assessment(
                time_data['wind_speed'], 
                variance
            )
            risk_time_series.append({
                'time_step': time_data['time_step'],
                'composite_risk': time_risk['composite_risk'],
                'wind_risk': time_risk['wind_risk'],
                'turbulence_risk': time_risk['turbulence_risk']
            })
        
        trend_data = TimeSeriesAnalyzer.analyze_risk_trend(risk_time_series)
        
        # 检测风险异常
        anomalies = TimeSeriesAnalyzer.detect_risk_anomalies(trend_data)
        if anomalies:
            logger.info("\n检测到风险异常:")
            for anomaly in anomalies:
                logger.info(f"  时间步 {anomaly['time_step']}: 平均风险 {anomaly['mean_risk']:.2f}, 偏差 {anomaly['deviation']:.2f}")
        
        # 预测风险趋势
        predictions = TimeSeriesAnalyzer.predict_risk_trend(trend_data, n_steps=3)
        if predictions:
            logger.info("\n风险趋势预测:")
            for pred in predictions:
                logger.info(f"  时间步 {pred['time_step']}: 预测平均风险 {pred['predicted_mean_risk']:.2f}")
        
        # 扩展趋势数据，包含预测结果
        extended_trend_data = trend_data.copy()
        for pred in predictions:
            extended_trend_data.append({
                'time_step': pred['time_step'],
                'mean_risk': pred['predicted_mean_risk'],
                'max_risk': 4,  # 预测最大值
                'high_risk_area': 0.0,
                'risk_std': 0.0,
                'moderate_risk_area': 0.0,
                'predicted': True
            })
        
        save_results(wrf_data, obs_data, assimilation_result, risk_result, OUTPUT_DIR, extended_trend_data)

        logger.info("\n" + "="*60)
        logger.info("案例分析结果")
        logger.info("="*60)
        logger.info(f"同化分析完成")
        logger.info(f"风险热力图已生成")
        logger.info(f"识别到 {len(risk_result['risk_zones'])} 个风险区域")
        logger.info(f"综合风险百分比: {risk_result['composite_risk_percentage']:.2f}%")

        logger.info("\n" + "="*60)
        logger.info("下一步操作")
        logger.info("="*60)
        logger.info("1. 根据风险热力图调整飞行路线")
        logger.info("2. 避开高风险区域")
        logger.info("3. 重新规划路径")
        logger.info("4. 持续气象监测")
    else:
        logger.error("同化失败，请检查数据和配置")

    logger.info("\n" + "="*60)
    logger.info("演示完成")
    logger.info("="*60)

    return assimilation_result.get('success', False)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)