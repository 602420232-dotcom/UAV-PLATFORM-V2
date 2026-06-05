"""融合模块测试"""
import torch
from fusion.ensemble import DynamicWeightFusion, PhysicsConstraint


def test_fusion():
    fusion = DynamicWeightFusion()
    fields = {
        "model_a": torch.randn(1, 6, 50, 50),
        "model_b": torch.randn(1, 6, 50, 50),
    }
    fused = fusion.fuse(fields)
    assert fused.shape == (1, 6, 50, 50)


def test_fusion_single_model():
    """单模型不应该炸"""
    fusion = DynamicWeightFusion()
    fields = {"only_model": torch.randn(1, 6, 50, 50)}
    fused = fusion.fuse(fields)
    assert fused is not None


def test_physics_constraint():
    pc = PhysicsConstraint()
    field = torch.randn(1, 6, 50, 50) * 0.1
    # 故意造一个不符合物理的值
    field[:, 2] = 150  # t2m = 150K, 低于180
    constrained = pc(field)
    assert (constrained[:, 2] >= 180).all()
    assert (constrained[:, 3] >= 0).all()
    assert (constrained[:, 4] >= 50000).all()
