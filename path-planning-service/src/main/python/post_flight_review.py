#!/usr/bin/env python3
"""
飞行后复盘报告生成器

支持:
- 飞行数据分析
- 异常事件检测
- 改进建议生成
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class FlightEvent:
    """飞行事件"""
    timestamp: float
    event_type: str  # TAKEOFF, LANDING, WAYPOINT, WARNING, ERROR
    description: str
    severity: str = "INFO"  # INFO, WARNING, ERROR, CRITICAL
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlightSegment:
    """飞行段"""
    start_time: float
    end_time: float
    start_position: tuple
    end_position: tuple
    distance: float
    avg_speed: float
    max_speed: float
    energy_consumed: float
    risk_score: float


class PostFlightReview:
    """
    飞行后复盘分析器

    分析飞行日志，生成结构化复盘报告。
    """

    def __init__(self, mission_name: str = ""):
        self.mission_name = mission_name
        self.events: List[FlightEvent] = []
        self.segments: List[FlightSegment] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def add_event(self, event: FlightEvent):
        """添加飞行事件"""
        self.events.append(event)
        self.events.sort(key=lambda e: e.timestamp)

    def add_segment(self, segment: FlightSegment):
        """添加飞行段"""
        self.segments.append(segment)

    def set_flight_time(self, start: float, end: float):
        """设置飞行起止时间"""
        self.start_time = start
        self.end_time = end

    def analyze_anomalies(self) -> List[Dict]:
        """
        检测飞行中的异常事件

        Returns:
            异常事件列表
        """
        anomalies = []

        # 检查急转弯
        for i in range(1, len(self.segments)):
            seg = self.segments[i]
            if seg.max_speed > 15.0 and seg.avg_speed > 10.0:
                anomalies.append({
                    'type': 'HIGH_SPEED',
                    'time': seg.start_time,
                    'description': f"飞行段速度过高: 平均{seg.avg_speed:.1f}m/s, 最大{seg.max_speed:.1f}m/s",
                    'severity': 'WARNING',
                    'suggestion': '建议降低巡航速度至10m/s以下以提高安全性'
                })

        # 检查高风险区域
        for seg in self.segments:
            if seg.risk_score > 50:
                anomalies.append({
                    'type': 'HIGH_RISK',
                    'time': seg.start_time,
                    'description': f"经过高风险区域: 风险评分{seg.risk_score:.1f}",
                    'severity': 'WARNING',
                    'suggestion': '建议重新规划路径避开高风险区域'
                })

        # 检查能耗异常
        if len(self.segments) >= 2:
            avg_energy = sum(s.energy_consumed for s in self.segments) / len(self.segments)
            for seg in self.segments:
                if seg.energy_consumed > avg_energy * 1.5:
                    anomalies.append({
                        'type': 'HIGH_ENERGY',
                        'time': seg.start_time,
                        'description': f"能耗异常: {seg.energy_consumed:.1f} (平均{avg_energy:.1f})",
                        'severity': 'INFO',
                        'suggestion': '检查该段是否存在逆风或载重变化'
                    })

        return anomalies

    def generate_report(self) -> Dict:
        """
        生成完整复盘报告

        Returns:
            结构化复盘报告
        """
        anomalies = self.analyze_anomalies()

        # 统计
        total_distance = sum(s.distance for s in self.segments)
        total_energy = sum(s.energy_consumed for s in self.segments)
        avg_speed = sum(s.avg_speed for s in self.segments) / len(self.segments) if self.segments else 0
        max_risk = max((s.risk_score for s in self.segments), default=0)

        # 事件统计
        warning_count = sum(1 for e in self.events if e.severity == 'WARNING' or e.severity == 'ERROR')

        # 生成改进建议
        improvements = []
        if total_energy > 100:
            improvements.append("能耗较高，建议优化航线减少逆风段")
        if max_risk > 60:
            improvements.append(f"任务中存在高风险区域(评分{max_risk:.1f})，建议避开")
        if warning_count > 0:
            improvements.append(f"飞行中存在{warning_count}个异常事件，建议检查飞行参数")
        if self.segments and avg_speed < 5:
            improvements.append("平均航速较低，可优化时间窗规划")

        report = {
            'mission_name': self.mission_name,
            'report_generated': datetime.now().isoformat(),
            'flight_summary': {
                'total_distance': round(total_distance, 2),
                'total_energy': round(total_energy, 2),
                'avg_speed': round(avg_speed, 2),
                'max_risk_score': round(max_risk, 2),
                'segment_count': len(self.segments),
                'event_count': len(self.events),
                'warning_count': warning_count,
                'flight_duration': (self.end_time - self.start_time) if self.start_time and self.end_time else 0
            },
            'anomalies': anomalies,
            'improvement_suggestions': improvements,
            'events': [
                {
                    'time': e.timestamp,
                    'type': e.event_type,
                    'description': e.description,
                    'severity': e.severity
                }
                for e in self.events
            ],
            'segments': [
                {
                    'start_time': s.start_time,
                    'end_time': s.end_time,
                    'distance': round(s.distance, 2),
                    'avg_speed': round(s.avg_speed, 2),
                    'energy': round(s.energy_consumed, 2),
                    'risk_score': round(s.risk_score, 2)
                }
                for s in self.segments
            ]
        }

        return report

    def export_json(self, filepath: str):
        """导出复盘报告为JSON文件"""
        report = self.generate_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"复盘报告已导出至: {filepath}")


if __name__ == "__main__":
    # 演示
    review = PostFlightReview("示例任务-001")

    review.set_flight_time(0, 600)
    review.add_segment(FlightSegment(0, 120, (0, 0), (100, 0), 100, 8.3, 12.0, 15.0, 20))
    review.add_segment(FlightSegment(120, 240, (100, 0), (200, 50), 111.8, 8.3, 18.0, 18.0, 65))
    review.add_segment(FlightSegment(240, 600, (200, 50), (0, 0), 206.2, 8.3, 10.0, 30.0, 30))

    review.add_event(FlightEvent(0, "TAKEOFF", "无人机起飞", "INFO"))
    review.add_event(FlightEvent(120, "WAYPOINT", "到达航点 1", "INFO"))
    review.add_event(FlightEvent(240, "WAYPOINT", "到达航点 2", "INFO"))
    review.add_event(FlightEvent(600, "LANDING", "降落完成", "INFO"))

    report = review.generate_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
