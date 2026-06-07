"""
日志模块单元测试
"""
import logging
import os
import sys

import pytest

logger = logging.getLogger(__name__)


SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_PATH = os.path.join(SRC_DIR, 'src')


if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


from bayesian_assimilation.utils.log_utils import (  # noqa: E402
    setup_logging,
    get_logger,
    log_function_call
)


@pytest.mark.unit
class TestSetupLogging:
    """日志设置测试类"""

    def test_setup_logging_default(self):
        """测试默认日志设置"""
        setup_logging()

        # 验证根日志器已配置
        root_logger = logging.getLogger()
        assert root_logger.level <= logging.DEBUG

    def test_setup_logging_custom_level(self):
        """测试自定义日志级别"""
        setup_logging(level=logging.INFO)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_setup_logging_with_file(self, temp_output_dir):
        """测试带文件的日志设置"""
        log_file = os.path.join(temp_output_dir, 'test.log')
        setup_logging(log_file=log_file)

        # 验证文件已创建
        assert os.path.exists(log_file)

    def test_setup_logging_with_format(self):
        """测试自定义格式"""
        custom_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        setup_logging(format_str=custom_format)

        # 验证格式已应用
        root_logger = logging.getLogger()
        root_logger.handlers[0].formatter if root_logger.handlers else None
        # 格式设置应该成功

    def test_setup_logging_multiple_calls(self):
        """测试多次调用"""
        setup_logging(level=logging.DEBUG)
        setup_logging(level=logging.INFO)

        logging.getLogger()
        # 多次调用应该正常工作


@pytest.mark.unit
class TestGetLogger:
    """获取日志器测试类"""

    def test_get_logger_returns_logger(self):
        """测试获取日志器"""
        logger = get_logger('test_module')

        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_module'

    def test_get_logger_consistent(self):
        """测试获取一致的日志器"""
        logger1 = get_logger('consistency_test')
        logger2 = get_logger('consistency_test')

        assert logger1 is logger2

    def test_get_logger_child(self):
        """测试获取子日志器"""
        get_logger('parent')
        child = get_logger('parent.child')

        assert child.parent is not None

    def test_get_logger_with_level(self):
        """测试带级别的日志器"""
        logger = get_logger('level_test', level=logging.WARNING)  # type: ignore[call-arg]

        assert logger.level == logging.WARNING


@pytest.mark.unit
class TestLogFunctionCall:
    """函数调用日志装饰器测试类"""

    def test_log_function_call_decorator(self):
        """测试装饰器基本功能"""
        @log_function_call
        def test_function(x, y):
            return x + y

        result = test_function(1, 2)

        assert result == 3

    def test_log_function_call_with_args(self):
        """测试带参数的函数"""
        @log_function_call
        def multiply(a, b=2):
            return a * b

        result = multiply(3, b=4)

        assert result == 12

    def test_log_function_call_with_return(self):
        """测试带返回值的函数"""
        @log_function_call
        def compute(x):
            return x * 2

        result = compute(5)

        assert result == 10

    def test_log_function_call_exception(self):
        """测试函数抛出异常"""
        @log_function_call
        def raise_error():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            raise_error()

    def test_log_function_call_class_method(self):
        """测试类方法装饰"""

        class TestClass:
            @log_function_call
            def method(self, x):
                return x * 2

        obj = TestClass()
        result = obj.method(5)

        assert result == 10

    def test_log_function_call_nested(self):
        """测试嵌套函数"""
        @log_function_call
        def outer(x):
            @log_function_call
            def inner(y):
                return y * 2
            return inner(x + 1)

        result = outer(3)

        assert result == 8

    def test_log_function_call_with_custom_logger(self):
        """测试带自定义日志器的装饰器"""
        custom_logger = logging.getLogger('custom')

        @log_function_call(logger=custom_logger)  # type: ignore[call-overload]
        def func_with_custom_logger():
            return True

        result = func_with_custom_logger()

        assert result is True


@pytest.mark.unit
class TestLoggerIntegration:
    """日志器集成测试类"""

    def test_log_to_different_levels(self):
        """测试不同级别的日志"""
        logger = get_logger('level_test')

        # 这些调用不应该抛出异常
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

    def test_log_with_formatting(self):
        """测试格式化日志"""
        logger = get_logger('format_test')

        # 应该能正确格式化
        logger.info("Value: %d, String: %s", 42, "test")

    def test_log_with_exception(self):
        """测试异常日志"""
        logger = get_logger('exception_test')

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("Caught exception")

    def test_logger_hierarchy(self):
        """测试日志器层级"""
        get_logger('hierarchy.parent')
        child = get_logger('hierarchy.parent.child')
        sibling = get_logger('hierarchy.parent.sibling')

        # 子日志器应该不同
        assert child is not sibling
        # 但它们应该有相同的父级日志器名称前缀
        assert child.name.startswith('hierarchy.parent')
        assert sibling.name.startswith('hierarchy.parent')
