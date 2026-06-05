"""
时间序列分析器
提供时间序列生成、趋势分析、异常检测和预测功能
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class TimeSeriesAnalyzer:
    """
    时间序列分析类
    """

    @staticmethod
    def generate_time_series_data(domain_size: tuple, n_time_steps: int = 6) -> list:
        """
        生成时间序列数据

        Args:
            domain_size: 域大小 (x, y, z)
            n_time_steps: 时间步数

        Returns:
            时间序列数据列表
        """
        time_series = []

        for t in range(n_time_steps):
            # 生成随时间变化的风速场
            nx, ny, nz = 50, 50, 10
            x = np.linspace(0, domain_size[0], nx)
            y = np.linspace(0, domain_size[1], ny)
            z = np.linspace(0, domain_size[2], nz)

            xx, yy, zz = np.meshgrid(x, y, z, indexing='ij')

            # 随时间变化的风速模式 - 更真实的时间演变
            time_factor = np.sin(2 * np.pi * t / 12)  # 12小时周期
            # 添加趋势成分
            trend = 0.1 * t
            # 天气系统移动
            system_center_x = domain_size[0] / 2 + 500 * np.sin(2 * np.pi * t / 24)
            system_center_y = domain_size[1] / 2 + 500 * np.cos(2 * np.pi * t / 24)

            # 计算距离天气系统中心的距离
            distance = np.sqrt((xx - system_center_x)**2 + (yy - system_center_y)**2)

            # 基于距离的风速分布
            u_wind = 5.0 + trend + 2.0 * time_factor * np.sin(2 * np.pi * xx / 1000) * np.cos(2 * np.pi * yy / 1000)
            v_wind = 3.0 + trend + 1.5 * time_factor * np.cos(2 * np.pi * xx / 800) * np.sin(2 * np.pi * yy / 1200)
            # 天气系统中心附近风速增强
            system_effect = 3.0 * np.exp(-(distance / 1000)**2)
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

        return time_series

    @staticmethod
    def analyze_risk_trend(risk_time_series: list) -> list:
        """
        分析风险趋势

        Args:
            risk_time_series: 风险时间序列数据

        Returns:
            趋势数据分析结果
        """
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
    def detect_risk_anomalies(trend_data: list, threshold: float = 2.0) -> list:
        """
        检测风险异常

        Args:
            trend_data: 趋势数据
            threshold: 异常检测阈值

        Returns:
            异常列表
        """
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
    def predict_risk_trend(trend_data: list, n_steps: int = 2) -> list:
        """
        预测风险趋势（简单线性预测）

        Args:
            trend_data: 趋势数据
            n_steps: 预测步数

        Returns:
            预测结果列表
        """
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

    @staticmethod
    def advanced_time_series_prediction(trend_data: list, n_steps: int = 3) -> list:
        """
        使用ARIMA模型进行更准确的风险预测

        Args:
            trend_data: 趋势数据
            n_steps: 预测步数

        Returns:
            预测结果列表
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
        except ImportError:
            logger.warning("statsmodels 未安装，使用简单线性预测")
            return TimeSeriesAnalyzer.predict_risk_trend(trend_data, n_steps)

        risks = [item['mean_risk'] for item in trend_data]

        # 检查数据是否足够
        if len(risks) < 5:
            return TimeSeriesAnalyzer.predict_risk_trend(trend_data, n_steps)

        try:
            # 拟合ARIMA模型
            model = ARIMA(risks, order=(2, 1, 1))
            model_fit = model.fit()

            # 预测
            predictions = model_fit.forecast(steps=n_steps)
            return [{
                'time_step': len(risks) + i,
                'predicted_mean_risk': float(max(0, min(4, predictions[i])))
            } for i in range(n_steps)]
        except Exception as e:
            logger.warning(f"ARIMA预测失败: {e}，使用简单线性预测")
            return TimeSeriesAnalyzer.predict_risk_trend(trend_data, n_steps)

    @staticmethod
    def seasonal_risk_analysis(time_series_data: list) -> Optional[Dict[str, Any]]:
        """
        季节性风险分析

        Args:
            time_series_data: 时间序列数据

        Returns:
            季节性分析结果（如果数据足够）
        """
        if len(time_series_data) < 24:  # 至少需要24小时数据
            return None

        # 提取每小时的风险数据
        hourly_risks = [data['mean_risk'] for data in time_series_data]

        # 傅里叶分析检测周期性
        from scipy import fftpack
        fft_result = fftpack.fft(hourly_risks)
        frequencies = fftpack.fftfreq(len(hourly_risks), d=1.0)  # 假设1小时间隔

        # 找到主要周期
        dominant_freq = frequencies[np.argmax(np.abs(fft_result[1:])) + 1]
        dominant_period = 1 / abs(dominant_freq) if dominant_freq != 0 else None

        # 日变化分析
        daily_pattern = []
        for hour in range(24):
            hour_data = [hourly_risks[i] for i in range(hour, len(hourly_risks), 24)]
            if hour_data:
                daily_pattern.append({
                    'hour': hour,
                    'mean_risk': np.mean(hour_data),
                    'std_risk': np.std(hour_data)
                })

        return {
            'dominant_period': dominant_period,
            'daily_pattern': daily_pattern,
            'fft_result': fft_result
        }
