"""
贝叶斯同化系统版本信息
"""

__version__ = "1.0.0"
__author__ = "Bayesian Assimilation Team"
__email__ = "H13396600636@163.COM"
__license__ = "Apache 2.0"

VERSION = __version__

def get_version():
    """获取版本信息"""
    return __version__

def get_version_info():
    """获取完整的版本信息"""
    return {
        'version': __version__,
        'author': __author__,
        'email': __email__,
        'license': __license__
    }
