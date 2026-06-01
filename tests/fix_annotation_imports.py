#!/usr/bin/env python3
"""Restore annotation wildcard imports that were incorrectly removed."""
import re, os

ROOT = r'd:\Developer\workplace\py\iteam\trae'
SKIP = {'.git','node_modules','target','__pycache__','.idea','.pytest_cache','.trae'}
fixed = 0

for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in SKIP]
    for f in fn:
        if not f.endswith('.java'):
            continue
        fp = os.path.join(dp, f)
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
        except:
            continue
        
        needs_spring_web = bool(re.search(
            r'@(RestController|RequestMapping|GetMapping|PostMapping|PutMapping|'
            r'DeleteMapping|PathVariable|RequestParam|RequestBody|RequestHeader)',
            content))
        has_spring_web = 'import org.springframework.web.bind.annotation.' in content
        
        needs_jpa = bool(re.search(
            r'@(Entity|Table|Id|GeneratedValue|Column|OneToMany|ManyToOne|JoinColumn)',
            content))
        has_jpa = ('import jakarta.persistence.' in content or
                   'import javax.persistence.' in content)
        
        changes = []
        if needs_spring_web and not has_spring_web:
            content = 'import org.springframework.web.bind.annotation.*;\n' + content
            changes.append('spring-web')
        if needs_jpa and not has_jpa and 'jakarta.persistence' not in content:
            content = 'import jakarta.persistence.*;\n' + content
            changes.append('jpa')
        
        if changes:
            # Fix package import ordering
            lines = content.split('\n')
            pkg_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('package '):
                    pkg_idx = i
                    break
            if pkg_idx >= 0 and pkg_idx > 0:
                pkg_line = lines.pop(pkg_idx)
                lines.insert(0, pkg_line)
            content = '\n'.join(lines)
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            with open(fp, 'w', encoding='utf-8') as fh:
                fh.write(content)
            fixed += 1
            rel = os.path.relpath(fp, ROOT)
            print(f'  OK {rel}: {", ".join(changes)}')

print(f'\nFixed {fixed} files')
