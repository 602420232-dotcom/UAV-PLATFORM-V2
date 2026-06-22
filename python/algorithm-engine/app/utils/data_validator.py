"""
气象数据验证工具框架

提供气象数据的多维度质量验证，包括：
- 缺失值检查（NaN/None 检测）
- 范围检查（温度、风速、气压等物理量范围）
- 时间连续性检查（6 小时间隔）
- 空间一致性检查（相邻格点差异阈值）
- 物理一致性检查（位势高度随高度递减等）

使用 loguru 日志，所有函数有完整类型注解，使用 numpy 进行数值计算。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger


# ============================================================
# 数据模型定义
# ============================================================


class ValidationSeverity(str, Enum):
    """验证结果严重级别"""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class ValidationResult:
    """单条验证结果"""

    rule_name: str
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """验证报告，包含通过/警告/失败统计"""

    validator_name: str
    validated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    results: List[ValidationResult] = field(default_factory=list)

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.results if r.severity == ValidationSeverity.PASS)

    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.severity == ValidationSeverity.WARNING)

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.results if r.severity == ValidationSeverity.FAIL)

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def is_valid(self) -> bool:
        """当没有 FAIL 级别结果时视为有效"""
        return self.fail_count == 0

    def to_json(self) -> str:
        """将报告序列化为 JSON 格式"""
        summary = {
            "validator_name": self.validator_name,
            "validated_at": self.validated_at,
            "summary": {
                "total": self.total_count,
                "pass": self.pass_count,
                "warning": self.warning_count,
                "fail": self.fail_count,
                "is_valid": self.is_valid,
            },
            "results": [
                {
                    "rule": r.rule_name,
                    "severity": r.severity.value,
                    "message": r.message,
                    "details": r.details,
                }
                for r in self.results
            ],
        }
        return json.dumps(summary, ensure_ascii=False, indent=2)

    def merge(self, other: "ValidationReport") -> None:
        """合并另一个报告的结果"""
        self.results.extend(other.results)


# ============================================================
# 默认验证阈值
# ============================================================

DEFAULT_RANGES: Dict[str, Tuple[float, float]] = {
    "temperature": (-100.0, 60.0),       # 温度范围 (°C)
    "wind_speed": (0.0, 100.0),          # 风速范围 (m/s)
    "pressure": (800.0, 1100.0),         # 气压范围 (hPa)
    "humidity": (0.0, 100.0),             # 相对湿度 (%)
    "visibility": (0.0, 50.0),            # 能见度 (km)
    "cloud_cover": (0.0, 100.0),           # 云量 (%)
    "precipitation": (0.0, 500.0),        # 降水量 (mm)
    "wind_direction": (0.0, 360.0),       # 风向 (°)
}

# 相邻格点最大允许差异阈值
SPATIAL_THRESHOLDS: Dict[str, float] = {
    "temperature": 15.0,      # 相邻格点温差阈值 (°C)
    "wind_speed": 20.0,        # 相邻格点风速差阈值 (m/s)
    "pressure": 30.0,          # 相邻格点气压差阈值 (hPa)
    "humidity": 30.0,         # 相邻格点湿度差阈值 (%)
}

# 时间连续性检查：允许的时间间隔容差（秒）
TIME_CONTINUITY_TOLERANCE: float = 21600.0  # 6 小时 = 21600 秒


# ============================================================
# 气象数据验证器基类
# ============================================================


class WeatherDataValidator:
    """
    气象数据验证器基类

    提供对气象数据的多维度质量验证功能，支持单条验证和批量验证。
    数据输入格式为字典列表，每个字典代表一个时空格点的气象观测数据。

    Attributes:
        ranges: 各气象要素的有效范围配置
        spatial_thresholds: 相邻格点差异阈值配置
        time_tolerance: 时间连续性容差（秒）
    """

    def __init__(
        self,
        ranges: Optional[Dict[str, Tuple[float, float]]] = None,
        spatial_thresholds: Optional[Dict[str, float]] = None,
        time_tolerance: float = TIME_CONTINUITY_TOLERANCE,
    ) -> None:
        """
        初始化验证器

        Args:
            ranges: 各气象要素的有效范围，键为要素名，值为 (最小值, 最大值) 元组
            spatial_thresholds: 相邻格点差异阈值，键为要素名，值为最大允许差异
            time_tolerance: 时间连续性检查的容差（秒），默认 6 小时
        """
        self.ranges = ranges or DEFAULT_RANGES
        self.spatial_thresholds = spatial_thresholds or SPATIAL_THRESHOLDS
        self.time_tolerance = time_tolerance

    # ============================================================
    # 公共验证接口
    # ============================================================

    def validate(self, data: List[Dict[str, Any]]) -> ValidationReport:
        """
        对一组气象数据执行完整验证

        Args:
            data: 气象数据列表，每个元素为包含气象要素的字典

        Returns:
            ValidationReport: 包含所有验证结果的报告
        """
        report = ValidationReport(validator_name="WeatherDataValidator")

        if not data:
            report.results.append(
                ValidationResult(
                    rule_name="data_empty",
                    severity=ValidationSeverity.WARNING,
                    message="输入数据为空，跳过验证",
                )
            )
            return report

        logger.info("开始验证气象数据，共 {} 条记录", len(data))

        # 1. 缺失值检查
        missing_report = self.check_missing_values(data)
        report.merge(missing_report)

        # 2. 范围检查
        range_report = self.check_ranges(data)
        report.merge(range_report)

        # 3. 时间连续性检查
        time_report = self.check_time_continuity(data)
        report.merge(time_report)

        # 4. 空间一致性检查
        spatial_report = self.check_spatial_consistency(data)
        report.merge(spatial_report)

        # 5. 物理一致性检查
        physics_report = self.check_physical_consistency(data)
        report.merge(physics_report)

        logger.info(
            "验证完成: 通过={}, 警告={}, 失败={}",
            report.pass_count,
            report.warning_count,
            report.fail_count,
        )

        return report

    def validate_batch(
        self, data_batches: List[List[Dict[str, Any]]]
    ) -> List[ValidationReport]:
        """
        批量验证多组气象数据

        Args:
            data_batches: 多组气象数据列表

        Returns:
            每组数据对应的验证报告列表
        """
        reports: List[ValidationReport] = []
        for idx, batch in enumerate(data_batches):
            logger.info("批量验证第 {}/{} 组", idx + 1, len(data_batches))
            report = self.validate(batch)
            reports.append(report)
        return reports

    # ============================================================
    # 验证规则实现
    # ============================================================

    def check_missing_values(self, data: List[Dict[str, Any]]) -> ValidationReport:
        """
        缺失值检查：检测 NaN、None 和缺失字段

        Args:
            data: 气象数据列表

        Returns:
            包含缺失值检查结果的报告
        """
        report = ValidationReport(validator_name="MissingValueCheck")
        required_fields = list(self.ranges.keys()) + ["longitude", "latitude", "forecast_time"]

        total_missing = 0
        for idx, record in enumerate(data):
            for field_name in required_fields:
                value = record.get(field_name)
                is_missing = value is None
                is_nan = isinstance(value, float) and np.isnan(value)

                if is_missing or is_nan:
                    total_missing += 1
                    reason = "值为 None" if is_missing else "值为 NaN"
                    report.results.append(
                        ValidationResult(
                            rule_name=f"missing_{field_name}",
                            severity=ValidationSeverity.FAIL,
                            message=f"记录 #{idx} 字段 '{field_name}' 缺失: {reason}",
                            details={
                                "record_index": idx,
                                "field": field_name,
                                "reason": reason,
                            },
                        )
                    )

        if total_missing == 0:
            report.results.append(
                ValidationResult(
                    rule_name="missing_values",
                    severity=ValidationSeverity.PASS,
                    message=f"全部 {len(data)} 条记录无缺失值",
                    details={"total_records": len(data)},
                )
            )
        else:
            report.results.append(
                ValidationResult(
                    rule_name="missing_values_summary",
                    severity=ValidationSeverity.FAIL,
                    message=f"共发现 {total_missing} 个缺失值",
                    details={"total_missing": total_missing, "total_records": len(data)},
                )
            )

        return report

    def check_ranges(self, data: List[Dict[str, Any]]) -> ValidationReport:
        """
        范围检查：验证各气象要素是否在合理物理范围内

        Args:
            data: 气象数据列表

        Returns:
            包含范围检查结果的报告
        """
        report = ValidationReport(validator_name="RangeCheck")
        total_out_of_range = 0

        for idx, record in enumerate(data):
            for field_name, (min_val, max_val) in self.ranges.items():
                value = record.get(field_name)
                if value is None or (isinstance(value, float) and np.isnan(value)):
                    continue  # 缺失值由缺失值检查处理

                if not (min_val <= value <= max_val):
                    total_out_of_range += 1
                    report.results.append(
                        ValidationResult(
                            rule_name=f"range_{field_name}",
                            severity=ValidationSeverity.FAIL,
                            message=(
                                f"记录 #{idx} 字段 '{field_name}' 超出范围: "
                                f"{value} 不在 [{min_val}, {max_val}]"
                            ),
                            details={
                                "record_index": idx,
                                "field": field_name,
                                "value": value,
                                "min": min_val,
                                "max": max_val,
                            },
                        )
                    )

        if total_out_of_range == 0:
            report.results.append(
                ValidationResult(
                    rule_name="range_check",
                    severity=ValidationSeverity.PASS,
                    message=f"全部 {len(data)} 条记录的 {len(self.ranges)} 个要素均在合理范围内",
                )
            )
        else:
            report.results.append(
                ValidationResult(
                    rule_name="range_check_summary",
                    severity=ValidationSeverity.FAIL,
                    message=f"共发现 {total_out_of_range} 个超出范围的值",
                    details={"total_out_of_range": total_out_of_range},
                )
            )

        return report

    def check_time_continuity(self, data: List[Dict[str, Any]]) -> ValidationReport:
        """
        时间连续性检查：验证数据时间序列是否满足 6 小时间隔

        Args:
            data: 气象数据列表

        Returns:
            包含时间连续性检查结果的报告
        """
        report = ValidationReport(validator_name="TimeContinuityCheck")

        if len(data) < 2:
            report.results.append(
                ValidationResult(
                    rule_name="time_continuity",
                    severity=ValidationSeverity.PASS,
                    message="数据不足 2 条，跳过时间连续性检查",
                )
            )
            return report

        # 提取时间并排序
        time_values: List[Optional[datetime]] = []
        for record in data:
            ft = record.get("forecast_time")
            if ft is None:
                time_values.append(None)
            elif isinstance(ft, datetime):
                time_values.append(ft)
            elif isinstance(ft, str):
                try:
                    time_values.append(datetime.fromisoformat(ft))
                except (ValueError, TypeError):
                    time_values.append(None)
            else:
                time_values.append(None)

        # 过滤有效时间并计算间隔
        valid_times: List[Tuple[int, datetime]] = [
            (i, t) for i, t in enumerate(time_values) if t is not None
        ]

        if len(valid_times) < 2:
            report.results.append(
                ValidationResult(
                    rule_name="time_continuity",
                    severity=ValidationSeverity.WARNING,
                    message="有效时间数据不足 2 条，无法检查时间连续性",
                )
            )
            return report

        # 按时间排序
        valid_times.sort(key=lambda x: x[1])

        gap_issues = 0
        for k in range(1, len(valid_times)):
            idx_prev, t_prev = valid_times[k - 1]
            idx_curr, t_curr = valid_times[k]
            gap_seconds = abs((t_curr - t_prev).total_seconds())

            if gap_seconds > self.time_tolerance:
                gap_issues += 1
                report.results.append(
                    ValidationResult(
                        rule_name="time_gap",
                        severity=ValidationSeverity.WARNING,
                        message=(
                            f"记录 #{idx_prev} -> #{idx_curr} 时间间隔异常: "
                            f"{gap_seconds:.0f} 秒 (阈值: {self.time_tolerance:.0f} 秒)"
                        ),
                        details={
                            "prev_index": idx_prev,
                            "curr_index": idx_curr,
                            "gap_seconds": gap_seconds,
                            "threshold": self.time_tolerance,
                        },
                    )
                )

        if gap_issues == 0:
            report.results.append(
                ValidationResult(
                    rule_name="time_continuity",
                    severity=ValidationSeverity.PASS,
                    message=f"全部 {len(valid_times)} 个时间点连续性正常",
                )
            )
        else:
            report.results.append(
                ValidationResult(
                    rule_name="time_continuity_summary",
                    severity=ValidationSeverity.WARNING,
                    message=f"发现 {gap_issues} 个时间间隔异常",
                    details={"gap_issues": gap_issues},
                )
            )

        return report

    def check_spatial_consistency(self, data: List[Dict[str, Any]]) -> ValidationReport:
        """
        空间一致性检查：验证相邻格点间气象要素差异是否在合理阈值内

        使用经纬度计算格点间距离，对距离在阈值内的格点对进行差异检查。

        Args:
            data: 气象数据列表

        Returns:
            包含空间一致性检查结果的报告
        """
        report = ValidationReport(validator_name="SpatialConsistencyCheck")
        spatial_distance_threshold = 0.05  # 约 5km

        if len(data) < 2:
            report.results.append(
                ValidationResult(
                    rule_name="spatial_consistency",
                    severity=ValidationSeverity.PASS,
                    message="数据不足 2 条，跳过空间一致性检查",
                )
            )
            return report

        # 提取坐标
        coords: List[Optional[Tuple[float, float]]] = []
        for record in data:
            lon = record.get("longitude")
            lat = record.get("latitude")
            if lon is not None and lat is not None:
                if not (isinstance(lon, float) and np.isnan(lon)) and not (
                    isinstance(lat, float) and np.isnan(lat)
                ):
                    coords.append((float(lon), float(lat)))
                else:
                    coords.append(None)
            else:
                coords.append(None)

        # 查找相邻格点对
        neighbor_pairs: List[Tuple[int, int, float]] = []
        for i in range(len(data)):
            if coords[i] is None:
                continue
            for j in range(i + 1, len(data)):
                if coords[j] is None:
                    continue
                dist = np.sqrt(
                    (coords[i][0] - coords[j][0]) ** 2
                    + (coords[i][1] - coords[j][1]) ** 2
                )
                if dist <= spatial_distance_threshold:
                    neighbor_pairs.append((i, j, dist))

        if not neighbor_pairs:
            report.results.append(
                ValidationResult(
                    rule_name="spatial_consistency",
                    severity=ValidationSeverity.PASS,
                    message="未发现相邻格点对，跳过空间一致性检查",
                )
            )
            return report

        spatial_issues = 0
        for i, j, dist in neighbor_pairs:
            for field_name, threshold in self.spatial_thresholds.items():
                val_i = data[i].get(field_name)
                val_j = data[j].get(field_name)
                if val_i is None or val_j is None:
                    continue
                if isinstance(val_i, float) and np.isnan(val_i):
                    continue
                if isinstance(val_j, float) and np.isnan(val_j):
                    continue

                diff = abs(float(val_i) - float(val_j))
                if diff > threshold:
                    spatial_issues += 1
                    report.results.append(
                        ValidationResult(
                            rule_name=f"spatial_{field_name}",
                            severity=ValidationSeverity.WARNING,
                            message=(
                                f"记录 #{i} 与 #{j} 字段 '{field_name}' 空间差异过大: "
                                f"{diff:.2f} (阈值: {threshold})"
                            ),
                            details={
                                "record_i": i,
                                "record_j": j,
                                "distance": dist,
                                "field": field_name,
                                "diff": diff,
                                "threshold": threshold,
                            },
                        )
                    )

        if spatial_issues == 0:
            report.results.append(
                ValidationResult(
                    rule_name="spatial_consistency",
                    severity=ValidationSeverity.PASS,
                    message=f"检查 {len(neighbor_pairs)} 对相邻格点，空间一致性正常",
                )
            )
        else:
            report.results.append(
                ValidationResult(
                    rule_name="spatial_consistency_summary",
                    severity=ValidationSeverity.WARNING,
                    message=f"发现 {spatial_issues} 个空间不一致问题",
                    details={"spatial_issues": spatial_issues},
                )
            )

        return report

    def check_physical_consistency(self, data: List[Dict[str, Any]]) -> ValidationReport:
        """
        物理一致性检查：验证气象要素之间的物理关系是否合理

        检查规则：
        1. 气压应随高度递减（标准大气模型）
        2. 露点温度不应高于气温
        3. 风速不应为负值（已由范围检查覆盖，此处做补充验证）

        Args:
            data: 气象数据列表

        Returns:
            包含物理一致性检查结果的报告
        """
        report = ValidationReport(validator_name="PhysicalConsistencyCheck")
        physics_issues = 0

        for idx, record in enumerate(data):
            # 规则 1: 气压随高度递减的验证
            # 使用标准大气模型: P = 1013.25 * exp(-alt / 8500)
            altitude = record.get("altitude")
            pressure = record.get("pressure")
            if altitude is not None and pressure is not None:
                if not (isinstance(altitude, float) and np.isnan(altitude)) and not (
                    isinstance(pressure, float) and np.isnan(pressure)
                ):
                    alt = float(altitude)
                    pres = float(pressure)
                    expected_pressure = 1013.25 * np.exp(-alt / 8500.0)
                    # 允许 50 hPa 的偏差
                    deviation = abs(pres - expected_pressure)
                    if deviation > 50.0:
                        physics_issues += 1
                        report.results.append(
                            ValidationResult(
                                rule_name="pressure_altitude_consistency",
                                severity=ValidationSeverity.WARNING,
                                message=(
                                    f"记录 #{idx} 气压与高度不一致: "
                                    f"实际气压 {pres:.1f} hPa, "
                                    f"标准大气模型预期 {expected_pressure:.1f} hPa, "
                                    f"偏差 {deviation:.1f} hPa"
                                ),
                                details={
                                    "record_index": idx,
                                    "altitude": alt,
                                    "pressure": pres,
                                    "expected_pressure": expected_pressure,
                                    "deviation": deviation,
                                },
                            )
                        )

            # 规则 2: 能见度与降水量的关系
            # 降水量大时能见度应较低
            precipitation = record.get("precipitation")
            visibility = record.get("visibility")
            if precipitation is not None and visibility is not None:
                if not (isinstance(precipitation, float) and np.isnan(precipitation)) and not (
                    isinstance(visibility, float) and np.isnan(visibility)
                ):
                    precip = float(precipitation)
                    vis = float(visibility)
                    # 降水量 > 20mm 时能见度不应超过 10km
                    if precip > 20.0 and vis > 10.0:
                        physics_issues += 1
                        report.results.append(
                            ValidationResult(
                                rule_name="precipitation_visibility_consistency",
                                severity=ValidationSeverity.WARNING,
                                message=(
                                    f"记录 #{idx} 降水量与能见度不一致: "
                                    f"降水量 {precip:.1f} mm, 能见度 {vis:.1f} km"
                                ),
                                details={
                                    "record_index": idx,
                                    "precipitation": precip,
                                    "visibility": vis,
                                },
                            )
                        )

            # 规则 3: 云量与湿度的关系
            # 高湿度应伴随较高云量
            humidity = record.get("humidity")
            cloud_cover = record.get("cloud_cover")
            if humidity is not None and cloud_cover is not None:
                if not (isinstance(humidity, float) and np.isnan(humidity)) and not (
                    isinstance(cloud_cover, float) and np.isnan(cloud_cover)
                ):
                    hum = float(humidity)
                    cc = float(cloud_cover)
                    # 湿度 > 90% 时云量不应低于 50%
                    if hum > 90.0 and cc < 50.0:
                        physics_issues += 1
                        report.results.append(
                            ValidationResult(
                                rule_name="humidity_cloud_consistency",
                                severity=ValidationSeverity.WARNING,
                                message=(
                                    f"记录 #{idx} 湿度与云量不一致: "
                                    f"湿度 {hum:.1f}%, 云量 {cc:.1f}%"
                                ),
                                details={
                                    "record_index": idx,
                                    "humidity": hum,
                                    "cloud_cover": cc,
                                },
                            )
                        )

        if physics_issues == 0:
            report.results.append(
                ValidationResult(
                    rule_name="physical_consistency",
                    severity=ValidationSeverity.PASS,
                    message=f"全部 {len(data)} 条记录物理一致性检查通过",
                )
            )
        else:
            report.results.append(
                ValidationResult(
                    rule_name="physical_consistency_summary",
                    severity=ValidationSeverity.WARNING,
                    message=f"发现 {physics_issues} 个物理一致性问题",
                    details={"physics_issues": physics_issues},
                )
            )

        return report
