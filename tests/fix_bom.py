#!/usr/bin/env python3
"""Fix UTF-8 BOM in files."""
import os, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else r'd:\Developer\workplace\py\iteam\trae'

bom_files = []
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in {'.git', 'node_modules', 'target', '__pycache__', '.idea', '.pytest_cache'}]
    for f in fn:
        fp = os.path.join(dp, f)
        if not f.endswith(('.py','.java','.yml','.yaml','.xml','.json','.sh','.md','.properties','.js','.ts','.vue','.css')):
            continue
        try:
            with open(fp, 'rb') as fh:
                data = fh.read()
            if data.startswith(b'\xef\xbb\xbf'):
                bom_files.append(fp)
                with open(fp, 'wb') as fh:
                    fh.write(data[3:])
        except:
            pass

print(f'Fixed {len(bom_files)} BOM files:')
for f in bom_files:
    print(f'  {os.path.relpath(f, ROOT)}')
