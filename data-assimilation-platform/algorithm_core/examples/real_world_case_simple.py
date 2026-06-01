"""
Real-world case example — simplified alias.

This module is a simplified subset of real_world_case.py.
New code should use real_world_case.py directly.

Most classes and functions are re-exported from real_world_case.py
to maintain backward compatibility.
"""

import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import logging
import sys

src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

from real_world_case import (
    MeteorologicalQualityControl,
    MeteorologicalRiskAssessment,
    calculate_vertical_shear,
    enhanced_risk_assessment,
    check_netcdf_available,
    load_wrf_data_mock,
    process_observation_data,
    run_assimilation,
    generate_risk_heatmap,
    TimeSeriesAnalyzer,
    main,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    main()
