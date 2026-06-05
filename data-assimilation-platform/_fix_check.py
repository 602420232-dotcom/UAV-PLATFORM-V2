import os

base = r'd:\Developer\workplace\py\iteam\trae\data-assimilation-platform'


files = [
    'algorithm_core/docker/README.md',
    'benchmarks/README.md',
    'algorithm_core/examples/TESTING.md',
    'algorithm_core/docs/CHANGELOG.md',
    'algorithm_core/examples/结果分析.md',
    'algorithm_core/README.md',
    'README.md',
    'docs/index.md',
    'docs/development.md',
    'docs/uav_integration.md',
    'docs/tutorials.md',
    'docs/api.md',
    'docs/architecture.md',
    'deployments/README.md',
    '.github/PULL_REQUEST_TEMPLATE.md',
    'shared/protos/README.md',
    'shared/README.md',
    'service_spring/README.md',
    'scripts/README.md',
    'shared/protos/common/README.md',
    'service_python/README.md',
]


for f in files:
    path = os.path.join(base, f)
    with open(path, 'rb') as fh:
        data = fh.read()
    text = data.decode('utf-8', errors='replace')
    lines = text.split('\n')
    for i, line in enumerate(lines):
        pos = line.find('?')
        if pos >= 0:
            ctx_start = max(0, pos - 10)
            ctx_end = min(len(line), pos + 10)
            print(f'{f}:{i+1}: ...{line[ctx_start:ctx_end]}...')
