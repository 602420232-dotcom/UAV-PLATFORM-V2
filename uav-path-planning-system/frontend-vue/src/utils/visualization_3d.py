"""
可视化增强引擎 - 3D轨迹可视化 + 气象场动态展示 + 多无人机协同展示
"""
import numpy as np
from typing import List, Tuple, Dict


class TrajectoryVisualizer3D:
    """3D轨迹可视化生成器"""

    @staticmethod
    def generate_trajectory_geojson(waypoints_3d: List[Tuple[float, float, float]],
                                    drone_id: str, color: str = "#00d4ff") -> dict:
        """生成3D轨迹GeoJSON"""
        coordinates = [[lng, lat, alt] for lat, lng, alt in waypoints_3d]
        return {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {
                    "drone_id": drone_id,
                    "stroke": color,
                    "stroke-width": 3,
                    "stroke-opacity": 0.8
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates
                }
            }]
        }

    @staticmethod
    def generate_waypoint_markers(
            waypoints: List[Tuple[float, float, float]],
            drone_id: str) -> dict:
        """生成航点标记"""
        features = []
        for i, (lat, lng, alt) in enumerate(waypoints):
            features.append({
                "type": "Feature",
                "properties": {
                    "drone_id": drone_id,
                    "waypoint_index": i,
                    "altitude": alt,
                    "marker-color": "#ff6b6b"
                    if i == 0 else "#ffd700"
                    if i == len(waypoints) - 1 else "#4ecdc4",
                    "marker-size": "large",
                    "marker-symbol": "circle"
                },
                "geometry": {"type": "Point", "coordinates": [lng, lat, alt]}
            })
        return {"type": "FeatureCollection", "features": features}


class WeatherFieldVisualizer:
    """气象场动态可视化"""

    @staticmethod
    def generate_wind_field(weather_grid: List[Dict], bounds: Tuple) -> dict:
        """生成风场箭头图数据"""
        arrows = []
        for cell in weather_grid:
            arrows.append({
                "lon": cell["lon"],
                "lat": cell["lat"],
                "u": cell.get("wind_u", 0),
                "v": cell.get("wind_v", 0),
                "speed": cell.get("wind_speed", 0),
                "color": "#ff0000"
                if cell.get("wind_speed", 0) > 10
                else "#ffaa00"
                if cell.get("wind_speed", 0) > 5
                else "#00ff00"
            })
        return {
            "type": "wind_field",
            "arrows": arrows,
            "bounds": {"west": bounds[0], "south": bounds[1], "east": bounds[2], "north": bounds[3]}
        }

    @staticmethod
    def generate_risk_heatmap(weather_data: List[Dict], grid_size: int = 20) -> dict:
        """生成风险热力图"""
        heatmap = []
        for i in range(grid_size):
            for j in range(grid_size):
                base_lat = 39.8 + i * 0.01
                base_lon = 116.3 + j * 0.01
                wind = np.random.exponential(3) if weather_data else 5
                risk = min(100, wind * 8)
                heatmap.append({
                    "lat": base_lat, "lon": base_lon,
                    "value": risk,
                    "level": "HIGH" if risk > 60 else "MEDIUM" if risk > 30 else "LOW"
                })
        return {"type": "heatmap", "grid": heatmap, "grid_size": grid_size}


class MultiDroneCoordinator:
    """多无人机协同展示编排器"""

    def __init__(self):
        self.drones: Dict[str, dict] = {}
        self.flight_paths: Dict[str, list] = {}

    def register_drone(self, drone_id: str, initial_position: Tuple[float, float, float]):
        """注册无人机"""
        self.drones[drone_id] = {
            "id": drone_id,
            "position": {"lon": initial_position[0], "lat": initial_position[1], "alt": initial_position[2]},
            "status": "idle",
            "battery": 100,
            "speed": 0,
            "heading": 0
        }

    def update_drone_position(self, drone_id: str, position: Tuple[float, float, float],
                              status: str = None, battery: float = None):
        """更新无人机位置"""
        if drone_id in self.drones:
            self.drones[drone_id]["position"] = {"lon": position[0], "lat": position[1], "alt": position[2]}
            if status:
                self.drones[drone_id]["status"] = status
            if battery is not None:
                self.drones[drone_id]["battery"] = battery
            if drone_id not in self.flight_paths:
                self.flight_paths[drone_id] = []
            self.flight_paths[drone_id].append(position)

    def get_scene_state(self) -> dict:
        """获取完整场景状态"""
        return {
            "drones": list(self.drones.values()),
            "paths": {k: v[-100:] for k, v in self.flight_paths.items()},
            "active_count": sum(1 for d in self.drones.values() if d["status"] in ("flying", "hovering")),
            "timestamp": __import__("time").time()
        }

    def detect_conflicts(self) -> List[dict]:
        """检测多机冲突"""
        conflicts = []
        positions = {did: d["position"] for did, d in self.drones.items()
                     if d["status"] in ("flying", "hovering")}
        ids = list(positions.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                p1, p2 = positions[ids[i]], positions[ids[j]]
                dist = ((p1["lon"] - p2["lon"])**2 + (p1["lat"] - p2["lat"])**2)**0.5 * 111000
                if dist < 50:
                    conflicts.append({
                        "drone_a": ids[i], "drone_b": ids[j],
                        "distance_m": round(dist, 1),
                        "risk": "HIGH" if dist < 20 else "MEDIUM",
                        "suggestion": "调整航向" if dist > 20 else "紧急避让"
                    })
        return conflicts
