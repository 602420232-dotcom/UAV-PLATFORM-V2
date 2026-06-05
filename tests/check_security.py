#!/usr/bin/env python
"""
安全漏洞扫描
"""
import ast
import glob
import os
import sys
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityChecker(ast.NodeVisitor):

    def __init__(self):
        self.findings = []
        self.current_file = None

    def check_file(self, filepath):
        self.current_file = filepath
        self.findings = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=filepath)
            self.visit(tree)

            # Check for hardcoded secrets
            self._check_hardcoded_secrets(source)

            # Check for unsafe functions
            self._check_unsafe_functions(source)

        except Exception as e:
            self.findings.append(('ERROR', 0, f"Parse error: {e}"))

        return self.findings

    def _check_hardcoded_secrets(self, source):
        # Look for common secret patterns
        secret_patterns = [
            (r'password\s*[:=]\s*["\']([^"\']{8,})["\']', 'Hardcoded password'),
            (r'secret\s*[:=]\s*["\']([^"\']{8,})["\']', 'Hardcoded secret'),
            (r'api[_-]?key\s*[:=]\s*["\']([^"\']{16,})["\']', 'Hardcoded API key'),
            (r'token\s*[:=]\s*["\']([^"\']{16,})["\']', 'Hardcoded token'),
        ]

        lines = source.split('\n')
        for lineno, line in enumerate(lines, 1):
            for pattern, message in secret_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                if matches:
                    self.findings.append(('HIGH', lineno, message))

    def _check_unsafe_functions(self, source):
        unsafe_funcs = ['eval', 'exec', 'compile', '__import__', 'pickle', 'subprocess']
        lines = source.split('\n')
        for lineno, line in enumerate(lines, 1):
            for func in unsafe_funcs:
                if re.search(r'\b' + re.escape(func) + r'\s*\(', line):
                    self.findings.append(('MEDIUM', lineno, f"Usage of potentially unsafe function: {func}"))

    def visit_Call(self, node):
        # Check for unsafe function calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in ['eval', 'exec', 'compile']:
                self.findings.append(('HIGH', node.lineno, f"Use of {func_name}() can be unsafe"))
            elif func_name in ['pickle.load', 'pickle.loads']:
                self.findings.append(('HIGH', node.lineno, "Use of unpickling functions is unsafe"))
        self.generic_visit(node)

    def visit_With(self, node):
        # Check for unsafe context managers
        for item in node.items:
            if isinstance(item.context_expr, ast.Call) and isinstance(item.context_expr.func, ast.Name):
                if item.context_expr.func.id == 'open':
                    pass  # This is OK
        self.generic_visit(node)


def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    python_files = glob.glob(os.path.join(project_root, '**', '*.py'), recursive=True)

    all_findings = []

    logger.info("Scanning for security issues...")

    for filepath in python_files:
        if any(skip in filepath for skip in ['__pycache__', '.venv', 'venv', 'node_modules', '.git', 'build', 'dist']):
            continue

        checker = SecurityChecker()
        findings = checker.check_file(filepath)

        if findings:
            for severity, lineno, message in findings:
                all_findings.append((filepath, severity, lineno, message))
                logger.info(f"{filepath}:{lineno}: [{severity}] {message}")

    logger.info(f"\nTotal security findings: {len(all_findings)}")

    # Categorize by severity
    high = [f for f in all_findings if f[1] == 'HIGH']
    medium = [f for f in all_findings if f[1] == 'MEDIUM']
    low = [f for f in all_findings if f[1] == 'LOW']

    logger.info(f"High severity: {len(high)}")
    logger.info(f"Medium severity: {len(medium)}")
    logger.info(f"Low severity: {len(low)}")

    return 0 if len(all_findings) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
