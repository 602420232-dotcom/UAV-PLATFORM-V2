"""智能算法调度器 - 根据任务特征自动选择最优同化算法。

本模块实现了 SmartAlgorithmScheduler 类，基于决策树策略为数据同化任务
自动匹配最合适的算法。决策依据包括：网格规模、观测数量、时间预算、
GPU 可用性、是否需要风险场/概率输出等条件。

设计参考：docs/5dvar-implementation-and-algorithm-orchestration.md 中的
AlgorithmScheduler 章节。
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 算法 ID 常量
# ---------------------------------------------------------------------------
ALGORITHM_5DVAR = "5dvar"
ALGORITHM_4DVAR_GPU = "4dvar-gpu"
ALGORITHM_4DVAR = "4dvar"
ALGORITHM_ENKF = "enkf"
ALGORITHM_HYBRID = "hybrid_assimilation"
ALGORITHM_3DVAR = "3dvar"
ALGORITHM_ADAPTIVE_HYBRID = "adaptive_hybrid"

# ---------------------------------------------------------------------------
# 决策树阈值
# ---------------------------------------------------------------------------
_LARGE_GRID_THRESHOLD = 100  # grid_size > 100x100 时考虑 4DVAR GPU
_MANY_OBSERVATIONS_THRESHOLD = 50  # observation_count > 50 时考虑 EnKF
_MODERATE_OBSERVATIONS_THRESHOLD = 20  # observation_count > 20 时考虑 Hybrid
_ENKF_TIME_BUDGET_SECONDS = 30.0  # EnKF 需要的时间预算下限
_FAST_TIME_BUDGET_SECONDS = 10.0  # 3DVAR 快速路径的时间预算上限


class SmartAlgorithmScheduler:
    """智能算法调度器 - 根据任务特征自动选择最优同化算法。

    决策树（按优先级从高到低）：

    1. 有 ``risk_field`` 参数 + 需要 ``risk_cost``  -> **5dvar**
    2. ``grid_size`` > 100x100 且有 GPU              -> **4dvar-gpu**
       （当前 GPU 版本不可用时回退到普通 **4dvar**）
    3. ``observation_count`` > 50 且 ``time_budget`` > 30s -> **enkf**
    4. ``observation_count`` > 20                     -> **hybrid_assimilation**
    5. ``observation_count`` <= 20 且 ``time_budget`` < 10s -> **3dvar**
    6. 需要 probabilistic 输出                        -> **enkf** + adaptive_variance_field
    7. 默认                                           -> **adaptive_hybrid**

    使用示例::

        scheduler = SmartAlgorithmScheduler()
        result = scheduler.select_algorithm(
            params={"risk_field": ...},
            grid_shape=(120, 120),
            observation_count=60,
            time_budget_seconds=45.0,
            require_risk_aware=True,
        )
        print(result["algorithm_id"])   # "5dvar"
        print(result["reason"])
    """

    def __init__(self) -> None:
        self._last_decision: list[dict[str, str]] = []

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def select_algorithm(
        self,
        params: dict[str, Any],
        grid_shape: tuple[int, ...] | None = None,
        observation_count: int | None = None,
        time_budget_seconds: float | None = None,
        require_probabilistic: bool = False,
        require_risk_aware: bool = False,
        gpu_available: bool = False,
    ) -> dict[str, Any]:
        """根据输入条件自动选择最优同化算法。

        Parameters
        ----------
        params:
            算法参数字典。调度器会检查其中是否包含 ``risk_field``、
            ``risk_cost`` 等关键字段以辅助决策。
        grid_shape:
            背景场的网格形状，如 ``(nx, ny)`` 或 ``(nz, nx, ny)``。
            为 ``None`` 时无法进行网格规模判断。
        observation_count:
            可用观测数量。为 ``None`` 时视为未知。
        time_budget_seconds:
            允许的最大执行时间（秒）。为 ``None`` 时视为无限制。
        require_probabilistic:
            是否需要概率性输出（集合/方差场）。
        require_risk_aware:
            是否需要风险感知能力（飞行风险代价）。
        gpu_available:
            当前是否有可用的 GPU 资源。

        Returns
        -------
        dict
            包含三个键：

            - ``algorithm_id`` (str): 选中的算法标识符
            - ``reason`` (str): 选择该算法的文本说明
            - ``config_overrides`` (dict): 建议传递给算法的额外配置覆盖
        """
        # 重置决策记录
        self._last_decision = []

        # ---- 从 params 中提取辅助信息 ----
        has_risk_field = "risk_field" in params or "risk_cost" in params

        # ---- 计算网格总元素数 ----
        grid_total = self._compute_grid_total(grid_shape)

        # ---- 决策树（按优先级从高到低） ----

        # 规则 1: 风险感知 -> 5DVAR
        if require_risk_aware and has_risk_field:
            self._record(
                "risk_aware",
                "命中",
                "需要风险场 + 存在 risk_field 参数",
                selected_algorithm=ALGORITHM_5DVAR,
            )
            return self._make_result(
                algorithm_id=ALGORITHM_5DVAR,
                reason=(
                    "任务需要风险感知能力，且输入参数中包含 risk_field / risk_cost，选择 5D-VAR（含风险代价项 J_risk）"
                ),
                config_overrides={
                    "enable_risk_cost": True,
                    "risk_field": params.get("risk_field"),
                    "risk_cost_weight": params.get("risk_cost", 1.0),
                },
            )
        self._record("risk_aware", "未命中", "不需要风险感知 或 缺少 risk_field 参数")

        # 规则 2: 大网格 + GPU -> 4DVAR-GPU（回退到 4DVAR）
        if grid_total is not None and grid_total > _LARGE_GRID_THRESHOLD**2:
            if gpu_available:
                self._record(
                    "large_grid_gpu",
                    "命中",
                    f"网格 {grid_total} > {_LARGE_GRID_THRESHOLD}^2 且 GPU 可用",
                    selected_algorithm=ALGORITHM_4DVAR_GPU,
                )
                return self._make_result(
                    algorithm_id=ALGORITHM_4DVAR_GPU,
                    reason=(
                        f"网格规模较大（总元素 {grid_total} > "
                        f"{_LARGE_GRID_THRESHOLD}x{_LARGE_GRID_THRESHOLD}），"
                        f"且 GPU 可用，选择 4D-VAR GPU 加速版"
                    ),
                    config_overrides={
                        "use_gpu": True,
                        "grid_shape": grid_shape,
                    },
                )
            else:
                self._record(
                    "large_grid_gpu",
                    "部分命中",
                    f"网格 {grid_total} > {_LARGE_GRID_THRESHOLD}^2 但 GPU 不可用，回退到 4DVAR",
                    selected_algorithm=ALGORITHM_4DVAR,
                )
                return self._make_result(
                    algorithm_id=ALGORITHM_4DVAR,
                    reason=(
                        f"网格规模较大（总元素 {grid_total} > "
                        f"{_LARGE_GRID_THRESHOLD}x{_LARGE_GRID_THRESHOLD}），"
                        f"但 GPU 不可用，回退到标准 4D-VAR"
                    ),
                    config_overrides={
                        "use_gpu": False,
                        "grid_shape": grid_shape,
                    },
                )
        self._record("large_grid_gpu", "未命中", "网格规模未超过阈值")

        # 规则 3: 大量观测 + 充裕时间 -> EnKF
        if observation_count is not None and observation_count > _MANY_OBSERVATIONS_THRESHOLD:
            if time_budget_seconds is None or time_budget_seconds > _ENKF_TIME_BUDGET_SECONDS:
                self._record(
                    "many_obs_enkf",
                    "命中",
                    f"观测数 {observation_count} > {_MANY_OBSERVATIONS_THRESHOLD}，时间预算充足",
                    selected_algorithm=ALGORITHM_ENKF,
                )
                return self._make_result(
                    algorithm_id=ALGORITHM_ENKF,
                    reason=(
                        f"观测数量充足（{observation_count} > {_MANY_OBSERVATIONS_THRESHOLD}），"
                        f"且时间预算"
                        f"{'无限制' if time_budget_seconds is None else f'{time_budget_seconds}s'}"
                        f"{'>' if time_budget_seconds else '>='}{_ENKF_TIME_BUDGET_SECONDS}s，"
                        f"选择 EnKF（集合卡尔曼滤波）以充分利用观测信息"
                    ),
                    config_overrides={
                        "ensemble_size": min(observation_count, 100),
                    },
                )
            else:
                self._record(
                    "many_obs_enkf",
                    "未命中",
                    f"观测数 {observation_count} > {_MANY_OBSERVATIONS_THRESHOLD} "
                    f"但时间预算 {time_budget_seconds}s 不够",
                )
        else:
            self._record(
                "many_obs_enkf",
                "未命中",
                f"观测数 {observation_count} 未超过 {_MANY_OBSERVATIONS_THRESHOLD}",
            )

        # 规则 4: 中等观测量 -> Hybrid
        if observation_count is not None and observation_count > _MODERATE_OBSERVATIONS_THRESHOLD:
            self._record(
                "moderate_obs_hybrid",
                "命中",
                f"观测数 {observation_count} > {_MODERATE_OBSERVATIONS_THRESHOLD}",
                selected_algorithm=ALGORITHM_HYBRID,
            )
            return self._make_result(
                algorithm_id=ALGORITHM_HYBRID,
                reason=(
                    f"观测数量中等（{observation_count} > {_MODERATE_OBSERVATIONS_THRESHOLD}），"
                    f"选择混合同化（Hybrid Assimilation）以平衡变分与集合方法的优势"
                ),
                config_overrides={
                    "ensemble_size": min(max(observation_count // 2, 10), 50),
                    "hybrid_weight": 0.5,
                },
            )
        self._record(
            "moderate_obs_hybrid",
            "未命中",
            f"观测数 {observation_count} 未超过 {_MODERATE_OBSERVATIONS_THRESHOLD}",
        )

        # 规则 5: 少量观测 + 紧迫时间 -> 3DVAR
        if (
            observation_count is not None
            and observation_count <= _MODERATE_OBSERVATIONS_THRESHOLD
            and time_budget_seconds is not None
            and time_budget_seconds < _FAST_TIME_BUDGET_SECONDS
        ):
            self._record(
                "few_obs_fast",
                "命中",
                f"观测数 {observation_count} <= {_MODERATE_OBSERVATIONS_THRESHOLD}，"
                f"时间预算 {time_budget_seconds}s < {_FAST_TIME_BUDGET_SECONDS}s",
                selected_algorithm=ALGORITHM_3DVAR,
            )
            return self._make_result(
                algorithm_id=ALGORITHM_3DVAR,
                reason=(
                    f"观测数量较少（{observation_count} <= {_MODERATE_OBSERVATIONS_THRESHOLD}）"
                    f"且时间预算紧迫（{time_budget_seconds}s < {_FAST_TIME_BUDGET_SECONDS}s），"
                    f"选择 3D-VAR 以获得最快的收敛速度"
                ),
                config_overrides={
                    "max_iterations": 10,
                },
            )
        self._record("few_obs_fast", "未命中", "不满足少量观测+紧迫时间条件")

        # 规则 6: 需要概率输出 -> EnKF + adaptive_variance_field
        if require_probabilistic:
            self._record("probabilistic", "命中", "需要概率性输出", selected_algorithm=ALGORITHM_ENKF)
            return self._make_result(
                algorithm_id=ALGORITHM_ENKF,
                reason=(
                    "任务需要概率性输出（集合/方差场），选择 EnKF 并启用 adaptive_variance_field 以提供不确定性量化"
                ),
                config_overrides={
                    "enable_adaptive_variance": True,
                    "ensemble_size": observation_count if observation_count else 30,
                },
            )
        self._record("probabilistic", "未命中", "不需要概率性输出")

        # 规则 7: 默认 -> adaptive_hybrid
        self._record(
            "default", "命中", "所有特定规则均未命中，使用默认策略", selected_algorithm=ALGORITHM_ADAPTIVE_HYBRID
        )
        return self._make_result(
            algorithm_id=ALGORITHM_ADAPTIVE_HYBRID,
            reason=("未匹配到特定决策规则，使用自适应混合同化（Adaptive Hybrid）作为默认策略，兼顾计算效率与分析质量"),
            config_overrides={
                "ensemble_size": observation_count if observation_count else 20,
                "hybrid_weight": "adaptive",
            },
        )

    def get_decision_explanation(self) -> str:
        """返回最近一次 ``select_algorithm`` 调用的完整决策过程说明。

        Returns
        -------
        str
            格式化的决策链文本，包含每条规则的检查结果和最终选择。
            若尚未调用 ``select_algorithm``，返回提示信息。
        """
        if not self._last_decision:
            return "尚未执行算法选择，请先调用 select_algorithm()。"

        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("  智能算法调度器 - 决策过程说明")
        lines.append("=" * 60)
        lines.append("")

        for idx, step in enumerate(self._last_decision, start=1):
            rule_name = step.get("rule", "unknown")
            status = step.get("status", "unknown")
            detail = step.get("detail", "")
            marker = "[命中]" if "命中" in status else "[未命中]"
            lines.append(f"  规则 {idx}: {rule_name}")
            lines.append(f"    状态: {marker} {status}")
            lines.append(f"    详情: {detail}")
            lines.append("")

        # 提取最终结果
        final = self._last_decision[-1]
        lines.append("-" * 60)
        if "命中" in final.get("status", ""):
            lines.append(f"  最终选择: {final.get('selected_algorithm', 'N/A')}")
        lines.append("=" * 60)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_grid_total(grid_shape: tuple[int, ...] | None) -> int | None:
        """计算网格总元素数。若 grid_shape 为 None 则返回 None。"""
        if grid_shape is None:
            return None
        if not grid_shape:
            return 0
        total = 1
        for dim in grid_shape:
            total *= dim
        return total

    def _record(
        self,
        rule: str,
        status: str,
        detail: str,
        selected_algorithm: str | None = None,
    ) -> None:
        """记录一条决策步骤。"""
        entry: dict[str, str] = {
            "rule": rule,
            "status": status,
            "detail": detail,
        }
        if selected_algorithm is not None:
            entry["selected_algorithm"] = selected_algorithm
        self._last_decision.append(entry)

    @staticmethod
    def _make_result(
        algorithm_id: str,
        reason: str,
        config_overrides: dict[str, Any],
    ) -> dict[str, Any]:
        """构造标准化的返回字典。"""
        return {
            "algorithm_id": algorithm_id,
            "reason": reason,
            "config_overrides": config_overrides,
        }
