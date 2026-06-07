"""
新旧方法对比测试

传统方法: WRF + EnKF/3D-Var (原项目)
新方法:   CNN订正 + U-Net降尺度 + GPR风险场 (model-engine)


对比维度:
  - 预报精度 (RMSE, MAE)
  - 计算耗时
  - 内存占用
  - 不确定性量化质量
"""
import time
import numpy as np
import torch
from dataclasses import dataclass
from typing import Callable, Dict


@dataclass
class ComparisonMetrics:
    """对比指标"""
    # 精度
    rmse: float = 0.0
    mae: float = 0.0
    bias: float = 0.0
    correlation: float = 0.0

    # 性能
    inference_time_ms: float = 0.0
    peak_memory_mb: float = 0.0

    # 不确定性
    nll_score: float = 0.0  # Negative Log-Likelihood
    reliability: float = 0.0  # 可靠性曲线下面积


class MethodBenchmark:
    """
    方法对比基准

    使用方法:
        benchmark = MethodBenchmark()
        benchmark.run_comparison(test_data)
        benchmark.report()
    """

    def __init__(self):
        self.results: Dict[str, ComparisonMetrics] = {}

    def run_comparison(self, test_data, methods: Dict[str, Callable]):
        """
        运行对比

        Args:
            test_data: (coarse, fine_truth) 测试数据
            methods: {"方法名": 预测函数}
        """
        coarse, truth = test_data
        results = {}

        for name, predict_fn in methods.items():
            metrics = ComparisonMetrics()

            # 推理时间
            t0 = time.perf_counter()
            pred = predict_fn(coarse)
            t1 = time.perf_counter()
            metrics.inference_time_ms = (t1 - t0) * 1000

            # 精度指标
            pred_np = pred.cpu().numpy() if torch.is_tensor(pred) else pred
            truth_np = truth.cpu().numpy() if torch.is_tensor(truth) else truth

            diff = pred_np - truth_np
            metrics.rmse = float(np.sqrt((diff ** 2).mean()))
            metrics.mae = float(np.abs(diff).mean())
            metrics.bias = float(diff.mean())

            # 相关性
            pred_flat = pred_np.ravel()
            truth_flat = truth_np.ravel()
            if np.std(pred_flat) > 1e-8 and np.std(truth_flat) > 1e-8:
                metrics.correlation = float(np.corrcoef(pred_flat, truth_flat)[0, 1])

            results[name] = metrics
            print(f"  [{name}] RMSE={metrics.rmse:.4f}, "
                  f"耗时={metrics.inference_time_ms:.1f}ms, "
                  f"相关={metrics.correlation:.3f}")

        self.results = results
        return results

    def report(self) -> str:
        """生成对比报告"""
        if not self.results:
            return "无对比数据"

        lines = ["\n" + "=" * 60,
                 "新旧方法对比报告",
                 "=" * 60]

        header = f"{'方法':<20} {'RMSE':<10} {'MAE':<10} {'耗时(ms)':<10} {'相关性':<8}"
        lines.append(header)
        lines.append("-" * 60)

        for name, m in sorted(self.results.items()):
            lines.append(
                f"{name:<20} {m.rmse:<10.4f} {m.mae:<10.4f} "
                f"{m.inference_time_ms:<10.1f} {m.correlation:<8.3f}"
            )

        if len(self.results) >= 2:
            names = list(self.results.keys())
            base = self.results[names[0]]
            for name in names[1:
                              ]:
                m = self.results[name]
                improvement = (base.rmse - m.rmse) / base.rmse * 100
                speedup = base.inference_time_ms / m.inference_time_ms
                lines.append("-" * 60)
                lines.append(f"{name}  vs  {names[0]}:")
                lines.append(f"  RMSE 改善: {improvement:+.1f}%")
                lines.append(f"  速度提升: {speedup:.1f}x")

        lines.append("=" * 60)
        return "\n".join(lines)


# ── 合成对比数据 ─────────────────────────────────


def make_comparison_data(n_samples: int = 10) -> list:
    """生成用于对比的测试数据"""
    from data_pipeline.training_data import PhysicsConstrainedGenerator
    gen = PhysicsConstrainedGenerator()
    pairs = []
    for i in range(n_samples):
        coarse, fine = gen.generate_pair(
            ["plain_winter", "summer_heat", "rain_event",
             "mountain_wave", "city_heat_island"][i % 5]
        )
        pairs.append((
            torch.from_numpy(coarse).float().unsqueeze(0),
            torch.from_numpy(fine).float().unsqueeze(0),
        ))
    return pairs


# ── 简易 pytest 集成 ───────────────────────────


def test_comparison_output():
    """集成测试: 确认对比脚本可运行 (不要求精度)"""
    pairs = make_comparison_data(2)
    coarse, truth = pairs[0]

    # 方法1: 原样输出 (noop baseline)

    def method_noop(x):
        return x[:, :6]

    bm = MethodBenchmark()
    bm.run_comparison(
        (coarse, truth),
        {"noop_baseline": method_noop}
    )
    report = bm.report()
    assert "对比报告" in report
    assert "noop_baseline" in report
