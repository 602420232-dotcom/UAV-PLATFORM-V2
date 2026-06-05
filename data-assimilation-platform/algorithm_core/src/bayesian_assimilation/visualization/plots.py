"""
静态绘图模块
提供方差场、风场等静态数据的可视化功能
"""

import numpy as np
import logging
from typing import Optional, Tuple
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class VarianceFieldPlotter:
    """
    方差场绘图器
    用于可视化同化结果的方差分布
    """

    def __init__(self, resolution: float = 100.0):
        """
        Args:
            resolution: 网格分辨率（米）
        """
        self.resolution = resolution

    def plot_2d_slice(self,
                      variance_field: np.ndarray,
                      slice_axis: int = 2,
                      slice_index: Optional[int] = None,
                      title: Optional[str] = None,
                      cmap: str = 'viridis',
                      figsize: Tuple[int, int] = (10, 8)) -> Figure:
        """
        绘制2D切片图

        Args:
            variance_field: 方差场数据 (nx, ny, nz)
            slice_axis: 切片轴 (0=x, 1=y, 2=z)
            slice_index: 切片索引，None则取中间
            title: 图表标题
            cmap: 颜色映射
            figsize: 图形大小

        Returns:
            matplotlib Figure对象
        """
        if variance_field.ndim != 3:
            raise ValueError(f"期望3D数据，实际维度: {variance_field.ndim}")

        nx, ny, nz = variance_field.shape

        if slice_index is None:
            slice_index = variance_field.shape[slice_axis] // 2

        # 提取切片
        if slice_axis == 0:
            data_slice = variance_field[slice_index, :, :]
            xlabel, ylabel = 'Y (m)', 'Z (m)'
            extent = [0, ny * self.resolution, 0, nz * self.resolution]
        elif slice_axis == 1:
            data_slice = variance_field[:, slice_index, :]
            xlabel, ylabel = 'X (m)', 'Z (m)'
            extent = [0, nx * self.resolution, 0, nz * self.resolution]
        else:
            data_slice = variance_field[:, :, slice_index]
            xlabel, ylabel = 'X (m)', 'Y (m)'
            extent = [0, nx * self.resolution, 0, ny * self.resolution]

        fig, ax = plt.subplots(figsize=figsize)
        im = ax.imshow(data_slice.T, origin='lower', cmap=cmap, extent=extent, aspect='auto')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title or f'Variance Field Slice (Axis={slice_axis}, Index={slice_index})')
        plt.colorbar(im, ax=ax, label='Variance')

        logger.info(f"绘制2D切片: axis={slice_axis}, index={slice_index}")
        return fig

    def plot_3d_surface(self,
                       variance_field: np.ndarray,
                       threshold: Optional[float] = None,
                       title: str = 'Variance Field 3D Surface',
                       figsize: Tuple[int, int] = (12, 10)) -> Figure:
        """
        绘制3D表面图

        Args:
            variance_field: 方差场数据
            threshold: 显示阈值，高于该值才显示
            title: 图表标题
            figsize: 图形大小

        Returns:
            matplotlib Figure对象
        """
        nx, ny, nz = variance_field.shape

        # 简化：绘制中心切面的3D表面
        mid_z = nz // 2
        data_slice = variance_field[:, :, mid_z]

        if threshold is not None:
            data_slice = np.where(data_slice > threshold, data_slice, np.nan)

        x = np.arange(nx) * self.resolution
        y = np.arange(ny) * self.resolution
        X, Y = np.meshgrid(x, y, indexing='ij')

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')

        surf = ax.plot_surface(X, Y, data_slice, cmap='viridis',
                               linewidth=0, antialiased=True, alpha=0.8)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Variance')
        ax.set_title(title)
        fig.colorbar(surf, ax=ax, shrink=0.5, label='Variance')

        logger.info("绘制3D表面图")
        return fig

    def plot_contour(self,
                    variance_field: np.ndarray,
                    slice_index: int = -1,
                    levels: int = 20,
                    title: Optional[str] = None,
                    figsize: Tuple[int, int] = (10, 8)) -> Figure:
        """
        绘制等值线图

        Args:
            variance_field: 方差场数据
            slice_index: 切片索引
            levels: 等值线数量
            title: 图表标题
            figsize: 图形大小

        Returns:
            matplotlib Figure对象
        """
        data_slice = variance_field[:, :, slice_index]
        nx, ny = data_slice.shape

        x = np.arange(nx) * self.resolution
        y = np.arange(ny) * self.resolution

        fig, ax = plt.subplots(figsize=figsize)
        cs = ax.contourf(x, y, data_slice, levels=levels, cmap='plasma')
        ax.contour(x, y, data_slice, levels=levels, colors='k', linewidths=0.5, alpha=0.3)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_title(title or 'Variance Field Contour')
        plt.colorbar(cs, ax=ax, label='Variance')

        logger.info("绘制等值线图")
        return fig

    def plot_histogram(self,
                      variance_field: np.ndarray,
                      bins: int = 50,
                      title: str = 'Variance Distribution',
                      figsize: Tuple[int, int] = (10, 6)) -> Figure:
        """
        绘制方差分布直方图

        Args:
            variance_field: 方差场数据
            bins: 直方图bin数量
            title: 图表标题
            figsize: 图形大小

        Returns:
            matplotlib Figure对象
        """
        data = variance_field.flatten()

        fig, ax = plt.subplots(figsize=figsize)
        ax.hist(data, bins=bins, color='steelblue', edgecolor='black', alpha=0.7)
        ax.set_xlabel('Variance')
        ax.set_ylabel('Frequency')
        ax.set_title(title)
        ax.axvline(np.mean(data), color='red', linestyle='--', label=f'Mean: {np.mean(data):.4f}')
        ax.axvline(np.median(data), color='green', linestyle='--', label=f'Median: {np.median(data):.4f}')
        ax.legend()

        logger.info("绘制直方图")
        return fig


class WindFieldPlotter:
    """
    风场绘图器
    用于可视化风速/风向分布
    """

    def __init__(self, resolution: float = 100.0):
        """
        Args:
            resolution: 网格分辨率（米）
        """
        self.resolution = resolution

    def plot_quiver(self,
                   u: np.ndarray,
                   v: np.ndarray,
                   slice_index: int = -1,
                   skip: int = 3,
                   title: str = 'Wind Field',
                   figsize: Tuple[int, int] = (10, 8)) -> Figure:
        """
        绘制风场矢量图（箭头图）

        Args:
            u: U风分量 (x方向)
            v: V风分量 (y方向)
            slice_index: 切片索引
            skip: 跳过的网格点数
            title: 图表标题
            figsize: 图形大小

        Returns:
            matplotlib Figure对象
        """
        if u.shape != v.shape:
            raise ValueError("u和v形状不匹配")

        data_slice_u = u[:, :, slice_index]
        data_slice_v = v[:, :, slice_index]

        nx, ny = data_slice_u.shape
        x = np.arange(nx) * self.resolution
        y = np.arange(ny) * self.resolution

        # 下采样
        X, Y = np.meshgrid(x, y, indexing='ij')
        X_sub = X[::skip, ::skip]
        Y_sub = Y[::skip, ::skip]
        U_sub = data_slice_u[::skip, ::skip]
        V_sub = data_slice_v[::skip, ::skip]

        fig, ax = plt.subplots(figsize=figsize)
        q = ax.quiver(X_sub, Y_sub, U_sub, V_sub,
                     np.sqrt(U_sub**2 + V_sub**2),
                     cmap='coolwarm', scale=50, width=0.003)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_title(title)
        plt.colorbar(q, ax=ax, label='Wind Speed (m/s)')

        logger.info("绘制风场矢量图")
        return fig

    def plot_streamlines(self,
                        u: np.ndarray,
                        v: np.ndarray,
                        slice_index: int = -1,
                        density: float = 2.0,
                        title: str = 'Wind Streamlines',
                        figsize: Tuple[int, int] = (10, 8)) -> Figure:
        """
        绘制流线图

        Args:
            u: U风分量
            v: V风分量
            slice_index: 切片索引
            density: 流线密度
            title: 图表标题
            figsize: 图形大小

        Returns:
            matplotlib Figure对象
        """
        data_slice_u = u[:, :, slice_index]
        data_slice_v = v[:, :, slice_index]

        nx, ny = data_slice_u.shape
        x = np.arange(nx) * self.resolution
        y = np.arange(ny) * self.resolution

        fig, ax = plt.subplots(figsize=figsize)
        speed = np.sqrt(data_slice_u**2 + data_slice_v**2)
        strm = ax.streamplot(x, y, data_slice_u.T, data_slice_v.T,
                           color=speed.T, cmap='coolwarm', density=density)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_title(title)
        plt.colorbar(strm.lines, ax=ax, label='Wind Speed (m/s)')

        logger.info("绘制流线图")
        return fig

    def plot_wind_speed_contourf(self,
                                  u: np.ndarray,
                                  v: np.ndarray,
                                  slice_index: int = -1,
                                  levels: int = 20,
                                  title: str = 'Wind Speed Contour',
                                  figsize: Tuple[int, int] = (10, 8)) -> Figure:
        """
        绘制风速等值线填色图

        Args:
            u: U风分量
            v: V风分量
            slice_index: 切片索引
            levels: 等值线数量
            title: 图表标题
            figsize: 图形大小

        Returns:
            matplotlib Figure对象
        """
        data_slice_u = u[:, :, slice_index]
        data_slice_v = v[:, :, slice_index]

        wind_speed = np.sqrt(data_slice_u**2 + data_slice_v**2)

        nx, ny = wind_speed.shape
        x = np.arange(nx) * self.resolution
        y = np.arange(ny) * self.resolution

        fig, ax = plt.subplots(figsize=figsize)
        cs = ax.contourf(x, y, wind_speed, levels=levels, cmap='YlOrRd')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_title(title)
        plt.colorbar(cs, ax=ax, label='Wind Speed (m/s)')

        logger.info("绘制风速等值线填色图")
        return fig


class ComparisonPlotter:
    """
    对比绘图器
    用于对比背景场、分析场等
    """

    def __init__(self, resolution: float = 100.0):
        self.resolution = resolution

    def plot_horizontal_comparison(self,
                                  background: np.ndarray,
                                  analysis: np.ndarray,
                                  observations: Optional[np.ndarray] = None,
                                  obs_locations: Optional[np.ndarray] = None,
                                  slice_index: int = -1,
                                  title: Optional[str] = None,
                                  figsize: Tuple[int, int] = (16, 5)) -> Figure:
        """
        水平对比图：背景场 vs 分析场

        Args:
            background: 背景场
            analysis: 分析场
            observations: 观测数据（可选）
            obs_locations: 观测位置（可选）
            slice_index: 切片索引
            title: 图表标题
            figsize: 图形大小

        Returns:
            matplotlib Figure对象
        """
        bg_slice = background[:, :, slice_index]
        analysis_slice = analysis[:, :, slice_index]

        nx, ny = bg_slice.shape
        x = np.arange(nx) * self.resolution  # noqa: F841
        y = np.arange(ny) * self.resolution  # noqa: F841

        vmin = min(np.nanmin(bg_slice), np.nanmin(analysis_slice))
        vmax = max(np.nanmax(bg_slice), np.nanmax(analysis_slice))

        fig, axes = plt.subplots(1, 3, figsize=figsize)

        # 背景场
        im1 = axes[0].imshow(bg_slice.T, origin='lower', cmap='RdBu_r',
                            vmin=vmin, vmax=vmax, extent=[0, nx*self.resolution, 0, ny*self.resolution])
        axes[0].set_xlabel('X (m)')
        axes[0].set_ylabel('Y (m)')
        axes[0].set_title('Background Field')
        plt.colorbar(im1, ax=axes[0])

        # 分析场
        im2 = axes[1].imshow(analysis_slice.T, origin='lower', cmap='RdBu_r',
                            vmin=vmin, vmax=vmax, extent=[0, nx*self.resolution, 0, ny*self.resolution])
        axes[1].set_xlabel('X (m)')
        axes[1].set_ylabel('Y (m)')
        axes[1].set_title('Analysis Field')
        plt.colorbar(im2, ax=axes[1])

        # 增量
        increment = analysis_slice - bg_slice
        im3 = axes[2].imshow(increment.T, origin='lower', cmap='RdBu_r',
                            extent=[0, nx*self.resolution, 0, ny*self.resolution])
        axes[2].set_xlabel('X (m)')
        axes[2].set_ylabel('Y (m)')
        axes[2].set_title('Increment (Analysis - Background)')
        plt.colorbar(im3, ax=axes[2])

        if title:
            fig.suptitle(title)

        logger.info("绘制水平对比图")
        return fig

    def plot_profile_comparison(self,
                               background: np.ndarray,
                               analysis: np.ndarray,
                               point: Tuple[int, int],
                               title: str = 'Vertical Profile Comparison',
                               figsize: Tuple[int, int] = (10, 6)) -> Figure:
        """
        绘制垂直廊线对比图

        Args:
            background: 背景场
            analysis: 分析场
            point: (x, y) 位置索引
            title: 图表标题
            figsize: 图形大小

        Returns:
            matplotlib Figure对象
        """
        ix, iy = point
        bg_profile = background[ix, iy, :]
        analysis_profile = analysis[ix, iy, :]

        nz = len(bg_profile)
        z = np.arange(nz) * self.resolution

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(bg_profile, z, 'b-o', label='Background', linewidth=2, markersize=4)
        ax.plot(analysis_profile, z, 'r-s', label='Analysis', linewidth=2, markersize=4)
        ax.set_xlabel('Value')
        ax.set_ylabel('Height (m)')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        logger.info(f"绘制垂直廊线对比图 at point {point}")
        return fig


def save_figure(fig: Figure, filepath: str, dpi: int = 300, bbox_inches: str = 'tight'):
    """
    保存图像到文件

    Args:
        fig: matplotlib Figure对象
        filepath: 保存路径
        dpi: 分辨率
        bbox_inches: 边框裁剪模式
    """
    fig.savefig(filepath, dpi=dpi, bbox_inches=bbox_inches)
    logger.info(f"图像已保存到: {filepath}")
    plt.close(fig)


def close_all():
    """关闭所有matplotlib窗口"""
    plt.close('all')
