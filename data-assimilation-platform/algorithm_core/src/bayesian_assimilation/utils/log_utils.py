import logging
from typing import Optional


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


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name)


def log_function_call(func):
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"调用函数: {func.__name__}, args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数返回: {func.__name__} -> {result}")
            return result
        except Exception as e:
            logger.error(f"函数异常: {func.__name__} -> {e}", exc_info=True)
            raise
    return wrapper
