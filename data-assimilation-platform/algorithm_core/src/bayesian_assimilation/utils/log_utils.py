import logging
from typing import Optional

logger = logging.getLogger(__name__)


def setup_logging(level: int = logging.INFO,
                  format_str: Optional[str] = None,
                  log_file: Optional[str] = None) -> logging.Logger:
    if format_str is None:
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers.clear()
    formatter = logging.Formatter(format_str)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


def get_logger(name: Optional[str] = None, level: Optional[int] = None) -> logging.Logger:
    logger_instance = logging.getLogger(name)
    if level is not None:
        logger_instance.setLevel(level)
    return logger_instance


def log_function_call(func=None, *, logger=None):
    """装饰器：记录函数调用日志。可作为无参装饰器 @log_function_call 或带参数 @log_function_call(logger=...) 使用。"""
    import functools

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            _logger = logger if logger is not None else logging.getLogger(f.__module__)
            _logger.debug(f"调用函数: {f.__name__}, args={args}, kwargs={kwargs}")
            try:
                result = f(*args, **kwargs)
                _logger.debug(f"函数返回: {f.__name__} -> {result}")
                return result
            except Exception as e:
                _logger.error(f"函数异常: {f.__name__} -> {e}", exc_info=True)
                raise
        return wrapper

    # 无参调用：@log_function_call 直接装饰函数
    if func is not None:
        return decorator(func)
    return decorator
