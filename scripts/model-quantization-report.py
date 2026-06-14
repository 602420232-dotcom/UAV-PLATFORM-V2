#!/usr/bin/env python
"""模型量化评估报告脚本。

对 5 个代表性算法模型进行量化评估，生成对比表格（原始 vs INT8 vs FP16），
输出 Markdown 格式报告。

用法:
    python scripts/model-quantization-report.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

# 确保项目根目录在 sys.path 中
_project_root = Path(__file__).resolve().parent.parent / "python" / "algorithm-engine"
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.algorithms.edge.model_quantization import ModelQuantizer, QuantizationReport  # noqa: E402  # pyright: ignore[reportMissingImports]


# ---------------------------------------------------------------------------
# 代表性模型定义
# ---------------------------------------------------------------------------

REPRESENTATIVE_MODELS: list[dict[str, Any]] = [
    {
        "name": "PathPlanner-CNN",
        "description": "路径规划卷积神经网络",
        "weight_shape": (256, 128),
        "n_params": 256 * 128,
    },
    {
        "name": "RiskEstimator-LSTM",
        "description": "风险评估LSTM循环网络",
        "weight_shape": (512, 256),
        "n_params": 512 * 256,
    },
    {
        "name": "WeatherPredictor-UNet",
        "description": "气象预测U-Net网络",
        "weight_shape": (1024, 512),
        "n_params": 1024 * 512,
    },
    {
        "name": "ObstacleDetector-YOLO",
        "description": "障碍物检测YOLO模型",
        "weight_shape": (2048, 1024),
        "n_params": 2048 * 1024,
    },
    {
        "name": "DecisionAgent-PPO",
        "description": "决策智能体PPO强化学习模型",
        "weight_shape": (128, 64),
        "n_params": 128 * 64,
    },
]


def generate_model_weights(shape: tuple[int, ...], seed: int = 42) -> np.ndarray:
    """生成模拟模型权重。

    使用 He 初始化方式生成符合实际分布的权重。
    """
    rng = np.random.RandomState(seed)
    fan_in = shape[1] if len(shape) >= 2 else shape[0]  # pyright: ignore[reportGeneralTypeIssues]
    std = np.sqrt(2.0 / fan_in)
    return rng.randn(*shape).astype(np.float32) * std


def run_evaluation() -> list[dict[str, Any]]:
    """对所有代表性模型执行量化评估。

    Returns:
        评估结果列表，每个元素包含原始、INT8、FP16 的报告。
    """
    quantizer = ModelQuantizer()
    results = []

    for model_info in REPRESENTATIVE_MODELS:
        print(f"评估模型: {model_info['name']} ...")

        weights = generate_model_weights(model_info["weight_shape"])

        # 原始 FP32 基线
        report_fp32 = quantizer.run_quantization_pipeline(
            weights=weights,
            model_name=model_info["name"],
            quantization_type="fp32",
        )

        # INT8 量化
        report_int8 = quantizer.run_quantization_pipeline(
            weights=weights,
            model_name=model_info["name"],
            quantization_type="int8",
            apply_qat=True,
            qat_epochs=10,
        )

        # FP16 量化
        report_fp16 = quantizer.run_quantization_pipeline(
            weights=weights,
            model_name=model_info["name"],
            quantization_type="fp16",
            apply_qat=True,
            qat_epochs=10,
        )

        results.append({
            "model": model_info,
            "fp32": report_fp32,
            "int8": report_int8,
            "fp16": report_fp16,
        })

    return results


def generate_markdown_report(results: list[dict[str, Any]]) -> str:
    """生成 Markdown 格式的量化评估报告。"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines: list[str] = []
    lines.append("# 模型量化评估报告")
    lines.append("")
    lines.append(f"> 生成时间: {now}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 概览表格
    lines.append("## 1. 量化概览")
    lines.append("")
    # fmt: off
    lines.append("| 模型名称 | 描述 | 参数量 | 原始大小 (MB) | INT8 大小 (MB) | FP16 大小 (MB) | INT8 压缩比 | FP16 压缩比 |")
    lines.append("|:---------|:-----|-------:|-------------:|--------------:|--------------:|-----------:|-----------:|")
    # fmt: on

    for r in results:
        m = r["model"]
        fp32_size_mb = r["fp32"].original_size_bytes / (1024 * 1024)
        int8_size_mb = r["int8"].quantized_size_bytes / (1024 * 1024)
        fp16_size_mb = r["fp16"].quantized_size_bytes / (1024 * 1024)
        lines.append(
            f"| {m['name']} | {m['description']} | {m['n_params']:,} "
            f"| {fp32_size_mb:.2f} | {int8_size_mb:.2f} | {fp16_size_mb:.2f} "
            f"| {r['int8'].compression_ratio:.2f}x | {r['fp16'].compression_ratio:.2f}x |"
        )

    lines.append("")

    # 推理延迟对比
    lines.append("## 2. 推理延迟对比")
    lines.append("")
    # fmt: off
    lines.append("| 模型名称 | FP32 延迟 (ms) | INT8 延迟 (ms) | FP16 延迟 (ms) | INT8 延迟降低 | FP16 延迟降低 |")
    lines.append("|:---------|-------------:|-------------:|-------------:|-----------:|-----------:|")
    # fmt: on

    for r in results:
        m = r["model"]
        lines.append(
            f"| {m['name']} "
            f"| {r['fp32'].quantized_latency_ms:.3f} "
            f"| {r['int8'].quantized_latency_ms:.3f} "
            f"| {r['fp16'].quantized_latency_ms:.3f} "
            f"| {r['int8'].latency_reduction_pct:.1f}% "
            f"| {r['fp16'].latency_reduction_pct:.1f}% |"
        )

    lines.append("")

    # 精度损失评估
    lines.append("## 3. 精度损失评估")
    lines.append("")
    # fmt: off
    lines.append("| 模型名称 | INT8 RMSE | INT8 MAE | INT8 Cosine Sim | FP16 RMSE | FP16 MAE | FP16 Cosine Sim |")
    lines.append("|:---------|----------:|---------:|---------------:|----------:|---------:|---------------:|")
    # fmt: on

    for r in results:
        m = r["model"]
        int8_report = r["int8"]
        fp16_report = r["fp16"]
        # 从完整报告中获取余弦相似度（通过单独计算）
        weights = generate_model_weights(m["weight_shape"])
        int8_cos = _cosine_similarity(weights, int8_report)
        fp16_cos = _cosine_similarity(weights, fp16_report)

        lines.append(
            f"| {m['name']} "
            f"| {int8_report.rmse:.6f} "
            f"| {int8_report.mean_absolute_error:.6f} "
            f"| {int8_cos:.6f} "
            f"| {fp16_report.rmse:.6f} "
            f"| {fp16_report.mean_absolute_error:.6f} "
            f"| {fp16_cos:.6f} |"
        )

    lines.append("")

    # QAT 效果
    lines.append("## 4. 量化感知训练 (QAT) 效果")
    lines.append("")
    lines.append("| 模型名称 | INT8 QAT 恢复率 | FP16 QAT 恢复率 | QAT 轮数 |")
    lines.append("|:---------|---------------:|---------------:|--------:|")

    for r in results:
        m = r["model"]
        lines.append(
            f"| {m['name']} "
            f"| {r['int8'].qat_accuracy_recovery:.4f} "
            f"| {r['fp16'].qat_accuracy_recovery:.4f} "
            f"| {r['int8'].qat_epochs} |"
        )

    lines.append("")

    # 综合推荐
    lines.append("## 5. 综合推荐")
    lines.append("")

    for r in results:
        m = r["model"]
        int8_cr = r["int8"].compression_ratio
        int8_rmse = r["int8"].rmse
        fp16_rmse = r["fp16"].rmse

        # 推荐策略：精度损失小且压缩比高的优先
        if int8_rmse < 0.01 and int8_cr >= 3.5:
            recommendation = "**INT8** (高压缩比，精度损失可忽略)"
        elif fp16_rmse < 0.001:
            recommendation = "**FP16** (极低精度损失，推荐精度优先场景)"
        else:
            recommendation = "**FP16** (精度损失更小)"

        lines.append(f"- **{m['name']}**: 推荐 {recommendation}")

    lines.append("")

    # 详细报告
    lines.append("## 6. 详细量化报告")
    lines.append("")

    for r in results:
        m = r["model"]
        lines.append(f"### {m['name']}")
        lines.append("")
        lines.append(f"**描述**: {m['description']}")
        lines.append(f"**参数量**: {m['n_params']:,}")
        lines.append(f"**权重形状**: {m['weight_shape']}")
        lines.append("")

        lines.append("#### INT8 量化")
        lines.append("")
        lines.append("```json")
        lines.append(_format_report_dict(r["int8"].to_dict()))
        lines.append("```")
        lines.append("")

        lines.append("#### FP16 量化")
        lines.append("")
        lines.append("```json")
        lines.append(_format_report_dict(r["fp16"].to_dict()))
        lines.append("```")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*报告由 model-quantization-report.py 自动生成*")

    return "\n".join(lines)


def _cosine_similarity(
    weights: np.ndarray, report: QuantizationReport
) -> float:
    """计算余弦相似度（辅助函数）。"""
    quantizer = ModelQuantizer()
    quantized, q_info = quantizer.quantize_weights(
        weights, report.quantization_type
    )
    dequantized = quantizer.dequantize(quantized, q_info)
    cos_sim = float(
        np.dot(weights.flatten(), dequantized.flatten())
        / max(
            float(np.linalg.norm(weights.flatten()))
            * float(np.linalg.norm(dequantized.flatten())),
            1e-10,
        )
    )
    return cos_sim


def _format_report_dict(d: dict[str, Any], indent: int = 2) -> str:
    """格式化报告字典为 JSON 字符串。"""
    import json
    return json.dumps(d, indent=indent, ensure_ascii=False)


def main() -> None:
    """主函数：执行评估并输出报告。"""
    print("=" * 60)
    print("模型量化评估报告生成器")
    print("=" * 60)
    print()

    # 执行评估
    print("开始量化评估...")
    results = run_evaluation()
    print()

    # 生成报告
    report_md = generate_markdown_report(results)

    # 输出到文件
    report_path = (
        Path(__file__).resolve().parent.parent
        / "scripts" / "model-quantization-report.md"
    )
    report_path.write_text(report_md, encoding="utf-8")
    print(f"报告已生成: {report_path}")

    # 同时输出到 stdout
    print()
    print(report_md)


if __name__ == "__main__":
    main()
