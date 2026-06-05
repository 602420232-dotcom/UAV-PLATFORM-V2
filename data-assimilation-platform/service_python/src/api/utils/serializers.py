import numpy as np


def serialize_grid(grid_data: np.ndarray) -> dict:
    return {
        "shape": list(grid_data.shape),
        "dtype": str(grid_data.dtype),
        "min": float(grid_data.min()) if grid_data.size > 0 else 0,
        "max": float(grid_data.max()) if grid_data.size > 0 else 0,
        "mean": float(grid_data.mean()) if grid_data.size > 0 else 0,
    }


def serialize_analysis(analysis: np.ndarray, variance: np.ndarray = None) -> dict:
    result = {"analysis": serialize_grid(analysis)}
    if variance is not None:
        result["variance"] = serialize_grid(variance)
    return result
