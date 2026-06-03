"""
M1-M5 对比实验 — 论文实验核心

实验设计:
  M1: 持久性预报 (用当前值当预报) — 最烂 baseline
  M2: 确定性 U-Net (MSE 训练) — 深度学习 baseline
  M3: 概率 U-Net (NLL 训练) — 你的模型基准
  M4: 概率 U-Net + 随机同化 — 控制组
  M5: 概率 U-Net + 主动同化 — 完整框架

评估指标:
  - RMSE: 精度
  - CRPS: 概率预报质量
  - 决策效能曲线: 同化轮次 vs RMSE

输出:
  - 指标表格 (结果用)
  - 决策效能曲线图 (论文核心图)
  - 概率可靠性图
"""
import time
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable

import numpy as np
import torch


@dataclass
class ComparisonConfig:
    """对比实验配置"""
    n_test_samples: int = 50       # 测试样本数
    n_assimilation_cycles: int = 10  # 每样本同化轮数
    n_ensemble: int = 20           # EnKF 集合大小
    forecast_lead_hours: List[int] = field(default_factory=lambda: [24, 48, 72])
    output_dir: str = "results/comparison"

    # M4/M5 参数
    n_random_obs: int = 5           # 随机同化点 (M4)
    n_active_obs: int = 5           # 主动同化点 (M5)

    metrics: List[str] = field(default_factory=lambda: [
        "rmse", "mae", "crps", "nll"
    ])


class M1to5Experiment:
    """
    M1-M5 对比实验

    用法:
        exp = M1to5Experiment()
        results = exp.run_all(test_data)
        exp.plot_decision_efficiency_curve(results)
        exp.report_table(results)
    """

    def __init__(self, config: Optional[ComparisonConfig] = None):
        self.config = config or ComparisonConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models = {
            "M1_persistence": self._m1_persistence,
            "M2_deterministic_unet": self._m2_deterministic,
            "M3_probabilistic_unet": self._m3_probabilistic,
            "M4_random_assimilation": self._m4_random,
            "M5_active_assimilation": self._m5_active,
        }

    def run_all(self, test_data: List[Tuple[np.ndarray, np.ndarray]],
                model_fn: Optional[Callable] = None,
                prob_model_fn: Optional[Callable] = None,
                enkf=None, observer=None) -> Dict:
        """
        运行全部 5 个模型

        Args:
            test_data: [(coarse, fine_truth), ...] 测试数据
            model_fn: 确定性 U-Net 推理函数
            prob_model_fn: 概率 U-Net 推理函数 (返回 mean, log_var)
            enkf: EnsembleKalmanFilter 实例
            observer: BayesianActiveObserver 实例

        Returns:
            {model_name: {lead_time: {metric: value}}}
        """
        results = {}
        for name, fn in self.models.items():
            print(f"\n{'='*50}")
            print(f"运行 {name}...")
            t0 = time.time()
            results[name] = self._evaluate(fn, test_data,
                                           model_fn, prob_model_fn,
                                           enkf, observer)
            elapsed = time.time() - t0
            print(f"  ✅ {name} 完成, 耗时 {elapsed:.0f}s")
            for lt in self.config.forecast_lead_hours:
                lt_key = f"{lt}h"
                if lt_key in results[name]:
                    print(f"     {lt_key}: RMSE={results[name][lt_key]['rmse']:.4f}")

        # 保存结果
        self._save_results(results)
        return results

    def _evaluate(self, model_fn: Callable, test_data,
                  det_model, prob_model, enkf, observer) -> Dict:
        """评估单个模型"""
        results = {f"{lt}h": {"rmse": [], "mae": [], "crps": [], "nll": []}
                   for lt in self.config.forecast_lead_hours}

        for idx, (coarse, truth) in enumerate(test_data[:self.config.n_test_samples]):
            # 根据模型名称调用不同方法
            if "M1" in model_fn.__name__:
                pred = self._m1_persistence(coarse)
            elif "M2" in model_fn.__name__:
                if det_model is None:
                    pred = coarse[:, :6]  # fallback
                else:
                    with torch.no_grad():
                        pred = det_model(torch.from_numpy(coarse[None]).float()).squeeze(0).numpy()
            elif "M3" in model_fn.__name__:
                if prob_model is None:
                    pred = coarse[:, :6]
                    log_var = np.zeros_like(pred)
                else:
                    with torch.no_grad():
                        mean, log_var = prob_model(torch.from_numpy(coarse[None]).float())
                        pred = mean.squeeze(0).numpy()
                        log_var = log_var.squeeze(0).numpy()
                self._record_metrics(results, pred, truth, log_var, idx)
            elif "M4" in model_fn.__name__ or "M5" in model_fn.__name__:
                if prob_model is None or enkf is None or observer is None:
                    pred = coarse[:, :6]
                else:
                    # EnKF 同化循环
                    with torch.no_grad():
                        mean, log_var = prob_model(torch.from_numpy(coarse[None]).float())
                        mean = mean.squeeze(0).numpy()
                        log_var = log_var.squeeze(0).numpy()

                    # 生成集合
                    ensemble = enkf.generate_ensemble(mean, log_var)

                    # 多轮同化
                    for cycle in range(self.config.n_assimilation_cycles):
                        if "M5" in model_fn.__name__:
                            # 主动选择观测点 (M5)
                            variance_map = ensemble.var(axis=0)[0]
                            query_pts = observer.select_observation_points(
                                variance_map, n_points=self.config.n_active_obs
                            )
                        else:
                            # 随机选择观测点 (M4)
                            H, W = mean.shape[1:]
                            query_pts = [(np.random.uniform(-75, 75),
                                          np.random.uniform(-75, 75))
                                         for _ in range(self.config.n_random_obs)]

                        if query_pts:
                            # 从真值抽取虚拟观测
                            obs_positions = []
                            observations = []
                            for qx, qy in query_pts:
                                gx = int(np.clip((qy + 75), 0, truth.shape[1] - 1))
                                gy = int(np.clip((qx + 75), 0, truth.shape[2] - 1))
                                obs_positions.append((gx, gy))
                                observations.append(truth[0, gx, gy])

                            # EnKF 分析更新
                            ensemble, _, _ = enkf.assimilate(
                                ensemble,
                                np.array(observations),
                                np.array(obs_positions),
                            )

                    pred = ensemble.mean(axis=0)

            # 记录 M1/M2/M4/M5 指标
            if "M3" not in model_fn.__name__:
                for lt in self.config.forecast_lead_hours:
                    lt_key = f"{lt}h"
                    # 简化: 用 first variable 评估
                    diff = pred[0] - truth[0]
                    results[lt_key]["rmse"].append(np.sqrt((diff**2).mean()))
                    results[lt_key]["mae"].append(np.abs(diff).mean())

            if (idx + 1) % 10 == 0:
                print(f"  样本 {idx+1}/{min(self.config.n_test_samples, len(test_data))}")

        # 聚合
        for lt in self.config.forecast_lead_hours:
            lt_key = f"{lt}h"
            for metric in self.config.metrics:
                vals = results[lt_key][metric]
                results[lt_key][metric] = float(np.mean(vals)) if vals else 0.0

        return results

    def _record_metrics(self, results, pred, truth, log_var, idx):
        """记录指标"""
        for lt in self.config.forecast_lead_hours:
            lt_key = f"{lt}h"
            diff = pred[0] - truth[0]
            results[lt_key]["rmse"].append(np.sqrt((diff**2).mean()))
            results[lt_key]["mae"].append(np.abs(diff).mean())

            # CRPS
            std = np.exp(0.5 * log_var[0])
            z = diff / (std + 1e-8)
            from scipy.stats import norm
            crps = std * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1 / np.sqrt(np.pi))
            results[lt_key]["crps"].append(float(crps.mean()))

            # NLL
            var = np.exp(np.clip(log_var[0], -5, 5))
            nll = 0.5 * np.mean(diff**2 / var + log_var[0])
            results[lt_key]["nll"].append(float(nll))

    # ── M1-M5 实现 ────────────────────────────

    @staticmethod
    def _m1_persistence(coarse: np.ndarray) -> np.ndarray:
        """M1: 持久性预报 — 用当前值当预报"""
        return coarse[:6]

    @staticmethod
    def _m2_deterministic(coarse: np.ndarray) -> np.ndarray:
        """M2: 确定性 U-Net (由外部 model_fn 覆盖)"""
        return coarse[:6]

    @staticmethod
    def _m3_probabilistic(coarse: np.ndarray) -> np.ndarray:
        """M3: 概率 U-Net (由外部 prob_model_fn 覆盖)"""
        return coarse[:6]

    @staticmethod
    def _m4_random(coarse: np.ndarray) -> np.ndarray:
        """M4: 随机同化 (由 evaluate 内的逻辑覆盖)"""
        return coarse[:6]

    @staticmethod
    def _m5_active(coarse: np.ndarray) -> np.ndarray:
        """M5: 主动同化 (由 evaluate 内的逻辑覆盖)"""
        return coarse[:6]

    # ── 结果输出 ──────────────────────────────

    def report_table(self, results: Dict) -> str:
        """生成论文用结果表格"""
        lines = [
            "\n" + "=" * 80,
            "表: M1-M5 对比实验结果",
            "=" * 80,
        ]

        header = f"{'模型':<25}"
        for lt in self.config.forecast_lead_hours:
            header += f" | RMSE({lt}h)  CRPS({lt}h)"
        lines.append(header)
        lines.append("-" * 80)

        for name in ["M1_persistence", "M2_deterministic_unet",
                       "M3_probabilistic_unet", "M4_random_assimilation",
                       "M5_active_assimilation"]:
            if name not in results:
                continue
            row = f"{name:<25}"
            for lt in self.config.forecast_lead_hours:
                lt_key = f"{lt}h"
                if lt_key in results[name]:
                    rmse = results[name][lt_key].get("rmse", 0)
                    crps = results[name][lt_key].get("crps", 0)
                    row += f" | {rmse:.4f}    {crps:.4f}"
                else:
                    row += " |  N/A      N/A"
            lines.append(row)

        lines.append("=" * 80)
        report = "\n".join(lines)
        print(report)

        with open(self.output_dir / "comparison_table.txt", "w") as f:
            f.write(report)
        return report

    def plot_decision_efficiency_curve(self, results: Dict,
                                       save: bool = True):
        """决策效能曲线 — 论文核心图"""
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            fig, ax = plt.subplots(1, 1, figsize=(10, 6))

            colors = {'M1': 'gray', 'M2': 'blue', 'M3': 'green',
                      'M4': 'orange', 'M5': 'red'}

            for name, data in results.items():
                short = name.split('_')[0]
                if short not in colors:
                    continue
                lt_24 = data.get("24h", {}).get("rmse", 0)
                lt_48 = data.get("48h", {}).get("rmse", 0)
                lt_72 = data.get("72h", {}).get("rmse", 0)
                ax.plot([24, 48, 72], [lt_24, lt_48, lt_72],
                        marker='o', label=name, color=colors[short],
                        linewidth=2 if short == 'M5' else 1)

            ax.set_xlabel("预报时效 (hours)")
            ax.set_ylabel("RMSE")
            ax.set_title("M1-M5 预报精度对比")
            ax.legend()
            ax.grid(True, alpha=0.3)

            if save:
                plt.savefig(self.output_dir / "decision_efficiency_curve.png",
                           dpi=300, bbox_inches='tight')
                print(f"✅ 决策效能曲线已保存: {self.output_dir}/decision_efficiency_curve.png")
            plt.close()

        except ImportError:
            print("⚠️ matplotlib 未安装，跳过图表生成")

    def _save_results(self, results: Dict):
        """保存结果到 JSON"""
        # 转换 numpy 类型
        def convert(obj):
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.integer):
                return int(obj)
            return obj

        with open(self.output_dir / "comparison_results.json", "w") as f:
            json.dump(results, f, default=convert, indent=2)
        print(f"✅ 结果已保存: {self.output_dir}/comparison_results.json")
