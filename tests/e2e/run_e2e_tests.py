"""
E2E测试运行脚本
"""

import logging
import subprocess
import sys
import os

logger = logging.getLogger(__name__)


def run_e2e_tests():
    """运行E2E测试"""
    # 设置环境变量
    os.environ['TEST_ENV'] = 'e2e'
    os.environ['API_BASE_URL'] = os.getenv('API_BASE_URL', 'http://localhost:8088')

    # 运行pytest
    result = subprocess.run(
        [
            sys.executable, '-m', 'pytest',
            'tests/e2e/',
            '-v',
            '--tb=short',
            '--markers=e2e',
            '-m', 'e2e',
            '--html=reports/e2e_report.html',
            '--self-contained-html'
        ],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    return result.returncode


if __name__ == '__main__':
    exit_code = run_e2e_tests()
    sys.exit(exit_code)
