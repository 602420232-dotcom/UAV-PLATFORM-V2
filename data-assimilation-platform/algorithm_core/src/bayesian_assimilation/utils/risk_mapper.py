#!/usr/bin/env python3
"""
气象风险映射模块
将同化后的气象物理量映射为飞行风险指数

核心功能：
1. 将风场(U,V)映射为风速风险
2. 将涡流耗散率(EDR)映射为湍流风险
3. 综合计算飞行区域风险等级
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AircraftConstraints:
    """飞行器约束参数"""
    max_crosswind_speed: float = 10.0  # 最大侧风速度 (m/s)
    max_headwind_speed: float = 15.0   # 最大逆风速度 (m/s)
    max_turbulence_edr: float = 0.3     # 最大涡流耗散率
    max_altitude: float = 300.0         # 最大飞行高度 (m)
    min_altitude: float = 30.0          # 最小飞行高度 (m)


class RiskLevel:
    """风险等级常量"""
    LOW = "LOW"          # 可安全飞行
    MEDIUM = "MEDIUM"    # 需谨慎飞行
    HIGH = "HIGH"        # 建议规避
    EXTREME = "EXTREME"  # 禁止飞行


class WeatherToRiskMapper:
    """
    气象场 → 飞行风险映射器

    将同化输出的物理量转换为路径规划可用的风险指数
    """

    def __init__(
        self,
        grid_resolution: float = 100.0,  # 网格分辨率 (米)
        constraints: Optional[AircraftConstraints] = None
    ):
        """
        Args:
            grid_resolution: 风险栅格分辨率，默认100米
            constraints: 飞行器约束参数
        """
        self.grid_resolution = grid_resolution
        self.constraints = constraints or AircraftConstraints()

        # 风险等级阈值
        self.wind_speed_thresholds = {
            RiskLevel.LOW: 5.0,
            RiskLevel.MEDIUM: 10.0,
            RiskLevel.HIGH: 15.0,
            RiskLevel.EXTREME: 20.0
        }

        self.edr_thresholds = {
            RiskLevel.LOW: 0.1,
            RiskLevel.MEDIUM: 0.2,
            RiskLevel.HIGH: 0.3,
            RiskLevel.EXTREME: 0.5
        }

    def compute_wind_speed(self, u_wind: np.ndarray, v_wind: np.ndarray) -> np.ndarray:
        """
        计算风速大小

        Args:
            u_wind: U分量 (东西向风)
            v_wind: V分量 (南北向风)

        Returns:
            风速大小数组
        """
        return np.sqrt(u_wind ** 2 + v_wind ** 2)

    def compute_crosswind(self, u_wind: np.ndarray,
                          v_wind: np.ndarray,
                          heading: float) -> np.ndarray:
        """
        计算侧风分量

        Args:
            u_wind: U分量
            v_wind: V分量
            heading: 飞行航向 (弧度)

        Returns:
            侧风速度数组
        """
        # 侧风 = sin(航向) * U + cos(航向) * V
        return np.abs(np.sin(heading) * u_wind + np.cos(heading) * v_wind)

    def estimate_edr_from_wind_shear(
        self,
        u_wind: np.ndarray,
        v_wind: np.ndarray,
        vertical_wind: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        从风切变估算涡流耗散率(EDR)

        这是简化估算，实际应使用机载传感器数据或AI模型

        Args:
            u_wind: U分量
            v_wind: V分量
            vertical_wind: 垂直风分量 (可选)

        Returns:
            估算的EDR数组
        """
        # 计算风切变
        du_dx = np.gradient(u_wind, axis=1)
        du_dy = np.gradient(u_wind, axis=0)
        dv_dx = np.gradient(v_wind, axis=1)
        dv_dy = np.gradient(v_wind, axis=0)

        # 水平风切变强度
        shear_magnitude = np.sqrt(du_dx**2 + du_dy**2 + dv_dx**2 + dv_dy**2)

        # 简化EDR估算: EDR ≈ 0.4 * shear^0.5 (经验公式)
        edr_estimate = 0.4 * np.sqrt(np.clip(shear_magnitude, 0, 1))

        # 如果有垂直风分量，增加湍流强度
        if vertical_wind is not None:
            dw = np.gradient(vertical_wind, axis=0)
            edr_estimate += 0.2 * np.abs(dw)

        return edr_estimate

    def compute_wind_risk(
        self,
        wind_speed: np.ndarray,
        crosswind: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        计算风速风险指数 (0-1)

        Args:
            wind_speed: 风速大小
            crosswind: 侧风速度 (可选)

        Returns:
            风险指数数组 (0=无风险, 1=极高风险)
        """
        risk = np.zeros_like(wind_speed, dtype=float)

        # 使用约束条件动态调整阈值
        max_wind = self.constraints.max_crosswind_speed

        # 风速风险
        risk += np.clip(wind_speed / max_wind, 0, 1) * 0.6

        # 侧风风险 (如果提供)
        if crosswind is not None:
            crosswind_risk = np.clip(crosswind / max_wind, 0, 1) * 0.4
            risk = np.maximum(risk, crosswind_risk)

        return np.clip(risk, 0, 1)

    def compute_turbulence_risk(self, edr: np.ndarray) -> np.ndarray:
        """
        计算湍流风险指数 (0-1)

        Args:
            edr: 涡流耗散率

        Returns:
            风险指数数组
        """
        max_edr = self.constraints.max_turbulence_edr
        return np.clip(edr / max_edr, 0, 1)

    def compute_comprehensive_risk(
        self,
        assimilation_result: Dict,
        heading: float = 0.0
    ) -> Dict[str, Any]:
        """
        计算综合飞行风险

        Args:
            assimilation_result: 同化结果，格式如下：
                {
                    'variables': {
                        'u_wind': np.ndarray,
                        'v_wind': np.ndarray,
                        'temperature': np.ndarray (可选)
                    },
                    'grid': {
                        'shape': (rows, cols),
                        'resolution': float (可选)
                    }
                }
            heading: 飞行航向 (弧度)

        Returns:
            风险场结果：
            {
                'risk_grid': np.ndarray,      # 风险指数 (0-1)
                'risk_level': np.ndarray,      # 风险等级
                'wind_speed': np.ndarray,       # 风速
                'turbulence_edr': np.ndarray,   # 湍流强度
                'risk_threshold_mask': np.ndarray, # 高风险区域掩码
                'summary': {
                    'avg_risk': float,
                    'max_risk': float,
                    'safe_area_ratio': float
                }
            }
        """
        try:
            variables = assimilation_result.get('variables', {})

            # 提取风场
            u_wind = variables.get('u_wind', np.zeros((10, 10)))
            v_wind = variables.get('v_wind', np.zeros((10, 10)))

            # 计算风速和风险
            wind_speed = self.compute_wind_speed(u_wind, v_wind)
            crosswind = self.compute_crosswind(u_wind, v_wind, heading)
            wind_risk = self.compute_wind_risk(wind_speed, crosswind)

            # 估算并计算湍流风险
            edr = self.estimate_edr_from_wind_shear(u_wind, v_wind)
            turbulence_risk = self.compute_turbulence_risk(edr)

            # 综合风险 = 0.6*风速风险 + 0.4*湍流风险
            risk_grid = 0.6 * wind_risk + 0.4 * turbulence_risk

            # 风险等级分类
            risk_level = np.full_like(risk_grid, RiskLevel.LOW, dtype=object)
            risk_level[risk_grid >= 0.3] = RiskLevel.MEDIUM
            risk_level[risk_grid >= 0.6] = RiskLevel.HIGH
            risk_level[risk_grid >= 0.85] = RiskLevel.EXTREME

            # 高风险区域掩码 (风险 > 0.6)
            risk_threshold_mask = risk_grid >= 0.6

            # 统计摘要
            summary = {
                'avg_risk': float(np.mean(risk_grid)),
                'max_risk': float(np.max(risk_grid)),
                'min_risk': float(np.min(risk_grid)),
                'safe_area_ratio': float(np.sum(risk_grid < 0.3) / risk_grid.size),
                'high_risk_ratio': float(np.sum(risk_threshold_mask) / risk_grid.size)
            }

            logger.info(
                f"风险计算完成: 平均风险={summary['avg_risk']:.3f}, "
                f"最大风险={summary['max_risk']:.3f}, "
                f"安全区域占比={summary['safe_area_ratio']:.1%}"
            )

            return {
                'risk_grid': risk_grid,
                'risk_level': risk_level,
                'wind_speed': wind_speed,
                'turbulence_edr': edr,
                'wind_risk': wind_risk,
                'turbulence_risk': turbulence_risk,
                'risk_threshold_mask': risk_threshold_mask,
                'summary': summary,
                'grid_shape': risk_grid.shape
            }

        except Exception as e:
            logger.error(f"风险计算失败: {e}")
            raise

    def generate_risk_aware_obstacles(
        self,
        risk_result: Dict,
        risk_threshold: float = 0.6
    ) -> List[Dict]:
        """
        将高风险区域转换为路径规划器可用的障碍物

        Args:
            risk_result: compute_comprehensive_risk 的输出
            risk_threshold: 风险阈值，超过此值视为障碍

        Returns:
            障碍物列表 [{'location': (x, y), 'radius': float}, ...]
        """
        risk_grid = risk_result['risk_grid']
        rows, cols = risk_grid.shape

        obstacles = []
        # 将栅格索引转换为近似坐标
        for i in range(rows):
            for j in range(cols):
                if risk_grid[i, j] >= risk_threshold:
                    # 简化的坐标转换 (假设规则网格)
                    x = j * self.grid_resolution
                    y = i * self.grid_resolution
                    # 障碍物半径与风险成正比
                    radius = self.grid_resolution * (0.5 + risk_grid[i, j] * 0.5)
                    obstacles.append({
                        'location': (x, y),
                        'radius': radius,
                        'risk_level': risk_grid[i, j]
                    })

        logger.info(f"生成 {len(obstacles)} 个风险障碍物")
        return obstacles


class RiskAwarePathCostCalculator:
    """
    风险感知路径代价计算器

    用于在路径规划算法中集成气象风险
    """

    def __init__(self, risk_mapper: WeatherToRiskMapper):
        self.risk_mapper = risk_mapper
        self.risk_grid: Optional[np.ndarray] = None
        self.grid_shape: Optional[Tuple[int, int]] = None

    def set_risk_field(self, risk_result: Dict):
        """设置风险场"""
        self.risk_grid = risk_result['risk_grid']
        self.grid_shape = risk_result['grid_shape']

    def get_risk_at_position(self, position: Tuple[float, float]) -> float:
        """
        获取指定位置的风险值

        Args:
            position: 位置 (x, y) 单位：米

        Returns:
            风险值 (0-1)
        """
        if self.risk_grid is None:
            return 0.0

        # 坐标转换
        x, y = position
        j = int(x / self.risk_mapper.grid_resolution)
        i = int(y / self.risk_mapper.grid_resolution)

        # 边界检查
        if self.grid_shape is None:
            return 0.0
        rows, cols = self.grid_shape
        if 0 <= i < rows and 0 <= j < cols:
            return float(self.risk_grid[i, j])
        return 0.0

    def compute_segment_risk_cost(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        steps: int = 10
    ) -> float:
        """
        计算路径段的累积风险代价

        Args:
            start: 起点
            end: 终点
            steps: 采样步数

        Returns:
            累积风险代价
        """
        total_risk = 0.0

        for k in range(steps + 1):
            t = k / steps
            x = start[0] + t * (end[0] - start[0])
            y = start[1] + t * (end[1] - start[1])
            total_risk += self.get_risk_at_position((x, y))

        return total_risk / (steps + 1)

    def is_high_risk_zone(self, position: Tuple[float, float], threshold: float = 0.6) -> bool:
        """检查是否为高风险区域"""
        return self.get_risk_at_position(position) >= threshold


def demo():
    """演示风险映射功能"""
    print("=" * 60)
    logger.info("气象风险映射模块 - 演示")
    print("=" * 60)

    # 创建示例同化结果
    np.random.seed(42)
    shape = (20, 20)  # 20x20 栅格

    # 模拟风场 (带一些随机扰动)
    x = np.linspace(0, 2 * np.pi, shape[0])
    y = np.linspace(0, 2 * np.pi, shape[1])
    X, Y = np.meshgrid(x, y)

    u_wind = 5 + 3 * np.sin(X) + np.random.normal(0, 0.5, shape)
    v_wind = 3 + 2 * np.cos(Y) + np.random.normal(0, 0.5, shape)

    # 模拟高风速区域 (右侧)
    u_wind[:, 15:] += 5

    assimilation_result = {
        'variables': {
            'u_wind': u_wind,
            'v_wind': v_wind
        },
        'grid': {'shape': shape}
    }

    # 创建风险映射器
    mapper = WeatherToRiskMapper(grid_resolution=100.0)
    cost_calculator = RiskAwarePathCostCalculator(mapper)

    # 计算风险
    logger.info("\n1. 计算综合风险场...")
    risk_result = mapper.compute_comprehensive_risk(assimilation_result, heading=0.0)

    logger.info("\n2. 风险统计:")
    summary = risk_result['summary']
    print(f"   - 平均风险: {summary['avg_risk']:.3f}")
    print(f"   - 最大风险: {summary['max_risk']:.3f}")
    print(f"   - 安全区域占比: {summary['safe_area_ratio']:.1%}")
    print(f"   - 高风险区域占比: {summary['high_risk_ratio']:.1%}")

    # 风险等级分布
    logger.info("\n3. 风险等级分布:")
    risk_grid = risk_result['risk_grid']
    risk_levels, counts = np.unique(risk_result['risk_level'], return_counts=True)
    for level, count in zip(risk_levels, counts):
        print(f"   - {level}: {count} 单元格 ({count/risk_grid.size:.1%})")

    # 生成障碍物
    logger.info("\n4. 生成风险障碍物...")
    obstacles = mapper.generate_risk_aware_obstacles(risk_result, risk_threshold=0.6)
    print(f"   - 生成的障碍物数量: {len(obstacles)}")

    # 测试位置查询
    logger.info("\n5. 测试路径代价计算...")
    cost_calculator.set_risk_field(risk_result)
    test_positions = [(100, 100), (500, 500), (1500, 1500)]

    for pos in test_positions:
        risk = cost_calculator.get_risk_at_position(pos)
        print(f"   - 位置 {pos}: 风险值 = {risk:.3f}")

    # 测试路径段代价
    logger.info("\n6. 测试路径段代价:")
    segment_cost = cost_calculator.compute_segment_risk_cost(
        (100, 100), (500, 500), steps=20
    )
    print(f"   - 从 (100,100) 到 (500,500): 累积风险 = {segment_cost:.3f}")

    print("\n" + "=" * 60)
    logger.info("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
