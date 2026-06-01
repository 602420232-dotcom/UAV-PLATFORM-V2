"""
Web 界面模块
提供贝叶斯同化系统的 Web 可视化界面
"""

import logging
import os
import sys
from typing import Optional

logger = logging.getLogger(__name__)

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


def create_app(debug: bool = False):
    """
    创建 Web 应用
    
    Args:
        debug: 是否启用调试模式
        
    Returns:
        Flask 应用实例
    """
    try:
        from flask import Flask, render_template, request, jsonify, send_from_directory
        from flask_cors import CORS
        
        app = Flask(__name__, template_folder='templates', static_folder='static')
        app.config['DEBUG'] = debug
        
        # 启用 CORS
        CORS(app)
        
        # 导入核心功能
        from bayesian_assimilation.core.assimilator import BayesianAssimilator
        from bayesian_assimilation.utils.config import AssimilationConfig
        from bayesian_assimilation.quality_control import MeteorologicalQualityControl
        from bayesian_assimilation.risk_assessment import MeteorologicalRiskAssessment
        from bayesian_assimilation.time_series import TimeSeriesAnalyzer
        from bayesian_assimilation.utils.logging import setup_logging
        
        setup_logging()
        
        # 主页路由
        @app.route('/')
        def index():
            """主页"""
            return render_template('index.html')
        
        # API 路由 - 执行同化
        @app.route('/api/assimilate', methods=['POST'])
        def assimilate():
            """执行贝叶斯同化"""
            try:
                data = request.get_json()
                
                background_data = data.get('background', {})
                observations = data.get('observations', {})
                config = data.get('config', {})
                
                # 创建配置
                assimilation_config = AssimilationConfig()
                assimilation_config.update(config)
                
                # 创建同化器
                assimilator = BayesianAssimilator(assimilation_config)
                
                # 提取数据
                import numpy as np
                background = np.array(background_data.get('wind_speed', []))
                obs_values = np.array(observations.get('values', []))
                obs_locations = np.array(observations.get('locations', []))
                
                # 质量控制
                background = MeteorologicalQualityControl.validate_wind_speed(background)
                
                # 执行同化
                analysis, variance = assimilator.assimilate(
                    background, obs_values, obs_locations
                )
                
                return jsonify({
                    'success': True,
                    'message': '同化成功',
                    'data': {
                        'analysis_shape': list(analysis.shape),
                        'variance_shape': list(variance.shape),
                        'analysis_range': [float(analysis.min()), float(analysis.max())],
                        'variance_range': [float(variance.min()), float(variance.max())]
                    }
                })
                
            except Exception as e:
                logger.error(f"同化失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'message': '同化失败',
                    'error': str(e)
                }), 500
        
        # API 路由 - 质量控制
        @app.route('/api/quality-control', methods=['POST'])
        def quality_control():
            """质量控制"""
            try:
                data = request.get_json()
                input_data = data.get('data', {})
                data_type = data.get('data_type', 'all')
                
                results = {}
                
                import numpy as np
                
                if data_type in ['wind_speed', 'all']:
                    if 'wind_speed' in input_data:
                        results['wind_speed'] = MeteorologicalQualityControl.validate_wind_speed(
                            np.array(input_data['wind_speed'])
                        ).tolist()
                
                if data_type in ['temperature', 'all']:
                    if 'temperature' in input_data:
                        results['temperature'] = MeteorologicalQualityControl.validate_temperature(
                            np.array(input_data['temperature'])
                        ).tolist()
                
                if data_type in ['humidity', 'all']:
                    if 'humidity' in input_data:
                        results['humidity'] = MeteorologicalQualityControl.validate_humidity(
                            np.array(input_data['humidity'])
                        ).tolist()
                
                return jsonify({
                    'success': True,
                    'message': '质量控制完成',
                    'data': results
                })
                
            except Exception as e:
                logger.error(f"质量控制失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'message': '质量控制失败',
                    'error': str(e)
                }), 500
        
        # API 路由 - 风险评估
        @app.route('/api/risk-assessment', methods=['POST'])
        def risk_assessment():
            """风险评估"""
            try:
                data = request.get_json()
                
                import numpy as np
                wind_speed = np.array(data.get('wind_speed', []))
                variance = data.get('variance')
                if variance is not None:
                    variance = np.array(variance)
                
                risk_result = MeteorologicalRiskAssessment.composite_risk_assessment(
                    wind_speed, variance
                )
                
                return jsonify({
                    'success': True,
                    'message': '风险评估完成',
                    'data': {
                        'max_wind_risk': int(risk_result['wind_risk'].max()),
                        'max_turbulence_risk': int(risk_result['turbulence_risk'].max()),
                        'max_composite_risk': int(risk_result['composite_risk'].max()),
                        'high_risk_percentage': float(
                            np.sum(risk_result['composite_risk'] >= 3) / 
                            risk_result['composite_risk'].size * 100
                        )
                    }
                })
                
            except Exception as e:
                logger.error(f"风险评估失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'message': '风险评估失败',
                    'error': str(e)
                }), 500
        
        # API 路由 - 时间序列分析
        @app.route('/api/time-series', methods=['POST'])
        def time_series():
            """时间序列分析"""
            try:
                data = request.get_json()
                time_series_data = data.get('time_series', [])
                predict_steps = data.get('predict_steps', 3)
                
                analyzer = TimeSeriesAnalyzer()
                
                trend_data = analyzer.analyze_risk_trend(time_series_data)
                anomalies = analyzer.detect_risk_anomalies(trend_data)
                predictions = analyzer.predict_risk_trend(trend_data, n_steps=predict_steps)
                
                return jsonify({
                    'success': True,
                    'message': '时间序列分析完成',
                    'data': {
                        'trend_data': trend_data,
                        'anomalies': anomalies,
                        'predictions': predictions,
                        'n_anomalies': len(anomalies),
                        'n_predictions': len(predictions)
                    }
                })
                
            except Exception as e:
                logger.error(f"时间序列分析失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'message': '时间序列分析失败',
                    'error': str(e)
                }), 500
        
        # API 路由 - 版本信息
        @app.route('/api/version')
        def version():
            """获取版本信息"""
            from ..__version__ import __version__
            return jsonify({
                'success': True,
                'data': {'version': __version__}
            })
        
        # API 路由 - 健康检查
        @app.route('/api/health')
        def health():
            """健康检查"""
            return jsonify({'status': 'healthy'})
        
        # 静态文件服务
        @app.route('/static/<path:path>')
        def send_static(path: str):
            return send_from_directory('static', path)
        
        return app
        
    except ImportError as e:
        logger.warning(f"Flask 相关依赖未安装: {e}")
        raise RuntimeError("Flask 未安装，请先安装: pip install flask flask-cors")


def run(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    """
    启动 Web 服务
    
    Args:
        host: 主机地址
        port: 端口号
        debug: 是否启用调试模式
    """
    app = create_app(debug)
    logger.info(f"启动 Web 服务: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run()
