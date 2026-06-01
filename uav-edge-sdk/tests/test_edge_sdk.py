#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UAV Edge SDK - 测试文件
覆盖: path_planner, risk_assessor, flight_controller, SDKConfig, mission
"""
import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(__file__))

from edge_sdk import EdgeSDK, create_sdk
from edge_sdk.config import SDKConfig


def test_path_planner():
    """测试路径规划"""
    sdk = create_sdk({'grid_width': 100, 'grid_height': 100, 'resolution': 1.0})
    path = sdk.plan_path(start=(0, 0), goal=(10, 10), obstacles=[])
    assert len(path) > 0, "Path should not be empty"
    path2 = sdk.plan_path(start=(0, 0), goal=(10, 10), obstacles=[(5, 5), (5, 6)])
    assert len(path2) > 0, "Path with obstacles should not be empty"
    path3 = sdk.plan_path(start=(0, 0), goal=(10, 10), obstacles=[(i, i) for i in range(11)])
    print(f"  No-path case: length={len(path3)}")
    print("✅ Path Planner tests passed!")


def test_risk_assessor():
    """测试气象风险评估"""
    sdk = create_sdk()
    low = sdk.assess_weather_risk({'wind_speed': 3.0, 'temperature': 20.0, 'visibility': 15.0, 'has_thunderstorm': False})
    assert low['level'] == 'LOW', f"Expected LOW, got {low['level']}"
    high = sdk.assess_weather_risk({'wind_speed': 15.0, 'temperature': 35.0, 'visibility': 2.0, 'has_thunderstorm': False})
    assert high['level'] in ['HIGH', 'SEVERE'], f"Expected HIGH/SEVERE, got {high['level']}"
    storm = sdk.assess_weather_risk({'wind_speed': 5.0, 'temperature': 25.0, 'visibility': 8.0, 'has_thunderstorm': True})
    assert '雷暴' in str(storm['warnings']), "Should have thunderstorm warning"
    print("✅ Risk Assessor tests passed!")


def test_flight_controller():
    """测试飞控接口"""
    sdk = create_sdk()
    assert sdk.connect_flight_controller() is True
    state = sdk.get_uav_state()
    assert isinstance(state, dict), f"Expected dict, got {type(state)}"
    assert sdk.arm() is True
    assert sdk.disarm() is True
    sdk.disconnect_flight_controller()
    print("✅ Flight Controller tests passed!")


def test_takeoff_and_land():
    """测试起飞和降落"""
    sdk = create_sdk()
    sdk.connect_flight_controller()
    sdk.arm()
    result_takeoff = sdk.takeoff(altitude=10)
    assert result_takeoff is not None, "Takeoff should return a result"
    result_land = sdk.land()
    assert result_land is not None, "Land should return a result"
    sdk.disarm()
    sdk.disconnect_flight_controller()
    print("✅ Takeoff & Land tests passed!")


def test_upload_and_execute_mission():
    """测试上传和执行任务"""
    sdk = create_sdk()
    waypoints = [(0, 0, 10), (1, 1, 15), (2, 2, 10)]
    result_upload = sdk.upload_mission(waypoints)
    assert result_upload is not None, "Upload mission should return a result"
    result_exec = sdk.execute_mission()
    assert result_exec is not None, "Execute mission should return a result"
    print("✅ Upload & Execute Mission tests passed!")


def test_sdk_config():
    """测试SDKConfig配置管理"""
    config = SDKConfig()
    assert config.get('grid_width') == 100, "Default grid_width should be 100"
    assert config.get('nonexistent', 'default') == 'default', "Missing key should return default"
    config.set('grid_width', 200)
    assert config.get('grid_width') == 200, "Should return updated value"
    config.update({'resolution': 2.0, 'offline_mode': False})
    assert config.get('resolution') == 2.0
    assert config.get('offline_mode') is False
    d = config.to_dict()
    assert isinstance(d, dict) and len(d) > 5

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        fpath = f.name
    try:
        config.save(fpath)
        loaded = SDKConfig.load(fpath)
        assert loaded.get('grid_width') == 200
        assert loaded.get('resolution') == 2.0
    finally:
        os.unlink(fpath)

    config2 = SDKConfig({'wind_speed_threshold': 12.0})
    assert config2.get('wind_speed_threshold') == 12.0
    assert config2.get('grid_width') == 100

    global_config = SDKConfig()
    assert global_config.get('log_level') == 'INFO'
    print("✅ SDKConfig tests passed!")


def main():
    print("=" * 60)
    print("UAV Edge SDK - Test Suite")
    print("=" * 60)
    tests = [
        test_path_planner, test_risk_assessor, test_flight_controller,
        test_takeoff_and_land, test_upload_and_execute_mission, test_sdk_config
    ]
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"❌ {t.__name__} failed: {e}")
            import traceback; traceback.print_exc()
            return 1
    print("\n" + "=" * 60)
    print("🎉 All tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
