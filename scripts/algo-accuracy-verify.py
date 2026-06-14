#!/usr/bin/env python3
"""
UAV Platform V2 - 算法精度验证脚本

验证以下算法精度:
1. 5D-VAR vs 3D-VAR 对比: 比较 RMSE
2. GPR 置信区间验证: 验证覆盖真实值的比例 >= 80%
3. 路径规划算法对比: A* vs RRT* 路径长度和计算时间

使用 pytest 框架，可独立运行:
    python scripts/algo-accuracy-verify.py
    pytest scripts/algo-accuracy-verify.py -v
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pytest
import requests

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
ALGORITHM_ENGINE_URL = "http://localhost:9095"
TIMEOUT_SECONDS = 120


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
@dataclass
class TestCaseResult:
    """单个测试用例结果."""

    algorithm_id: str
    success: bool
    elapsed_ms: float = 0.0
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""


@dataclass
class ComparisonResult:
    """对比测试结果."""

    name: str
    algo_a_result: TestCaseResult
    algo_b_result: TestCaseResult
    metric_a: float = 0.0
    metric_b: float = 0.0
    improvement_pct: float = 0.0
    verdict: str = ""


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def call_algorithm(algorithm_id: str, params: dict[str, Any]) -> TestCaseResult:
    """调用 algorithm-engine 的任务提交接口并等待结果."""
    url = f"{ALGORITHM_ENGINE_URL}/api/v1/tasks/submit"
    start = time.perf_counter()

    try:
        resp = requests.post(
            url,
            json={"algorithm_id": algorithm_id, "params": params},
            timeout=TIMEOUT_SECONDS,
        )
        elapsed = (time.perf_counter() - start) * 1000

        if resp.status_code != 200:
            return TestCaseResult(
                algorithm_id=algorithm_id,
                success=False,
                elapsed_ms=elapsed,
                error=f"HTTP {resp.status_code}: {resp.text[:200]}",
            )

        data = resp.json()
        task_id = data.get("task_id")
        if not task_id:
            return TestCaseResult(
                algorithm_id=algorithm_id,
                success=False,
                elapsed_ms=elapsed,
                error="No task_id in response",
            )

        # 轮询等待任务完成
        result = _poll_task(task_id, start)
        return result

    except requests.exceptions.ConnectionError:
        elapsed = (time.perf_counter() - start) * 1000
        return TestCaseResult(
            algorithm_id=algorithm_id,
            success=False,
            elapsed_ms=elapsed,
            error="Connection refused - algorithm engine not running",
        )
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return TestCaseResult(
            algorithm_id=algorithm_id,
            success=False,
            elapsed_ms=elapsed,
            error=str(e),
        )


def _poll_task(task_id: str, submit_start: float) -> TestCaseResult:
    """轮询任务状态直到完成."""
    max_wait = TIMEOUT_SECONDS
    poll_interval = 0.5

    while True:
        elapsed_total = time.perf_counter() - submit_start
        if elapsed_total > max_wait:
            return TestCaseResult(
                algorithm_id=task_id,
                success=False,
                elapsed_ms=elapsed_total * 1000,
                error="Task timed out",
            )

        try:
            status_resp = requests.get(
                f"{ALGORITHM_ENGINE_URL}/api/v1/tasks/{task_id}",
                timeout=10,
            )
            status_data = status_resp.json()
            task_status = status_data.get("status", "")

            if task_status == "success":
                elapsed_ms = (time.perf_counter() - submit_start) * 1000
                return TestCaseResult(
                    algorithm_id=status_data.get("algorithm_id", task_id),
                    success=True,
                    elapsed_ms=elapsed_ms,
                    result=status_data.get("result", {}),
                )
            elif task_status in ("failed", "cancelled"):
                elapsed_ms = (time.perf_counter() - submit_start) * 1000
                return TestCaseResult(
                    algorithm_id=status_data.get("algorithm_id", task_id),
                    success=False,
                    elapsed_ms=elapsed_ms,
                    error=status_data.get("error", f"Task {task_status}"),
                )
            # still pending/running
            time.sleep(poll_interval)

        except Exception:
            time.sleep(poll_interval)


def compute_rmse(predicted: list[float], truth: list[float]) -> float:
    """计算 RMSE."""
    if len(predicted) != len(truth) or len(predicted) == 0:
        return float("inf")
    return math.sqrt(
        sum((p - t) ** 2 for p, t in zip(predicted, truth)) / len(predicted)
    )


def path_length(path: list[list[float]]) -> float:
    """计算路径总长度."""
    if len(path) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(path)):
        dx = path[i][0] - path[i - 1][0]
        dy = path[i][1] - path[i - 1][1]
        total += math.sqrt(dx * dx + dy * dy)
    return total


def flatten_field(field: Any) -> list[float]:
    """将嵌套的二维场展平为一维列表."""
    if isinstance(field, list):
        result = []
        for item in field:
            if isinstance(item, list):
                result.extend(flatten_field(item))
            else:
                result.append(float(item))
        return result
    return [float(field)]


# ---------------------------------------------------------------------------
# 模拟数据生成
# ---------------------------------------------------------------------------
def generate_meteorological_data(
    grid_rows: int = 20,
    grid_cols: int = 20,
    num_observations: int = 50,
    noise_std: float = 2.0,
    seed: int = 42,
) -> dict[str, Any]:
    """生成模拟气象数据用于同化算法测试.

    Returns:
        包含 background_field, observations, truth_field 的字典
    """
    rng = np.random.RandomState(seed)

    # 生成真实场 (使用简单的正弦波组合模拟气象场)
    x = np.linspace(0, 4 * np.pi, grid_cols)
    y = np.linspace(0, 4 * np.pi, grid_rows)
    xx, yy = np.meshgrid(x, y)
    truth_field = (
        10.0
        + 3.0 * np.sin(xx * 0.5) * np.cos(yy * 0.3)
        + 2.0 * np.cos(xx * 0.7 + yy * 0.5)
        + 1.5 * np.sin(yy * 0.8)
    )

    # 背景场 = 真实场 + 背景误差
    bg_error = rng.randn(grid_rows, grid_cols) * 1.5
    background_field = truth_field + bg_error

    # 观测 = 真实场 + 观测误差
    observations = []
    for _ in range(num_observations):
        i = rng.randint(0, grid_rows)
        j = rng.randint(0, grid_cols)
        obs_value = float(truth_field[i, j] + rng.randn() * noise_std)
        observations.append(
            {"position": [int(i), int(j)], "value": round(obs_value, 4)}
        )

    return {
        "background_field": background_field.tolist(),
        "observations": observations,
        "truth_field": truth_field.tolist(),
        "grid_shape": [grid_rows, grid_cols],
    }


def generate_gpr_data(
    n_train: int = 40,
    n_test: int = 20,
    noise_std: float = 0.5,
    seed: int = 42,
) -> dict[str, Any]:
    """生成模拟数据用于 GPR 不确定性量化测试.

    Returns:
        包含 train_x, train_y, test_x, test_y 的字典
    """
    rng = np.random.RandomState(seed)

    # 生成训练数据 (一维回归)
    # GPR 的 cdist 需要 2D 输入，因此 train_x 和 test_x 使用 [[x]] 格式
    train_x = [[x] for x in rng.uniform(0, 10, n_train).tolist()]
    # 真实函数: sin(x) + 0.5*cos(2x)
    def _true_func(x: float) -> float:
        return math.sin(x) + 0.5 * math.cos(2 * x)

    true_func = _true_func
    train_y = [true_func(x[0]) + rng.randn() * noise_std for x in train_x]

    # 生成测试数据
    test_x = [[x] for x in rng.uniform(0, 10, n_test).tolist()]
    test_y = [true_func(x[0]) for x in test_x]

    return {
        "train_x": train_x,
        "train_y": train_y,
        "test_x": test_x,
        "test_y": test_y,
    }


def generate_planning_data(
    grid_size: int = 50,
    obstacle_ratio: float = 0.15,
    seed: int = 42,
) -> dict[str, Any]:
    """生成模拟数据用于路径规划算法测试.

    A* 使用 _world_to_grid(pos) = pos + grid_size/2 进行坐标转换，
    因此 start/goal 需要使用以原点为中心的坐标。

    Returns:
        包含 start, goal, grid_size, obstacles 的字典
    """
    rng = np.random.RandomState(seed)

    half = grid_size // 2
    # A* _world_to_grid: grid_pos = world_pos + grid_size/2
    # 要让 grid_pos 在 [1, grid_size-2] 范围内
    start = [-half + 1, -half + 1]
    goal = [half - 2, half - 2]

    # 生成随机障碍物 (使用网格坐标)
    obstacles = []
    for i in range(grid_size):
        for j in range(grid_size):
            if rng.random() < obstacle_ratio:
                # 不在起点和终点附近放置障碍物
                if abs(i - (half - 1 + 1)) + abs(j - (half - 1 + 1)) > 3:
                    if abs(i - (half + half - 2)) + abs(j - (half + half - 2)) > 3:
                        obstacles.append([i, j])

    return {
        "start": start,
        "goal": goal,
        "grid_size": [grid_size, grid_size],
        "obstacles": obstacles,
    }


# ---------------------------------------------------------------------------
# 测试函数
# ---------------------------------------------------------------------------

def test_5dvar_vs_3dvar() -> ComparisonResult:
    """测试1: 5D-VAR vs 3D-VAR 对比."""
    print("\n" + "=" * 70)
    print("测试1: 5D-VAR vs 3D-VAR 对比")
    print("=" * 70)

    data = generate_meteorological_data()
    truth_flat = flatten_field(data["truth_field"])

    # 执行 3D-VAR
    params_3dvar = {
        "background_field": data["background_field"],
        "observations": data["observations"],
        "grid_shape": data["grid_shape"],
        "resolution": 1.0,
        "config": {
            "grid_shape": tuple(data["grid_shape"]),
            "resolution": 1.0,
            "sigma_b": 1.5,
            "correlation_length": 5.0,
            "observation_error_scale": 2.0,
            "max_iterations": 50,
        },
    }
    result_3dvar = call_algorithm("3dvar", params_3dvar)

    # 执行 5D-VAR
    params_5dvar = {
        "background_field": data["background_field"],
        "observations": data["observations"],
        "grid_shape": data["grid_shape"],
        "risk_weight": 0.1,
        "config": {
            "grid_shape": tuple(data["grid_shape"]),
            "resolution": 1.0,
            "sigma_b": 1.5,
            "observation_error_scale": 2.0,
            "risk_weight": 0.1,
            "max_iterations": 30,
            "learning_rate": 0.01,
            "n_outer_iterations": 2,
        },
    }
    result_5dvar = call_algorithm("5dvar", params_5dvar)

    # 计算 RMSE
    rmse_3dvar = float("inf")
    rmse_5dvar = float("inf")

    if result_3dvar.success and "analysis_field" in result_3dvar.result:
        pred_3dvar = flatten_field(result_3dvar.result["analysis_field"])
        rmse_3dvar = compute_rmse(pred_3dvar, truth_flat)

    if result_5dvar.success and "analysis_field" in result_5dvar.result:
        pred_5dvar = flatten_field(result_5dvar.result["analysis_field"])
        rmse_5dvar = compute_rmse(pred_5dvar, truth_flat)

    # 计算改进百分比
    if rmse_3dvar > 0 and rmse_5dvar < float("inf"):
        improvement = ((rmse_3dvar - rmse_5dvar) / rmse_3dvar) * 100
    else:
        improvement = 0.0

    verdict = (
        f"5D-VAR RMSE={'%.4f' % rmse_5dvar}, "
        f"3D-VAR RMSE={'%.4f' % rmse_3dvar}, "
        f"改进={improvement:+.2f}%"
    )

    comparison = ComparisonResult(
        name="5D-VAR vs 3D-VAR",
        algo_a_result=result_5dvar,
        algo_b_result=result_3dvar,
        metric_a=rmse_5dvar,
        metric_b=rmse_3dvar,
        improvement_pct=improvement,
        verdict=verdict,
    )

    _print_comparison(comparison)
    return comparison


def test_gpr_confidence_interval() -> ComparisonResult:
    """测试2: GPR 置信区间验证."""
    print("\n" + "=" * 70)
    print("测试2: GPR 置信区间验证")
    print("=" * 70)

    data = generate_gpr_data()
    test_y = data["test_y"]

    params = {
        "train_x": data["train_x"],
        "train_y": data["train_y"],
        "test_x": data["test_x"],
        "config": {
            "length_scale": 1.0,
            "signal_variance": 1.0,
            "noise_variance": 0.25,
        },
    }

    result = call_algorithm("gpr_uncertainty", params)

    coverage_rate = 0.0
    n_covered = 0
    n_total = len(test_y)

    if result.success:
        res = result.result
        lower = res.get("confidence_95_lower", [])
        upper = res.get("confidence_95_upper", [])

        if len(lower) == len(upper) == len(test_y):
            for i in range(n_total):
                if lower[i] <= test_y[i] <= upper[i]:
                    n_covered += 1
            coverage_rate = (n_covered / n_total) * 100 if n_total > 0 else 0.0

    pass_threshold = 80.0
    passed = coverage_rate >= pass_threshold

    verdict = (
        f"覆盖率={coverage_rate:.1f}% ({n_covered}/{n_total}), "
        f"阈值={pass_threshold:.0f}%, "
        f"结果={'PASS' if passed else 'FAIL'}"
    )

    comparison = ComparisonResult(
        name="GPR 置信区间",
        algo_a_result=result,
        algo_b_result=TestCaseResult(algorithm_id="threshold", success=True),
        metric_a=coverage_rate,
        metric_b=pass_threshold,
        improvement_pct=coverage_rate - pass_threshold,
        verdict=verdict,
    )

    _print_comparison(comparison)
    return comparison


def test_astar_vs_rrt_star() -> ComparisonResult:
    """测试3: A* vs RRT* 路径规划对比."""
    print("\n" + "=" * 70)
    print("测试3: A* vs RRT* 路径规划对比")
    print("=" * 70)

    data = generate_planning_data()

    # 执行 A*
    params_astar = {
        "start": data["start"],
        "goal": data["goal"],
        "grid_size": data["grid_size"],
        "obstacles": data["obstacles"],
    }
    result_astar = call_algorithm("a_star", params_astar)

    # 执行 RRT*
    params_rrt = {
        "start": data["start"],
        "goal": data["goal"],
        "grid_size": data["grid_size"],
        "obstacles": data["obstacles"],
        "max_iterations": 2000,
        "step_size": 2.0,
    }
    result_rrt = call_algorithm("rrt_star", params_rrt)

    # 计算路径长度
    len_astar = 0.0
    len_rrt = 0.0

    if result_astar.success and "path" in result_astar.result:
        len_astar = path_length(result_astar.result["path"])

    if result_rrt.success and "path" in result_rrt.result:
        len_rrt = path_length(result_rrt.result["path"])

    verdict_parts = []
    verdict_parts.append(f"A* 路径长度={len_astar:.2f}, 耗时={result_astar.elapsed_ms:.1f}ms")
    verdict_parts.append(f"RRT* 路径长度={len_rrt:.2f}, 耗时={result_rrt.elapsed_ms:.1f}ms")

    if len_astar > 0 and len_rrt > 0:
        diff_pct = ((len_rrt - len_astar) / len_astar) * 100
        verdict_parts.append(f"RRT* 相对 A* 路径差异={diff_pct:+.2f}%")
    elif len_astar == 0:
        verdict_parts.append("A* 未找到路径")
    elif len_rrt == 0:
        verdict_parts.append("RRT* 未找到路径")

    comparison = ComparisonResult(
        name="A* vs RRT*",
        algo_a_result=result_astar,
        algo_b_result=result_rrt,
        metric_a=len_astar,
        metric_b=len_rrt,
        improvement_pct=0.0,
        verdict=", ".join(verdict_parts),
    )

    _print_comparison(comparison)
    return comparison


# ---------------------------------------------------------------------------
# 报告输出
# ---------------------------------------------------------------------------
def _print_comparison(c: ComparisonResult) -> None:
    """打印单个对比结果."""
    print(f"\n  算法 A: {c.algo_a_result.algorithm_id}")
    print(f"    成功: {c.algo_a_result.success}")
    print(f"    耗时: {c.algo_a_result.elapsed_ms:.1f} ms")
    if not c.algo_a_result.success:
        print(f"    错误: {c.algo_a_result.error}")

    print(f"\n  算法 B: {c.algo_b_result.algorithm_id}")
    print(f"    成功: {c.algo_b_result.success}")
    print(f"    耗时: {c.algo_b_result.elapsed_ms:.1f} ms")
    if not c.algo_b_result.success:
        print(f"    错误: {c.algo_b_result.error}")

    print(f"\n  结论: {c.verdict}")


def print_summary_table(results: list[ComparisonResult]) -> None:
    """打印汇总表格."""
    print("\n")
    print("=" * 70)
    print("算法精度验证汇总报告")
    print("=" * 70)
    print(
        f"{'测试项':<25} {'算法A':<15} {'算法B':<15} "
        f"{'指标A':<12} {'指标B':<12} {'结论':<20}"
    )
    print("-" * 110)

    for r in results:
        algo_a = r.algo_a_result.algorithm_id
        algo_b = r.algo_b_result.algorithm_id

        if r.name == "GPR 置信区间":
            metric_a_str = f"{r.metric_a:.1f}%"
            metric_b_str = f">={r.metric_b:.0f}%"
        elif r.name == "A* vs RRT*":
            metric_a_str = f"{r.metric_a:.2f}"
            metric_b_str = f"{r.metric_b:.2f}"
        else:
            metric_a_str = f"{r.metric_a:.4f}"
            metric_b_str = f"{r.metric_b:.4f}"

        # 判断状态
        if r.name == "GPR 置信区间":
            status = "PASS" if r.metric_a >= 80.0 else "FAIL"
        elif r.name == "A* vs RRT*":
            status = "PASS" if r.metric_a > 0 and r.metric_b > 0 else "FAIL"
        else:
            status = "PASS" if r.algo_a_result.success and r.algo_b_result.success else "FAIL"

        print(
            f"{r.name:<25} {algo_a:<15} {algo_b:<15} "
            f"{metric_a_str:<12} {metric_b_str:<12} {status:<20}"
        )

    print("-" * 110)

    # 统计
    total = len(results)
    passed = sum(
        1
        for r in results
        if (
            r.name == "GPR 置信区间"
            and r.metric_a >= 80.0
        )
        or (
            r.name == "A* vs RRT*"
            and r.metric_a > 0
            and r.metric_b > 0
        )
        or (
            r.name not in ("GPR 置信区间", "A* vs RRT*")
            and r.algo_a_result.success
            and r.algo_b_result.success
        )
    )
    print(f"\n总计: {passed}/{total} 项测试通过")
    print("=" * 70)


# ---------------------------------------------------------------------------
# pytest 测试用例
# ---------------------------------------------------------------------------

class TestAlgorithmAccuracy:
    """pytest 测试类 - 算法精度验证."""

    def test_engine_health(self):
        """验证 algorithm-engine 服务可达."""
        try:
            resp = requests.get(f"{ALGORITHM_ENGINE_URL}/health", timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
            assert data["algorithms_registered"] > 0
        except requests.exceptions.ConnectionError:
            pytest.fail(
                "Algorithm engine not reachable at "
                f"{ALGORITHM_ENGINE_URL}. Start it first."
            )

    def test_5dvar_vs_3dvar(self):
        """5D-VAR vs 3D-VAR: 两者均应成功执行并返回分析场."""
        result = test_5dvar_vs_3dvar()
        assert result.algo_a_result.success, (
            f"5D-VAR failed: {result.algo_a_result.error}"
        )
        assert result.algo_b_result.success, (
            f"3D-VAR failed: {result.algo_b_result.error}"
        )
        assert "analysis_field" in result.algo_a_result.result
        assert "analysis_field" in result.algo_b_result.result

    def test_gpr_confidence_interval(self):
        """GPR 置信区间: 覆盖率应 >= 80%."""
        result = test_gpr_confidence_interval()
        assert result.algo_a_result.success, (
            f"GPR failed: {result.algo_a_result.error}"
        )
        assert result.metric_a >= 80.0, (
            f"GPR coverage {result.metric_a:.1f}% < 80% threshold"
        )

    def test_astar_vs_rrt_star(self):
        """A* vs RRT*: 两者均应成功找到路径."""
        result = test_astar_vs_rrt_star()
        assert result.algo_a_result.success, (
            f"A* failed: {result.algo_a_result.error}"
        )
        assert result.algo_b_result.success, (
            f"RRT* failed: {result.algo_b_result.error}"
        )
        assert result.metric_a > 0, "A* path length should be > 0"
        assert result.metric_b > 0, "RRT* path length should be > 0"


# ---------------------------------------------------------------------------
# 独立运行入口
# ---------------------------------------------------------------------------
def main():
    """独立运行所有验证测试并输出报告."""
    print("UAV Platform V2 - 算法精度验证")
    print(f"Algorithm Engine: {ALGORITHM_ENGINE_URL}")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 健康检查
    try:
        resp = requests.get(f"{ALGORITHM_ENGINE_URL}/health", timeout=10)
        health = resp.json()
        print(f"引擎状态: {health['status']}, 注册算法数: {health['algorithms_registered']}")
    except requests.exceptions.ConnectionError:
        print(f"错误: 无法连接到 {ALGORITHM_ENGINE_URL}")
        print("请确保 algorithm-engine 容器正在运行:")
        print("  docker compose up -d algorithm-engine")
        return

    results: list[ComparisonResult] = []

    # 测试1: 5D-VAR vs 3D-VAR
    try:
        results.append(test_5dvar_vs_3dvar())
    except Exception as e:
        print(f"  测试1异常: {e}")

    # 测试2: GPR 置信区间
    try:
        results.append(test_gpr_confidence_interval())
    except Exception as e:
        print(f"  测试2异常: {e}")

    # 测试3: A* vs RRT*
    try:
        results.append(test_astar_vs_rrt_star())
    except Exception as e:
        print(f"  测试3异常: {e}")

    # 输出汇总
    print_summary_table(results)


if __name__ == "__main__":
    main()
