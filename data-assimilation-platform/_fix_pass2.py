import os
import re

base = r'd:\Developer\workplace\py\iteam\trae\data-assimilation-platform'

# Second pass - handle remaining ? characters per file
# Use regex-based approach where needed
fixes = {}


def fix_file(rel_path, replacements):
    file_path = os.path.join(base, rel_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    for old, new in replacements:
        content = content.replace(old, new)
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'FIXED: {rel_path}')
    else:
        print(f'NO CHANGES: {rel_path}')


# File 3: algorithm_core/examples/TESTING.md


fix_file('algorithm_core/examples/TESTING.md', [
    ('在 ?`algorithm_core', '在 `algorithm_core'),
    ('在 ?`test_performance', '在 `test_performance'),
    ('在 ?`check_performance', '在 `check_performance'),
    ('| ≥?100万点/秒|', '| ≥100万点/秒|'),
    ('| ≤?1GB |', '| ≤1GB |'),
    ('| ≤?1秒|', '| ≤1秒|'),
])

# File 5: algorithm_core/examples/结果分析.md


fix_file('algorithm_core/examples/结果分析.md', [
    ('生成?\n', '生成\n'),
    ('分辨率?\n', '分辨率\n'),
    ('准确?\n', '准确性\n'),
])

# File 6: algorithm_core/README.md - tree structure


fix_file('algorithm_core/README.md', [
    ('    # 数据适配?\n', '    # 数据适配器\n'),
    ('    # 可视化模?\n', '    # 可视化模块\n'),
    ('    # 工作流管?\n', '    # 工作流管理\n'),
])

# File 8: docs/index.md


fix_file('docs/index.md', [
    ('支?DaskMPIRa', '支持 Dask、MPI、Ra'),
])

# File 9: docs/development.md


fix_file('docs/development.md', [
    ('执?`pip', '执行 `pip'),
])

# File 10: docs/uav_integration.md - ASCII diagram and other issues


fix_file('docs/uav_integration.md', [
    ('集成?\n', '集成\n'),
    ('接口?\n', '接口\n'),
])

# File 18: service_spring/README.md


fix_file('service_spring/README.md', [
    ('接口?\n', '接口\n'),
    ('# 配置?\n', '# 配置类\n'),
])

# File 20: shared/protos/common/README.md


fix_file('shared/protos/common/README.md', [
    ('定义?\n', '定义\n'),
])

# Now handle docs/uav_integration.md ASCII diagram separately
# The ? in the diagram are box-drawing characters that got corrupted
path = os.path.join(base, 'docs/uav_integration.md')


with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the ASCII diagram - rebuild it
old_diagram = """```
无人机路径规划系?            贝叶斯同化平?
?        ?
? WRF 处理层  数据适配器          ?
? (Java)          ? HTTP   ? (WRF Adapter)       ?


?        ?
                                      ?
?        ?
? 气象预测服务     ? ? 贝叶斯同化核?      ?
? (Java)          ? gRPC   ? (3D-VAR/EnKF)      ?


?        ?
                                      ?
?        ?
? 路径规划服务     ?        ? 同化结果输出         ?
? (Java)          ?        ? (分析?方差?      ?
?        ?
```"""

new_diagram = """```
无人机路径规划系统              贝叶斯同化平台
┌─────────────────┐             ┌──────────────────────┐
│  WRF 处理层     │  数据适配器  │                      │
│  (Java)         │  ←─HTTP──→  │  (WRF Adapter)       │
│                 │             │                      │


└─────────────────┘             └──────────────────────┘
                                          │
┌─────────────────┐             ┌──────────────────────┐
│  气象预测服务   │             │  贝叶斯同化核心      │
│  (Java)         │  ←─gRPC──→  │  (3D-VAR/EnKF)      │
│                 │             │                      │


└─────────────────┘             └──────────────────────┘
                                          │
┌─────────────────┐             ┌──────────────────────┐
│  路径规划服务   │             │  同化结果输出         │
│  (Java)         │             │  (分析场/方差场)     │
│                 │             │                      │
└─────────────────┘             └──────────────────────┘
```"""


if old_diagram in content:
    content = content.replace(old_diagram, new_diagram)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('FIXED diagram: docs/uav_integration.md')


else:
    print('Diagram not found in docs/uav_integration.md - checking manually')
    # Try to find the diagram
    idx = content.find('无人机路径规划系')
    if idx >= 0:
        end_idx = content.find('```', idx + 50)
        print(f'  Found at offset {idx}, ends at {end_idx}')
        # Show context
        print(f'  Content: {repr(content[idx:end_idx+3][:200])}')
