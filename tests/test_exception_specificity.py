"""
异常处理精度验证测试

验证 meteor_forecast.py、bayesian_assimilation.py、three_layer_planner.py
中的 except Exception 已被替换为具体的异常类型组合。
"""

import ast
import logging
import os
import unittest

logger = logging.getLogger(__name__)


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestExceptionSpecificity(unittest.TestCase):

    def _get_except_handlers(self, filepath):
        """解析文件，返回所有 except 子句捕获的异常类型"""
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                exc_type = node.type
                if exc_type is None:
                    results.append(("bare_except", node.lineno))
                elif isinstance(exc_type, ast.Name):
                    results.append((exc_type.id, node.lineno))
                elif isinstance(exc_type, ast.Tuple):
                    names = []
                    for elt in exc_type.elts:
                        if isinstance(elt, ast.Name):
                            names.append(elt.id)
                    results.append((tuple(names), node.lineno))
        return results

    def test_bayesian_assimilation_no_bare_exception(self):
        filepath = os.path.join(
            PROJECT_ROOT,
            "data-assimilation-service/src/main/python/bayesian_assimilation.py",
        )
        handlers = self._get_except_handlers(filepath)
        bare = [h for h in handlers if h[0] == "bare_except"]
        self.assertEqual(len(bare), 0, f"禁止裸 except: 行号 {[h[1] for h in bare]}")

    def test_meteor_forecast_no_bare_exception(self):
        filepath = os.path.join(
            PROJECT_ROOT,
            "meteor-forecast-service/src/main/python/meteor_forecast.py",
        )
        handlers = self._get_except_handlers(filepath)
        bare = [h for h in handlers if h[0] == "bare_except"]
        self.assertEqual(len(bare), 0, f"禁止裸 except: 行号 {[h[1] for h in bare]}")

    def test_three_layer_planner_no_bare_exception(self):
        filepath = os.path.join(
            PROJECT_ROOT,
            "path-planning-service/src/main/python/three_layer_planner.py",
        )
        handlers = self._get_except_handlers(filepath)
        bare = [h for h in handlers if h[0] == "bare_except"]
        self.assertEqual(len(bare), 0, f"禁止裸 except: 行号 {[h[1] for h in bare]}")

    def test_exception_replaced_with_tuples(self):
        """验证 except Exception 已被替换为 except (SpecificType1, SpecificType2, ...)"""
        files = [
            "data-assimilation-service/src/main/python/bayesian_assimilation.py",
            "meteor-forecast-service/src/main/python/meteor_forecast.py",
            "path-planning-service/src/main/python/three_layer_planner.py",
        ]
        for relpath in files:
            filepath = os.path.join(PROJECT_ROOT, relpath)
            handlers = self._get_except_handlers(filepath)
            single_exception = [h for h in handlers if h[0] == "Exception"]
            self.assertEqual(
                len(single_exception), 0,
                f"{os.path.basename(filepath)}: except Exception 未替换，行号 {[h[1] for h in single_exception]}"
            )

    def test_specific_exceptions_include_common_types(self):
        files = [
            "data-assimilation-service/src/main/python/bayesian_assimilation.py",
            "meteor-forecast-service/src/main/python/meteor_forecast.py",
            "path-planning-service/src/main/python/three_layer_planner.py",
        ]
        for relpath in files:
            filepath = os.path.join(PROJECT_ROOT, relpath)
            handlers = self._get_except_handlers(filepath)
            tuple_handlers = [h for h in handlers if isinstance(h[0], tuple)]
            self.assertGreater(
                len(tuple_handlers), 0,
                f"{os.path.basename(filepath)}: 应至少包含 1 个 except (...) 多元组"
            )

    def test_all_files_syntax_valid(self):
        files = [
            "data-assimilation-service/src/main/python/bayesian_assimilation.py",
            "meteor-forecast-service/src/main/python/meteor_forecast.py",
            "path-planning-service/src/main/python/three_layer_planner.py",
        ]
        for relpath in files:
            filepath = os.path.join(PROJECT_ROOT, relpath)
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            try:
                ast.parse(source)
            except SyntaxError as e:
                self.fail(f"{os.path.basename(filepath)} 语法错误: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
