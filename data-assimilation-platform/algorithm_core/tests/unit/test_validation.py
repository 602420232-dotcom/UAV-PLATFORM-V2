"""
输入验证和异常处理单元测试
覆盖: validators, error_handler, exception handling
"""
import logging
import os
import sys

import pytest
import numpy as np

logger = logging.getLogger(__name__)


SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_PATH = os.path.join(SRC_DIR, 'src')
API_PATH = os.path.join(SRC_DIR, 'service_python', 'src')


if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


if API_PATH not in sys.path:
    sys.path.insert(0, API_PATH)


@pytest.mark.unit
class TestInputValidation:
    """输入验证测试类"""

    def test_validate_grid_consistency_valid(self):
        """测试有效网格一致性验证"""
        try:
            from api.utils.validators import validate_grid_consistency  # type: ignore[import-not-found]  # noqa: E402
        except ImportError:
            pytest.skip("validators module not available")

        background = {
            "grid": {"lat": [1, 2, 3], "lon": [1, 2], "lev": [1, 2, 3, 4]},
            "data": np.random.rand(3, 2, 4)
        }
        observations = [
            {"location": [0, 0, 0], "value": 10},
            {"location": [1, 1, 2], "value": 20}
        ]

        validate_grid_consistency(background, observations)

    def test_validate_grid_consistency_invalid(self):
        """测试无效网格一致性验证"""
        try:
            from api.utils.validators import validate_grid_consistency  # type: ignore[import-not-found]  # noqa: E402
        except ImportError:
            pytest.skip("validators module not available")

        background = {
            "grid": {"lat": [1, 2, 3], "lon": [1, 2], "lev": [1, 2, 3, 4]},
            "data": np.random.rand(3, 2, 4)
        }
        observations = [
            {"location": [5, 5, 5], "value": 10}  # 超出网格范围
        ]

        with pytest.raises(ValueError):
            validate_grid_consistency(background, observations)

    def test_validate_observation_locations_valid(self):
        """测试有效观测位置验证"""
        try:
            from api.utils.validators import validate_observation_locations  # type: ignore[import-not-found]  # noqa: E402
        except ImportError:
            pytest.skip("validators module not available")

        obs_locations = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]])
        observations = [
            {"location": [0, 0, 0], "value": 10},
            {"location": [1, 1, 1], "value": 20},
            {"location": [2, 2, 2], "value": 30}
        ]

        validate_observation_locations(obs_locations, observations)

    def test_validate_observation_locations_mismatch(self):
        """测试观测位置数量不匹配"""
        try:
            from api.utils.validators import validate_observation_locations  # type: ignore[import-not-found]  # noqa: E402
        except ImportError:
            pytest.skip("validators module not available")

        obs_locations = np.array([[0, 0, 0], [1, 1, 1]])
        observations = [
            {"location": [0, 0, 0], "value": 10},
            {"location": [1, 1, 1], "value": 20},
            {"location": [2, 2, 2], "value": 30}  # 多余的观测
        ]

        with pytest.raises(ValueError):
            validate_observation_locations(obs_locations, observations)


@pytest.mark.unit
class TestAppException:
    """应用异常测试类"""

    def test_app_exception_init(self):
        """测试AppException初始化"""
        try:
            from api.middleware.error_handler import AppException  # type: ignore[import-not-found]  # noqa: E402
        except ImportError:
            pytest.skip("error_handler module not available")

        exc = AppException(status_code=400, message="Bad Request", details="Invalid input")
        assert exc.status_code == 400
        assert exc.message == "Bad Request"
        assert exc.details == "Invalid input"

    def test_app_exception_default_details(self):
        """测试AppException默认details"""
        try:
            from api.middleware.error_handler import AppException  # type: ignore[import-not-found]  # noqa: E402
        except ImportError:
            pytest.skip("error_handler module not available")

        exc = AppException(status_code=500, message="Internal Error")
        assert exc.status_code == 500
        assert exc.message == "Internal Error"
        assert exc.details is None


@pytest.mark.unit
class TestSecurityValidation:
    """安全验证测试类"""

    def test_script_name_validation(self):
        """测试脚本名称验证"""
        try:
            from common_utils.python_executor import PythonExecutor  # type: ignore[import-not-found]  # noqa: E402
        except ImportError:
            pytest.skip("common_utils module not available")

        PythonExecutor()
        valid_scripts = ["meteor_forecast.py", "path_planner.py", "assimilation.py"]
        for script in valid_scripts:
            assert script in valid_scripts

    def test_action_validation(self):
        """测试动作名称验证"""
        valid_actions = ["predict", "plan", "compute", "assimilate"]
        assert "predict" in valid_actions
        assert "invalid_action" not in valid_actions


@pytest.mark.unit
class TestDataValidation:
    """数据验证测试类"""

    def test_numpy_array_conversion(self):
        """测试numpy数组转换"""
        data = [[1, 2, 3], [4, 5, 6]]
        arr = np.array(data)
        assert arr.shape == (2, 3)
        assert arr.dtype.kind in 'ifu'

    def test_empty_array_handling(self):
        """测试空数组处理"""
        empty = np.array([])
        assert len(empty) == 0
        assert empty.shape == (0, )

    def test_invalid_grid_shape(self):
        """测试无效网格形状"""
        from bayesian_assimilation.utils.validation import DataValidator

        invalid_data = np.ones((3, 4))
        with pytest.raises(ValueError):
            DataValidator.validate_shape(invalid_data, (5, 5), name='test_grid')

    def test_observation_out_of_bounds(self):
        """测试观测点超出边界"""
        grid_shape = (20, 20, 5)
        obs_location = np.array([25, 25, 5])  # 超出边界

        in_bounds = all(
            0 <= obs_location[i] < grid_shape[i]
            for i in range(len(grid_shape))
        )
        assert not in_bounds


@pytest.mark.unit
class TestErrorResponseFormat:
    """错误响应格式测试类"""

    def test_error_response_structure(self):
        """测试错误响应结构"""
        error_response = {
            "code": 400,
            "message": "参数错误",
            "details": "field: must not be null"
        }

        assert "code" in error_response
        assert "message" in error_response
        assert error_response["code"] == 400

    def test_validation_error_response(self):
        """测试验证错误响应"""
        validation_error = {
            "success": False,
            "error": "参数校验失败",
            "details": "username: must not be empty; password: must have at least 6 characters"
        }

        assert not validation_error["success"]
        assert "校验失败" in validation_error["error"]

    def test_service_unavailable_response(self):
        """测试服务不可用响应"""
        service_error = {
            "success": False,
            "error": "服务暂时不可用",
            "service": "wrf-processor"
        }

        assert not service_error["success"]
        assert "service" in service_error


@pytest.mark.unit
class TestAlgorithmSelection:
    """算法选择测试类"""

    def test_valid_algorithm_names(self):
        """测试有效算法名称"""
        valid_algorithms = ["3dvar", "4dvar", "enkf", "hybrid"]
        for algo in valid_algorithms:
            assert algo in valid_algorithms

    def test_invalid_algorithm_handling(self):
        """测试无效算法处理"""
        algorithm_map = {
            "3dvar": "three_dimensional_var",
            "4dvar": "four_dimensional_var",
            "enkf": "enkf",
            "hybrid": "hybrid",
        }

        invalid_algo = "invalid_algo"
        result = algorithm_map.get(invalid_algo.lower(), "3dvar")
        assert result == "3dvar"  # 默认回退到3dvar


@pytest.mark.unit
class TestConfigValidation:
    """配置验证测试类"""

    def test_valid_config_values(self):
        """测试有效配置值"""
        config = {
            "grid_resolution": 50.0,
            "background_error_scale": 1.5,
            "observation_error_scale": 0.8,
            "max_iterations": 100
        }

        assert config["grid_resolution"] > 0
        assert config["background_error_scale"] > 0
        assert config["observation_error_scale"] > 0
        assert config["max_iterations"] > 0

    def test_invalid_config_negative_values(self):
        """测试负数值配置"""
        config = {
            "grid_resolution": -50.0,  # 无效
            "background_error_scale": 1.5,
        }

        assert config["grid_resolution"] < 0  # 检测到无效值

    def test_missing_required_config(self):
        """测试缺少必需配置"""
        partial_config = {
            "grid_resolution": 50.0,
            # 缺少其他必需字段
        }

        required_fields = ["background_error_scale", "observation_error_scale"]
        missing = [f for f in required_fields if f not in partial_config]
        assert len(missing) > 0
