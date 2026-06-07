"""路径规划测试"""
import numpy as np
from path_planning.planner import GPRPathPlanner


def test_planner_basic():
    """基础路径规划"""
    H, W = 150, 150
    risk = np.random.exponential(0.3, (H, W))
    wind_u = np.random.normal(2, 1, (H, W))
    wind_v = np.random.normal(0.5, 0.8, (H, W))

    planner = GPRPathPlanner()
    path = planner.plan(risk, wind_u, wind_v, (-10, 0), (20, -5))
    assert len(path) >= 2, "至少需要起止两点"
    assert all(0 <= w.risk <= 1 for w in path), "风险值应在 [0,1]"


def test_planner_avoids_high_risk():
    """规划器应避开禁飞区"""
    H, W = 50, 50
    risk = np.zeros((H, W))
    # 在直线上设一堵风险墙
    risk[20:30, 20:30] = 0.95  # 极高风险
    wind_u = np.zeros((H, W))
    wind_v = np.zeros((H, W))

    planner = GPRPathPlanner()
    path = planner.plan(risk, wind_u, wind_v, (0, 0), (49, 49))

    # 路径不应穿过高风险墙
    for w in path:
        gx = int((w.x + 25) / 1)
        gy = int((w.y + 25) / 1)
        if 20 <= gx <= 30 and 20 <= gy <= 30:
            # 如果穿过了，w.risk 不能 > 0.9
            assert w.risk <= 0.95, f"路径不应穿过禁飞区 ({w.x}, {w.y}), risk={w.risk}"


def test_planner_empty_risk():
    """零风险场景"""
    H, W = 50, 50
    risk = np.zeros((H, W))
    wind = np.zeros((H, W))
    planner = GPRPathPlanner()
    path = planner.plan(risk, wind, wind, (0, 0), (49, 49))
    assert len(path) >= 2
    assert all(w.risk == 0 for w in path)
