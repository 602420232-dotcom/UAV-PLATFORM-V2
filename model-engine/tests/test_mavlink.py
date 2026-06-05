"""MAVLink 输出测试 (不依赖 torch)"""
import json
from pathlib import Path
from dataclasses import dataclass


from path_planning.mavlink_output import (
    GeoConverter, MissionPlanGenerator, MAVLinkEncoder, export_to_mavlink
)


@dataclass
class MockWaypoint:
    x: float = 0.0
    y: float = 0.0
    z: float = 100.0
    risk: float = 0.0
    wind_u: float = 0.0
    wind_v: float = 0.0


def test_geo_converter():
    conv = GeoConverter(ref_lat=30.67, ref_lon=104.07)
    gp = conv.local_to_geo(0, 0, 100)
    assert abs(gp.lat - 30.67) < 0.001
    assert abs(gp.lon - 104.07) < 0.001

    gp_east = conv.local_to_geo(10, 0, 100)
    assert gp_east.lon > gp.lon
    gp_north = conv.local_to_geo(0, 10, 100)
    assert gp_north.lat > gp.lat


def test_geo_to_local():
    conv = GeoConverter(ref_lat=30.67, ref_lon=104.07)
    x, y, alt = conv.geo_to_local(30.67, 104.07, 500)
    assert abs(x) < 0.1
    assert abs(y) < 0.1
    x2, _, _ = conv.geo_to_local(30.67, 105.07, 500)
    assert x2 > 95


def test_plan_generation():
    wps = [
        MockWaypoint(x=0, y=0, z=100),
        MockWaypoint(x=5, y=5, z=100),
        MockWaypoint(x=10, y=0, z=100),
    ]
    gen = MissionPlanGenerator()
    plan_str = gen.generate_plan(wps, cruise_speed=15, home=(30.67, 104.07, 500))
    plan = json.loads(plan_str)
    assert plan["version"] == 1
    items = plan["mission"]["items"]
    assert len(items) >= 4
    assert items[-1]["command"] == 20


def test_plan_save():
    wps = [MockWaypoint(x=0, y=0, z=100), MockWaypoint(x=1, y=1, z=100)]
    gen = MissionPlanGenerator()
    path = gen.save_plan(wps, "/tmp/test_mission.plan", cruise_speed=10)
    assert Path(path).exists()
    content = json.loads(Path(path).read_text())
    assert content["mission"]["cruiseSpeed"] == 10


def test_export_to_plan():
    wps = [MockWaypoint(x=0, y=0, z=100), MockWaypoint(x=2, y=3, z=150)]
    result = export_to_mavlink(wps, output_type="plan", speed=15)
    plan = json.loads(result)
    assert "mission" in plan


def test_export_to_mavlink_binary():
    wps = [MockWaypoint(x=0, y=0, z=100)]
    result = export_to_mavlink(wps, output_type="mavlink")
    assert isinstance(result, str)
    assert len(result) > 0


def test_mavlink_encoder_heartbeat():
    encoder = MAVLinkEncoder()
    frame = encoder.heartbeat(armed=False)
    assert frame[0] == 0xFD
    assert frame[6] == 1


def test_mavlink_encoder_goto():
    encoder = MAVLinkEncoder()
    frame = encoder.goto_waypoint(30.67, 104.07, 100, 10)
    assert frame[0] == 0xFD
    assert frame[8] == 76


def test_mavlink_rtl():
    encoder = MAVLinkEncoder()
    frame = encoder.rtl()
    assert frame[0] == 0xFD
