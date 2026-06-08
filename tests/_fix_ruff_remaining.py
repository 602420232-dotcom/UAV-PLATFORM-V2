#!/usr/bin/env python3
"""Fix E402: move logger after all imports, add noqa for sys.path-dependent imports.

Strategy (minimal change):
1. Find all imports that appear after sys.path/sys.modules ops -> add # noqa: E402
2. Move logger = logging.getLogger(__name__) to after the last standard import
   (before any sys.path ops or non-import code)
"""
import logging
logger = logging.getLogger(__name__)

import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

FILES = [
    "batch_fixer.py",
    "fix_wildcard_imports.py",
    "e2e/test_e2e_flows.py",
    "test_ai_decision.py",
    "test_algorithm.py",
    "test_basic.py",
    "test_coordinator.py",
    "test_detection_drone_e2e.py",
    "test_errors.py",
    "test_exception_specificity.py",
    "test_federated_learning.py",
    "test_integration.py",
    "test_optimized_algorithm.py",
    "test_security.py",
]

IS_IMPORT = re.compile(r'^(import |from )')
IS_SYSPATH = re.compile(r'^(sys\.path\.|sys\.modules\[)')


def fix(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = list(content.split('\n'))

    # Step 1: Add noqa to imports after sys.path ops
    in_syspath_section = False
    for i in range(len(lines)):
        s = lines[i].strip()
        if IS_SYSPATH.match(s):
            in_syspath_section = True
        elif IS_IMPORT.match(s) and in_syspath_section:
            if '# noqa: E402' not in lines[i]:
                lines[i] = lines[i] + '  # noqa: E402'

    # Step 2: Find logger line
    logger_idx = None
    for i in range(len(lines)):
        if lines[i].strip() == 'logger = logging.getLogger(__name__)':
            logger_idx = i
            break

    if logger_idx is None:
        return False

    # Step 3: Find last standard import (before any sys.path op or non-import code)
    # Look from the top: the last consecutive import/from line that appears
    # before any sys.path op or non-import executable code.
    last_std_import = -1
    for i in range(len(lines)):
        if i == logger_idx:
            continue
        s = lines[i].strip()
        if IS_SYSPATH.match(s):
            break  # stop at first sys.path op
        if IS_IMPORT.match(s):
            last_std_import = i
        elif s == '' or s.startswith('#'):
            continue  # blank lines and comments are fine between imports
        else:
            # Non-import, non-comment, non-blank line - this is executable code
            # Only break if it's actually code (not a docstring)
            if not s.startswith('"""') and not s.startswith("'''"):
                break

    # Step 4: Rebuild with logger moved
    result = []
    logger_inserted = False

    for i in range(len(lines)):
        if i == logger_idx:
            continue  # skip old position

        result.append(lines[i])

        # Insert logger after last standard import
        if not logger_inserted and i == last_std_import:
            result.append('logger = logging.getLogger(__name__)')
            logger_inserted = True

    # If logger wasn't inserted (e.g., no std imports found),
    # put it at the beginning after any initial docstring
    if not logger_inserted:
        # Find first non-docstring, non-comment position
        insert_pos = 0
        in_docstring = False
        for i in range(len(result)):
            s = result[i].strip()
            if s.startswith('"""') or s.startswith("'''"):
                if in_docstring:
                    in_docstring = False
                    insert_pos = i + 1
                else:
                    in_docstring = True
            elif in_docstring:
                continue
            elif s == '' or s.startswith('#'):
                continue
            else:
                insert_pos = i
                break
        result.insert(insert_pos, 'logger = logging.getLogger(__name__)')

    new_content = '\n'.join(result)
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def main():
    fixed = 0
    for fname in FILES:
        fp = os.path.join(ROOT, fname)
        if not os.path.exists(fp):
            print(f"SKIP: {fname}")
            continue
        if fix(fp):
            print(f"FIXED: {fname}")
            fixed += 1
        else:
            print(f"OK: {fname}")
    print(f"\nTotal fixed: {fixed}")


if __name__ == '__main__':
    main()
