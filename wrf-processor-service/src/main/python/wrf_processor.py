#!/usr/bin/env python3
"""
WRF气象数据处理服务
负责解析WRF输出的NetCDF4文件，提取低空气象参数
支持参数: 三维风场、温度、湿度、湍流、能见度、闪电风险评估
"""

import netCDF4 as nc
import numpy as np
import json
import sys
import logging
import math
from typing import Optional, Dict, List

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
logger = logging.getLogger(__name__)


# ─── 常量定义 ─────────────────────────────────────────────────────────────
HEIGHT_LAYERS = [0, 10, 50, 100, 200, 300, 500, 800, 1000]  # 0-1000m分层
TURBULENCE_THRESHOLDS = {'LOW': 0.5, 'MODERATE': 1.5, 'SEVERE': 3.0}
VISIBILITY_THRESHOLDS = {
    'EXCELLENT': 20000,
    'GOOD': 10000,
    'MODERATE': 5000,
    'POOR': 2000,
    'HAZARDOUS': 0
}
LIGHTNING_RISK_LEVELS = ['LOW', 'MODERATE', 'HIGH', 'EXTREME']

# ─── NetCDF 格式检测 ─────────────────────────────────────────────────────


def detect_netcdf_format(filepath: str) -> str:
    """检测 NetCDF 文件格式版本"""
    try:
        with open(filepath, 'rb') as f:
            magic = f.read(4)
        if magic == b'\x89HDF':
            return 'NETCDF4'
        if magic == b'CDF\x01':
            return 'NETCDF3_CLASSIC'
        if magic == b'CDF\x02':
            return 'NETCDF3_64BIT'
        return 'UNKNOWN'
    except Exception as e:
        logger.warning(f"Cannot detect format for {filepath}: {e}")
        return 'UNKNOWN'


# ═══════════════════════════════════════════════════════════════════════════
#  WRF 气象数据处理器
# ═══════════════════════════════════════════════════════════════════════════


class WrfProcessor:
    """WRF气象数据处理器 - 支持所有微尺度气象参数"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.dataset = None
        self.variables = {}

    def open_dataset(self) -> bool:
        """打开NetCDF4数据集"""
        try:
            self.dataset = nc.Dataset(self.file_path, 'r')
            fmt = detect_netcdf_format(self.file_path)
            if fmt in ('NETCDF3_CLASSIC', 'NETCDF3_64BIT'):
                logger.info(f"Detected {fmt} format, converting via netCDF4 library")
            logger.info(f"成功打开WRF文件: {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"打开WRF文件失败: {e}")
            return False

    def close_dataset(self):
        """关闭数据集"""
        if self.dataset:
            self.dataset.close()
            logger.info("成功关闭WRF文件")

    def get_variables(self) -> Dict:
        """获取所有变量"""
        if not self.dataset:
            logger.error("数据集未打开")
            return {}
        variables = {}
        for var_name in self.dataset.variables:
            var = self.dataset.variables[var_name]
            variables[var_name] = {
                'shape': var.shape,
                'units': getattr(var, 'units', 'unknown'),
                'long_name': getattr(var, 'long_name', var_name)
            }
        self.variables = variables
        return variables

    # ─── 基础气象数据提取 ────────────────────────────────────────────────

    def extract_meteorological_data(self, height: int = 100) -> Dict:
        """提取指定高度的气象数据"""
        if not self.dataset:
            logger.error("数据集未打开")
            return {}

        try:
            data = {}
            # 提取时间
            if 'Times' in self.dataset.variables:
                times = self.dataset.variables['Times'][:]
                data['times'] = [''.join([chr(c) for c in t]) for t in times]

            # 提取风场
            if 'U' in self.dataset.variables and 'V' in self.dataset.variables:
                U = self.dataset.variables['U'][:]
                V = self.dataset.variables['V'][:]
                data['wind_speed'] = np.sqrt(U**2 + V**2).tolist()
                data['wind_direction'] = np.degrees(np.arctan2(V, U)).tolist()
                data['u_component'] = U.tolist()
                data['v_component'] = V.tolist()

            # 提取温度
            if 'T' in self.dataset.variables:
                T = self.dataset.variables['T'][:]
                data['temperature'] = (T + 300).tolist()
            elif 'TK' in self.dataset.variables:
                TK = self.dataset.variables['TK'][:]
                data['temperature'] = (TK - 273.15).tolist()

            # 提取湿度
            if 'Q2' in self.dataset.variables:
                Q2 = self.dataset.variables['Q2'][:]
                data['humidity'] = Q2.tolist()
            elif 'QVAPOR' in self.dataset.variables:
                QV = self.dataset.variables['QVAPOR'][:]
                data['humidity'] = (QV * 100).tolist()

            # 提取气压
            if 'PSFC' in self.dataset.variables:
                PSFC = self.dataset.variables['PSFC'][:]
                data['pressure'] = (PSFC / 100).tolist()
            elif 'P' in self.dataset.variables:
                P = self.dataset.variables['P'][:]
                PB = self.dataset.variables.get('PB', None)
                data['pressure'] = ((P + (PB if PB is not None else 0)) / 100).tolist()

            logger.info(f"成功提取高度 {height} 米的气象数据")
            return data

        except Exception as e:
            logger.error(f"提取气象数据失败: {e}")
            return {}

    # ─── 湍流参数提取 ────────────────────────────────────────────────────

    def extract_turbulence(self) -> Dict:
        """
        提取湍流参数（Turbulent Kinetic Energy）

        使用WRF的TKE变量（如'QKE', 'TKE'），或从风场波动计算。
        返回: {
            'tke': [...],  # 湍流动能 (m²/s²)
            'turbulence_intensity': str,  # LOW/MODERATE/SEVERE
            'dissipation_rate': float,  # 耗散率
            'eddy_diffusivity': [...]    # 湍流扩散系数
        }
        """
        if not self.dataset:
            logger.error("数据集未打开")
            return {}

        result = {'tke': None, 'turbulence_intensity': 'UNKNOWN', 'dissipation_rate': 0.0}

        try:
            tke_data = None

            # 优先级1: 直接使用WRF的TKE/QKE变量
            for tke_var in ['QKE', 'TKE', 'TKE_PBL', 'tke']:
                if tke_var in self.dataset.variables:
                    raw = self.dataset.variables[tke_var][:]
                    tke_data = np.mean(raw, axis=tuple(range(1, len(raw.shape)))) if raw.ndim > 1 else raw
                    logger.info(f"使用WRF变量 {tke_var} 提取湍流动能")
                    break

            # 优先级2: 从风场波动计算TKE = 0.5 * (u'² + v'²)
            if tke_data is None and all(v in self.dataset.variables for v in ['U', 'V']):
                U = self.dataset.variables['U'][:]
                V = self.dataset.variables['V'][:]
                U_mean = np.mean(U, axis=0)
                V_mean = np.mean(V, axis=0)
                u_prime = U - U_mean
                v_prime = V - V_mean
                tke_data = 0.5 * (u_prime**2 + v_prime**2)
                if tke_data.ndim > 1:
                    tke_data = np.mean(tke_data, axis=tuple(range(1, tke_data.ndim)))
                logger.info("从风场波动计算湍流动能")

            if tke_data is not None:
                avg_tke = float(np.mean(tke_data))
                result['tke'] = tke_data.tolist() if hasattr(tke_data, 'tolist') else tke_data
                result['tke_mean'] = avg_tke
                result['tke_max'] = float(np.max(tke_data))
                result['tke_min'] = float(np.min(tke_data))

                # 湍流强度分级
                if avg_tke >= TURBULENCE_THRESHOLDS['SEVERE']:
                    result['turbulence_intensity'] = 'SEVERE'
                    result['turbulence_description'] = '严重湍流 - 对无人机飞行构成严重威胁'
                elif avg_tke >= TURBULENCE_THRESHOLDS['MODERATE']:
                    result['turbulence_intensity'] = 'MODERATE'
                    result['turbulence_description'] = '中等湍流 - 需谨慎飞行'
                elif avg_tke >= TURBULENCE_THRESHOLDS['LOW']:
                    result['turbulence_intensity'] = 'LOW'
                    result['turbulence_description'] = '轻度湍流 - 可正常飞行'
                else:
                    result['turbulence_intensity'] = 'NEGLIGIBLE'
                    result['turbulence_description'] = '几乎无湍流 - 飞行条件极佳'

                # 耗散率近似 (ε ≈ TKE^1.5 / L, L为湍流尺度~100m)
                L = 100.0  # 湍流尺度
                result['dissipation_rate'] = round(avg_tke**1.5 / L, 4)
                logger.info(f"湍流评估完成: {result['turbulence_intensity']} (TKE={avg_tke:.3f})")
            else:
                logger.warning("无法计算湍流参数")

            return result

        except Exception as e:
            logger.error(f"提取湍流参数失败: {e}")
            return {'tke': None, 'turbulence_intensity': 'UNKNOWN', 'error': str(e)}

    # ─── 能见度计算 ──────────────────────────────────────────────────────

    def calculate_visibility(self) -> Dict:
        """
        计算能见度

        基于温度、湿度数据，使用Koschmieder公式估算：
            visibility = 3.912 / β
        其中β为消光系数，基于湿度和温度估算。

        返回: {
            'visibility_m': float,  # 能见度(米)
            'visibility_category': str,  # EXCELLENT/GOOD/MODERATE/POOR/HAZARDOUS
            'extinction_coefficient': float  # 消光系数
        }
        """
        if not self.dataset:
            logger.error("数据集未打开")
            return {}

        result = {'visibility_m': 10000, 'visibility_category': 'MODERATE'}

        try:
            # 获取温度和湿度
            temperature = None
            humidity = None

            if 'T' in self.dataset.variables:
                T = self.dataset.variables['T'][:]
                temperature = float(np.mean(T) + 300)
            elif 'TK' in self.dataset.variables:
                TK = self.dataset.variables['TK'][:]
                temperature = float(np.mean(TK))

            if 'Q2' in self.dataset.variables:
                Q2 = self.dataset.variables['Q2'][:]
                humidity = float(np.mean(Q2))
            elif 'QVAPOR' in self.dataset.variables:
                QV = self.dataset.variables['QVAPOR'][:]
                humidity = float(np.mean(QV) * 100)

            # 获取气溶胶数据（如果有）
            aerosol_optical_depth = 0.1
            if 'AOD' in self.dataset.variables:
                AOD = self.dataset.variables['AOD'][:]
                aerosol_optical_depth = float(np.mean(AOD))

            if temperature is not None and humidity is not None:
                # 计算饱和水汽压 (Magnus公式)
                es = 6.112 * math.exp(
                    17.67 * (temperature - 273.15) /
                    ((temperature - 273.15) + 243.5)
                )

                # 计算实际水汽压
                if humidity > 1:  # 相对湿度为百分比
                    rh = humidity
                else:
                    rh = humidity * 100

                e = es * (rh / 100.0)

                # 消光系数估算 (Koschmieder公式变体)
                # β = β_rayleigh + β_aerosol + β_humidity
                beta_rayleigh = 0.013  # 瑞利散射 (1/km)
                beta_aerosol = aerosol_optical_depth * 0.15
                beta_humidity = 0.02 * (rh / 100.0)**2  # 湿度影响

                extinction_coefficient = beta_rayleigh + beta_aerosol + beta_humidity

                # 能见度 (Koschmieder: V = 3.912 / β)
                visibility_km = 3.912 / max(extinction_coefficient, 0.001)
                visibility_m = visibility_km * 1000

                result['visibility_m'] = round(visibility_m, 1)
                result['extinction_coefficient'] = round(extinction_coefficient, 4)
                result['temperature_c'] = round(temperature - 273.15, 1)
                result['humidity_percent'] = round(rh, 1)

                # 能见度分级
                if visibility_m >= VISIBILITY_THRESHOLDS['EXCELLENT']:
                    result['visibility_category'] = 'EXCELLENT'
                    result['visibility_description'] = '能见度极佳，适合飞行'
                elif visibility_m >= VISIBILITY_THRESHOLDS['GOOD']:
                    result['visibility_category'] = 'GOOD'
                    result['visibility_description'] = '能见度良好，可正常飞行'
                elif visibility_m >= VISIBILITY_THRESHOLDS['MODERATE']:
                    result['visibility_category'] = 'MODERATE'
                    result['visibility_description'] = '能见度一般，需注意飞行'
                elif visibility_m >= VISIBILITY_THRESHOLDS['POOR']:
                    result['visibility_category'] = 'POOR'
                    result['visibility_description'] = '能见度较差，建议谨慎飞行'
                else:
                    result['visibility_category'] = 'HAZARDOUS'
                    result['visibility_description'] = '能见度极差，禁止飞行'

                logger.info(f"能见度计算完成: {result['visibility_category']} ({visibility_m:.0f}m)")

        except Exception as e:  # noqa: F841
            logger.error(f"计算能见度失败: {e}")
            result['error'] = str(e)

        return result

    # ─── 闪电风险评估 ────────────────────────────────────────────────────

    def assess_lightning_risk(self) -> Dict:
        """
        评估闪电风险

        基于WRF对流参数（CAPE, CIN, LCL等）评估闪电发生风险。
        使用代理指标：
        - CAPE (对流有效位能): 越大→风险越高
        - CIN (对流抑制): 越小→风险越高
        - LCL (抬升凝结高度): 越低→风险越高

        返回: {
            'risk_level': str,  # LOW/MODERATE/HIGH/EXTREME
            'cape': float,  # 对流有效位能 (J/kg)
            'cin': float,  # 对流抑制 (J/kg)
            'lcl': float,  # 抬升凝结高度 (m)
            'risk_score': float         # 综合风险评分 0-100
        }
        """
        if not self.dataset:
            logger.error("数据集未打开")
            return {}

        result = {
            'risk_level': 'LOW',
            'risk_score': 0.0,
            'cape': 0.0,
            'cin': 0.0,
            'lcl': 0.0
        }

        try:
            cape, cin, lcl = 0.0, 0.0, 500.0
            has_convective_data = False

            # 优先级1: 使用WRF对流变量
            if 'CAPE' in self.dataset.variables:
                cape = float(np.mean(self.dataset.variables['CAPE'][:]))
                has_convective_data = True
                logger.info(f"使用WRF CAPE变量: {cape:.1f} J/kg")

            if 'CIN' in self.dataset.variables:
                cin = float(np.mean(self.dataset.variables['CIN'][:]))

            if 'LCL' in self.dataset.variables:
                lcl = float(np.mean(self.dataset.variables['LCL'][:]))

            # 优先级2: 从温湿度估算对流参数
            if not has_convective_data:
                T_var = self.dataset.variables.get('T', None)
                Q_var = self.dataset.variables.get('Q2', None) \
                    or self.dataset.variables.get('QVAPOR', None)
                if T_var is not None and Q_var is not None:
                    T_mean = float(np.mean(T_var[:])) + 300
                    Q_mean = float(np.mean(Q_var[:]))
                    # 近似估算CAPE (经验公式)
                    cape = max(0, (T_mean - 290) * 80 + Q_mean * 200)
                    lcl = max(100, (20 + (T_mean - 273.15) / 5) * 100)
                    has_convective_data = True

            # 计算综合风险评分 (0-100)
            risk_score = 0.0

            # CAPE贡献 (权重0.4)
            if cape < 500:
                risk_score += 5
            elif cape < 1000:
                risk_score += 15
            elif cape < 2000:
                risk_score += 25
            elif cape < 3000:
                risk_score += 32
            else:
                risk_score += 40

            # CIN贡献 (权重0.2)
            if cin > -20:
                risk_score += 2
            elif cin > -50:
                risk_score += 8
            elif cin > -100:
                risk_score += 14
            else:
                risk_score += 20

            # LCL贡献 (权重0.2)
            if lcl > 2000:
                risk_score += 5
            elif lcl > 1000:
                risk_score += 10
            elif lcl > 500:
                risk_score += 15
            else:
                risk_score += 20

            # 基本风险 (权重0.2, 所有区域都有一定基础风险)
            risk_score += 20

            result['cape'] = round(cape, 1)
            result['cin'] = round(cin, 1)
            result['lcl'] = round(lcl, 1)
            result['risk_score'] = round(risk_score, 1)

            # 风险等级判定
            if risk_score >= 80:
                result['risk_level'] = 'EXTREME'
                result['risk_description'] = '闪电风险极高 - 严禁飞行'
            elif risk_score >= 60:
                result['risk_level'] = 'HIGH'
                result['risk_description'] = '闪电风险高 - 禁止飞行'
            elif risk_score >= 35:
                result['risk_level'] = 'MODERATE'
                result['risk_description'] = '闪电风险中等 - 需谨慎评估'
            else:
                result['risk_level'] = 'LOW'
                result['risk_description'] = '闪电风险低 - 可正常飞行'

            logger.info(f"闪电风险评估完成: {result['risk_level']} (评分={risk_score:.1f})")

        except Exception as e:
            logger.error(f"评估闪电风险失败: {e}")
            result['error'] = str(e)

        return result

    # ─── 0-1000m分层数据提取 ────────────────────────────────────────────

    def extract_height_layers(self, target_layers: Optional[List[int]] = None) -> Dict:
        """
        提取0-1000米分层气象数据

        Args:
            target_layers: 目标高度层列表(米)，默认使用HEIGHT_LAYERS

        Returns:
            Dict: {
                'layers': [{height, wind_speed, wind_dir, temperature, humidity, pressure, turbulence}, ...],
                'layer_count': int,
                'max_height': int
            }
        """
        if not self.dataset:
            logger.error("数据集未打开")
            return {}

        layers = target_layers or HEIGHT_LAYERS
        result = {'layers': [], 'layer_count': len(layers), 'max_height': max(layers)}

        try:
            # 提取基础数据
            base_data = self.extract_meteorological_data(100)
            turb_data = self.extract_turbulence()

            # 获取垂直剖面数据
            z_vals = None
            if 'Z' in self.dataset.variables:
                z_vals = self.dataset.variables['Z'][:]
            elif 'z' in self.dataset.variables:
                z_vals = self.dataset.variables['z'][:]
            elif 'height' in self.dataset.variables:
                z_vals = self.dataset.variables['height'][:]

            # 获取各高度的风场
            u_profile = None
            v_profile = None
            t_profile = None
            q_profile = None

            if 'U' in self.dataset.variables:
                u_profile = self.dataset.variables['U'][:]
            if 'V' in self.dataset.variables:
                v_profile = self.dataset.variables['V'][:]
            if 'T' in self.dataset.variables:
                t_profile = self.dataset.variables['T'][:]
            if 'Q2' in self.dataset.variables:
                q_profile = self.dataset.variables['Q2'][:]
            elif 'QVAPOR' in self.dataset.variables:
                q_profile = self.dataset.variables['QVAPOR'][:]

            for h in layers:
                layer_data = {'height': h}

                # 如果存在垂直剖面，按高度插值
                if z_vals is not None and u_profile is not None and v_profile is not None:
                    z_flat = z_vals.flatten()
                    # 找到最接近目标高度的层
                    if len(z_flat) > 0:
                        idx = np.argmin(np.abs(z_flat - h))
                        if u_profile.ndim > 1:
                            u_h = float(np.mean(u_profile[..., idx])) \
                                if idx < u_profile.shape[-1] else 0
                            v_h = float(np.mean(v_profile[..., idx])) \
                                if idx < v_profile.shape[-1] else 0
                        else:
                            u_h = float(u_profile[idx])
                            v_h = float(v_profile[idx])

                        layer_data['wind_speed'] = round(math.sqrt(u_h**2 + v_h**2), 2)
                        layer_data['wind_direction'] = round(math.degrees(math.atan2(v_h, u_h)), 1)
                        layer_data['u_component'] = round(u_h, 2)
                        layer_data['v_component'] = round(v_h, 2)

                        if t_profile is not None:
                            t_h = float(np.mean(t_profile[..., idx])) \
                                if t_profile.ndim > 1 else float(t_profile[idx])
                            layer_data['temperature'] = round(t_h + 300, 1)

                        if q_profile is not None:
                            q_h = float(np.mean(q_profile[..., idx])) \
                                if q_profile.ndim > 1 else float(q_profile[idx])
                            layer_data['humidity'] = round(q_h * 100 if q_h < 1 else q_h, 1)

                # 无垂直剖面时使用基础数据
                if 'wind_speed' not in layer_data:
                    # 使用高度缩放因子模拟垂直变化
                    height_factor = 1 + 0.3 * math.log(h / 100 + 1) if h > 0 else 0.1
                    if base_data.get('wind_speed'):
                        ws = float(np.mean(base_data['wind_speed']))
                        layer_data['wind_speed'] = round(ws * height_factor, 2)
                        layer_data['wind_direction'] = float(
                            np.mean(base_data.get('wind_direction', [0]))) \
                            if base_data.get('wind_direction') else 0

                if 'temperature' not in layer_data:
                    # 温度递减率 ~6.5°C/km
                    if base_data.get('temperature'):
                        t_base = float(np.mean(base_data['temperature']))
                        layer_data['temperature'] = round(t_base - 0.0065 * h, 1)

                if 'humidity' not in layer_data:
                    if base_data.get('humidity'):
                        rh_base = float(np.mean(base_data['humidity']))
                        layer_data['humidity'] = round(max(10, rh_base - 0.002 * h), 1)

                # 湍流随高度变化
                if turb_data.get('tke_mean'):
                    tke_base = turb_data['tke_mean']
                    layer_data['turbulence_tke'] = round(max(0, tke_base * math.exp(-h / 500)), 4)
                    if layer_data['turbulence_tke'] >= TURBULENCE_THRESHOLDS['SEVERE']:
                        layer_data['turbulence_intensity'] = 'SEVERE'
                    elif layer_data['turbulence_tke'] >= TURBULENCE_THRESHOLDS['MODERATE']:
                        layer_data['turbulence_intensity'] = 'MODERATE'
                    elif layer_data['turbulence_tke'] >= TURBULENCE_THRESHOLDS['LOW']:
                        layer_data['turbulence_intensity'] = 'LOW'
                    else:
                        layer_data['turbulence_intensity'] = 'NEGLIGIBLE'

                result['layers'].append(layer_data)

            logger.info(f"成功提取 {len(layers)} 个高度层的数据 (0-{max(layers)}m)")
            return result

        except Exception as e:
            logger.error(f"提取分层数据失败: {e}")
            return {'layers': [], 'error': str(e)}

    # ─── 综合数据提取 ────────────────────────────────────────────────────

    def extract_all_parameters(self, height: int = 100) -> Dict:
        """提取所有气象参数的综合方法"""
        meteorological = self.extract_meteorological_data(height)
        turbulence = self.extract_turbulence()
        visibility = self.calculate_visibility()
        lightning = self.assess_lightning_risk()
        layers = self.extract_height_layers()

        return {
            'meteorological': meteorological,
            'turbulence': turbulence,
            'visibility': visibility,
            'lightning_risk': lightning,
            'height_layers': layers,
            'statistics': self.get_statistics()
        }

    # ─── 统计信息 ────────────────────────────────────────────────────────

    def get_statistics(self) -> Dict:
        """计算所有参数的数据统计信息"""
        if not self.dataset:
            logger.error("数据集未打开")
            return {}

        stats = {}

        # 风速统计
        if 'U' in self.dataset.variables and 'V' in self.dataset.variables:
            U = self.dataset.variables['U'][:]
            V = self.dataset.variables['V'][:]
            wind_speed = np.sqrt(U**2 + V**2)
            stats['wind_speed'] = {
                'mean': float(np.mean(wind_speed)),
                'min': float(np.min(wind_speed)),
                'max': float(np.max(wind_speed)),
                'std': float(np.std(wind_speed))
            }

        # 温度统计
        if 'T' in self.dataset.variables:
            T = self.dataset.variables['T'][:]
            temperature = T + 300
            stats['temperature'] = {
                'mean': float(np.mean(temperature)),
                'min': float(np.min(temperature)),
                'max': float(np.max(temperature)),
                'std': float(np.std(temperature))
            }

        # 湿度统计
        if 'Q2' in self.dataset.variables:
            Q2 = self.dataset.variables['Q2'][:]
            stats['humidity'] = {
                'mean': float(np.mean(Q2)),
                'min': float(np.min(Q2)),
                'max': float(np.max(Q2)),
                'std': float(np.std(Q2))
            }

        logger.info("成功计算数据统计信息")
        return stats

    # ─── 分块读取 ────────────────────────────────────────────────────────

    def read_variable_chunked(self, varname: str, chunk_size: int = 100) -> np.ndarray:
        """分块读取大型变量（防止内存溢出）"""
        with nc.Dataset(self.file_path, 'r') as ds:
            if varname not in ds.variables:
                raise ValueError(f"Variable {varname} not found in dataset")
            var = ds.variables[varname]
            shape = var.shape

            if len(shape) <= 2:
                return var[:]

            time_steps = shape[0]
            if time_steps <= chunk_size:
                return var[:]

            chunks = []
            for start in range(0, time_steps, chunk_size):
                end = min(start + chunk_size, time_steps)
                indices = [slice(start, end)] + [slice(None)] * (len(shape) - 1)
                chunk = var[tuple(indices)]
                chunks.append(chunk)
                logger.info(f"  Read chunk [{start}:{end}] of {time_steps}")

            return np.concatenate(chunks, axis=0)


# ═══════════════════════════════════════════════════════════════════════════
#  主处理函数
# ═══════════════════════════════════════════════════════════════════════════


def process_wrf_file(file_path: str, height: int = 100) -> Dict:
    """处理WRF文件的主函数 - 完整参数提取"""
    processor = WrfProcessor(file_path)
    try:
        if not processor.open_dataset():
            return {'success': False, 'error': '无法打开WRF文件'}

        result = processor.extract_all_parameters(height)
        variables = processor.get_variables()

        return {
            'success': True,
            'data': result,
            'variables': variables
        }
    finally:
        processor.close_dataset()


def process_single_parameter(file_path: str, param: str, height: int = 100) -> Dict:
    """提取单个参数（快速查询用）"""
    processor = WrfProcessor(file_path)
    try:
        if not processor.open_dataset():
            return {'success': False, 'error': '无法打开WRF文件'}

        param_funcs = {
            'meteorological': processor.extract_meteorological_data,
            'turbulence': processor.extract_turbulence,
            'visibility': processor.calculate_visibility,
            'lightning': processor.assess_lightning_risk,
            'layers': lambda: processor.extract_height_layers(),
            'statistics': processor.get_statistics,
            'variables': processor.get_variables,
        }

        if param not in param_funcs:
            return {'success': False, 'error': f'未知参数类型: {param}'}

        data = param_funcs[param]() if param != 'variables' else param_funcs[param]()
        return {'success': True, 'data': data}
    finally:
        processor.close_dataset()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        logger.error("缺少文件路径参数")
        logger.info(json.dumps({'success': False, 'error': '缺少文件路径参数'}))
        return

    file_path = sys.argv[1]
    height = 100
    param_type = None

    if len(sys.argv) > 2:
        try:
            height = int(sys.argv[2])
        except ValueError:
            logger.warning("高度参数无效，使用默认值100米")

    if len(sys.argv) > 3:
        param_type = sys.argv[3].lower()

    logger.info(f"开始处理WRF文件: {file_path}, 高度: {height}米, 参数: {param_type or '全部'}")

    if param_type:
        result = process_single_parameter(file_path, param_type, height)
    else:
        result = process_wrf_file(file_path, height)

    logger.info(f"WRF文件处理完成: {file_path}")
    logger.info(json.dumps(result))


if __name__ == "__main__":
    main()
