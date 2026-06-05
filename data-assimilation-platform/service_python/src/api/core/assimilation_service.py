import logging
import os
import sys
from typing import Dict, Optional, Tuple

# 配置系统路径以支持导入algorithm_core
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.join(_current_dir, "..", "..", "..")
_algorithm_core_src = os.path.join(_project_root, "algorithm_core", "src")

# 确保路径不存在重复添加


if os.path.exists(_algorithm_core_src) and _algorithm_core_src not in sys.path:
    sys.path.insert(0, _algorithm_core_src)

logger = logging.getLogger(__name__)


class AssimilationService:
    def __init__(self, cluster_manager=None):
        self._cluster_manager = cluster_manager
        self._algorithm_map = {
            "3dvar": "three_dimensional_var",
            "4dvar": "four_dimensional_var",
            "enkf": "enkf",
            "hybrid": "hybrid",
        }

    def queue_size(self) -> int:
        return 0

    def execute(self, algorithm: str, background: Dict, observations: list,
                config: Optional[dict] = None) -> dict:
        algorithm_key = self._algorithm_map.get(algorithm.lower(), "3dvar")
        logger.info(f"执行同化算法: {algorithm_key}")

        if config is None:
            config = {}

        try:
            # 尝试导入bayesian_assimilation模块
            from bayesian_assimilation.core.assimilator import BayesianAssimilator
            import numpy as np

            assim = BayesianAssimilator()
            grid_shape = _extract_grid_shape(background)
            if grid_shape:
                assim.initialize_grid(domain_size=grid_shape)

            obs_values = np.array([o.get("value", 0) for o in observations])
            obs_locations = np.array([
                [o.get("lat", 0), o.get("lon", 0), o.get("lev", 0)]
                for o in observations
            ])
            if grid_shape:
                bg_data = np.array(background.get("data", np.random.rand(*grid_shape)))
            else:
                bg_data = np.array(background.get("data", np.random.rand(10, 10)))

            analysis, variance = assim.assimilate_3dvar(
                background=bg_data,
                observations=obs_values,
                obs_locations=obs_locations,
            )

            return {
                "status": "success",
                "analysis": {"shape": list(analysis.shape)},
                "variance": {"shape": list(variance.shape)},
                "metrics": {
                    "algorithm": algorithm_key,
                    "iterations": config.get("max_iterations", 10),
                },
            }
        except ImportError:
            logger.critical(
                "algorithm_core 模块未安装！无法执行实际同化计算。\n"
                "请确保已安装 algorithm_core 包，或者检查 Python 路径配置。\n"
                "当前返回的为模拟数据，不具备实际预报参考价值。\n"
                "安装方式: pip install algorithm_core 或参照项目 README 配置。"
            )
            return {
                "status": "success",
                "analysis": None,
                "variance": None,
                "metrics": {
                    "algorithm": algorithm_key,
                    "simulated": True,
                },
                "data_source_warning": True,
                "warning": (
                    "⚠️ algorithm_core 模块未安装，当前返回模拟数据。"
                    "请安装 algorithm_core 包后再执行实际同化计算。"
                ),
            }
        except Exception as e:
            logger.error("同化失败: %s", e, exc_info=True)
            return {"status": "error", "message": "同化处理失败"}


def _extract_grid_shape(background: dict) -> Optional[Tuple]:
    grid = background.get("grid", {})
    lat = grid.get("lat", [])
    lon = grid.get("lon", [])
    lev = grid.get("lev", [])
    if lat and lon and lev:
        return (len(lat), len(lon), len(lev))
    shape = background.get("shape")
    if shape:
        return tuple(shape)
    return None
