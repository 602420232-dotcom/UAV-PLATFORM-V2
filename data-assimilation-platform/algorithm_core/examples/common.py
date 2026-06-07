"""
Common utilities shared across data assimilation examples.

Consolidates duplicated functions found across multiple example scripts
to reduce code duplication and prevent naming conflicts.
"""

import numpy as np
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def create_synthetic_data(domain_size: Tuple[int, int, int], resolution: float, n_obs: int = 50):
    """
    Create synthetic 3D meteorological data for demonstration.

    Args:
        domain_size: (nx, ny, nz) grid dimensions.
        resolution: Grid spacing.
        n_obs: Number of synthetic observation points.

    Returns:
        Tuple of (background_field, observations, observation_locations).
    """
    nx = int(domain_size[0] / resolution) + 1
    ny = int(domain_size[1] / resolution) + 1
    nz = int(domain_size[2] / resolution) + 1

    x, y, z = np.meshgrid(
        np.linspace(0, domain_size[0], nx),
        np.linspace(0, domain_size[1], ny),
        np.linspace(0, domain_size[2], nz),
        indexing='ij',
    )

    background = np.sin(2 * np.pi * x / domain_size[0]) * \
                 np.cos(2 * np.pi * y / domain_size[1]) * \
                 np.exp(-z / domain_size[2] * 2) + 1.5

    np.random.seed(42)
    obs_locations = np.random.rand(n_obs, 3) * np.array(domain_size)
    true_values = np.sin(2 * np.pi * obs_locations[:, 0] / domain_size[0]) * \
                  np.cos(2 * np.pi * obs_locations[:, 1] / domain_size[1]) * \
                  np.exp(-obs_locations[:, 2] / domain_size[2] * 2) + 1.5
    observations = true_values + np.random.randn(n_obs) * 0.1

    return background, observations, obs_locations


def check_cuda_available() -> bool:
    """
    Check if CUDA is available for GPU acceleration.

    Returns:
        True if CUDA is available, False otherwise.
    """
    try:
        from bayesian_assimilation.accelerators import CUDAAccelerator
        cuda_acc = CUDAAccelerator()
        if cuda_acc.initialize():
            logger.info("CUDA available")
            return True
        logger.info("CUDA not available")
        return False
    except ImportError:
        logger.info("CUDA libraries not installed")
        return False


def check_jax_available() -> bool:
    """
    Check if JAX is available for GPU acceleration.

    Returns:
        True if JAX is available, False otherwise.
    """
    try:
        import jax  # noqa: F401
        logger.info("JAX available")
        return True
    except ImportError:
        logger.info("JAX not installed")
        return False
