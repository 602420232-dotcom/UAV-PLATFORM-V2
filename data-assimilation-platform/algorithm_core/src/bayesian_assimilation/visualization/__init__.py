"""
可视化模块
提供数据可视化、动画生成和监控面板功能
"""

# 静态绘图模块


from .plots import (
    VarianceFieldPlotter,
    WindFieldPlotter,
    ComparisonPlotter,
    save_figure,
    close_all
)

# 动画生成模块


from .animator import (
    TimeSeriesAnimator,
    VarianceHeatmapAnimator,
    AssimilationCycleAnimator,
    save_animation,
    display_animation
)

# 监控面板模块


from .dashboards import (
    AssimilationDashboard,
    PerformanceDashboard,
    InteractiveDashboard,
    create_summary_dashboard
)


__all__ = [
    # 静态绘图
    'VarianceFieldPlotter',
    'WindFieldPlotter',
    'ComparisonPlotter',
    'save_figure',
    'close_all',

    # 动画生成
    'TimeSeriesAnimator',
    'VarianceHeatmapAnimator',
    'AssimilationCycleAnimator',
    'save_animation',
    'display_animation',

    # 监控面板
    'AssimilationDashboard',
    'PerformanceDashboard',
    'InteractiveDashboard',
    'create_summary_dashboard'
]
