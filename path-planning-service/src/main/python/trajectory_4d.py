"""
4D轨迹可视化引擎
三维空间(x, y, z) + 时间轴(t) 四维轨迹生成与分析
"""
import numpy as np
from typing import List, Tuple, Optional
from datetime import datetime, timedelta


class Trajectory4DGenerator:
    """4D轨迹生成器 (x, y, z, t)"""

    @staticmethod
    def generate_4d(waypoints: List[Tuple[float, float, float]],
                    speeds: List[float] = None,
                    start_time: str = None) -> dict:
        """生成4D轨迹"""
        speeds = speeds or [10.0] * (len(waypoints) - 1)
        start_time = start_time or datetime.now().isoformat()
        current_time = datetime.fromisoformat(start_time)

        track = []
        segments = []
        total_distance = 0.0

        for i in range(len(waypoints) - 1):
            x1, y1, z1 = waypoints[i]
            x2, y2, z2 = waypoints[i + 1]
            dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)
            speed = speeds[i] if i < len(speeds) else 10.0
            duration = dist / speed if speed > 0 else 1.0

            n_points = max(10, int(duration * 10))
            for j in range(n_points):
                t = j / n_points
                px = x1 + (x2 - x1) * t
                py = y1 + (y2 - y1) * t
                pz = z1 + (z2 - z1) * t
                track.append({
                    "x": round(px, 4), "y": round(py, 4), "z": round(pz, 1),
                    "t": current_time.isoformat(),
                    "segment": i, "progress": round(t * 100, 1),
                    "speed": round(speed, 1)
                })
                current_time += timedelta(seconds=duration / n_points)

            segments.append({
                "from": i, "to": i + 1,
                "distance": round(dist, 2),
                "duration": round(duration, 1),
                "speed": round(speed, 1),
                "start_time": (current_time - timedelta(seconds=duration)).isoformat(),
                "end_time": current_time.isoformat()
            })
            total_distance += dist

        return {
            "type": "FeatureCollection",
            "metadata": {
                "total_distance": round(total_distance, 2),
                "total_duration": round(sum(s["duration"] for s in segments), 1),
                "waypoint_count": len(waypoints),
                "start_time": start_time,
                "end_time": current_time.isoformat(),
                "dimensions": ["x", "y", "z", "t"]
            },
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[p["x"], p["y"], p["z"], p["t"]] for p in track]
                },
                "properties": {"type": "4d_trajectory"}
            }],
            "track": track,
            "segments": segments
        }


class Trajectory4DAnalyzer:
    """4D轨迹分析器"""

    @staticmethod
    def analyze_speed_profile(track: List[dict]) -> dict:
        speeds = [p["speed"] for p in track if "speed" in p]
        return {
            "avg_speed": round(np.mean(speeds), 2) if speeds else 0,
            "max_speed": round(max(speeds), 2) if speeds else 0,
            "min_speed": round(min(speeds), 2) if speeds else 0,
            "speed_std": round(np.std(speeds), 2) if speeds else 0
        }

    @staticmethod
    def detect_anomalies(track: List[dict], z_threshold: float = 50) -> List[dict]:
        anomalies = []
        for i, p in enumerate(track):
            if p["z"] > 300:
                anomalies.append({"index": i, "time": p["t"], "type": "altitude_warning", "value": p["z"]})
            if i > 0 and p.get("speed", 0) > 20:
                anomalies.append({"index": i, "time": p["t"], "type": "speed_warning", "value": p["speed"]})
        return anomalies


class Trajectory4DPlayer:
    """4D轨迹播放器 - 时间轴控制"""

    def __init__(self, track: List[dict]):
        self.track = track
        self.total_frames = len(track)
        self.current_frame = 0

    def next_frame(self) -> Optional[dict]:
        if self.current_frame < self.total_frames:
            frame = self.track[self.current_frame]
            self.current_frame += 1
            return frame
        return None

    def seek_to(self, progress: float) -> List[dict]:
        idx = int(progress / 100 * self.total_frames)
        self.current_frame = min(idx, self.total_frames - 1)
        return self.track[:self.current_frame + 1]

    def get_time_slice(self, start_idx: int, end_idx: int) -> List[dict]:
        return self.track[start_idx:end_idx + 1]
