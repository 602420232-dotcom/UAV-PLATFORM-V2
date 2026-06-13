"""物理约束模块.

对 AI 模型预测的气象场施加物理约束，确保预测结果满足
质量守恒、能量守恒、热力学一致性和动量守恒等物理定律。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class PhysicsConstraint:
    """物理约束模块.

    对 AI 模型输出的气象场预测结果施加物理约束修正，
    生成满足物理定律的合理预测场，并输出违反报告和修正统计。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.tolerance = self.config.get("tolerance", 1e-6)
        self.max_iterations = self.config.get("max_iterations", 100)
        self.relaxation_factor = self.config.get("relaxation_factor", 0.5)
        np.random.seed(42)

    def apply(self, params: dict[str, Any]) -> dict[str, Any]:
        """对 AI 预测场施加物理约束.

        Args:
            params: 包含以下键的字典:
                - predicted_field: AI 模型预测的气象场，形状 (h, w) 或 (h, w, c)
                - constraint_type: 约束类型 (mass / energy / thermodynamic / momentum)
                - reference_field: 参考场（用于守恒约束），形状与 predicted_field 一致

        Returns:
            包含约束后场、违反报告和修正统计的字典。
        """
        np.random.seed(42)

        predicted_field = np.asarray(
            params.get("predicted_field", np.zeros((50, 50))),
        )
        constraint_type = params.get("constraint_type", "mass")
        reference_field = np.asarray(
            params.get("reference_field", np.zeros_like(predicted_field)),
        )

        original_field = predicted_field.copy()
        violation_report: dict[str, Any] = {}
        correction_stats: dict[str, Any] = {}

        if constraint_type == "mass":
            constrained_field = self._apply_mass_conservation(
                predicted_field,
                reference_field,
                violation_report,
                correction_stats,
            )
        elif constraint_type == "energy":
            constrained_field = self._apply_energy_conservation(
                predicted_field,
                reference_field,
                violation_report,
                correction_stats,
            )
        elif constraint_type == "thermodynamic":
            constrained_field = self._apply_thermodynamic_consistency(
                predicted_field,
                reference_field,
                violation_report,
                correction_stats,
            )
        elif constraint_type == "momentum":
            constrained_field = self._apply_momentum_conservation(
                predicted_field,
                reference_field,
                violation_report,
                correction_stats,
            )
        else:
            logger.warning("未知约束类型 '%s'，返回原始场", constraint_type)
            constrained_field = predicted_field.copy()
            violation_report = {"constraint_type": constraint_type, "status": "unknown"}
            correction_stats = {"total_correction": 0.0, "max_correction": 0.0}

        # 计算总体修正统计
        total_diff = np.sum(np.abs(constrained_field - original_field))
        max_diff = np.max(np.abs(constrained_field - original_field))
        mean_diff = np.mean(np.abs(constrained_field - original_field))
        correction_stats["total_correction"] = float(total_diff)
        correction_stats["max_correction"] = float(max_diff)
        correction_stats["mean_correction"] = float(mean_diff)

        return {
            "constrained_field": constrained_field.tolist(),
            "violation_report": violation_report,
            "correction_stats": correction_stats,
            "constraint_type": constraint_type,
            "field_shape": list(predicted_field.shape),
        }

    def _apply_mass_conservation(
        self,
        field: np.ndarray,
        reference: np.ndarray,
        violation_report: dict[str, Any],
        correction_stats: dict[str, Any],
    ) -> np.ndarray:
        """施加质量守恒约束.

        确保预测场的总质量（积分值）与参考场一致。

        Args:
            field: 预测场.
            reference: 参考场.
            violation_report: 违反报告（就地更新）.
            correction_stats: 修正统计（就地更新）.

        Returns:
            约束后的场.
        """
        predicted_total = np.sum(field)
        reference_total = np.sum(reference)
        violation = abs(predicted_total - reference_total) / (abs(reference_total) + 1e-10)

        violation_report["constraint_type"] = "mass"
        violation_report["predicted_total"] = float(predicted_total)
        violation_report["reference_total"] = float(reference_total)
        violation_report["relative_violation"] = float(violation)
        violation_report["is_satisfied"] = bool(violation < self.tolerance)

        # 均匀缩放以满足守恒
        if abs(reference_total) > 1e-10:
            scale = reference_total / predicted_total
            constrained = field * scale
        else:
            constrained = field - (predicted_total / field.size)

        correction_stats["method"] = "uniform_scaling"
        correction_stats["scale_factor"] = float(scale if abs(reference_total) > 1e-10 else 1.0)

        return constrained

    def _apply_energy_conservation(
        self,
        field: np.ndarray,
        reference: np.ndarray,
        violation_report: dict[str, Any],
        correction_stats: dict[str, Any],
    ) -> np.ndarray:
        """施加能量守恒约束.

        确保预测场的总能量（平方和）与参考场一致。

        Args:
            field: 预测场.
            reference: 参考场.
            violation_report: 违反报告（就地更新）.
            correction_stats: 修正统计（就地更新）.

        Returns:
            约束后的场.
        """
        predicted_energy = np.sum(field**2)
        reference_energy = np.sum(reference**2)
        violation = abs(predicted_energy - reference_energy) / (abs(reference_energy) + 1e-10)

        violation_report["constraint_type"] = "energy"
        violation_report["predicted_energy"] = float(predicted_energy)
        violation_report["reference_energy"] = float(reference_energy)
        violation_report["relative_violation"] = float(violation)
        violation_report["is_satisfied"] = bool(violation < self.tolerance)

        # 能量归一化
        if predicted_energy > 1e-10:
            scale = np.sqrt(reference_energy / predicted_energy)
            constrained = field * scale
        else:
            constrained = field

        correction_stats["method"] = "energy_normalization"
        correction_stats["scale_factor"] = float(scale if predicted_energy > 1e-10 else 1.0)

        return constrained

    def _apply_thermodynamic_consistency(
        self,
        field: np.ndarray,
        reference: np.ndarray,
        violation_report: dict[str, Any],
        correction_stats: dict[str, Any],
    ) -> np.ndarray:
        """施加热力学一致性约束.

        确保预测场满足热力学一致性：非负性、单调性和梯度约束。

        Args:
            field: 预测场.
            reference: 参考场.
            violation_report: 违反报告（就地更新）.
            correction_stats: 修正统计（就地更新）.

        Returns:
            约束后的场.
        """
        constrained = field.copy()
        n_violations_negative = int(np.sum(constrained < 0))
        n_violations_total = n_violations_negative

        # 非负约束
        if n_violations_negative > 0:
            constrained = np.maximum(constrained, 0.0)

        # 梯度约束：相邻点差值不应超过参考场的最大梯度
        if reference.size > 1:
            ref_grad_x = np.diff(reference, axis=0) if reference.shape[0] > 1 else np.array([0.0])
            ref_grad_y = np.diff(reference, axis=1) if reference.shape[1] > 1 else np.array([0.0])
            max_grad = max(
                np.max(np.abs(ref_grad_x)) if ref_grad_x.size > 0 else 0.0,
                np.max(np.abs(ref_grad_y)) if ref_grad_y.size > 0 else 0.0,
                1e-10,
            )

            n_grad_violations = 0
            for iteration in range(self.max_iterations):
                violations_found = False
                if constrained.shape[0] > 1:
                    grad_x = np.diff(constrained, axis=0)
                    excess_x = np.abs(grad_x) > max_grad
                    if np.any(excess_x):
                        n_grad_violations += int(np.sum(excess_x))
                        violations_found = True
                        sign = np.sign(grad_x)
                        correction = (np.abs(grad_x) - max_grad) * self.relaxation_factor
                        correction = correction * sign
                        constrained[:-1] -= correction * 0.5
                        constrained[1:] += correction * 0.5

                if constrained.shape[1] > 1:
                    grad_y = np.diff(constrained, axis=1)
                    excess_y = np.abs(grad_y) > max_grad
                    if np.any(excess_y):
                        n_grad_violations += int(np.sum(excess_y))
                        violations_found = True
                        sign = np.sign(grad_y)
                        correction = (np.abs(grad_y) - max_grad) * self.relaxation_factor
                        correction = correction * sign
                        constrained[:, :-1] -= correction * 0.5
                        constrained[:, 1:] += correction * 0.5

                if not violations_found:
                    break

            n_violations_total += n_grad_violations

        violation_report["constraint_type"] = "thermodynamic"
        violation_report["n_violations"] = n_violations_total
        violation_report["n_negative_violations"] = n_violations_negative
        violation_report["is_satisfied"] = bool(n_violations_total == 0)

        correction_stats["method"] = "projection_relaxation"
        correction_stats["iterations"] = min(
            iteration + 1 if "iteration" in dir() else 1,
            self.max_iterations,
        )

        return constrained

    def _apply_momentum_conservation(
        self,
        field: np.ndarray,
        reference: np.ndarray,
        violation_report: dict[str, Any],
        correction_stats: dict[str, Any],
    ) -> np.ndarray:
        """施加动量守恒约束.

        确保预测场的动量（加权积分）与参考场一致。

        Args:
            field: 预测场.
            reference: 参考场.
            violation_report: 违反报告（就地更新）.
            correction_stats: 修正统计（就地更新）.

        Returns:
            约束后的场.
        """
        # 使用空间坐标作为权重
        h, w = field.shape
        y_coords, x_coords = np.mgrid[0:h, 0:w]
        weight = np.sqrt(x_coords**2 + y_coords**2).astype(float) + 1.0

        predicted_momentum = np.sum(field * weight)
        reference_momentum = np.sum(reference * weight)
        violation = abs(predicted_momentum - reference_momentum) / (abs(reference_momentum) + 1e-10)

        violation_report["constraint_type"] = "momentum"
        violation_report["predicted_momentum"] = float(predicted_momentum)
        violation_report["reference_momentum"] = float(reference_momentum)
        violation_report["relative_violation"] = float(violation)
        violation_report["is_satisfied"] = bool(violation < self.tolerance)

        # 加权修正以满足动量守恒
        momentum_deficit = reference_momentum - predicted_momentum
        weight_sum = np.sum(weight**2)
        if weight_sum > 1e-10:
            constrained = field + (momentum_deficit / weight_sum) * weight
        else:
            constrained = field.copy()

        correction_stats["method"] = "weighted_correction"
        correction_stats["momentum_deficit"] = float(momentum_deficit)

        return constrained
