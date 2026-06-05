"""
REST API 封装模块
提供贝叶斯同化系统的 RESTful API 接口
"""

import logging
import sys
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from http import HTTPStatus

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from bayesian_assimilation.core.assimilator import BayesianAssimilator  # noqa: E402
from bayesian_assimilation.utils.config import AssimilationConfig  # noqa: E402
from bayesian_assimilation.quality_control import MeteorologicalQualityControl  # noqa: E402
from bayesian_assimilation.risk_assessment import MeteorologicalRiskAssessment  # noqa: E402
from bayesian_assimilation.time_series import TimeSeriesAnalyzer  # noqa: E402
from bayesian_assimilation.utils.logging import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """API 响应对象"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            'success': self.success,
            'message': self.message
        }
        if self.data is not None:
            result['data'] = self.data
        if self.error is not None:
            result['error'] = self.error
        return result


class AssimilationAPI:
    """
    贝叶斯同化 REST API 接口
    """

    def __init__(self):
        setup_logging()
        self.assimilator_cache: Dict[str, BayesianAssimilator] = {}

    def _get_assimilator(self, config_id: str = 'default') -> BayesianAssimilator:
        """获取或创建同化器"""
        if config_id not in self.assimilator_cache:
            config = AssimilationConfig()
            self.assimilator_cache[config_id] = BayesianAssimilator(config)
        return self.assimilator_cache[config_id]

    def assimilate(self, background_data: Dict[str, Any],
                   observations: Dict[str, Any],
                   config: Optional[Dict[str, Any]] = None) -> APIResponse:
        """
        执行贝叶斯同化

        Args:
            background_data: 背景场数据
            observations: 观测数据
            config: 可选配置参数

        Returns:
            APIResponse: 同化结果
        """
        try:
            logger.info("收到同化请求")

            # 创建配置
            assimilation_config = AssimilationConfig()
            if config:
                assimilation_config.update(config)

            # 创建同化器
            assimilator = BayesianAssimilator(assimilation_config)

            # 提取数据
            background = background_data.get('wind_speed')
            obs_values = observations.get('observations')
            obs_locations = observations.get('locations')

            if background is None:
                return APIResponse(
                    success=False,
                    message="缺少背景场数据",
                    error="wind_speed not found in background_data"
                )

            if obs_values is None or obs_locations is None:
                return APIResponse(
                    success=False,
                    message="缺少观测数据",
                    error="observations or locations not found in observations"
                )

            # 质量控制
            background = MeteorologicalQualityControl.validate_wind_speed(background)

            # 执行同化
            analysis, variance = assimilator.assimilate(
                background, obs_values, obs_locations
            )

            result = {
                'analysis_shape': list(analysis.shape),
                'variance_shape': list(variance.shape),
                'analysis_range': [float(analysis.min()), float(analysis.max())],
                'variance_range': [float(variance.min()), float(variance.max())],
                'analysis': analysis.tolist(),
                'variance': variance.tolist()
            }

            return APIResponse(
                success=True,
                message="同化成功",
                data=result
            )

        except Exception as e:
            logger.error(f"同化失败: {e}", exc_info=True)
            return APIResponse(
                success=False,
                message="同化失败",
                error=str(e)
            )

    def quality_control(self, data: Dict[str, Any],
                       data_type: str = 'all') -> APIResponse:
        """
        质量控制

        Args:
            data: 输入数据
            data_type: 数据类型 (wind_speed, temperature, humidity, all)

        Returns:
            APIResponse: 质量控制结果
        """
        try:
            logger.info(f"收到质量控制请求，类型: {data_type}")

            results = {}

            if data_type in ['wind_speed', 'all']:
                if 'wind_speed' in data:
                    results['wind_speed'] = MeteorologicalQualityControl.validate_wind_speed(
                        data['wind_speed']
                    ).tolist()

            if data_type in ['temperature', 'all']:
                if 'temperature' in data:
                    results['temperature'] = MeteorologicalQualityControl.validate_temperature(
                        data['temperature']
                    ).tolist()

            if data_type in ['humidity', 'all']:
                if 'humidity' in data:
                    results['humidity'] = MeteorologicalQualityControl.validate_humidity(
                        data['humidity']
                    ).tolist()

            return APIResponse(
                success=True,
                message="质量控制完成",
                data=results
            )

        except Exception as e:
            logger.error(f"质量控制失败: {e}", exc_info=True)
            return APIResponse(
                success=False,
                message="质量控制失败",
                error=str(e)
            )

    def risk_assessment(self, wind_speed: Any, variance: Optional[Any] = None) -> APIResponse:
        """
        风险评估

        Args:
            wind_speed: 风速数据
            variance: 方差数据（可选）

        Returns:
            APIResponse: 风险评估结果
        """
        try:
            logger.info("收到风险评估请求")

            import numpy as np

            if isinstance(wind_speed, list):
                wind_speed = np.array(wind_speed)

            if variance is not None and isinstance(variance, list):
                variance = np.array(variance)

            risk_result = MeteorologicalRiskAssessment.composite_risk_assessment(
                wind_speed, variance
            )

            result = {
                'wind_risk': risk_result['wind_risk'].tolist(),
                'turbulence_risk': risk_result['turbulence_risk'].tolist(),
                'composite_risk': risk_result['composite_risk'].tolist(),
                'max_wind_risk': int(risk_result['wind_risk'].max()),
                'max_turbulence_risk': int(risk_result['turbulence_risk'].max()),
                'max_composite_risk': int(risk_result['composite_risk'].max()),
                'high_risk_percentage': float(
                    np.sum(risk_result['composite_risk'] >= 3) /
                    risk_result['composite_risk'].size * 100
                )
            }

            return APIResponse(
                success=True,
                message="风险评估完成",
                data=result
            )

        except Exception as e:
            logger.error(f"风险评估失败: {e}", exc_info=True)
            return APIResponse(
                success=False,
                message="风险评估失败",
                error=str(e)
            )

    def time_series_analysis(self, time_series_data: Dict[str, Any],
                            predict_steps: int = 3) -> APIResponse:
        """
        时间序列分析

        Args:
            time_series_data: 时间序列数据
            predict_steps: 预测步数

        Returns:
            APIResponse: 时间序列分析结果
        """
        try:
            logger.info("收到时间序列分析请求")

            analyzer = TimeSeriesAnalyzer()

            # 分析风险趋势
            trend_data = analyzer.analyze_risk_trend(time_series_data)

            # 检测异常
            anomalies = analyzer.detect_risk_anomalies(trend_data)

            # 预测
            predictions = analyzer.predict_risk_trend(trend_data, n_steps=predict_steps)

            result = {
                'trend_data': trend_data,
                'anomalies': anomalies,
                'predictions': predictions,
                'n_anomalies': len(anomalies),
                'n_predictions': len(predictions)
            }

            return APIResponse(
                success=True,
                message="时间序列分析完成",
                data=result
            )

        except Exception as e:
            logger.error(f"时间序列分析失败: {e}", exc_info=True)
            return APIResponse(
                success=False,
                message="时间序列分析失败",
                error=str(e)
            )

    def validate_data(self, data: Dict[str, Any]) -> APIResponse:
        """
        数据验证

        Args:
            data: 待验证的数据

        Returns:
            APIResponse: 验证结果
        """
        try:
            logger.info("收到数据验证请求")

            from ..utils.validation import DataValidator

            validator = DataValidator()
            result = validator.validate(data)

            return APIResponse(
                success=result['valid'],
                message="数据验证完成",
                data=result
            )

        except Exception as e:
            logger.error(f"数据验证失败: {e}", exc_info=True)
            return APIResponse(
                success=False,
                message="数据验证失败",
                error=str(e)
            )

    def get_version(self) -> APIResponse:
        """获取版本信息"""
        try:
            from ..__version__ import __version__

            return APIResponse(
                success=True,
                message="获取版本信息成功",
                data={'version': __version__}
            )

        except Exception as e:
            logger.error(f"获取版本信息失败: {e}", exc_info=True)
            return APIResponse(
                success=False,
                message="获取版本信息失败",
                error=str(e)
            )


# FastAPI 路由定义


try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import List, Optional

    class AssimilationRequest(BaseModel):
        """同化请求模型"""
        background: Dict[str, Any]
        observations: Dict[str, Any]
        config: Optional[Dict[str, Any]] = None

    class QualityControlRequest(BaseModel):
        """质量控制请求模型"""
        data: Dict[str, Any]
        data_type: str = 'all'

    class RiskAssessmentRequest(BaseModel):
        """风险评估请求模型"""
        wind_speed: List[List[List[float]]]
        variance: Optional[List[List[List[float]]]] = None

    class TimeSeriesRequest(BaseModel):
        """时间序列分析请求模型"""
        time_series: List[Dict[str, Any]]
        predict_steps: int = 3

    class ValidationRequest(BaseModel):
        """数据验证请求模型"""
        data: Dict[str, Any]

    # 创建 FastAPI 应用
    app = FastAPI(
        title="贝叶斯同化系统 API",
        description="提供贝叶斯数据同化、质量控制、风险评估等功能的 REST API",
        version="1.0.0"
    )

    api = AssimilationAPI()

    @app.post("/assimilate", summary="执行贝叶斯同化")
    def assimilate_endpoint(request: AssimilationRequest):
        """执行贝叶斯数据同化"""
        response = api.assimilate(request.background, request.observations, request.config)
        if not response.success:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=response.error)
        return response.to_dict()

    @app.post("/quality-control", summary="质量控制")
    def quality_control_endpoint(request: QualityControlRequest):
        """对气象数据进行质量控制"""
        response = api.quality_control(request.data, request.data_type)
        if not response.success:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=response.error)
        return response.to_dict()

    @app.post("/risk-assessment", summary="风险评估")
    def risk_assessment_endpoint(request: RiskAssessmentRequest):
        """对风速数据进行风险评估"""
        response = api.risk_assessment(request.wind_speed, request.variance)
        if not response.success:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=response.error)
        return response.to_dict()

    @app.post("/time-series", summary="时间序列分析")
    def time_series_endpoint(request: TimeSeriesRequest):
        """对时间序列数据进行分析和预测"""
        response = api.time_series_analysis(request.time_series, request.predict_steps)
        if not response.success:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=response.error)
        return response.to_dict()

    @app.post("/validate", summary="数据验证")
    def validate_endpoint(request: ValidationRequest):
        """验证数据格式和质量"""
        response = api.validate_data(request.data)
        return response.to_dict()

    @app.get("/version", summary="获取版本信息")
    def version_endpoint():
        """获取系统版本信息"""
        response = api.get_version()
        return response.to_dict()

    @app.get("/health", summary="健康检查")
    def health_check():
        """检查 API 服务状态"""
        return {"status": "healthy", "service": "Bayesian Assimilation API"}

    def run(host: str = "0.0.0.0", port: int = 8000):
        """启动 API 服务"""
        import uvicorn
        logger.info(f"启动 API 服务: http://{host}:{port}")
        uvicorn.run(app, host=host, port=port)

except ImportError:
    logger.warning("FastAPI 未安装，REST API 功能不可用")

    def run(*args, **kwargs):
        raise RuntimeError("FastAPI 未安装，请先安装: pip install fastapi uvicorn")


if __name__ == '__main__':
    run(host='0.0.0.0', port=8000)
