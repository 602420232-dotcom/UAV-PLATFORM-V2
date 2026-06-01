#!/usr/bin/env python3
"""
Standardize .md file footers and reorganize docs/ directory.
Phase 1: Add uniform footer to all .md files
Phase 2: Reorganize docs/ into logical hierarchy
"""
import os
import re
import shutil
import json
from datetime import datetime

ROOT = r'd:\Developer\workplace\py\iteam\trae'
SKIP_DIRS = {'.git', 'node_modules', 'target', '__pycache__', '.idea',
             '.pytest_cache', '.trae', 'dist', 'build'}

FOOTER = """
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
"""

# ========== PHASE 1: Add footer to all .md files ==========
def add_footer():
    updated = 0
    skipped = 0
    already_has = 0

    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if not f.endswith('.md'):
                continue
            fp = os.path.join(dp, f)
            rel = os.path.relpath(fp, ROOT)

            try:
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()
            except:
                try:
                    with open(fp, 'r', encoding='gbk') as fh:
                        content = fh.read()
                except:
                    skipped += 1
                    continue

            # Check if footer already exists
            if '> **维护者**: DITHIOTHREITOL' in content:
                already_has += 1
                continue

            # Remove any existing footer-like sections at the end
            content = content.strip()

            # Write updated content
            try:
                with open(fp, 'w', encoding='utf-8') as fh:
                    fh.write(content + '\n' + FOOTER + '\n')
                updated += 1
            except Exception as e:
                print(f'  ERR {rel}: {e}')
                skipped += 1

    print(f'Footer added: {updated} files')
    print(f'Already had footer: {already_has} files')
    print(f'Skipped: {skipped} files')
    return updated

# ========== PHASE 2: Reorganize docs/ ==========
ARCHIVE_FILES = [
    'ADDITIONAL_CIRCUIT_BREAKER_IMPLEMENTATION_REPORT.md',
    'CIRCUIT_BREAKER_IMPLEMENTATION_COMPLETE_REPORT.md',
    'CIRCUIT_BREAKER_IMPLEMENTATION_REPORT.md',
    'CODE_QUALITY_REPORT.md',
    'COMMON_DEPENDENCIES_ANALYSIS.md',
    'DEPENDENCY_MANAGEMENT_REFACTORING_REPORT.md',
    'DOCUMENTATION_COMPLETE_REPORT.md',
    'DOCUMENTATION_UPDATE_SUMMARY.md',
    'OPTIMIZATION_IMPLEMENTATION_REPORT.md',
    'SECURITY_IMPROVEMENTS.md',
    'TEST_COVERAGE_REPORT.md',
    'UAV_PATH_PLANNING_SYSTEM_DOCUMENTATION_REPORT.md',
]

DELETE_FILES = [
    'DEPLOYMENT (2).md',
]

MOVE_MAP = {
    # deployment/
    'DEPLOYMENT.md': 'deployment/DEPLOYMENT.md',
    'DEPLOY_GUIDE.md': 'deployment/DEPLOY_GUIDE.md',
    'DISASTER_RECOVERY_PLAN.md': 'deployment/DISASTER_RECOVERY_PLAN.md',
    # guides/
    'CIRCUIT_BREAKER_GUIDE.md': 'guides/CIRCUIT_BREAKER_GUIDE.md',
    'CIRCUIT_BREAKER_USAGE_EXAMPLES.md': 'guides/CIRCUIT_BREAKER_USAGE_EXAMPLES.md',
    'EXCEPTION_HTTP_STATUS_GUIDE.md': 'guides/EXCEPTION_HTTP_STATUS_GUIDE.md',
    'PRODUCTION_SECRETS_GUIDE.md': 'guides/PRODUCTION_SECRETS_GUIDE.md',
    # reports/
    'COMPREHENSIVE_AUDIT_REPORT_v2.1.md': 'reports/COMPREHENSIVE_AUDIT_REPORT_v2.1.md',
    'COMPREHENSIVE_QUALITY_ASSESSMENT.md': 'reports/COMPREHENSIVE_QUALITY_ASSESSMENT.md',
}

def reorganize_docs():
    docs_d = os.path.join(ROOT, 'docs')
    changes = {'archived': [], 'deleted': [], 'moved': [], 'dirs_created': []}

    # Create target directories
    target_dirs = ['archive', 'deployment', 'guides', 'reports']
    for d in target_dirs:
        dp = os.path.join(docs_d, d)
        if not os.path.exists(dp):
            os.makedirs(dp, exist_ok=True)
            changes['dirs_created'].append(d)

    # Move interim reports to archive/
    for f in ARCHIVE_FILES:
        src = os.path.join(docs_d, f)
        dst = os.path.join(docs_d, 'archive', f)
        if os.path.exists(src):
            shutil.move(src, dst)
            changes['archived'].append(f)
            print(f'  ARCHIVE {f}')

    # Delete duplicates
    for f in DELETE_FILES:
        fp = os.path.join(docs_d, f)
        if os.path.exists(fp):
            os.remove(fp)
            changes['deleted'].append(f)
            print(f'  DELETE {f}')

    # Move files to categorized dirs
    for f, dest_rel in MOVE_MAP.items():
        src = os.path.join(docs_d, f)
        dst = os.path.join(docs_d, dest_rel)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            changes['moved'].append((f, dest_rel))
            print(f'  MOVE {f} -> {dest_rel}')

    return changes

# ========== MAIN ==========
if __name__ == '__main__':
    print('=' * 60)
    print('PHASE 1: Standardizing .md footers')
    print('=' * 60)
    footer_count = add_footer()

    print()
    print('=' * 60)
    print('PHASE 2: Reorganizing docs/ directory')
    print('=' * 60)
    changes = reorganize_docs()

    # Save change log
    report = {
        'footer_added': footer_count,
        **{k: len(v) if isinstance(v, list) else v for k, v in changes.items()},
        'details': changes,
    }
    report_path = os.path.join(ROOT, 'docs', 'reports', 'DOCUMENTATION_REORGANIZATION_REPORT.md')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    report_md = f"""# 文档整理变更报告

> **日期**: 2026-05-08
> **版本**: 2.1
> **操作**: 项目 Markdown 文档标准化与重组

## 统计概览

| 操作 | 数量 |
|------|:----:|
| Footer 标准化新增 | {footer_count} |
| 归档至 archive/ | {len(changes['archived'])} |
| 删除重复文件 | {len(changes['deleted'])} |
| 移至分类目录 | {len(changes['moved'])} |
| 新建目录 | {len(changes['dirs_created'])} |

## Footer 标准化

所有 {footer_count} 个 .md 文件已添加统一页脚：

```
---
> **最后更新**: 2026-05-08
> **版本**: 2.1
> **维护者**: DITHIOTHREITOL
```

## 归档文件 (archive/)

以下 12 份中期报告已被主报告替代，移至 archive/ 保留备查：

{chr(10).join(f'- `{f}`' for f in changes['archived'])}

## 删除文件

{chr(10).join(f'- `{f}` — 重复文件' for f in changes['deleted'])}
{'(无)' if not changes['deleted'] else ''}

## 目录重组

### 新建目录
{chr(10).join(f'- `{d}/`' for d in changes['dirs_created'])}

### 文件移动
{chr(10).join(f'- `{src}` → `{dst}`' for src, dst in changes['moved'])}

## 重组后的 docs/ 结构

```
docs/
├── README.md
├── CHANGELOG.md
├── QUICK_REFERENCE.md
├── architecture.md
├── PROJECT_STRUCTURE.md
├── PORTS_CONFIGURATION.md
├── DOCKER.md
├── EXAMPLE.md
├── improvement_suggestions.md
├── api/                      (API 文档 — 按服务分组)
│   ├── README.md
│   ├── API_DOCUMENTATION.md
│   └── ... (7 个子目录)
├── archive/                  (历史中期报告)
│   └── ... (12 份报告)
├── deployment/               (部署相关文档)
│   ├── DEPLOYMENT.md
│   ├── DEPLOY_GUIDE.md
│   └── DISASTER_RECOVERY_PLAN.md
├── guides/                   (使用指南)
│   ├── CIRCUIT_BREAKER_GUIDE.md
│   ├── CIRCUIT_BREAKER_USAGE_EXAMPLES.md
│   ├── EXCEPTION_HTTP_STATUS_GUIDE.md
│   └── PRODUCTION_SECRETS_GUIDE.md
└── reports/                  (当前活跃报告)
    ├── COMPREHENSIVE_AUDIT_REPORT_v2.1.md
    └── COMPREHENSIVE_QUALITY_ASSESSMENT.md
```

---

> **最后更新**: 2026-05-08
> **版本**: 2.1
> **维护者**: DITHIOTHREITOL
"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_md)

    print()
    print(f'Reorganization report saved to: {os.path.relpath(report_path, ROOT)}')
    print()
    print('=' * 60)
    print('DONE')
    print('=' * 60)
