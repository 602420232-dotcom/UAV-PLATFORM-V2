#!/usr/bin/env python3
"""
批量修复Python文件中的print()语句为logging
将 print(json.dumps(...)) 替换为 logger.info(...)
并自动添加logging导入和logger定义
"""

import os
import re
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 需要处理的目录
TARGET_DIRS = [
    "data-assimilation-platform/algorithm_core",
    "data-assimilation-service/src/main/python",
    "path-planning-service/src/main/python",
    "meteor-forecast-service/src/main/python",
    "wrf-processor-service/src/main/python",
    "edge-cloud-coordinator",
    "uav-edge-sdk/edge_sdk",
    "tests",
]

def fix_file(filepath):
    """修复单个文件中的print()语句"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # 1. 替换 print(json.dumps(...)) 为 logger.info(...)
        # 匹配: print(json.dumps(...))
        pattern1 = r'print\(json\.dumps\((.*?)\)\)'
        replacement1 = r'logger.info(json.dumps(\1))'
        new_content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
        if new_content != content:
            content = new_content
            modified = True
        
        # 2. 替换简单的 print(...) 为 logger.info(...)
        # 匹配: logger.info("...") 或 logger.info('')
        pattern2 = r'print\(([\'"].*?[\'"])\)'
        replacement2 = r'logger.info(\1)'
        new_content = re.sub(pattern2, replacement2, content)
        if new_content != content:
            content = new_content
            modified = True
        
        # 3. 检查文件是否有 logging 导入
        if 'import logging' not in content and 'from logging import' not in content:            # 在文件开头添加 logging 导入
            lines = content.split('\n')
            # 找到第一个 import 语句的位置
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_pos = i
                    break
            lines.insert(insert_pos, 'import logging')
            lines.insert(insert_pos + 1, "logger = logging.getLogger(__name__)")
            lines.insert(insert_pos + 2, '')
            content = '\n'.join(lines)
            modified = True
        elif 'logger = logging.getLogger(__name__)' not in content:
            # 在 import logging 后添加 logger 定义
            content = content.replace(
                'import logging',
                'import logging\nlogger = logging.getLogger(__name__)'
            )
            modified = True
        
        # 只有当内容发生变化时才写入
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "已修复"
        else:
            return False, "无需修复"
            
    except Exception as e:
        return False, f"错误: {str(e)}"

def main():
    """主函数"""
    fixed_count = 0
    error_count = 0
    skipped_count = 0
    
    print("=" * 60)
    logger.info("批量修复 print() 语句为 logging")
    print("=" * 60)
    
    for target_dir in TARGET_DIRS:
        dir_path = PROJECT_ROOT / target_dir
        if not dir_path.exists():
            logger.info(f"跳过不存在的目录: {target_dir}")
            skipped_count += 1
            continue
        
        logger.info(f"\n扫描目录: {target_dir}")
        print("-" * 60)
        
        # 递归查找所有 .py 文件
        for py_file in dir_path.rglob("*.py"):
            try:
                modified, message = fix_file(py_file)
                if modified:
                    logger.info(f"✅ {py_file.relative_to(PROJECT_ROOT)} - {message}")
                    fixed_count += 1
                else:
                    if "错误" in message:
                        logger.info(f"❌ {py_file.relative_to(PROJECT_ROOT)} - {message}")
                        error_count += 1
                    else:
                        pass  # 无需修复，不输出
            except Exception as e:
                logger.info(f"❌ {py_file.relative_to(PROJECT_ROOT)} - 处理失败: {e}")
                error_count += 1
    
    print("\n" + "=" * 60)
    logger.info(f"修复完成！")
    logger.info(f"✅ 已修复: {fixed_count} 个文件")
    logger.info(f"❌ 错误: {error_count} 个文件")
    logger.info(f"⏭️ 跳过: {skipped_count} 个目录")
    print("=" * 60)

if __name__ == "__main__":
    main()

