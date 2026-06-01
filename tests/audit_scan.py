#!/usr/bin/env python3
"""Full project audit scanner - produces issues report."""
import os, re, json

ROOT = r'd:\Developer\workplace\py\iteam\trae'
SKIP_DIRS = {'.git', 'node_modules', 'target', '__pycache__', '.idea', '.pytest_cache', '.trae', 'dist', 'build'}

issues = {
    'hardcoded_secrets': [],
    'todo_fixme': [],
    'empty_files': [],
    'bom_files': [],
    'wildcard_imports': [],
    'print_statements': [],
    'broad_exception': [],
    'suppress_warnings': [],
}

for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in SKIP_DIRS]
    for f in fn:
        fp = os.path.join(dp, f)
        rel = os.path.relpath(fp, ROOT)
        
        # Check empty source files
        try:
            if os.path.getsize(fp) == 0 and f.endswith(('.java','.py','.xml','.yml','.yaml','.properties','.json','.sh')):
                issues['empty_files'].append(rel)
        except:
            pass
        
        if not f.endswith(('.java','.py','.xml','.yml','.yaml','.properties','.sh','.json','.js','.ts','.vue','.css')):
            continue
            
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read(100000)
        except:
            try:
                with open(fp, 'r', encoding='gbk') as fh:
                    content = fh.read(100000)
            except:
                continue
            
        # Check BOM
        try:
            with open(fp, 'rb') as fh2:
                if fh2.read(3) == b'\xef\xbb\xbf':
                    issues['bom_files'].append(rel)
        except:
            pass
        
        # Hardcoded secrets
        if re.search(r'(?:password|secret|token|apikey|api[-_]?key)\s*[:=]\s*["\'](?!\$\{|""|null)(?!changeme|test|example|your-|demo-)[^"\']{4,}["\']', content, re.IGNORECASE):
            issues['hardcoded_secrets'].append(rel)
        
        # TODO/FIXME
        if 'TODO' in content or 'FIXME' in content:
            issues['todo_fixme'].append(rel)
        
        # Java: wildcard imports
        if f.endswith('.java') and re.search(r'^import\s+\S+\.\*;', content, re.MULTILINE):
            issues['wildcard_imports'].append(rel)
        
        # Python: print statements
        if f.endswith('.py') and not f.startswith('test_') and not f.endswith('_test.py'):
            if re.search(r'^\s*print\s*\(', content, re.MULTILINE):
                issues['print_statements'].append(rel)
        
        # Broad exception
        if f.endswith('.java') and re.search(r'catch\s*\(\s*Exception\s+', content):
            issues['broad_exception'].append(rel)
        
        # @SuppressWarnings
        if f.endswith('.java') and '@SuppressWarnings' in content:
            issues['suppress_warnings'].append(rel)

for cat, lst in issues.items():
    print(f'\n### {cat.upper()}: {len(lst)} items')
    for item in lst[:20]:
        print(f'  - {item}')
    if len(lst) > 20:
        print(f'  ... and {len(lst)-20} more')

with open(os.path.join(ROOT, 'tests', 'audit_scan_results.json'), 'w') as out:
    json.dump(issues, out, indent=2, ensure_ascii=False)
print('\n\nFull results saved to tests/audit_scan_results.json')
