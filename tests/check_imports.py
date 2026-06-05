#!/usr/bin/env python
"""
简单的导入和变量使用检查
"""
import ast
import glob
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImportChecker(ast.NodeVisitor):

    def __init__(self):
        self.imports = {}
        self.used_names = set()
        self.current_file = None

    def visit_Import(self, node):
        for name in node.names:
            alias = name.asname or name.name.split('.')[0]
            self.imports[alias] = (name.name, node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for name in node.names:
            alias = name.asname or name.name
            self.imports[alias] = (f"{node.module}.{name.name}" if node.module else name.name, node.lineno)
        self.generic_visit(node)

    def visit_Name(self, node):
        self.used_names.add(node.id)
        self.generic_visit(node)


def check_file(filepath):
    """检查单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except Exception as e:
        return [], str(e)

    checker = ImportChecker()
    checker.current_file = filepath
    checker.visit(tree)

    unused_imports = []
    for alias, (full_name, lineno) in checker.imports.items():
        if alias not in checker.used_names:
            unused_imports.append((lineno, full_name, alias))

    return unused_imports, None


def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    python_files = glob.glob(os.path.join(project_root, '**', '*.py'), recursive=True)

    all_unused = []

    logger.info("Checking for unused imports...")

    for filepath in python_files:
        if any(skip in filepath for skip in ['__pycache__', '.venv', 'venv', 'node_modules', '.git', 'build', 'dist']):
            continue

        unused, error = check_file(filepath)
        if error:
            logger.info(f"ERROR {filepath}: {error}")
        elif unused:
            for lineno, full_name, alias in unused:
                all_unused.append((filepath, lineno, full_name, alias))
                logger.info(f"{filepath}:{lineno}: Unused import: {alias}")

    logger.info(f"\nTotal unused imports found: {len(all_unused)}")

    return 0 if len(all_unused) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
