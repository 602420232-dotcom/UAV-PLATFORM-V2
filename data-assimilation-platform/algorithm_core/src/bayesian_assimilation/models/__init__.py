
# bayesian_assimilation/models/__init__.py

import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from bayesian_assimilation.core.base import AssimilationBase  # noqa: E402
from bayesian_assimilation.models.three_dimensional_var import ThreeDimensionalVAR  # noqa: E402
from bayesian_assimilation.models.four_dimensional_var import FourDimensionalVar, four_dimensional_var  # noqa: E402
from bayesian_assimilation.models.enkf import EnKF  # noqa: E402
from bayesian_assimilation.models.hybrid import HybridAssimilation, AdaptiveHybridAssimilation  # noqa: E402
from bayesian_assimilation.models.enhanced_bayesian import EnhancedBayesianAssimilation  # noqa: E402
from bayesian_assimilation.models.variance_field_optimizer import VarianceFieldOptimizer, AdaptiveVarianceField  # noqa: E402


__all__ = [
    "AssimilationBase",
    "ThreeDimensionalVAR",
    "FourDimensionalVar",
    "four_dimensional_var",
    "EnKF",
    "HybridAssimilation",
    "AdaptiveHybridAssimilation",
    "EnhancedBayesianAssimilation",
    "VarianceFieldOptimizer",
    "AdaptiveVarianceField"
]
