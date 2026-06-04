"""
动画生成模块
提供时间序列数据的动画可视化功能
"""

import numpy as np
import logging
from typing import Optional, Tuple, List, Callable, Dict
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation, ArtistAnimation, PillowWriter, FFMpegWriter
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class TimeSeriesAnimator:
    """
    时间序列动画生成器
    用于生成随时间变化的数据动画
    """
    
    def __init__(self, resolution: float = 100.0):
        """
        Args:
            resolution: 网格分辨率（米）
        """
        self.resolution = resolution
    
    def create_variance_evolution(self,
                                  variance_fields: List[np.ndarray],
                                  times: Optional[List[str]] = None,
                                  slice_axis: int = 2,
                                  title: str = 'Variance Field Evolution',
                                  cmap: str = 'viridis',
                                  interval: int = 200,
                                  figsize: Tuple[int, int] = (10, 8)) -> FuncAnimation:
        """
        创建方差场时间演变动画
        
        Args:
            variance_fields: 方差场列表
            times: 时间标签列表
            slice_axis: 切片轴
            title: 动画标题
            cmap: 颜色映射
            interval: 帧间隔（毫秒）
            figsize: 图形大小
        
        Returns:
            FuncAnimation对象
        """
        if not variance_fields:
            raise ValueError("方差场列表为空")
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # 获取切片数据
        slice_index = variance_fields[0].shape[slice_axis] // 2
        
        def update(frame):
            ax.clear()
            
            if slice_axis == 0:
                data = variance_fields[frame][slice_index, :, :]
                extent = [0, variance_fields[frame].shape[1] * self.resolution, 
                         0, variance_fields[frame].shape[2] * self.resolution]
            elif slice_axis == 1:
                data = variance_fields[frame][:, slice_index, :]
                extent = [0, variance_fields[frame].shape[0] * self.resolution,
                         0, variance_fields[frame].shape[2] * self.resolution]
            else:
                data = variance_fields[frame][:, :, slice_index]
                extent = [0, variance_fields[frame].shape[0] * self.resolution,
                         0, variance_fields[frame].shape[1] * self.resolution]
            
            im = ax.imshow(data.T, origin='lower', cmap=cmap, extent=extent, aspect='auto')
            
            if times:
                ax.set_title(f'{title} - {times[frame]}')
            else:
                ax.set_title(f'{title} - Frame {frame + 1}/{len(variance_fields)}')
            
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            
            return [im]
        
        ani = FuncAnimation(fig, update, frames=len(variance_fields),
                           interval=interval, blit=True)
        
        logger.info(f"创建方差演变动画: {len(variance_fields)} 帧")
        return ani
    
    def create_wind_field_animation(self,
                                    u_fields: List[np.ndarray],
                                    v_fields: List[np.ndarray],
                                    times: Optional[List[str]] = None,
                                    slice_index: int = -1,
                                    skip: int = 5,
                                    title: str = 'Wind Field Evolution',
                                    interval: int = 200,
                                    figsize: Tuple[int, int] = (10, 8)) -> FuncAnimation:
        """
        创建风场动画
        
        Args:
            u_fields: U风分量列表
            v_fields: V风分量列表
            times: 时间标签列表
            slice_index: 切片索引
            skip: 跳过的网格点数
            title: 动画标题
            interval: 帧间隔（毫秒）
            figsize: 图形大小
        
        Returns:
            FuncAnimation对象
        """
        if len(u_fields) != len(v_fields):
            raise ValueError("u和v字段数量不匹配")
        
        fig, ax = plt.subplots(figsize=figsize)
        quiver = None
        
        def update(frame):
            nonlocal quiver
            
            ax.clear()
            
            u_slice = u_fields[frame][:, :, slice_index]
            v_slice = v_fields[frame][:, :, slice_index]
            
            nx, ny = u_slice.shape
            x = np.arange(nx) * self.resolution
            y = np.arange(ny) * self.resolution
            
            X, Y = np.meshgrid(x, y, indexing='ij')
            speed = np.sqrt(u_slice**2 + v_slice**2)
            
            quiver = ax.quiver(X[::skip, ::skip], Y[::skip, ::skip],
                              u_slice[::skip, ::skip], v_slice[::skip, ::skip],
                              speed[::skip, ::skip], cmap='coolwarm',
                              scale=100, width=0.002)
            
            if times:
                ax.set_title(f'{title} - {times[frame]}')
            else:
                ax.set_title(f'{title} - Frame {frame + 1}/{len(u_fields)}')
            
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_xlim(0, nx * self.resolution)
            ax.set_ylim(0, ny * self.resolution)
            
            return [quiver]
        
        ani = FuncAnimation(fig, update, frames=len(u_fields),
                           interval=interval, blit=True)
        
        logger.info(f"创建风场动画: {len(u_fields)} 帧")
        return ani
    
    def create_assimilation_comparison_animation(self,
                                                  backgrounds: List[np.ndarray],
                                                  analyses: List[np.ndarray],
                                                  observations: Optional[List[np.ndarray]] = None,
                                                  times: Optional[List[str]] = None,
                                                  slice_index: int = -1,
                                                  title: str = 'Assimilation Comparison',
                                                  interval: int = 300,
                                                  figsize: Tuple[int, int] = (16, 5)) -> FuncAnimation:
        """
        创建同化效果对比动画
        
        Args:
            backgrounds: 背景场列表
            analyses: 分析场列表
            observations: 观测数据列表
            times: 时间标签列表
            slice_index: 切片索引
            title: 动画标题
            interval: 帧间隔（毫秒）
            figsize: 图形大小
        
        Returns:
            FuncAnimation对象
        """
        fig, axes = plt.subplots(1, 3, figsize=figsize)
        
        def update(frame):
            for ax in axes:
                ax.clear()
            
            bg_slice = backgrounds[frame][:, :, slice_index]
            analysis_slice = analyses[frame][:, :, slice_index]
            increment = analysis_slice - bg_slice
            
            nx, ny = bg_slice.shape
            extent = [0, nx * self.resolution, 0, ny * self.resolution]
            
            vmin = min(np.nanmin(bg_slice), np.nanmin(analysis_slice))
            vmax = max(np.nanmax(bg_slice), np.nanmax(analysis_slice))
            
            axes[0].imshow(bg_slice.T, origin='lower', cmap='RdBu_r',
                          vmin=vmin, vmax=vmax, extent=extent)
            axes[0].set_title('Background')
            axes[0].set_xlabel('X (m)')
            axes[0].set_ylabel('Y (m)')
            
            axes[1].imshow(analysis_slice.T, origin='lower', cmap='RdBu_r',
                          vmin=vmin, vmax=vmax, extent=extent)
            axes[1].set_title('Analysis')
            axes[1].set_xlabel('X (m)')
            axes[1].set_ylabel('Y (m)')
            
            im3 = axes[2].imshow(increment.T, origin='lower', cmap='RdBu_r', extent=extent)
            axes[2].set_title('Increment')
            axes[2].set_xlabel('X (m)')
            axes[2].set_ylabel('Y (m)')
            
            if times:
                fig.suptitle(f'{title} - {times[frame]}')
            else:
                fig.suptitle(f'{title} - Frame {frame + 1}/{len(backgrounds)}')
            
            return []
        
        ani = FuncAnimation(fig, update, frames=len(backgrounds),
                           interval=interval, blit=False)
        
        logger.info(f"创建同化对比动画: {len(backgrounds)} 帧")
        return ani


class VarianceHeatmapAnimator:
    """
    方差热力图动画生成器
    用于生成方差随时间和空间演变的热力图动画
    """
    
    def __init__(self, resolution: float = 100.0):
        self.resolution = resolution
    
    def create_heatmap_animation(self,
                                  data: np.ndarray,
                                  title: str = 'Data Heatmap Evolution',
                                  cmap: str = 'hot',
                                  interval: int = 100,
                                  figsize: Tuple[int, int] = (12, 4)) -> FuncAnimation:
        """
        创建热力图动画（沿时间轴播放不同z层）
        
        Args:
            data: 数据 (time, nx, ny) 或 (time, nx, ny, nz)
            title: 动画标题
            cmap: 颜色映射
            interval: 帧间隔（毫秒）
            figsize: 图形大小
        
        Returns:
            FuncAnimation对象
        """
        if data.ndim == 3:
            data = data[:, :, :, np.newaxis]
        
        n_time, nx, ny, nz = data.shape
        
        fig, axes = plt.subplots(1, nz, figsize=figsize) if nz > 1 else plt.subplots(figsize=figsize)
        if nz == 1:
            axes = [axes]
        
        def update(frame):
            for i, ax in enumerate(axes):
                ax.clear()
                
                if nz == 1:
                    slice_data = data[frame, :, :, 0]
                else:
                    slice_data = data[frame, :, :, i]
                
                im = ax.imshow(slice_data.T, origin='lower', cmap=cmap, aspect='auto')
                ax.set_title(f'Level {i} - t={frame}')
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
            
            return []
        
        ani = FuncAnimation(fig, update, frames=n_time, interval=interval)
        
        logger.info(f"创建热力图动画: {n_time} 帧, {nz} 层")
        return ani


class AssimilationCycleAnimator:
    """
    同化循环动画生成器
    用于展示完整的同化循环过程
    """
    
    def __init__(self, resolution: float = 100.0):
        self.resolution = resolution
    
    def create_cycle_animation(self,
                               cycle_data: Dict[str, List[np.ndarray]],
                               times: List[str],
                               title: str = 'Assimilation Cycle',
                               interval: int = 500,
                               figsize: Tuple[int, int] = (14, 6)) -> FuncAnimation:
        """
        创建同化循环动画
        
        Args:
            cycle_data: 包含 'background', 'analysis', 'observations' 的字典
            times: 时间标签列表
            title: 动画标题
            interval: 帧间隔（毫秒）
            figsize: 图形大小
        
        Returns:
            FuncAnimation对象
        """
        backgrounds = cycle_data.get('background', [])
        analyses = cycle_data.get('analysis', [])
        
        if not backgrounds or not analyses:
            raise ValueError("需要提供 background 和 analysis 数据")
        
        fig = plt.figure(figsize=figsize)
        
        def update(frame):
            plt.clf()
            
            # 第一子图：背景场
            ax1 = plt.subplot(1, 3, 1)
            bg_slice = backgrounds[frame][:, :, -1]
            im1 = ax1.imshow(bg_slice.T, origin='lower', cmap='viridis', aspect='auto')
            ax1.set_title(f'Background\n{times[frame]}')
            ax1.set_xlabel('X (m)')
            ax1.set_ylabel('Y (m)')
            plt.colorbar(im1, ax=ax1)
            
            # 第二子图：分析场
            ax2 = plt.subplot(1, 3, 2)
            analysis_slice = analyses[frame][:, :, -1]
            im2 = ax2.imshow(analysis_slice.T, origin='lower', cmap='viridis', aspect='auto')
            ax2.set_title(f'Analysis\n{times[frame]}')
            ax2.set_xlabel('X (m)')
            ax2.set_ylabel('Y (m)')
            plt.colorbar(im2, ax=ax2)
            
            # 第三子图：增量
            ax3 = plt.subplot(1, 3, 3)
            increment = analysis_slice - bg_slice
            im3 = ax3.imshow(increment.T, origin='lower', cmap='RdBu_r', aspect='auto')
            ax3.set_title(f'Increment\n{times[frame]}')
            ax3.set_xlabel('X (m)')
            ax3.set_ylabel('Y (m)')
            plt.colorbar(im3, ax=ax3)
            
            plt.tight_layout()
            
            return []
        
        ani = FuncAnimation(fig, update, frames=len(backgrounds), interval=interval)
        
        logger.info(f"创建同化循环动画: {len(backgrounds)} 个循环")
        return ani


def save_animation(ani: FuncAnimation, 
                   filepath: str, 
                   writer: str = 'pillow',
                   fps: int = 5,
                   dpi: int = 100):
    """
    保存动画到文件
    
    Args:
        ani: FuncAnimation对象
        filepath: 保存路径
        writer: 写入器 ('pillow' 或 'ffmpeg')
        fps: 帧率
        dpi: 分辨率
    """
    if writer == 'pillow':
        ani.save(filepath, writer=PillowWriter(fps=fps), dpi=dpi)
    elif writer == 'ffmpeg':
        ani.save(filepath, writer=FFMpegWriter(fps=fps), dpi=dpi)
    else:
        raise ValueError(f"不支持的写入器: {writer}")
    
    logger.info(f"动画已保存到: {filepath}")


def display_animation(ani: FuncAnimation):
    """
    在Jupyter Notebook中显示动画
    
    Args:
        ani: FuncAnimation对象
    """
    from IPython.display import HTML
    return HTML(ani.to_jshtml())
