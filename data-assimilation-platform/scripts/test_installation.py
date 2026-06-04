#!/usr/bin/env python3
"""
测试安装和基本功能
"""

import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """测试所有模块导入"""
    print("测试模块导入...")
    
    modules_to_test = [
        ("bayesian_assimilation", "主模块"),
        ("bayesian_assimilation.utils.config", "配置模块"),
        ("bayesian_assimilation.core.assimilator", "同化器模块"),
        ("bayesian_assimilation.core.compatible_assimilator", "兼容性模块"),
    ]
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {description} 导入成功")
        except ImportError as e:
            print(f"❌ {description} 导入失败: {e}")
            return False
    
    return True


def test_quick_start():
    """快速启动测试"""
    print("\n快速启动测试...")
    
    try:
        from bayesian_assimilation.utils.config import ConfigFactory
        from bayesian_assimilation.core.assimilator import BaseAssimilator
        import numpy as np
        
        # 创建配置
        config = ConfigFactory.create("base", grid_resolution=50.0)
        
        # 创建同化器
        assim = BaseAssimilator(config)
        
        # 初始化小网格
        assim.initialize_grid((200, 200, 50), resolution=50)
        
        print(f"✅ 网格初始化: {assim.grid_shape}")
        
        # 创建模拟数据
        if assim.grid_shape:
            nx, ny, nz = assim.grid_shape
            background = np.random.normal(5, 1, (nx, ny, nz))
            
            # 模拟观测
            n_obs = 5
            observations = np.random.normal(5, 0.5, n_obs)
            obs_locations = np.random.randint(0, 10, (n_obs, 3))
            
            # 执行同化
            analysis, variance = assim.assimilate_3dvar(
                background, observations, obs_locations
            )
            
            print(f"✅ 同化完成，分析形状: {analysis.shape}")
            print(f"✅ 方差形状: {variance.shape}")
            print(f"✅ 平均方差: {np.mean(variance):.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 快速启动测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("="*60)
    print("贝叶斯同化系统 - 安装测试")
    print("="*60)
    
    # 测试导入
    if not test_imports():
        print("\n❌ 导入测试失败，请检查安装")
        return False
    
    # 快速启动测试
    if not test_quick_start():
        print("\n❌ 快速启动测试失败")
        return False
    
    print("\n" + "="*60)
    print("✅ 所有测试通过！")
    print("="*60)
    print("\n下一步:")
    print("1. 运行完整演示: python examples/all_demos.py")
    print("2. 运行GPU测试: python examples/gpu_acceleration.py")
    print("3. 运行性能测试: python examples/parallel_demo.py")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)