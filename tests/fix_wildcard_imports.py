#!/usr/bin/env python3
"""Fix wildcard imports and broad exceptions in Java files."""
import re, os

ROOT = r'd:\Developer\workplace\py\iteam\trae'
SKIP = {'.git','node_modules','target','__pycache__','.idea','.pytest_cache','.trae'}

# Map of packages to their common types
PKG_TYPES = {
    'java.util': ['List', 'Map', 'ArrayList', 'HashMap', 'Set', 'HashSet', 'Optional',
                  'Arrays', 'Collections', 'Date', 'Objects', 'Queue', 'Deque',
                  'LinkedList', 'UUID', 'concurrent.*', 'stream.*', 'function.*'],
    'java.util.concurrent': ['ExecutorService', 'Executors', 'Future', 'TimeUnit',
                             'Callable', 'ThreadPoolExecutor', 'LinkedBlockingQueue',
                             'ConcurrentHashMap', 'CountDownLatch', 'ScheduledExecutorService'],
    'java.util.stream': ['Collectors', 'Stream'],
    'java.util.function': ['Consumer', 'Supplier', 'Function', 'Predicate'],
    'java.io': ['BufferedReader', 'BufferedWriter', 'InputStreamReader', 'IOException',
                'OutputStreamWriter', 'File', 'FileInputStream', 'PrintWriter'],
    'java.net': ['InetSocketAddress', 'URI', 'URL'],
    'java.nio': ['Paths', 'Path', 'Files'],
    'java.nio.file': ['Paths', 'Path', 'Files', 'StandardCopyOption'],
    'java.time': ['LocalDateTime', 'Duration', 'Instant', 'LocalDate'],
    'java.security': ['MessageDigest', 'SecureRandom', 'NoSuchAlgorithmException'],
    'java.math': ['BigDecimal', 'BigInteger'],
}

# Global type detection - build a set of all Java identifiers used
JAVA_KEYWORDS = {'abstract','assert','boolean','break','byte','case','catch','char',
    'class','const','continue','default','do','double','else','enum','extends',
    'final','finally','float','for','goto','if','implements','import','instanceof',
    'int','interface','long','native','new','package','private','protected','public',
    'return','short','static','strictfp','super','switch','synchronized','this',
    'throw','throws','transient','try','void','volatile','while','true','false','null',
    'var','yield','sealed','permits','record'}

def detect_used_types(content):
    """Detect capitalized type names used in code (excluding keywords/annotations)"""
    types = set()
    for m in re.finditer(r'\b([A-Z][A-Za-z0-9_]+)\b', content):
        name = m.group(1)
        if name not in JAVA_KEYWORDS and not name.endswith('Test') and not name.endswith('Tests'):
            types.add(name)
    return types

def fix_wildcard_file(fp):
    """Replace wildcard imports with explicit ones"""
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()

    wildcard_lines = re.findall(r'^import\s+(\S+)\.\*;.*$', content, re.MULTILINE)
    if not wildcard_lines:
        return False

    used = detect_used_types(content)
    lines = content.split('\n')
    new_lines = []
    removed_packages = set()

    for line in lines:
        m = re.match(r'^import\s+(\S+)\.\*;$', line.strip())
        if m:
            pkg = m.group(1)
            removed_packages.add(pkg)
        else:
            new_lines.append(line)

    # Add specific imports
    added_imports = []
    for pkg in sorted(removed_packages):
        if pkg in PKG_TYPES:
            for t in PKG_TYPES[pkg]:
                if '*' in t:
                    continue
                if t in used:
                    imp = f'import {pkg}.{t};'
                    if imp not in [l.strip() for l in new_lines] and imp not in added_imports:
                        added_imports.append(imp)
        elif pkg.startswith('com.uav') or pkg.startswith('com.bayesian') or \
             pkg.startswith('com.meteor') or pkg.startswith('com.path') or \
             pkg.startswith('com.wrf') or pkg.startswith('com.assimilation'):
            # For model/entity packages - find actual types
            for t in sorted(used):
                imp = f'import {pkg}.{t};'
                if imp not in [l.strip() for l in new_lines]:
                    added_imports.append(imp)
    
    if not added_imports:
        # Fallback: keep the wildcard
        for pkg in removed_packages:
            new_lines.append(f'import {pkg}.*;')
    else:
        # Insert before first import or at top
        new_lines.extend(added_imports)

    # Sort imports
    import_lines = [l for l in new_lines if l.strip().startswith('import ')]
    non_import_lines = [l for l in new_lines if not l.strip().startswith('import ')]

    # Deduplicate
    seen = set()
    unique_imports = []
    for l in import_lines:
        if l.strip() not in seen:
            seen.add(l.strip())
            unique_imports.append(l)

    result = '\n'.join(unique_imports + [''] + non_import_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)

    with open(fp, 'w', encoding='utf-8') as f:
        f.write(result)
    return True

# Process all files
fixed = 0
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in SKIP]
    for f in fn:
        if not f.endswith('.java'): continue
        fp = os.path.join(dp, f)
        try:
            if fix_wildcard_file(fp):
                fixed += 1
                print(f'  OK {os.path.relpath(fp, ROOT)}')
        except Exception as e:
            print(f'  ERR {os.path.relpath(fp, ROOT)}: {e}')

print(f'\nFixed {fixed} files with wildcard imports.')
