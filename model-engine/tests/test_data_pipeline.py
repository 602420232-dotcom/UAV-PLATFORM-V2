"""数据管道测试"""
import numpy as np
from data_pipeline.training_data import PhysicsConstrainedGenerator


def test_generate_pair():
    gen = PhysicsConstrainedGenerator(seed=42)
    patterns = ["plain_winter", "summer_heat", "rain_event",
                "mountain_wave", "city_heat_island"]
    for p in patterns:
        coarse, fine = gen.generate_pair(p)
        assert coarse.shape == (11, 50, 50), f"{p}: coarse {coarse.shape}"
        assert fine.shape == (6, 150, 150), f"{p}: fine {fine.shape}"
        assert not np.any(np.isnan(coarse))
        assert not np.any(np.isnan(fine))


def test_physical_constraints():
    """物理约束检验: 温度不能低于180K"""
    gen = PhysicsConstrainedGenerator()
    for p in ["plain_winter", "summer_heat"]:
        coarse, fine = gen.generate_pair(p)
        assert (fine[2] > 180).all(), f"{p}: t2m < 180K"


def test_dem():
    gen = PhysicsConstrainedGenerator()
    dem = gen._add_dem(50, 50)
    assert dem.shape == (50, 50)
    # 成都平原西高东低
    assert dem[0, 0] > dem[-1, -1]  # 西北 > 东南
