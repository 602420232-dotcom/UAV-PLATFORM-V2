"""
命令行接口模块
提供贝叶斯同化系统的命令行工具
"""

import argparse
import logging
import sys
import json
import os
from typing import Optional, Dict, Any

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from bayesian_assimilation.core.assimilator import BayesianAssimilator
from bayesian_assimilation.utils.config import AssimilationConfig
from bayesian_assimilation.adapters.data import WRFDataAdapter, ObservationAdapter
from bayesian_assimilation.adapters.io import write_netcdf, write_hdf5
from bayesian_assimilation.quality_control import MeteorologicalQualityControl
from bayesian_assimilation.risk_assessment import MeteorologicalRiskAssessment
from bayesian_assimilation.time_series import TimeSeriesAnalyzer
from bayesian_assimilation.utils.logging import setup_logging

logger = logging.getLogger(__name__)


class AssimilationCLI:
    """
    贝叶斯同化命令行接口
    """
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='assimilation',
            description='贝叶斯数据同化系统命令行工具',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        self._setup_subparsers()
    
    def _setup_subparsers(self):
        """设置子命令解析器"""
        subparsers = self.parser.add_subparsers(dest='command', help='可用命令')
        
        # assimilate 命令
        assimilate_parser = subparsers.add_parser(
            'assimilate',
            help='执行贝叶斯同化',
            description='执行贝叶斯数据同化，将观测数据与背景场融合'
        )
        assimilate_parser.add_argument(
            '--config', '-c',
            type=str,
            help='配置文件路径'
        )
        assimilate_parser.add_argument(
            '--background', '-b',
            type=str,
            required=True,
            help='背景场数据文件路径'
        )
        assimilate_parser.add_argument(
            '--observations', '-o',
            type=str,
            required=True,
            help='观测数据文件路径'
        )
        assimilate_parser.add_argument(
            '--output', '-out',
            type=str,
            default='./output',
            help='输出目录路径'
        )
        assimilate_parser.add_argument(
            '--method', '-m',
            type=str,
            choices=['3dvar', 'enkf', 'enhanced'],
            default='3dvar',
            help='同化方法'
        )
        
        # quality_control 命令
        qc_parser = subparsers.add_parser(
            'quality-control',
            help='质量控制',
            description='对气象数据进行质量控制和验证'
        )
        qc_parser.add_argument(
            '--input', '-i',
            type=str,
            required=True,
            help='输入数据文件路径'
        )
        qc_parser.add_argument(
            '--output', '-o',
            type=str,
            default='./qc_output',
            help='输出目录路径'
        )
        qc_parser.add_argument(
            '--data-type', '-t',
            type=str,
            choices=['wind_speed', 'temperature', 'humidity', 'all'],
            default='all',
            help='数据类型'
        )
        
        # risk-assessment 命令
        risk_parser = subparsers.add_parser(
            'risk-assessment',
            help='风险评估',
            description='对同化结果进行气象风险评估'
        )
        risk_parser.add_argument(
            '--input', '-i',
            type=str,
            required=True,
            help='输入数据文件路径'
        )
        risk_parser.add_argument(
            '--output', '-o',
            type=str,
            default='./risk_output',
            help='输出目录路径'
        )
        risk_parser.add_argument(
            '--variance', '-v',
            type=str,
            help='方差场数据文件路径'
        )
        
        # time-series 命令
        ts_parser = subparsers.add_parser(
            'time-series',
            help='时间序列分析',
            description='对时序数据进行分析和预测'
        )
        ts_parser.add_argument(
            '--input', '-i',
            type=str,
            required=True,
            help='输入时间序列数据文件路径'
        )
        ts_parser.add_argument(
            '--output', '-o',
            type=str,
            default='./ts_output',
            help='输出目录路径'
        )
        ts_parser.add_argument(
            '--predict-steps', '-p',
            type=int,
            default=3,
            help='预测步数'
        )
        
        # validate 命令
        validate_parser = subparsers.add_parser(
            'validate',
            help='数据验证',
            description='验证数据格式和质量'
        )
        validate_parser.add_argument(
            '--input', '-i',
            type=str,
            required=True,
            help='输入数据文件路径'
        )
        validate_parser.add_argument(
            '--schema', '-s',
            type=str,
            help='JSON Schema 文件路径'
        )
        
        # version 命令
        subparsers.add_parser(
            'version',
            help='显示版本信息',
            description='显示贝叶斯同化系统版本信息'
        )
    
    def run(self, args: Optional[list] = None):
        """
        运行命令行接口
        
        Args:
            args: 命令行参数列表，如果为 None 则从 sys.argv 获取
        """
        if args is None:
            args = sys.argv[1:]
        
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return
        
        # 设置日志
        setup_logging()
        
        # 根据命令执行相应操作
        if parsed_args.command == 'assimilate':
            self._run_assimilate(parsed_args)
        elif parsed_args.command == 'quality-control':
            self._run_quality_control(parsed_args)
        elif parsed_args.command == 'risk-assessment':
            self._run_risk_assessment(parsed_args)
        elif parsed_args.command == 'time-series':
            self._run_time_series(parsed_args)
        elif parsed_args.command == 'validate':
            self._run_validate(parsed_args)
        elif parsed_args.command == 'version':
            self._run_version()
    
    def _run_assimilate(self, args):
        """执行同化命令"""
        logger.info("开始执行贝叶斯同化...")
        
        try:
            # 创建输出目录
            os.makedirs(args.output, exist_ok=True)
            
            # 加载配置
            if args.config:
                config = AssimilationConfig.from_file(args.config)
            else:
                config = AssimilationConfig()
            
            # 加载背景场数据
            logger.info(f"加载背景场数据: {args.background}")
            wrf_adapter = WRFDataAdapter()
            background_data = wrf_adapter.load(args.background)
            
            # 加载观测数据
            logger.info(f"加载观测数据: {args.observations}")
            obs_adapter = ObservationAdapter()
            obs_data = obs_adapter.load(args.observations)
            
            # 质量控制
            logger.info("执行质量控制...")
            wind_speed = background_data.get('wind_speed')
            if wind_speed is not None:
                wind_speed = MeteorologicalQualityControl.validate_wind_speed(wind_speed)
                background_data['wind_speed'] = wind_speed
            
            # 创建同化器
            assimilator = BayesianAssimilator(config)
            
            # 执行同化
            logger.info(f"执行{args.method.upper()}同化...")
            analysis, variance = assimilator.assimilate(
                background_data['wind_speed'],
                obs_data['observations'],
                obs_data['locations']
            )
            
            # 保存结果
            logger.info(f"保存结果到: {args.output}")
            output_path = os.path.join(args.output, 'analysis.nc')
            write_netcdf(output_path, {
                'analysis': analysis,
                'variance': variance
            })
            
            # 生成结果摘要
            summary = {
                'status': 'success',
                'method': args.method,
                'analysis_shape': list(analysis.shape),
                'variance_shape': list(variance.shape),
                'analysis_range': [float(analysis.min()), float(analysis.max())],
                'variance_range': [float(variance.min()), float(variance.max())]
            }
            
            summary_path = os.path.join(args.output, 'summary.json')
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info("同化完成！")
            
        except Exception as e:
            logger.error(f"同化失败: {e}", exc_info=True)
            sys.exit(1)
    
    def _run_quality_control(self, args):
        """执行质量控制命令"""
        logger.info("开始执行质量控制...")
        
        try:
            os.makedirs(args.output, exist_ok=True)
            
            # 加载数据
            data = self._load_data(args.input)
            
            # 质量控制
            results = {}
            
            if args.data_type in ['wind_speed', 'all']:
                if 'wind_speed' in data:
                    results['wind_speed'] = MeteorologicalQualityControl.validate_wind_speed(data['wind_speed'])
                    logger.info("风速数据质量控制完成")
            
            if args.data_type in ['temperature', 'all']:
                if 'temperature' in data:
                    results['temperature'] = MeteorologicalQualityControl.validate_temperature(data['temperature'])
                    logger.info("温度数据质量控制完成")
            
            if args.data_type in ['humidity', 'all']:
                if 'humidity' in data:
                    results['humidity'] = MeteorologicalQualityControl.validate_humidity(data['humidity'])
                    logger.info("湿度数据质量控制完成")
            
            # 保存结果
            output_path = os.path.join(args.output, 'qc_result.nc')
            write_netcdf(output_path, results)
            
            logger.info("质量控制完成！")
            
        except Exception as e:
            logger.error(f"质量控制失败: {e}", exc_info=True)
            sys.exit(1)
    
    def _run_risk_assessment(self, args):
        """执行风险评估命令"""
        logger.info("开始执行风险评估...")
        
        try:
            os.makedirs(args.output, exist_ok=True)
            
            # 加载数据
            data = self._load_data(args.input)
            
            # 加载方差数据（如果提供）
            variance = None
            if args.variance:
                variance_data = self._load_data(args.variance)
                variance = variance_data.get('variance')
            
            # 风险评估
            wind_speed = data.get('wind_speed')
            if wind_speed is not None:
                risk_result = MeteorologicalRiskAssessment.composite_risk_assessment(wind_speed, variance)
                
                # 保存结果
                output_path = os.path.join(args.output, 'risk_assessment.nc')
                write_netcdf(output_path, risk_result)
                
                # 生成摘要
                summary = {
                    'max_wind_risk': int(risk_result['wind_risk'].max()),
                    'max_turbulence_risk': int(risk_result['turbulence_risk'].max()),
                    'max_composite_risk': int(risk_result['composite_risk'].max()),
                    'high_risk_percentage': float(
                        np.sum(risk_result['composite_risk'] >= 3) / risk_result['composite_risk'].size * 100
                    )
                }
                
                summary_path = os.path.join(args.output, 'risk_summary.json')
                with open(summary_path, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2)
                
                logger.info("风险评估完成！")
            else:
                logger.error("未找到风速数据")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"风险评估失败: {e}", exc_info=True)
            sys.exit(1)
    
    def _run_time_series(self, args):
        """执行时间序列分析命令"""
        logger.info("开始执行时间序列分析...")
        
        try:
            os.makedirs(args.output, exist_ok=True)
            
            # 加载数据
            data = self._load_data(args.input)
            
            # 分析时间序列
            analyzer = TimeSeriesAnalyzer()
            
            if 'time_series' in data:
                trend_data = analyzer.analyze_risk_trend(data['time_series'])
                anomalies = analyzer.detect_risk_anomalies(trend_data)
                predictions = analyzer.predict_risk_trend(trend_data, n_steps=args.predict_steps)
                
                # 保存结果
                results = {
                    'trend_data': trend_data,
                    'anomalies': anomalies,
                    'predictions': predictions
                }
                
                summary_path = os.path.join(args.output, 'ts_analysis.json')
                with open(summary_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                
                logger.info("时间序列分析完成！")
                if anomalies:
                    logger.info(f"检测到 {len(anomalies)} 个异常")
                logger.info(f"预测了 {len(predictions)} 个时间步")
                
        except Exception as e:
            logger.error(f"时间序列分析失败: {e}", exc_info=True)
            sys.exit(1)
    
    def _run_validate(self, args):
        """执行数据验证命令"""
        logger.info("开始数据验证...")
        
        try:
            from ..utils.validation import DataValidator
            
            validator = DataValidator()
            result = validator.validate_file(args.input, args.schema)
            
            if result['valid']:
                logger.info("数据验证通过！")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                logger.error("数据验证失败！")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"数据验证失败: {e}", exc_info=True)
            sys.exit(1)
    
    def _run_version(self):
        """显示版本信息"""
        from ..__version__ import __version__
        logger.info(f"贝叶斯同化系统 v{__version__}")
    
    def _load_data(self, file_path: str) -> Dict[str, Any]:
        """加载数据文件"""
        import numpy as np
        
        _, ext = os.path.splitext(file_path)
        
        if ext == '.nc':
            from ..adapters.io import NetCDFReader
            reader = NetCDFReader()
            return reader.read(file_path)
        elif ext == '.h5':
            from ..adapters.io import HDF5Reader
            reader = HDF5Reader()
            return reader.read(file_path)
        elif ext == '.npy':
            return {'data': np.load(file_path)}
        else:
            raise ValueError(f"不支持的文件格式: {ext}")


def main():
    """命令行入口"""
    cli = AssimilationCLI()
    cli.run()


if __name__ == '__main__':
    main()

