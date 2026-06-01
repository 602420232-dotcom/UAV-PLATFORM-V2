# 教程

## 入门教程

### 1. 安装与配置

```bash
# 安装算法库
cd algorithm_core
pip install -e .

# 验证安装
python -c "from bayesian_assimilation import __version__; print(__version__)"
```

### 2. 基础同化流程

```python
from bayesian_assimilation.core.assimilator import BayesianAssimilator
import numpy as np

# 初始化同化器
assim = BayesianAssimilator()
assim.initialize_grid(domain_size=(50, 50, 20))

# 准备背景场
background = np.random.rand(50, 50, 20)

# 准备观测数据
obs_values = np.random.rand(500)
obs_locations = np.random.rand(500, 3)

# 执行三维变分同化
analysis, variance = assim.assimilate_3dvar(
    background=background,
    observations=obs_values,
    obs_locations=obs_locations
)

print(f"分析场形状: {analysis.shape}")
print(f"方差场形状: {variance.shape}")
```

### 3. 可视化结果

```python
from bayesian_assimilation.visualization.plots import plot_comparison

plot_comparison(
    background=background[:, :, 0],
    analysis=analysis[:, :, 0],
    title="3D-VAR 同化结果对比"
)
```

## 进阶教程

### 使用 EnKF 算法

```python
from bayesian_assimilation.models.enkf import EnKF

enkf = EnKF(
    ensemble_size=50,
    inflation_factor=1.05,
    localization_radius=5000
)

# 准备集合预报
ensemble = np.random.rand(50, 50, 50, 20)

# 更新同化
analysis_ensemble = enkf.update(ensemble, obs_values, obs_locations)
```

### 并行计算

```python
from bayesian_assimilation.parallel.dask import DaskParallelManager

# 创建 Dask 集群
parallel_mgr = DaskParallelManager(
    n_workers=4,
    threads_per_worker=2
)

# 并行执行同化
results = parallel_mgr.parallel_assimilate(
    assimilator=assim,
    background_chunks=list_of_chunks,
    observations=obs_values,
    obs_locations=obs_locations
)
```

## 完整工作流示例

### 批处理工作流

```python
from bayesian_assimilation.workflows.batch import BatchWorkflow

workflow = BatchWorkflow(
    config_path="configs/default.yaml",
    input_dir="data/input",
    output_dir="data/output"
)

workflow.run()
```

### 流水线工作流

```python
from bayesian_assimilation.workflows.pipeline import PipelineWorkflow

pipeline = PipelineWorkflow(steps=[
    ("load", "bayesian_assimilation.adapters.load_data"),
    ("quality_control", "bayesian_assimilation.quality_control.validate"),
    ("assimilate", "bayesian_assimilation.core.assimilate"),
    ("visualize", "bayesian_assimilation.visualization.plot")
])

pipeline.execute(config={"input": "data.nc"})
```

## CLI 使用

```bash
# 查看帮助
assimilate --help

# 查看版本
assimilate --version

# 执行同化
assimilate run --config configs/default.yaml --input data.nc --output result.nc

# 质量控制
assimilate quality-control --input data.nc --output qc_result.nc

# 风险评估
assimilate risk-assessment --input analysis.nc --output risk_map.nc
```

## REST API 调用

```bash
# 启动 API 服务
uvicorn bayesian_assimilation.api.rest:app --host 0.0.0.0 --port 8000

# 调用同化接口
curl -X POST http://localhost:8000/assimilate \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm": "3dvar",
    "background": {"data": [...], "grid": {...}},
    "observations": {"values": [...], "locations": [...]}
  }'
```
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
