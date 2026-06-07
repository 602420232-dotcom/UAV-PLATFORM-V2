"""
错误处理框架单元测试
"""

import logging
import os
import sys
import unittest

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'common-utils', 'src', 'main', 'python'))

from errors import AppError, ErrorCode, Result, handle_errors  # type: ignore[import-not-found]  # noqa: E402


class TestErrorCode(unittest.TestCase):

    def test_code_property(self):
        self.assertEqual(ErrorCode.SUCCESS.code, 0)
        self.assertEqual(ErrorCode.TASK_NOT_FOUND.code, 2000)

    def test_message_property(self):
        self.assertEqual(ErrorCode.NOT_FOUND.message, "资源不存在")

    def test_from_code_existing(self):
        ec = ErrorCode.from_code(2000)
        self.assertEqual(ec, ErrorCode.TASK_NOT_FOUND)

    def test_from_code_missing(self):
        ec = ErrorCode.from_code(99999)
        self.assertEqual(ec, ErrorCode.UNKNOWN_ERROR)


class TestAppError(unittest.TestCase):

    def test_basic_error(self):
        e = AppError(ErrorCode.TASK_NOT_FOUND)
        self.assertEqual(e.error_code.code, 2000)
        self.assertEqual(str(e), "任务不存在")

    def test_custom_detail(self):
        e = AppError(ErrorCode.TASK_NOT_FOUND, detail="task_abc 未找到")
        self.assertIn("task_abc", str(e))

    def test_extra_info(self):
        e = AppError(ErrorCode.VALIDATION_ERROR, detail="缺少字段", field="name")
        self.assertEqual(e.extra["field"], "name")

    def test_to_dict(self):
        e = AppError(ErrorCode.TASK_NOT_FOUND, task_id="task_001")
        d = e.to_dict()
        self.assertEqual(d["code"], 2000)
        self.assertEqual(d["extra"]["task_id"], "task_001")


class TestResult(unittest.TestCase):

    def test_ok(self):
        r = Result.ok(data={"path": [(0, 0)]})
        self.assertTrue(r.success)
        self.assertEqual(r.data["path"], [(0, 0)])

    def test_fail(self):
        r = Result.fail(ErrorCode.PLANNING_FAILED, "无法找到路径")
        self.assertFalse(r.success)
        self.assertEqual(r.error_code, ErrorCode.PLANNING_FAILED)

    def test_from_app_exception(self):
        e = AppError(ErrorCode.START_COLLISION)
        r = Result.from_exception(e)
        self.assertFalse(r.success)
        self.assertEqual(r.error_code.code, 3003)

    def test_from_unknown_exception(self):
        e = ValueError("something wrong")
        r = Result.from_exception(e)
        self.assertFalse(r.success)
        self.assertEqual(r.error_code, ErrorCode.INTERNAL_ERROR)

    def test_to_dict(self):
        r = Result.ok(data={"x": 1})
        d = r.to_dict()
        self.assertTrue(d["success"])
        self.assertEqual(d["data"]["x"], 1)


class TestHandleErrors(unittest.TestCase):

    def test_normal_return(self):
        @handle_errors
        def good_func():
            return {"result": "ok"}

        result = good_func()
        self.assertEqual(result["result"], "ok")

    def test_app_error_caught(self):
        @handle_errors
        def bad_func():
            raise AppError(ErrorCode.VALIDATION_ERROR, "无效参数")

        result = bad_func()
        self.assertFalse(result["success"])
        self.assertEqual(result["code"], 1001)

    def test_unknown_error_caught(self):
        @handle_errors
        def crash_func():
            raise RuntimeError("崩了")

        result = crash_func()
        self.assertFalse(result["success"])
        self.assertEqual(result["code"], 1005)


if __name__ == '__main__':
    unittest.main()
