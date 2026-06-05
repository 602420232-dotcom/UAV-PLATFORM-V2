"""
监控面板模块
提供实时监控和数据展示面板功能
"""

import numpy as np
import logging
from typing import Optional, Tuple
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Slider
import matplotlib
matplotlib.use('Agg')  # 非交互式后端

logger = logging.getLogger(__name__)


class AssimilationDashboard:
    """
    同化监控面板
    实时展示同化过程和结果
    """

    def __init__(self, resolution: float = 100.0, figsize: Tuple[int, int] = (16, 10)):
        """
        Args:
            resolution: 网格分辨率（米）
            figsize: 图形大小
        """
        self.resolution = resolution
        self.figsize = figsize
        self.fig = None
        self.axes = {}
        self._init_figure()

    def _init_figure(self):
        """初始化图形布局"""
        self.fig = plt.figure(figsize=self.figsize)
        gs = GridSpec(3, 3, figure=self.fig, hspace=0.3, wspace=0.3)

        # 主显示区：分析场切片
        self.axes['main'] = self.fig.add_subplot(gs[0:2, 0:2])

        # 右侧：方差分布
        self.axes['variance'] = self.fig.add_subplot(gs[0, 2])

        # 右下：统计信息
        self.axes['stats'] = self.fig.add_subplot(gs[1, 2])

        # 底部：时间序列
        self.axes['timeseries'] = self.fig.add_subplot(gs[2, :])

        # 初始化显示
        self._setup_axes()

    def _setup_axes(self):
        """设置坐标轴"""
        self.axes['main'].set_title('Analysis Field')
        self.axes['main'].set_xlabel('X (m)')
        self.axes['main'].set_ylabel('Y (m)')

        self.axes['variance'].set_title('Variance Distribution')
        self.axes['variance'].set_xlabel('Variance')
        self.axes['variance'].set_ylabel('Frequency')

        self.axes['stats'].set_title('Statistics')
        self.axes['stats'].axis('off')

        self.axes['timeseries'].set_title('Time Series')
        self.axes['timeseries'].set_xlabel('Time Step')
        self.axes['timeseries'].set_ylabel('Value')

    def update(self,
               analysis: np.ndarray,
               variance: np.ndarray,
               background: Optional[np.ndarray] = None,
               step: int = 0,
               time_label: Optional[str] = None):
        """
        更新面板显示

        Args:
            analysis: 分析场数据
            variance: 方差场数据
            background: 背景场数据（可选）
            step: 当前步骤
            time_label: 时间标签
        """
        if self.fig is None:
            self._init_figure()

        # 更新分析场切片
        ax = self.axes['main']
        ax.clear()

        if analysis.ndim == 3:
            slice_data = analysis[:, :, -1]
        else:
            slice_data = analysis

        nx, ny = slice_data.shape
        extent = [0, nx * self.resolution, 0, ny * self.resolution]

        vmin, vmax = np.nanmin(slice_data), np.nanmax(slice_data)
        im = ax.imshow(slice_data.T, origin='lower', cmap='viridis',
                      vmin=vmin, vmax=vmax, extent=extent, aspect='auto')
        ax.set_title(f'Analysis Field - Step {step}' + (f' ({time_label})' if time_label else ''))
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')

        # 颜色条
        if hasattr(self, '_cbar'):
            self._cbar.update_normal(im)
        else:
            self._cbar = plt.colorbar(im, ax=ax)

        # 更新方差分布
        ax = self.axes['variance']
        ax.clear()

        var_data = variance.flatten()
        ax.hist(var_data, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
        ax.set_title('Variance Distribution')
        ax.set_xlabel('Variance')
        ax.set_ylabel('Frequency')
        ax.axvline(np.mean(var_data), color='red', linestyle='--', label=f'Mean: {np.mean(var_data):.4f}')
        ax.legend(fontsize=8)

        # 更新统计信息
        ax = self.axes['stats']
        ax.clear()
        ax.axis('off')

        stats_text = self._format_stats(analysis, variance, background)
        ax.text(0.1, 0.5, stats_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='center',
               fontfamily='monospace')

        # 更新时间序列（简化版本：绘制当前值的趋势）
        ax = self.axes['timeseries']
        ax.clear()

        # 这里应该维护一个历史列表，但简化版本只显示当前位置的垂直廊线
        if analysis.ndim == 3:
            profile = analysis[nx//2, ny//2, :]
            z = np.arange(len(profile)) * self.resolution
            ax.plot(profile, z, 'b-', label='Analysis')

            if background is not None:
                bg_profile = background[nx//2, ny//2, :]
                ax.plot(bg_profile, z, 'g--', label='Background')

            ax.set_xlabel('Value')
            ax.set_ylabel('Height (m)')
            ax.legend()

        ax.set_title('Vertical Profile at Center')

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        logger.debug(f"仪表盘已更新: 步骤 {step}")

    def _format_stats(self, analysis: np.ndarray, variance: np.ndarray,
                     background: Optional[np.ndarray]) -> str:
        """格式化统计信息"""
        lines = [
            "=" * 30,
            "同化统计信息",
            "=" * 30,
            f"分析场均值: {np.nanmean(analysis):.4f}",
            f"分析场标准差: {np.nanstd(analysis):.4f}",
            f"分析场最小值: {np.nanmin(analysis):.4f}",
            f"分析场最大值: {np.nanmax(analysis):.4f}",
            "-" * 30,
            f"方差均值: {np.nanmean(variance):.4f}",
            f"方差标准差: {np.nanstd(variance):.4f}",
            f"方差最小值: {np.nanmin(variance):.4f}",
            f"方差最大值: {np.nanmax(variance):.4f}",
        ]

        if background is not None:
            improvement = (np.nanstd(background) - np.nanstd(analysis)) / np.nanstd(background)
            lines.extend([
                "-" * 30,
                f"背景标准差: {np.nanstd(background):.4f}",
                f"改进度: {improvement:.2%}",
            ])

        return "\n".join(lines)

    def save(self, filepath: str):
        """保存当前面板状态"""
        if self.fig:
            self.fig.savefig(filepath, dpi=150, bbox_inches='tight')
            logger.info(f"仪表盘已保存到: {filepath}")

    def close(self):
        """关闭面板"""
        plt.close(self.fig)
        self.fig = None


class PerformanceDashboard:
    """
    性能监控面板
    展示系统性能指标
    """

    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        """
        Args:
            figsize: 图形大小
        """
        self.figsize = figsize
        self.history = {
            'cpu': [],
            'memory': [],
            'time': []
        }
        self.max_history = 100

    def update(self, cpu_percent: float, memory_mb: float, elapsed_time: float):
        """
        更新性能指标

        Args:
            cpu_percent: CPU使用率
            memory_mb: 内存使用（MB）
            elapsed_time: 已用时间（秒）
        """
        self.history['cpu'].append(cpu_percent)
        self.history['memory'].append(memory_mb)
        self.history['time'].append(elapsed_time)

        # 限制历史长度
        for key in self.history:
            if len(self.history[key]) > self.max_history:
                self.history[key] = self.history[key][-self.max_history:]

    def plot(self) -> Figure:
        """
        绘制性能面板

        Returns:
            matplotlib Figure对象
        """
        fig, axes = plt.subplots(2, 2, figsize=self.figsize)

        # CPU使用率
        ax = axes[0, 0]
        ax.plot(self.history['time'], self.history['cpu'], 'b-', linewidth=2)
        ax.fill_between(self.history['time'], 0, self.history['cpu'], alpha=0.3)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('CPU Usage (%)')
        ax.set_title('CPU Usage')
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)

        # 内存使用
        ax = axes[0, 1]
        ax.plot(self.history['time'], self.history['memory'], 'g-', linewidth=2)
        ax.fill_between(self.history['time'], 0, self.history['memory'], alpha=0.3, color='green')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Memory (MB)')
        ax.set_title('Memory Usage')
        ax.grid(True, alpha=0.3)

        # 当前状态
        ax = axes[1, 0]
        ax.axis('off')

        current = len(self.history['time']) - 1
        if current >= 0:
            stats_text = """
            当前状态
            ───────────
            CPU使用率: {self.history['cpu'][current]:.1f}%
            内存使用: {self.history['memory'][current]:.1f} MB
            运行时间: {self.history['time'][current]:.1f} 秒
            采样次数: {current + 1}
            """
            ax.text(0.3, 0.5, stats_text, transform=ax.transAxes,
                   fontsize=12, verticalalignment='center',
                   fontfamily='monospace')

        # 统计摘要
        ax = axes[1, 1]
        ax.axis('off')

        if len(self.history['cpu']) > 0:
            summary_text = """
            统计摘要
            ───────────
            平均CPU: {np.mean(self.history['cpu']):.1f}%
            最大CPU: {np.max(self.history['cpu']):.1f}%
            平均内存: {np.mean(self.history['memory']):.1f} MB
            最大内存: {np.max(self.history['memory']):.1f} MB
            总耗时: {self.history['time'][-1]:.1f} 秒
            """
            ax.text(0.3, 0.5, summary_text, transform=ax.transAxes,
                   fontsize=12, verticalalignment='center',
                   fontfamily='monospace')

        plt.tight_layout()
        return fig

    def save(self, filepath: str):
        """保存性能面板"""
        fig = self.plot()
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"性能面板已保存到: {filepath}")


class InteractiveDashboard:
    """
    交互式仪表盘
    支持用户交互操作
    """

    def __init__(self, resolution: float = 100.0, figsize: Tuple[int, int] = (14, 10)):
        """
        Args:
            resolution: 网格分辨率
            figsize: 图形大小
        """
        self.resolution = resolution
        self.figsize = figsize
        self.current_slice = 0
        self.show_background = True
        self.show_increment = True
        self.data_cache = {}

        self._setup_gui()

    def _setup_gui(self):
        """设置GUI界面"""
        self.fig = plt.figure(figsize=self.figsize)
        gs = GridSpec(4, 4, figure=self.fig, hspace=0.4, wspace=0.3)

        # 主显示区
        self.ax_main = self.fig.add_subplot(gs[0:3, 0:3])

        # 控制面板
        self.ax_controls = self.fig.add_subplot(gs[3, 0])
        self.ax_slice_slider = self.fig.add_subplot(gs[3, 1])
        self.ax_slice_label = self.fig.add_subplot(gs[3, 2])
        self.ax_buttons = self.fig.add_subplot(gs[3, 3])

        # 隐藏控制轴的边框
        for ax in [self.ax_controls, self.ax_slice_label, self.ax_buttons]:
            ax.axis('off')

        # 初始化控件
        self._create_controls()

    def _create_controls(self):
        """创建交互控件"""
        # 切片滑块
        self.slice_slider = Slider(
            self.ax_slice_slider, 'Slice', 0, 10,
            valinit=0, valstep=1
        )
        self.slice_slider.on_changed(self._on_slice_change)

        # 切片标签
        self.ax_slice_label.text(0.5, 0.5, f'Slice: {self.current_slice}',
                                transform=self.ax_slice_label.transAxes,
                                ha='center', va='center', fontsize=12)

        # 按钮
        self.ax_buttons.text(0.1, 0.7, 'Controls:', transform=self.ax_buttons.transAxes, fontsize=10)
        self.ax_buttons.text(0.1, 0.4, 'Space: Next Step\nS: Save Image\nQ: Quit',
                           transform=self.ax_buttons.transAxes, fontsize=9)

    def _on_slice_change(self, val):
        """切片滑块回调"""
        self.current_slice = int(val)
        self.ax_slice_label.text(0.5, 0.5, f'Slice: {self.current_slice}',
                                transform=self.ax_slice_label.transAxes,
                                ha='center', va='center', fontsize=12)
        self._redraw()

    def set_data(self,
                analysis: np.ndarray,
                variance: np.ndarray,
                background: Optional[np.ndarray] = None):
        """
        设置显示数据

        Args:
            analysis: 分析场
            variance: 方差场
            background: 背景场
        """
        self.data_cache['analysis'] = analysis
        self.data_cache['variance'] = variance
        self.data_cache['background'] = background

        # 更新滑块范围
        nz = analysis.shape[2] if analysis.ndim == 3 else 1
        self.slice_slider.valmax = nz - 1
        self.slice_slider.ax.set_xlim(0, nz - 1)

        self._redraw()

    def _redraw(self):
        """重绘主显示区"""
        if 'analysis' not in self.data_cache:
            return

        ax = self.ax_main
        ax.clear()

        analysis = self.data_cache['analysis']
        background = self.data_cache.get('background')

        if analysis.ndim == 3:
            slice_data = analysis[:, :, self.current_slice]
            if background is not None:
                bg_slice = background[:, :, self.current_slice]
        else:
            slice_data = analysis
            bg_slice = None

        nx, ny = slice_data.shape
        extent = [0, nx * self.resolution, 0, ny * self.resolution]

        if self.show_increment and bg_slice is not None:
            data = slice_data - bg_slice
            cmap = 'RdBu_r'
        else:
            data = slice_data
            cmap = 'viridis'

        im = ax.imshow(data.T, origin='lower', cmap=cmap, extent=extent, aspect='auto')
        ax.set_title(f'Analysis (Slice {self.current_slice})')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        plt.colorbar(im, ax=ax)

        self.fig.canvas.draw()

    def save_image(self, filepath: str):
        """保存当前图像"""
        self.fig.savefig(filepath, dpi=150, bbox_inches='tight')
        logger.info(f"图像已保存到: {filepath}")

    def connect_keyboard(self):
        """连接键盘事件"""
        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)

    def _on_key_press(self, event):
        """键盘事件处理"""
        if event.key == ' ':
            self.slice_slider.set_val((self.current_slice + 1) % (self.slice_slider.valmax + 1))
        elif event.key == 's':
            self.save_image('dashboard_snapshot.png')
        elif event.key == 'b':
            self.show_background = not self.show_background
            self._redraw()
        elif event.key == 'i':
            self.show_increment = not self.show_increment
            self._redraw()
        elif event.key == 'q':
            plt.close(self.fig)


def create_summary_dashboard(analysis: np.ndarray,
                            variance: np.ndarray,
                            background: Optional[np.ndarray] = None,
                            observations: Optional[np.ndarray] = None,
                            resolution: float = 100.0,
                            figsize: Tuple[int, int] = (16, 12)) -> Figure:
    """
    创建综合摘要面板

    Args:
        analysis: 分析场
        variance: 方差场
        background: 背景场
        observations: 观测数据
        resolution: 分辨率
        figsize: 图形大小

    Returns:
        matplotlib Figure对象
    """
    fig = plt.figure(figsize=figsize)
    gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.3)

    # 分析场切片
    ax1 = fig.add_subplot(gs[0, 0])
    if analysis.ndim == 3:
        data = analysis[:, :, -1]
    else:
        data = analysis
    nx, ny = data.shape
    extent = [0, nx * resolution, 0, ny * resolution]
    im1 = ax1.imshow(data.T, origin='lower', cmap='viridis', extent=extent, aspect='auto')
    ax1.set_title('Analysis Field')
    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    plt.colorbar(im1, ax=ax1)

    # 方差场切片
    ax2 = fig.add_subplot(gs[0, 1])
    if variance.ndim == 3:
        var_data = variance[:, :, -1]
    else:
        var_data = variance
    im2 = ax2.imshow(var_data.T, origin='lower', cmap='hot', extent=extent, aspect='auto')
    ax2.set_title('Variance Field')
    ax2.set_xlabel('X (m)')
    ax2.set_ylabel('Y (m)')
    plt.colorbar(im2, ax=ax2)

    # 增量
    ax3 = fig.add_subplot(gs[0, 2])
    if background is not None:
        if background.ndim == 3:
            bg_slice = background[:, :, -1]
        else:
            bg_slice = background
        increment = data - bg_slice
        im3 = ax3.imshow(increment.T, origin='lower', cmap='RdBu_r', extent=extent, aspect='auto')
        ax3.set_title('Increment')
        ax3.set_xlabel('X (m)')
        ax3.set_ylabel('Y (m)')
        plt.colorbar(im3, ax=ax3)
    else:
        ax3.axis('off')

    # 方差分布直方图
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.hist(variance.flatten(), bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    ax4.set_title('Variance Distribution')
    ax4.set_xlabel('Variance')
    ax4.set_ylabel('Frequency')
    ax4.axvline(np.mean(variance), color='red', linestyle='--', label=f'Mean: {np.mean(variance):.4f}')
    ax4.legend()

    # 垂直廊线对比
    ax5 = fig.add_subplot(gs[1, 1])
    z = np.arange(data.shape[0]) * resolution
    if analysis.ndim == 3:
        profile = analysis[nx//2, ny//2, :]
        ax5.plot(profile, z, 'b-', label='Analysis', linewidth=2)
        if background is not None and background.ndim == 3:
            bg_profile = background[nx//2, ny//2, :]
            ax5.plot(bg_profile, z, 'g--', label='Background', linewidth=2)
        ax5.set_xlabel('Value')
        ax5.set_ylabel('Height (m)')
        ax5.set_title('Vertical Profile')
        ax5.legend()
        ax5.grid(True, alpha=0.3)
    else:
        ax5.axis('off')

    # 统计摘要
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis('off')

    stats = [
        "统计摘要",
        "=" * 30,
        f"分析均值: {np.nanmean(analysis):.4f}",
        f"分析标准差: {np.nanstd(analysis):.4f}",
        f"方差均值: {np.nanmean(variance):.4f}",
        f"方差范围: [{np.nanmin(variance):.4f}, {np.nanmax(variance):.4f}]",
    ]

    if background is not None:
        improvement = (np.nanstd(background) - np.nanstd(analysis)) / np.nanstd(background)
        stats.extend([
            "-" * 30,
            f"背景标准差: {np.nanstd(background):.4f}",
            f"改进度: {improvement:.2%}",
        ])

    if observations is not None:
        stats.extend([
            "-" * 30,
            f"观测数量: {len(observations)}",
        ])

    ax6.text(0.1, 0.9, "\n".join(stats), transform=ax6.transAxes,
            fontsize=10, verticalalignment='top',
            fontfamily='monospace')

    # 时间/空间平均廊线
    ax7 = fig.add_subplot(gs[2, :])
    if analysis.ndim == 3:
        # 空间平均的垂直廊线
        mean_profile = np.nanmean(analysis, axis=(0, 1))
        ax7.plot(mean_profile, z, 'b-', label='Analysis Mean Profile', linewidth=2)

        if background is not None and background.ndim == 3:
            bg_mean_profile = np.nanmean(background, axis=(0, 1))
            ax7.plot(bg_mean_profile, z, 'g--', label='Background Mean Profile', linewidth=2)

        ax7.set_xlabel('Value')
        ax7.set_ylabel('Height (m)')
        ax7.set_title('Spatially Averaged Vertical Profile')
        ax7.legend()
        ax7.grid(True, alpha=0.3)

    return fig
