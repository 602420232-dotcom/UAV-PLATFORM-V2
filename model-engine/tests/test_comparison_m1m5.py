"""M1-M5 对比实验测试"""
import numpy as np
from tests.comparison_m1_m5 import M1to5Experiment, ComparisonConfig


def test_m1_persistence():
    """M1: 持久性预报——直接返回当前值"""
    exp = M1to5Experiment(ComparisonConfig(n_test_samples=2))
    coarse = np.random.randn(11, 50, 50)
    truth = np.random.randn(6, 150, 150)
    test_data = [(coarse, truth)]
    results = exp.run_all(test_data)
    assert "M1_persistence" in results


def test_m1_m5_structure():
    """验证所有 5 个模型名称都存在"""
    exp = M1to5Experiment(ComparisonConfig(n_test_samples=1))
    assert "M1_persistence" in exp.models
    assert "M2_deterministic_unet" in exp.models
    assert "M3_probabilistic_unet" in exp.models
    assert "M4_random_assimilation" in exp.models
    assert "M5_active_assimilation" in exp.models


def test_results_output():
    """验证结果包含各预报时效的指标"""
    exp = M1to5Experiment(ComparisonConfig(n_test_samples=1))
    coarse = np.random.randn(11, 50, 50)
    truth = np.random.randn(6, 150, 150)
    test_data = [(coarse, truth)]
    results = exp.run_all(test_data)
    for name in results:
        for lt in exp.config.forecast_lead_hours:
            lt_key = f"{lt}h"
            assert lt_key in results[name], f"{name} 缺 {lt_key}"
            assert "rmse" in results[name][lt_key]
            assert results[name][lt_key]["rmse"] >= 0


def test_report_table():
    """表格生成不崩溃"""
    exp = M1to5Experiment(ComparisonConfig(n_test_samples=1))
    coarse = np.random.randn(11, 50, 50)
    truth = np.random.randn(6, 150, 150)
    test_data = [(coarse, truth)]
    results = exp.run_all(test_data)
    report = exp.report_table(results)
    assert "M1" in report
    assert "M5" in report
    assert "RMSE" in report
