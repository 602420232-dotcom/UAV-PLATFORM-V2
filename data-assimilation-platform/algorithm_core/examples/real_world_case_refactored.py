"""
WRF数据真实案例贝叶斯同化演示（重构版）
展示如何使用贝叶斯同化系统的各个模块
"""

import os
import sys
import logging
import numpy as np
from datetime import datetime

# 设置环境变量
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# 导入核心库模块
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

from bayesian_assimilation import ( # type: ignore
    BayesianAssimilator,
    AssimilationConfig,
    MeteorologicalQualityControl,
    MeteorologicalRiskAssessment,
    TimeSeriesAnalyzer,
    PerformanceMetrics,
    WRFDataAdapter,
    ObservationAdapter
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_wrf_data_mock(file_path=None):
    """
    模拟加载WRF气象数据
    """
    logger.info("="*60)
    logger.info("加载WRF气象数据（模拟）")
    logger.info("="*60)

    nx, ny, nz = 50, 50, 10
    domain_size = (5000, 5000, 1000)

    x = np.linspace(0, domain_size[0], nx)
    y = np.linspace(0, domain_size[1], ny)
    z = np.linspace(0, domain_size[2], nz)

    xx, yy, zz = np.meshgrid(x, y, z, indexing='ij')

    u_wind = 5.0 + 2.0 * np.sin(2 * np.pi * xx / 1000) * np.cos(2 * np.pi * yy / 1000)
    v_wind = 3.0 + 1.5 * np.cos(2 * np.pi * xx / 800) * np.sin(2 * np.pi * yy / 1200)
    temperature = 288.15 - 0.0065 * zz + 2.0 * np.random.randn(nx, ny, nz)

    wind_speed = np.sqrt(u_wind**2 + v_wind**2)

    # 生成模拟降水数据
    precipitation = np.zeros((nx, ny, nz))
    center_x, center_y = domain_size[0] // 2, domain_size[1] // 2
    for i in range(nx):
        for j in range(ny):
            distance = np.sqrt((x[i] - center_x)**2 + (y[j] - center_y)**2)
            if distance < 1000:
                precip_intensity = 20.0 * np.exp(-(distance / 500)**2)
                precipitation[i, j, :] = precip_intensity

    # 使用质量控制模块验证数据
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
        'precipitation': precipitation,
        'domain_size': domain_size
    }


def process_observation_data():
    """
    处理观测数据
    """
    logger.info("\n" + "="*60)
    logger.info("处理气象站观测数据（模拟）")
    logger.info("="*60)

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

        wind_speed_true = 5.0 + 2.0 * np.sin(2 * np.pi * obs_x / 1000) * np.cos(2 * np.pi * obs_y / 1000)
        wind_speed_obs = wind_speed_true + np.random.normal(0, 0.5)

        observations.append(wind_speed_obs)
        obs_locations.append([obs_x, obs_y, obs_z])
        obs_types.append('wind_speed')

        temp_true = 288.15 - 0.0065 * obs_z
        temp_obs = temp_true + np.random.normal(0, 1.0)
        observations.append(temp_obs)
        obs_locations.append([obs_x, obs_y, obs_z])
        obs_types.append('temperature')

        humidity_true = 60.0 - 0.05 * obs_z + 10.0 * np.sin(2 * np.pi * obs_x / 2000)
        humidity_obs = humidity_true + np.random.normal(0, 5.0)
        observations.append(humidity_obs)
        obs_locations.append([obs_x, obs_y, obs_z])
        obs_types.append('humidity')

    # 使用质量控制模块处理观测数据
    observations = np.array(observations)
    obs_locations = np.array(obs_locations)
    obs_types = np.array(obs_types)

    validated_obs, valid_mask = MeteorologicalQualityControl.quality_control_observations(observations, obs_types)

    if len(validated_obs) < len(observations):
        logger.info(f"过滤了 {len(observations) - len(validated_obs)} 个无效观测")
        obs_locations = obs_locations[valid_mask]
        obs_types = obs_types[valid_mask]
    else:
        validated_obs = observations

    logger.info(f"模拟观测数据加载完成")
    logger.info(f"站点数量: {n_stations}")
    logger.info(f"总观测数: {len(validated_obs)}")

    return {
        'observations': validated_obs,
        'obs_locations': obs_locations,
        'obs_types': obs_types,
        'n_stations': n_stations
    }


def run_assimilation(background_data, observation_data):
    """
    执行贝叶斯同化
    """
    logger.info("\n" + "="*60)
    logger.info("执行贝叶斯同化")
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

    # 只使用风速观测数据
    if len(obs_types) == len(observations):
        wind_mask = np.array(obs_types) == 'wind_speed'
        if np.any(wind_mask):
            observations = observations[wind_mask]
            obs_locations = obs_locations[wind_mask]
            logger.info(f"过滤了温度和湿度观测，只使用 {len(observations)} 个风速观测")

    try:
        analysis, variance = assimilator.assimilate_3dvar(
            background, observations, obs_locations
        )

        # 质量控制后处理
        analysis = MeteorologicalQualityControl.validate_wind_speed(analysis)
        analysis = MeteorologicalQualityControl.check_wind_gradient(analysis)

        logger.info(f"同化完成")
        logger.info(f"分析场形状: {analysis.shape}")
        logger.info(f"分析场范围: [{analysis.min():.2f}, {analysis.max():.2f}] m/s")
        logger.info(f"方差范围: [{variance.min():.4f}, {variance.max():.4f}]")

        return {
            'success': True,
            'analysis': analysis,
            'variance': variance,
            'mean_analysis': float(np.mean(analysis)),
            'mean_variance': float(np.mean(variance))
        }

    except Exception as e:
        logger.error(f"同化失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False}


def generate_risk_heatmap(analysis, variance, precipitation_data=None):
    """
    生成风险热力图
    """
    logger.info("\n" + "="*60)
    logger.info("生成气象风险热力图")
    logger.info("="*60)

    # 使用风险评估模块进行综合风险评估
    risk_assessment = MeteorologicalRiskAssessment.composite_risk_assessment(
        analysis, variance, precipitation_data,
        precipitation_duration=3, precipitation_trend=0.1
    )

    # 计算风险区域百分比
    total_points = variance.size
    composite_high_risk = risk_assessment['composite_risk'] >= 3
    composite_risk_percentage = np.sum(composite_high_risk) / total_points * 100

    # 传统基于方差的风险评估
    risk_threshold = variance.mean() + 2 * variance.std()
    high_risk_mask = variance > risk_threshold
    risk_percentage = np.sum(high_risk_mask) / total_points * 100

    logger.info(f"传统风险评估:")
    logger.info(f"  高风险区域: {np.sum(high_risk_mask)} 点 ({risk_percentage:.2f}%)")
    logger.info(f"\n增强版综合风险评估:")
    logger.info(f"  高风险区域: {np.sum(composite_high_risk)} 点 ({composite_risk_percentage:.2f}%)")
    logger.info(f"  最大风险等级: {np.max(risk_assessment['composite_risk'])}")

    return {
        'risk_threshold': risk_threshold,
        'high_risk_mask': high_risk_mask,
        'risk_percentage': risk_percentage,
        'composite_risk': risk_assessment['composite_risk'],
        'wind_risk': risk_assessment['wind_risk'],
        'turbulence_risk': risk_assessment['turbulence_risk'],
        'shear_risk': risk_assessment['shear_risk'],
        'precipitation_risk': risk_assessment['precipitation_risk'],
        'composite_risk_percentage': composite_risk_percentage,
        'vertical_shear': risk_assessment['vertical_shear'],
        'risk_zones': ["低风险: 整体风险可控"] if composite_risk_percentage <= 10 else 
                      ["中等风险: 中等风险区域，需要注意"] if composite_risk_percentage <= 20 else 
                      ["高风险: 高风险区域比例大，建议重新规划路线"]
    }


def save_results(background_data, observation_data, assimilation_result, risk_result, output_dir):
    """
    保存结果到文件
    """
    logger.info("\n" + "="*60)
    logger.info("保存结果")
    logger.info("="*60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    summary_data = {
        'timestamp': timestamp,
        'data_config': {
            'domain_size': list(background_data.get('domain_size', (5000, 5000, 1000))),
            'n_observations': len(observation_data['observations']),
            'n_stations': observation_data['n_stations']
        },
        'assimilation_result': {
            'analysis_shape': list(assimilation_result['analysis'].shape),
            'analysis_range': [float(assimilation_result['analysis'].min()), float(assimilation_result['analysis'].max())],
            'variance_range': [float(assimilation_result['variance'].min()), float(assimilation_result['variance'].max())],
            'mean_analysis': float(assimilation_result.get('mean_analysis', 0)),
            'mean_variance': float(assimilation_result.get('mean_variance', 0))
        },
        'risk_analysis': {
            'risk_threshold': float(risk_result['risk_threshold']),
            'risk_percentage': float(risk_result['risk_percentage']),
            'composite_risk_percentage': float(risk_result['composite_risk_percentage']),
            'max_composite_risk': int(np.max(risk_result['composite_risk'])),
            'risk_zones': risk_result['risk_zones']
        }
    }

    # 保存JSON摘要
    summary_path = os.path.join(output_dir, f'assimilation_summary_{timestamp}.json')
    import json
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    logger.info(f"摘要已保存: {summary_path}")

    # 保存分析场和方差场
    np.save(os.path.join(output_dir, f'analysis_field_{timestamp}.npy'), assimilation_result['analysis'])
    np.save(os.path.join(output_dir, f'variance_field_{timestamp}.npy'), assimilation_result['variance'])
    logger.info(f"分析场和方差场已保存")

    return {
        'summary_path': summary_path,
        'analysis_path': os.path.join(output_dir, f'analysis_field_{timestamp}.npy'),
        'variance_path': os.path.join(output_dir, f'variance_field_{timestamp}.npy')
    }


def main():
    """
    主函数
    """
    logger.info("="*60)
    logger.info("WRF数据真实案例贝叶斯同化演示（重构版）")
    logger.info("="*60)

    # 初始化性能监控
    performance_monitor = PerformanceMetrics()
    performance_monitor.start()

    # 加载数据
    wrf_data = load_wrf_data_mock()
    obs_data = process_observation_data()

    # 执行同化
    assimilation_result = run_assimilation(wrf_data, obs_data)

    if assimilation_result['success']:
        # 风险评估
        precipitation_data = wrf_data.get('precipitation', None)
        risk_result = generate_risk_heatmap(
            assimilation_result['analysis'],
            assimilation_result['variance'],
            precipitation_data
        )

        # 概率风险评估
        probabilistic_result = MeteorologicalRiskAssessment.probabilistic_risk_assessment(
            assimilation_result['analysis'],
            assimilation_result['variance']
        )
        logger.info(f"概率风险评估完成，置信水平: {probabilistic_result['confidence_level']}")

        # 时间序列分析
        time_series = TimeSeriesAnalyzer.generate_time_series_data(wrf_data['domain_size'], n_time_steps=6)
        risk_time_series = []
        
        for time_data in time_series:
            variance = np.random.randn(*time_data['wind_speed'].shape) * 0.5 + 1.0
            variance = np.abs(variance) * (0.1 * time_data['wind_speed'] + 0.5)
            
            time_risk = MeteorologicalRiskAssessment.composite_risk_assessment(
                time_data['wind_speed'], variance
            )
            risk_time_series.append({
                'time_step': time_data['time_step'],
                'composite_risk': time_risk['composite_risk']
            })
        
        trend_data = TimeSeriesAnalyzer.analyze_risk_trend(risk_time_series)
        
        # 检测风险异常
        anomalies = TimeSeriesAnalyzer.detect_risk_anomalies(trend_data)
        if anomalies:
            logger.info("\n检测到风险异常:")
            for anomaly in anomalies:
                logger.info(f"  时间步 {anomaly['time_step']}: 平均风险 {anomaly['mean_risk']:.2f}")
        
        # 风险预测
        predictions = TimeSeriesAnalyzer.advanced_time_series_prediction(trend_data, n_steps=3)
        if predictions:
            logger.info("\n风险趋势预测:")
            for pred in predictions:
                logger.info(f"  时间步 {pred['time_step']}: 预测平均风险 {pred['predicted_mean_risk']:.2f}")

        # 生成风险预警
        risk_alerts = MeteorologicalRiskAssessment.generate_risk_alerts(risk_result)
        if risk_alerts:
            logger.info("\n风险预警:")
            for alert in risk_alerts:
                logger.info(f"  [{alert['level'].upper()}] {alert['message']}")

        # 保存结果
        save_results(wrf_data, obs_data, assimilation_result, risk_result, OUTPUT_DIR)

        # 停止性能监控
        performance_metrics = performance_monitor.stop()
        
        logger.info("\n" + "="*60)
        logger.info("性能监控指标")
        logger.info("="*60)
        for metric, value in performance_metrics.items():
            if isinstance(value, float):
                logger.info(f"{metric}: {value:.2f}")
            else:
                logger.info(f"{metric}: {value}")

        logger.info("\n" + "="*60)
        logger.info("演示完成")
        logger.info("="*60)

        return True
    else:
        logger.error("同化失败，请检查数据和配置")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
