# 5D-VAR 实现说明与算法集成调度重构方案

## 一、5D-VAR 实现总结

### 1.1 实现位置

```
data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/
├── five_dimensional_var.py   ← 新增：5D-VAR 核心实现（~600行）
└── __init__.py               ← 已更新：注册 FiveDimensionalVar 及相关类
```

### 1.2 5D-VAR 的独特定义

本项目5D-VAR **不是**标准气象学中的5D-VAR（多参数/多变量扩展），而是基于 `docs_ref/5DVAR可行性.md` 的定义，在4D-VAR基础上增加**三个扩展维度**：

| 维度 | 名称 | 代价项 | 含义 |
|------|------|--------|------|
| D1-D4 | 空间+时间 | J_b + J_o | 标准4D-VAR（背景+观测约束） |
| D5a | **风险维度** | J_risk = α_r · ∫C_risk(x,t)dt | 将飞行风险嵌入同化代价函数 |
| D5b | **动态扰动维度** | B_5D = [B_WRF, C^T; C, P_ensemble] | 无人机集合观测扩展背景协方差 |
| D5c | **AI参数化维度** | J_param = λ · ‖H_AI(α) - y_obs‖² | AI模型修正量参与同化 |

### 1.3 核心类设计

```
FiveDimensionalVar(FourDimensionalVar)
├── FiveDVarConfig              # 配置数据类（30+参数）
├── RiskCostCalculator           # 风险代价计算器（风速/湍流/侧风→J_risk）
├── ExtendedBackgroundCovariance # 扩展B矩阵（WRF+无人机集合交叉协方差）
├── AICorrectionOperator         # AI修正算子（α参数化CNN/U-Net修正）
├── cost_function_5d()           # 完整代价函数 J = J_b + J_o + J_risk + J_param
├── adjoint_gradient_5d()        # 伴随梯度 ∇J = ∇J_b + ∇J_o + ∇J_risk
└── assimilate()                 # 两阶段优化：先x后(x,α)联合优化
```

### 1.4 两阶段优化策略

1. **阶段1**：固定 α=0，仅优化气象场 x（标准4D-VAR问题）
2. **阶段2**：联合优化扩展控制变量 [x; α]，同时调整气象场和AI修正参数

### 1.5 测试结果

```
网格: 20×20, 控制变量: 1600维, 观测: 8个, 时间窗口: 6步
代价: 7875.9 → 7530.9 (降低4.4%)
AI修正参数: α = [-0.051, 0.009, 0.002, 0.000]
风险场: avg=0.539, max=0.619, 高风险区域=9.8%
耗时: ~8秒
```

---

## 二、算法集成与调度重构方案

### 2.1 现状问题分析

当前项目中的算法分散在多个独立目录中，缺乏统一调度：

```
data-assimilation-platform/algorithm_core/   # 14个同化算法（3DVAR/4DVAR/EnKF/Hybrid...）
model-engine/                                 # ~25个模型（CNN/U-Net/GPR/MPC/EnKF...）
path-planning-service/src/main/python/        # 16个规划算法（Dijkstra/RRT*/GA/PSO/DWA...）
edge-cloud-coordinator/                       # 联邦学习/边缘推理/LLM决策
uav-edge-sdk/                                 # C++嵌入式算法（DWA/A*/Bezier）
```

**核心问题**：
1. **算法孤岛**：每个目录独立实现，没有统一接口和注册机制
2. **重复实现**：EnKF在 `algorithm_core` 和 `model-engine/gpr_risk` 各有一套
3. **调度硬编码**：算法选择逻辑散落在各处，无法动态切换
4. **无版本管理**：算法迭代无法追踪，A/B测试困难
5. **资源未隔离**：所有算法共享同一进程，一个OOM全部崩溃

### 2.2 重构目标：算法调度框架 (Algorithm Orchestration Framework)

在 `uav-platform-v2/python/` 下建立统一的算法调度层：

```
python/
├── assimilation-core/          # 同化算法核心（从 data-assimilation-platform 迁移）
│   ├── bayesian_assimilation/
│   │   ├── models/             # 所有同化模型（含5D-VAR）
│   │   ├── core/               # 基类、协方差、求解器、观测算子
│   │   └── utils/              # 风险映射、配置
│   └── pyproject.toml
│
├── model-engine/               # AI模型引擎（从原 model-engine 迁移）
│   ├── cnn_corrector/
│   ├── unet_downscaler/
│   ├── gpr_risk/
│   ├── fusion/
│   └── active_obs/
│
├── algo-orchestration/         # 【新增】算法调度框架
│   ├── __init__.py
│   ├── registry.py             # 算法注册中心
│   ├── scheduler.py            # 智能调度器
│   ├── pipeline.py             # 算法管线编排
│   ├── adapter.py              # 算法适配器（统一接口）
│   ├── context.py              # 执行上下文（状态/配置/历史）
│   ├── metrics.py               # 算法性能度量
│   └── config.py                # 调度配置
│
├── path-planning-core/         # 路径规划核心（从 path-planning-service 迁移）
│   ├── global/                 # 全局规划（VRPTW/GA/PSO/ACO）
│   ├── local/                  # 局部规划（DE-RRT*/A*/DWA）
│   └── risk_aware/             # 风险感知规划
│
└── edge-coordinator/           # 边云协同（从 edge-cloud-coordinator 迁移）
    ├── federated_learning/
    └── edge_inference/
```

### 2.3 算法注册中心 (Algorithm Registry)

```python
# algo-orchestration/registry.py

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Type, Callable, Optional, List

class AlgorithmCategory(Enum):
    ASSIMILATION = "assimilation"       # 同化算法
    CORRECTION = "correction"           # AI订正模型
    DOWNSCALING = "downscaling"          # 降尺度模型
    RISK_ESTIMATION = "risk_estimation" # 风险估计
    GLOBAL_PLANNING = "global_planning" # 全局路径规划
    LOCAL_PLANNING = "local_planning"   # 局部路径规划
    OBSERVATION = "observation"         # 主动观测决策
    CONTROL = "control"                 # 滚动时域控制

@dataclass
class AlgorithmSpec:
    """算法规格描述"""
    name: str                           # 算法唯一标识
    display_name: str                    # 显示名称
    category: AlgorithmCategory         # 所属类别
    version: str                         # 版本号
    description: str                     # 算法描述
    factory: Callable                   # 工厂函数（创建实例）
    input_schema: Dict                   # 输入数据格式
    output_schema: Dict                  # 输出数据格式
    complexity: str                      # 复杂度等级: low/medium/high/extreme
    gpu_required: bool = False          # 是否需要GPU
    max_grid_size: int = 100            # 最大网格尺寸
    estimated_time_ms: float = 100      # 估计执行时间（毫秒）
    tags: List[str] = None              # 标签（用于搜索）
    deprecated: bool = False            # 是否已弃用
    replaced_by: Optional[str] = None   # 替代算法

class AlgorithmRegistry:
    """
    算法注册中心（单例）

    所有算法在启动时自注册，运行时通过 registry 查询和实例化。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._algorithms: Dict[str, AlgorithmSpec] = {}
            cls._instance._aliases: Dict[str, str] = {}
        return cls._instance

    def register(self, spec: AlgorithmSpec):
        """注册算法"""
        if spec.deprecated and spec.replaced_by:
            logger.warning(f"算法 {spec.name} 已弃用，请使用 {spec.replaced_by}")
        self._algorithms[spec.name] = spec
        # 注册别名
        for alias in (spec.tags or []):
            self._aliases[alias] = spec.name

    def get(self, name: str) -> AlgorithmSpec:
        """获取算法规格"""
        resolved = self._aliases.get(name, name)
        if resolved not in self._algorithms:
            raise KeyError(f"算法 '{name}' 未注册")
        return self._algorithms[resolved]

    def list_by_category(self, category: AlgorithmCategory) -> List[AlgorithmSpec]:
        """按类别列出算法"""
        return [s for s in self._algorithms.values()
                if s.category == category and not s.deprecated]

    def find_best(self, category: AlgorithmCategory,
                  constraints: Dict) -> AlgorithmSpec:
        """根据约束条件推荐最佳算法"""
        candidates = self.list_by_category(category)
        # 按约束过滤和排序
        ...
```

### 2.4 统一算法接口 (Algorithm Adapter)

```python
# algo-orchestration/adapter.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
import time

@dataclass
class AlgorithmResult:
    """统一算法输出格式"""
    algorithm_name: str
    version: str
    success: bool
    data: Dict[str, Any]         # 算法输出数据
    metadata: Dict[str, Any]     # 元数据（耗时、迭代次数等）
    quality_score: float         # 质量评分 (0-1)
    risk_field: Optional[Dict] = None  # 风险场（如果适用）

class BaseAlgorithmAdapter(ABC):
    """
    算法适配器基类

    所有算法通过适配器包装，对外暴露统一接口。
    """

    def __init__(self, spec: AlgorithmSpec, config: Optional[Dict] = None):
        self.spec = spec
        self.config = config or {}
        self._instance = None  # 延迟实例化

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> AlgorithmResult:
        """执行算法"""
        ...

    def validate_input(self, input_data: Dict) -> bool:
        """验证输入数据格式"""
        ...

    def get_resource_requirements(self) -> Dict:
        """获取资源需求（GPU/内存/时间）"""
        return {
            'gpu': self.spec.gpu_required,
            'estimated_time_ms': self.spec.estimated_time_ms,
            'max_grid_size': self.spec.max_grid_size
        }

# 具体适配器示例
class AssimilationAdapter(BaseAlgorithmAdapter):
    """同化算法适配器"""

    def execute(self, input_data: Dict) -> AlgorithmResult:
        start = time.perf_counter()

        # 从注册中心获取算法实例
        algo = self.spec.factory(self.config)

        # 统一输入格式转换
        background = input_data['background']
        observations = input_data['observations']

        # 执行同化
        analysis, variance = algo.assimilate(background, observations)

        elapsed = time.perf_counter() - start

        return AlgorithmResult(
            algorithm_name=self.spec.name,
            version=self.spec.version,
            success=True,
            data={'analysis': analysis, 'variance': variance},
            metadata={'elapsed_ms': elapsed * 1000},
            quality_score=self._compute_quality(analysis, observations)
        )
```

### 2.5 智能调度器 (Smart Scheduler)

```python
# algo-orchestration/scheduler.py

class AlgorithmScheduler:
    """
    智能算法调度器

    根据输入特征、资源约束、历史性能自动选择最优算法。
    """

    def __init__(self, registry: AlgorithmRegistry):
        self.registry = registry
        self._history = []  # 历史执行记录

    def select_assimilation(
        self,
        grid_size: int,
        n_observations: int,
        has_drone_obs: bool = False,
        require_risk: bool = False,
        time_budget_ms: float = 5000,
        gpu_available: bool = False
    ) -> BaseAlgorithmAdapter:
        """
        智能选择同化算法

        决策树：
        - 网格 > 100×100 且有GPU → 4D-VAR（GPU加速版）
        - 有无人机观测 + 需要风险场 → 5D-VAR
        - 观测 > 50 且时间充裕 → EnKF
        - 观测 < 50 且时间紧迫 → 3D-VAR
        - 需要概率输出 → ProbabilisticUNet + EnKF
        """
        if require_risk and has_drone_obs:
            return self._create_adapter('5d-var')
        elif grid_size > 10000 and gpu_available:
            return self._create_adapter('4d-var-gpu')
        elif n_observations > 50 and time_budget_ms > 3000:
            return self._create_adapter('enkf')
        elif n_observations > 20:
            return self._create_adapter('hybrid-assimilation')
        else:
            return self._create_adapter('3d-var')

    def select_planning(
        self,
        n_waypoints: int,
        has_risk_field: bool,
        is_dynamic: bool,
        time_budget_ms: float
    ) -> BaseAlgorithmAdapter:
        """
        智能选择路径规划算法

        决策树：
        - 多点配送 + 时间窗 → VRPTW（全局）+ DE-RRT*（局部）+ DWA（避障）
        - 单点A→B + 动态环境 → DE-RRT* + DWA
        - 静态环境 + 精确约束 → A*
        - 大规模搜索 → GA/PSO
        """
        ...

    def select_correction(
        self,
        has_dem: bool,
        temporal_depth: int,
        model_types: List[str]
    ) -> List[BaseAlgorithmAdapter]:
        """
        选择AI订正模型组合

        典型管线：CNN空间订正 → LSTM时序订正 → XGBoost残差订正
        """
        pipeline = []
        if has_dem:
            pipeline.append(self._create_adapter('cnn-spatial-corrector'))
        if temporal_depth > 1:
            pipeline.append(self._create_adapter('lstm-temporal-corrector'))
        pipeline.append(self._create_adapter('xgboost-residual-corrector'))
        return pipeline
```

### 2.6 算法管线编排 (Pipeline Orchestration)

```python
# algo-orchestration/pipeline.py

class AlgorithmPipeline:
    """
    算法管线编排器

    将多个算法按DAG（有向无环图）组织，支持：
    - 串行管线：数据 → 融合 → 订正 → 降尺度 → 同化 → 风险 → 规划
    - 并行分支：同时运行多个模型，结果融合
    - 条件分支：根据中间结果选择不同路径
    - 缓存复用：相同输入跳过重复计算
    """

    # 标准气象-路径规划管线
    STANDARD_PIPELINE = {
        'stages': [
            {
                'name': 'data_fusion',
                'algorithm': 'dynamic-weight-fusion',
                'inputs': ['raw_weather_data'],
                'outputs': ['fused_field']
            },
            {
                'name': 'ai_correction',
                'algorithm': 'cnn-lstm-xgboost-pipeline',
                'inputs': ['fused_field'],
                'outputs': ['corrected_field']
            },
            {
                'name': 'downscaling',
                'algorithm': 'unet-downscaler',
                'inputs': ['corrected_field'],
                'outputs': ['high_res_field'],
                'parallel_alt': 'probabilistic-unet'  # 可替换为概率版本
            },
            {
                'name': 'assimilation',
                'algorithm': 'auto',  # 由调度器自动选择
                'inputs': ['high_res_field', 'observations'],
                'outputs': ['analysis', 'variance'],
                'selector': 'select_assimilation'  # 调度器方法名
            },
            {
                'name': 'risk_estimation',
                'algorithm': 'gpr-risk-estimator',
                'inputs': ['analysis', 'variance'],
                'outputs': ['risk_field']
            },
            {
                'name': 'path_planning',
                'algorithm': 'auto',
                'inputs': ['risk_field', 'waypoints'],
                'outputs': ['planned_path'],
                'selector': 'select_planning'
            },
            {
                'name': 'mpc_control',
                'algorithm': 'model-predictive-controller',
                'inputs': ['planned_path', 'risk_field'],
                'outputs': ['control_commands'],
                'loop': True  # 滚动执行
            }
        ]
    }

    def execute(self, input_data: Dict, pipeline_def: Dict = None) -> Dict:
        """执行完整管线"""
        ...
```

### 2.7 算法迁移映射表

| 原位置 | 新位置 | 类别 | 调度ID |
|--------|--------|------|--------|
| `algorithm_core/models/three_dimensional_var.py` | `assimilation-core/.../models/` | ASSIMILATION | `3d-var` |
| `algorithm_core/models/four_dimensional_var.py` | `assimilation-core/.../models/` | ASSIMILATION | `4d-var` |
| `algorithm_core/models/five_dimensional_var.py` | `assimilation-core/.../models/` | ASSIMILATION | `5d-var` |
| `algorithm_core/models/enkf.py` | `assimilation-core/.../models/` | ASSIMILATION | `enkf` |
| `algorithm_core/models/hybrid.py` | `assimilation-core/.../models/` | ASSIMILATION | `hybrid-assimilation` |
| `algorithm_core/models/enhanced_bayesian.py` | `assimilation-core/.../models/` | ASSIMILATION | `enhanced-bayesian` |
| `model-engine/cnn_corrector/` | `model-engine/cnn_corrector/` | CORRECTION | `cnn-spatial-corrector` |
| `model-engine/unet_downscaler/` | `model-engine/unet_downscaler/` | DOWNSCALING | `unet-downscaler` |
| `model-engine/unet_downscaler/probabilistic.py` | `model-engine/unet_downscaler/` | DOWNSCALING | `probabilistic-unet` |
| `model-engine/gpr_risk/` | `model-engine/gpr_risk/` | RISK_ESTIMATION | `gpr-risk-estimator` |
| `model-engine/fusion/ensemble.py` | `model-engine/fusion/` | CORRECTION | `dynamic-weight-fusion` |
| `model-engine/active_obs/` | `model-engine/active_obs/` | OBSERVATION | `bayesian-active-observer` |
| `model-engine/control/mpc.py` | `model-engine/control/` | CONTROL | `model-predictive-controller` |
| `model-engine/multi_uav/conflict_resolver.py` | `model-engine/multi_uav/` | CONTROL | `multi-uav-conflict-resolver` |
| `path-planning-service/.../vrptw*.py` | `path-planning-core/global/` | GLOBAL_PLANNING | `vrptw` |
| `path-planning-service/.../ga.py` | `path-planning-core/global/` | GLOBAL_PLANNING | `genetic-algorithm` |
| `path-planning-service/.../pso.py` | `path-planning-core/global/` | GLOBAL_PLANNING | `particle-swarm` |
| `path-planning-service/.../aco.py` | `path-planning-core/global/` | GLOBAL_PLANNING | `ant-colony` |
| `path-planning-service/.../de_rrt_star.py` | `path-planning-core/local/` | LOCAL_PLANNING | `de-rrt-star` |
| `path-planning-service/.../astar.py` | `path-planning-core/local/` | LOCAL_PLANNING | `a-star` |
| `path-planning-service/.../dwa.py` | `path-planning-core/local/` | LOCAL_PLANNING | `dwa` |
| `edge-cloud-coordinator/federated_learning.py` | `edge-coordinator/federated/` | CORRECTION | `federated-learning` |
| `edge-cloud-coordinator/edge_ai_inference.py` | `edge-coordinator/inference/` | DOWNSCALING | `edge-ai-inference` |
| `uav-edge-sdk/src/*.cpp` | `edge-coordinator/embedded/` | LOCAL_PLANNING | `edge-dwa`, `edge-astar` |

### 2.8 重复算法合并策略

| 重复算法 | 保留版本 | 处理方式 |
|----------|----------|----------|
| EnKF (algorithm_core) vs EnKF (model-engine/gpr_risk) | **两者保留** | algorithm_core版用于标准同化；model-engine版面向概率U-Net输出，接口不同 |
| GPR (model-engine) vs 风险映射 (risk_mapper.py) | **两者保留** | GPR用于不确定性量化；risk_mapper用于物理量→风险指数转换 |
| 风险感知A* (path-planning) vs GPR路径规划 (model-engine) | **合并** | 统一为 `risk_aware_astar`，通过参数切换GPR/规则风险源 |

### 2.9 实施优先级

| 阶段 | 内容 | 依赖 |
|------|------|------|
| **P0** | 创建 `algo-orchestration/` 骨架：registry + adapter + scheduler | 无 |
| **P1** | 迁移 assimilation-core，注册所有同化算法（含5D-VAR） | P0 |
| **P2** | 迁移 model-engine，注册AI模型 | P0 |
| **P3** | 实现标准管线编排（数据融合→订正→降尺度→同化→风险→规划） | P1+P2 |
| **P4** | 迁移 path-planning-core，注册规划算法 | P0 |
| **P5** | 迁移 edge-coordinator，注册边缘算法 | P0 |
| **P6** | 实现智能调度（自动算法选择 + A/B测试） | P3+P4 |
| **P7** | 性能优化（算法缓存、并行执行、资源隔离） | P6 |

### 2.10 关键设计原则

1. **延迟实例化**：算法在首次 execute() 时才创建实例，避免启动开销
2. **接口统一**：所有算法通过 `BaseAlgorithmAdapter.execute(input) → AlgorithmResult` 统一调用
3. **可观测性**：每次执行记录耗时、质量评分、资源消耗，用于调度优化
4. **版本共存**：同一算法多个版本可同时注册（如 `3d-var-v1`, `3d-var-v2`），支持A/B测试
5. **资源感知**：调度器根据GPU可用性、时间预算、网格大小自动选择合适算法
6. **渐进迁移**：旧代码通过 adapter 包装后可直接注册，无需重写
