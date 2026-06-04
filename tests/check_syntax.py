
#!/usr/bin/env python
"""
检查所有Python文件的语法错误
"""
import ast
import glob
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_python_file(filepath):
    """检查单个Python文件的语法"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source, filename=filepath)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} (line {e.lineno}, col {e.offset})"
    except Exception as e:
        return False, str(e)

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    python_files = glob.glob(os.path.join(project_root, '**', '*.py'), recursive=True)
    
    errors = []
    
    logger.info(f"Checking {len(python_files)} Python files...")
    
    for filepath in python_files:
        # 跳过一些目录
        if any(skip in filepath for skip in ['__pycache__', '.venv', 'venv', 'node_modules', '.git', 'build', 'dist']):
            continue
            
        valid, error = check_python_file(filepath)
        if not valid:
            errors.append((filepath, error))
            logger.info(f"ERROR {filepath}: {error}")
    
    logger.info(f"\nCheck complete! Found {len(errors)} errors.")
    
    return 0 if len(errors) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

