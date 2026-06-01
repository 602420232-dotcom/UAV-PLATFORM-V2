# 开发指南

## 环境搭建

### 前提条件

- Python 3.8+
- Git
- Docker（可选，用于容器化开发）
- CUDA Toolkit 12.x（可选，用于 GPU 加速）

### 克隆项目

```bash
git clone <项目地址>
cd data-assimilation-platform
```

### 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 安装依赖

```bash
# 基础安装（可编辑模式）
cd algorithm_core
pip install -e .

# 安装所有可选依赖
pip install -e .[api,parallel,gpu,dev]
```

### 环境变量配置

```bash
cp .env.example .env
# 编辑 .env 文件配置参数
```

## 项目结构

```
algorithm_core/
├── src/bayesian_assimilation/
│   ├── accelerators/      # 硬件加速模块
│   ├── adapters/          # 数据适配器
│   ├── api/               # API 接口
│   ├── components/        # 通用组件
│   ├── core/              # 核心算法基类
│   ├── data_sources/      # 数据源
│   ├── models/            # 同化模型
│   ├── parallel/          # 并行计算
│   ├── quality_control/   # 质量控制
│   ├── risk_assessment/   # 风险评估
│   ├── time_series/       # 时间序列
│   ├── utils/             # 工具函数
│   ├── visualization/     # 可视化
│   └── workflows/         # 工作流
├── configs/               # 配置文件
├── benchmarks/            # 性能测试
├── tests/                 # 单元测试
└── examples/              # 示例代码
```

## 编码规范

### Python 代码规范

- **格式化**：使用 Black，行长度 100
- **导入排序**：使用 isort，profile=black
- **类型检查**：使用 mypy
- **Lint**：使用 flake8

```bash
# 格式化代码
black src/

# 检查代码
flake8 src/

# 类型检查
mypy src/
```

### 测试规范

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_assimilator.py -v

# 生成覆盖率报告
pytest --cov=bayesian_assimilation --cov-report=html
```

## Git 工作流

1. 从 `dev` 分支创建功能分支：`git checkout -b feature/xxx`
2. 提交代码：遵循 Conventional Commits 规范
3. 推送分支：`git push origin feature/xxx`
4. 创建 Pull Request 到 `dev` 分支

### Commit 规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
refactor: 重构
test: 测试相关
chore: 构建/工具
```

## 构建与发布

### 构建包

```bash
cd algorithm_core
python -m build
```

### 发布到 PyPI

```bash
twine upload dist/*
```

### Docker 构建

```bash
cd algorithm_core/docker
docker build -t bayesian-assimilation:latest ..
```

## 调试技巧

### 日志级别

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 性能分析

```python
from bayesian_assimilation.utils.profiler import Profiler

profiler = Profiler()
with profiler.track("assimilation"):
    result = assimilator.assimilate_3dvar(background, obs, obs_loc)
print(profiler.report())
```

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 导入失败 | 确保在 `algorithm_core` 目录下执行 `pip install -e .` |
| GPU 不可用 | 检查 CUDA 版本，回退到 CPU 模式 |
| 内存不足 | 启用并行计算或降低数据分辨率 |
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
