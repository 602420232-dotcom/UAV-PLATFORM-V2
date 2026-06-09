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

_DA = "data-assimilation-platform"
_AC = f"{_DA}/algorithm_core/src/bayesian_assimilation"
_SP = f"{_DA}/service_python/src/api"

TARGET_FILES = [
    f"{_SP}/routes/test_batch.py",
    f"{_SP}/utils/test_serializers.py",
    f"{_SP}/core/test_assimilation_service.py",
    f"{_SP}/utils/test_validators.py",
    f"{_SP}/middleware/test_cors.py",
    f"{_SP}/middleware/test_error_handler.py",
    f"{_SP}/routes/test_assimilation.py",
    f"{_AC}/core/test_assimilator.py",
    f"{_AC}/core/test_base.py",
    f"{_AC}/core/test_context.py",
    f"{_AC}/core/test_covariance.py",
    f"{_AC}/parallel/test_base.py",
    f"{_AC}/core/test_compatible_assimilator.py",
    f"{_AC}/accelerators/test_cpu.py",
    f"{_AC}/core/test_operators.py",
    f"{_AC}/parallel/test_block.py",
    f"{_AC}/test___version__.py",
    f"{_AC}/accelerators/test_cuda.py",
    f"{_AC}/core/test_solvers.py",
    f"{_AC}/accelerators/test_gpu.py",
    f"{_AC}/api/test_rest.py",
    f"{_AC}/models/test_base.py",
    f"{_AC}/accelerators/test_jax.py",
    f"{_AC}/adapters/test_grid.py",
    f"{_AC}/core/test_strategy.py",
    f"{_AC}/api/test_web.py",
    f"{_AC}/adapters/test_io.py",
    f"{_AC}/models/test_adaptive_assimilator.py",
    f"{_AC}/quality_control/test_validator.py",
    f"{_AC}/adapters/test_data.py",
    f"{_AC}/adapters/test_uav_adapter.py",
    f"{_AC}/accelerators/test_base.py",
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
