"""
标准化对比报告生成器
生成符合期刊论文要求的图表和表格
"""
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from loguru import logger


@dataclass
class ReportConfig:
    """报告配置"""
    title: str
    author: str
    institution: str
    output_dir: str = "./experiments/reports"
    figure_dpi: int = 300
    figure_format: str = "png"  # png, pdf, svg
    table_format: str = "csv"   # csv, latex


class ReportGenerator:
    """标准化对比报告生成器"""
    
    def __init__(self, config: ReportConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置matplotlib中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
    def generate_comparison_report(self, 
                                   experiment_results: List[Dict],
                                   metrics: List[str],
                                   output_name: Optional[str] = None) -> str:
        """
        生成算法对比报告
        
        Args:
            experiment_results: 多个实验的结果列表
            metrics: 需要对比的指标名称
            output_name: 输出文件名（不含扩展名）
            
        Returns:
            生成的报告文件路径
        """
        output_name = output_name or f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        report_dir = self.output_dir / output_name
        report_dir.mkdir(exist_ok=True)
        
        # 1. 生成对比表格
        self._generate_comparison_table(experiment_results, metrics, report_dir)
        
        # 2. 生成雷达图
        self._generate_radar_chart(experiment_results, metrics, report_dir)
        
        # 3. 生成柱状图
        self._generate_bar_chart(experiment_results, metrics, report_dir)
        
        # 4. 生成折线图（时序指标）
        self._generate_line_chart(experiment_results, report_dir)
        
        # 5. 生成LaTeX报告模板
        self._generate_latex_template(experiment_results, metrics, report_dir)
        
        logger.info(f"对比报告已生成: {report_dir}")
        return str(report_dir)
        
    def _generate_comparison_table(self, results: List[Dict], metrics: List[str], 
                                   report_dir: Path):
        """生成对比表格"""
        # CSV格式
        csv_path = report_dir / "comparison_table.csv"
        with open(csv_path, 'w', encoding='utf-8') as f:
            # 表头
            headers = ['算法', '版本'] + metrics + ['运行时间(s)', '时间戳']
            f.write(','.join(headers) + '\n')
            
            # 数据行
            for result in results:
                row = [
                    result.get('algorithm_name', ''),
                    result.get('algorithm_version', ''),
                ]
                for metric in metrics:
                    value = result.get('metrics', {}).get(metric, 'N/A')
                    row.append(f"{value:.4f}" if isinstance(value, float) else str(value))
                row.append(f"{result.get('execution_time', 0):.2f}")
                row.append(result.get('timestamp', ''))
                f.write(','.join(row) + '\n')
                
        # LaTeX格式
        latex_path = report_dir / "comparison_table.tex"
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write('\\begin{table}[htbp]\n')
            f.write('\\centering\n')
            f.write('\\caption{算法性能对比}\n')
            f.write('\\begin{tabular}{l' + 'c' * len(metrics) + '}\n')
            f.write('\\hline\n')
            f.write('算法 & ' + ' & '.join(metrics) + ' \\\\n')
            f.write('\\hline\n')
            
            for result in results:
                row = [result.get('algorithm_name', '')]
                for metric in metrics:
                    value = result.get('metrics', {}).get(metric, 'N/A')
                    row.append(f"{value:.4f}" if isinstance(value, float) else str(value))
                f.write(' & '.join(row) + ' \\\\n')
                
            f.write('\\hline\n')
            f.write('\\end{tabular}\n')
            f.write('\\end{table}\n')
            
    def _generate_radar_chart(self, results: List[Dict], metrics: List[str], 
                              report_dir: Path):
        """生成雷达图"""
        if len(metrics) < 3:
            return
            
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]  # 闭合
        
        colors = plt.cm.tab10(np.linspace(0, 1, len(results)))
        
        for idx, result in enumerate(results):
            values = []
            for metric in metrics:
                value = result.get('metrics', {}).get(metric, 0)
                # 归一化到0-1范围（假设指标越大越好）
                max_val = max(r.get('metrics', {}).get(metric, 1) for r in results)
                values.append(value / max_val if max_val > 0 else 0)
            values += values[:1]  # 闭合
            
            ax.plot(angles, values, 'o-', linewidth=2, 
                   label=result.get('algorithm_name', ''), color=colors[idx])
            ax.fill(angles, values, alpha=0.15, color=colors[idx])
            
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics)
        ax.set_ylim(0, 1)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        ax.set_title('算法性能雷达图', pad=20)
        
        plt.tight_layout()
        plt.savefig(report_dir / f"radar_chart.{self.config.figure_format}", 
                   dpi=self.config.figure_dpi, bbox_inches='tight')
        plt.close()
        
    def _generate_bar_chart(self, results: List[Dict], metrics: List[str], 
                           report_dir: Path):
        """生成柱状图"""
        fig, axes = plt.subplots(1, len(metrics), figsize=(5 * len(metrics), 5))
        
        if len(metrics) == 1:
            axes = [axes]
            
        algorithm_names = [r.get('algorithm_name', f'Algo_{i}') 
                          for i, r in enumerate(results)]
        
        for idx, metric in enumerate(metrics):
            values = [r.get('metrics', {}).get(metric, 0) for r in results]
            
            axes[idx].bar(algorithm_names, values, color=plt.cm.tab10(np.linspace(0, 1, len(results))))
            axes[idx].set_title(f'{metric}')
            axes[idx].set_ylabel('数值')
            axes[idx].tick_params(axis='x', rotation=45)
            
        plt.tight_layout()
        plt.savefig(report_dir / f"bar_chart.{self.config.figure_format}", 
                   dpi=self.config.figure_dpi, bbox_inches='tight')
        plt.close()
        
    def _generate_line_chart(self, results: List[Dict], report_dir: Path):
        """生成折线图（时序指标）"""
        # 如果结果包含时序数据，生成折线图
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for result in results:
            if 'time_series' in result:
                ts_data = result['time_series']
                ax.plot(ts_data.get('timestamps', []), 
                       ts_data.get('values', []),
                       label=result.get('algorithm_name', ''),
                       linewidth=2)
                
        ax.set_xlabel('时间')
        ax.set_ylabel('指标值')
        ax.set_title('算法时序性能对比')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(report_dir / f"line_chart.{self.config.figure_format}", 
                   dpi=self.config.figure_dpi, bbox_inches='tight')
        plt.close()
        
    def _generate_latex_template(self, results: List[Dict], metrics: List[str], 
                                 report_dir: Path):
        """生成LaTeX报告模板"""
        latex_path = report_dir / "report_template.tex"
        
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write('\\documentclass{article}\n')
            f.write('\\usepackage{graphicx}\n')
            f.write('\\usepackage{booktabs}\n')
            f.write('\\usepackage{geometry}\n')
            f.write('\\geometry{a4paper, margin=1in}\n')
            f.write('\\begin{document}\n\n')
            
            f.write(f'\\title{{{self.config.title}}}\n')
            f.write(f'\\author{{{self.config.author}}}\n')
            f.write(f'\\date{{{datetime.now().strftime("%Y-%m-%d")}}}\n')
            f.write('\\maketitle\n\n')
            
            f.write('\\section{实验概述}\n')
            f.write(f'本实验对比了 {len(results)} 种算法的性能表现。\n\n')
            
            f.write('\\section{性能对比}\n')
            f.write('\\input{comparison_table}\n\n')
            
            f.write('\\section{可视化结果}\n')
            f.write('\\begin{figure}[htbp]\n')
            f.write('\\centering\n')
            f.write(f'\\includegraphics[width=0.8\\textwidth]{{radar_chart.{self.config.figure_format}}}\n')
            f.write('\\caption{算法性能雷达图}\n')
            f.write('\\end{figure}\n\n')
            
            f.write('\\begin{figure}[htbp]\n')
            f.write('\\centering\n')
            f.write(f'\\includegraphics[width=0.8\\textwidth]{{bar_chart.{self.config.figure_format}}}\n')
            f.write('\\caption{算法性能柱状图}\n')
            f.write('\\end{figure}\n\n')
            
            f.write('\\end{document}\n')
