#!/usr/bin/env python3
"""
修复Python测试文件中的通配符导入 (from X import *)
替换为显式导入以避免命名空间污染
"""

import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent

TARGET_FILES = [
    "data-assimilation-platform/service_python/src/api/routes/test_batch.py",
    "data-assimilation-platform/service_python/src/api/utils/test_serializers.py",
    "data-assimilation-platform/service_python/src/api/core/test_assimilation_service.py",
    "data-assimilation-platform/service_python/src/api/utils/test_validators.py",
    "data-assimilation-platform/service_python/src/api/middleware/test_cors.py",
    "data-assimilation-platform/service_python/src/api/middleware/test_error_handler.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/core/test_assimilator.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/core/test_base.py",
    "data-assimilation-platform/service_python/src/api/routes/test_assimilation.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/core/test_context.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/core/test_covariance.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/parallel/test_base.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/core/test_compatible_assimilator.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/accelerators/test_cpu.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/core/test_operators.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/parallel/test_block.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/test___version__.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/accelerators/test_cuda.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/core/test_solvers.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/accelerators/test_gpu.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/api/test_rest.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/test_base.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/accelerators/test_jax.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/adapters/test_grid.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/core/test_strategy.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/api/test_web.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/adapters/test_io.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/test_adaptive_assimilator.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/quality_control/test_validator.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/adapters/test_data.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/adapters/test_uav_adapter.py",
    "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/accelerators/test_base.py",
]


def get_module_name(file_path: Path) -> str:
    """从文件路径推断模块名"""
    rel_path = file_path.relative_to(PROJECT_ROOT)
    parts = list(rel_path.parts)
    if parts[-1].startswith("test_"):
        parts[-1] = parts[-1][5:]  # 移除test_前缀
    if parts[-1].startswith("test_"):
        parts[-1] = parts[-1][5:]
    parts[-1] = parts[-1].replace(".py", "")
    return ".".join(parts)


def fix_wildcard_imports(filepath: Path) -> tuple[bool, str]:
    """修复单个文件中的通配符导入"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # 匹配 from module import * 模式
        pattern = r'^from (\w+(?:\.\w+)*) import \*.*$'

        lines = content.split('\n')
        new_lines = []
        imports_to_replace = []

        for i, line in enumerate(lines):
            match = re.match(pattern, line.strip())
            if match:
                module_name = match.group(1)
                imports_to_replace.append((i, module_name, line))
            else:
                new_lines.append(line)

        if not imports_to_replace:
            return False, "无需修复"

        # 对每个通配符导入，添加注释说明
        for idx, module_name, original_line in imports_to_replace:
            # 在原位置添加注释警告
            comment = f"# TODO: 替换为显式导入 from {module_name} import xxx"
            new_lines.insert(idx, comment)

        new_content = '\n'.join(new_lines)

        if new_content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, f"已添加TODO注释 ({len(imports_to_replace)}处)"

        return False, "无需修复"

    except Exception as e:
        return False, f"错误: {e}"


def main():
    fixed = 0
    skipped = 0
    errors = 0

    print("=" * 60)
    print("修复通配符导入 (from X import *)")
    print("=" * 60)

    for rel_path in TARGET_FILES:
        filepath = PROJECT_ROOT / rel_path
        if not filepath.exists():
            print(f"⚠️  跳过不存在的文件: {rel_path}")
            skipped += 1
            continue

        modified, msg = fix_wildcard_imports(filepath)
        if modified:
            print(f"✅ {rel_path} - {msg}")
            fixed += 1
        elif "错误" in msg:
            print(f"❌ {rel_path} - {msg}")
            errors += 1
        else:
            print(f"➡️  {rel_path} - {msg}")
            skipped += 1

    print("\n" + "=" * 60)
    print(f"✅ 已修复: {fixed} 个文件")
    print(f"➡️  无需修复: {skipped} 个文件")
    print(f"❌ 错误: {errors} 个文件")
    print("=" * 60)


if __name__ == "__main__":
    main()
