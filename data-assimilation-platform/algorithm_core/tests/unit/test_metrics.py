"""
性能指标模块单元测试
"""
import logging
import os
import sys
import time

import pytest
import numpy as np

logger = logging.getLogger(__name__)


SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_PATH = os.path.join(SRC_DIR, 'src')


if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


from bayesian_assimilation.utils.metrics import (  # noqa: E402
    PerformanceMetrics,
    DataQualityMetrics,
    AssimilationMetrics,
    generate_performance_report
)


@pytest.mark.unit
class TestPerformanceMetrics:
    """性能指标测试类"""

    def test_init(self):
        """测试初始化"""
        metrics = PerformanceMetrics()

        assert metrics is not None
        assert metrics.start_time > 0
        assert isinstance(metrics.metrics, dict)

    def test_start_stop(self):
        """测试开始和停止"""
        metrics = PerformanceMetrics()

        metrics.start()
        time.sleep(0.01)  # 等待一小段时间
        result = metrics.stop()

        assert 'execution_time_seconds' in result
        assert result['execution_time_seconds'] > 0

    def test_get_metrics_empty(self):
        """测试获取空指标"""
        metrics = PerformanceMetrics()

        result = metrics.get_metrics()

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_get_metrics_after_stop(self, assimilation_result):
        """测试停止后获取指标"""
        # 这个测试主要用于验证metrics对象正常工作
        metrics = PerformanceMetrics()
        metrics.stop()

        result = metrics.get_metrics()

        assert 'execution_time_seconds' in result


@pytest.mark.unit
class TestDataQualityMetrics:
    """数据质量指标测试类"""

    def test_calculate_mean(self):
        """测试计算平均值"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        result = DataQualityMetrics.calculate_mean(data)

        assert result == 3.0

    def test_calculate_std(self):
        """测试计算标准差"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        result = DataQualityMetrics.calculate_std(data)

        assert result > 0

    def test_calculate_min(self):
        """测试计算最小值"""
        data = np.array([5.0, 3.0, 1.0, 4.0, 2.0])

        result = DataQualityMetrics.calculate_min(data)

        assert result == 1.0

    def test_calculate_max(self):
        """测试计算最大值"""
        data = np.array([5.0, 3.0, 1.0, 4.0, 2.0])

        result = DataQualityMetrics.calculate_max(data)

        assert result == 5.0

    def test_calculate_range(self):
        """测试计算值域"""
        data = np.array([1.0, 5.0, 3.0, 2.0, 4.0])

        result = DataQualityMetrics.calculate_range(data)

        assert result == 4.0

    def test_calculate_valid_ratio(self):
        """测试计算有效值比例"""
        data = np.array([1.0, 2.0, np.nan, 4.0, np.inf])

        result = DataQualityMetrics.calculate_valid_ratio(data)

        # 5个元素中有3个有效值
        assert result == 0.6

    def test_calculate_outlier_ratio(self):
        """测试计算异常值比例"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 100.0])

        result = DataQualityMetrics.calculate_outlier_ratio(data, threshold=2.0)

        assert result > 0  # 100.0 是异常值

    def test_calculate_correlation(self):
        """测试计算相关系数"""
        data1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        data2 = np.array([2.0, 4.0, 6.0, 8.0, 10.0])

        result = DataQualityMetrics.calculate_correlation(data1, data2)

        # 完美正相关
        assert abs(result - 1.0) < 0.001

    def test_calculate_correlation_mismatched_shapes(self):
        """测试形状不匹配"""
        data1 = np.array([1.0, 2.0, 3.0])
        data2 = np.array([1.0, 2.0])

        result = DataQualityMetrics.calculate_correlation(data1, data2)

        assert result == 0.0

    def test_compute_all(self):
        """测试计算所有指标"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        result = DataQualityMetrics.compute_all(data, name='test')

        assert 'test_mean' in result
        assert 'test_std' in result
        assert 'test_min' in result
        assert 'test_max' in result
        assert 'test_range' in result
        assert 'test_valid_ratio' in result
        assert 'test_outlier_ratio' in result


@pytest.mark.unit
class TestAssimilationMetrics:
    """同化指标测试类"""

    def test_calculate_analysis_improvement(self):
        """测试分析场改进度"""
        background = np.random.randn(10, 10, 5)
        analysis = np.random.randn(10, 10, 5) * 0.5  # 标准差更小

        result = AssimilationMetrics.calculate_analysis_improvement(background, analysis)

        assert result >= -1.0  # 可能在某些情况下为负

    def test_calculate_spread_reduction(self):
        """测试方差减少率"""
        background = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        analysis = np.array([2.0, 2.5, 3.0, 3.5, 4.0])

        result = AssimilationMetrics.calculate_spread_reduction(background, analysis)

        # analysis方差更小，应该是正数
        assert result >= 0

    def test_calculate_spread_reduction_zero_variance(self):
        """测试零方差情况"""
        background = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        analysis = np.array([1.0, 1.0, 1.0, 1.0, 1.0])

        result = AssimilationMetrics.calculate_spread_reduction(background, analysis)

        assert result == 0.0

    def test_compute_all(self, assimilation_result):
        """测试计算所有同化指标"""
        background = assimilation_result['background']
        analysis = assimilation_result['analysis']
        variance = assimilation_result['variance']

        result = AssimilationMetrics.compute_all(background, analysis, variance)

        assert 'analysis_improvement' in result
        assert 'spread_reduction' in result
        assert 'mean_analysis' in result
        assert 'mean_variance' in result
        assert 'max_variance' in result
        assert 'min_variance' in result


@pytest.mark.unit
class TestPerformanceReport:
    """性能报告测试类"""

    def test_generate_report(self):
        """测试生成性能报告"""
        metrics = {
            'execution_time_seconds': 1.5,
            'memory_usage_mb': 100.5,
            'cpu_usage_percent': 50.0
        }

        report = generate_performance_report(metrics)

        assert 'execution_time_seconds: 1.50' in report
        assert 'memory_usage_mb: 100.50' in report
        assert 'cpu_usage_percent: 50.00' in report

    def test_generate_report_with_non_float(self):
        """测试生成包含非浮点值的报告"""
        metrics = {
            'name': 'test',
            'count': 10,
            'rate': 0.95
        }

        report = generate_performance_report(metrics)

        assert 'name: test' in report
        assert 'count: 10' in report
        assert 'rate: 0.95' in report
