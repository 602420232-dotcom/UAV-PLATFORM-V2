# 贝叶斯同化方差场与LSTM+XGBoost订正模型集成文档

## 概述

本文档说明了贝叶斯同化方差场模块和LSTM+XGBoost订正模型的集成工作,包括API接口、前端集成、训练流程优化等内容。

## 1. 贝叶斯同化方差场模块

### 1.1 功能特性

方差场优化器模块提供了以下功能:

- **参数优化**: 自动优化背景误差尺度、观测误差尺度和相关长度尺度
- **交叉验证**: 支持K折交叉验证以提高参数泛化能力
- **自适应调整**: 根据同化质量动态调整方差参数
- **稀疏矩阵支持**: 高效处理大网格数据
- **并行计算**: 支持多线程加速计算

### 1.2 API接口

#### 计算方差场

```
POST /api/v1/variance/compute
```

**请求参数**:

```json
{
  "background": [[...]],          // 背景场数据 (2D或3D数组)
  "observations": [...],          // 观测数据
  "obs_locations": [[x, y, z],], // 观测位置
  "use_adaptive": false,          // 是否使用自适应方差场
  "use_cv": false,               // 是否使用交叉验证
  "n_folds": 5,                  // 交叉验证折数
  "method": "L-BFGS-B",          // 优化方法
  "verbose": 0                   // 输出详细程度
}
```

**响应**:

```json
{
  "status": "success",
  "variance_field": [[...]],
  "best_params": {
    "background_error_scale": 1.5,
    "observation_error_scale": 0.1,
    "correlation_length_scale": 10.0
  },
  "best_score": 0.001234,
  "optimization_history": [...]
}
```

#### 获取方差矩阵

```
POST /api/v1/variance/variance-matrix
```

**请求参数**:

```json
{
  "shape": [20, 20, 5],  // 网格形状 [nx, ny, nz]
  "config": {...}        // 可选配置
}
```

#### 自适应方差场调整

```
POST /api/v1/variance/adaptive
```

**请求参数**:

```json
{
  "analysis": [[...]],           // 分析场
  "background": [[...]],         // 背景场
  "observations": [...],         // 观测数据
  "obs_locations": [[x, y, z]], // 观测位置
  "adaptation_rate": 0.1         // 可选: 自适应率
}
```

#### 参数管理

```
GET /api/v1/variance/params    // 获取当前参数
POST /api/v1/variance/params   // 设置参数
POST /api/v1/variance/reset     // 重置优化器
GET /api/v1/variance/status     // 获取服务状态
```

### 1.3 前端集成

前端组件位于 `WeatherView.vue`,提供了以下功能:

1. **参数显示**: 实时显示当前方差场参数
2. **计算触发**: 一键计算方差场
3. **可视化**: 热力图展示方差场分布
4. **优化历史**: 显示参数优化过程
5. **配置管理**: 调整优化配置

**使用示例**:

```javascript
import { computeVariance, getVarianceParams } from '@/api/variance'

// 获取参数
const params = await getVarianceParams()
console.log(params.current_params)

// 计算方差场
const result = await computeVariance({
  background: backgroundData,
  observations: observationData,
  obs_locations: locationData,
  use_cv: true,
  n_folds: 5
})
console.log(result.variance_field)
```

### 1.4 算法说明

#### 目标函数

方差场优化的目标是最小化以下代价函数:

$$
J(x) = (x - x_b)^T B^{-1} (x - x_b) + (y - Hx)^T R^{-1} (y - Hx)
$$

其中:
- $x_b$: 背景场
- $B$: 背景误差协方差矩阵
- $y$: 观测数据
- $H$: 观测算子
- $R$: 观测误差协方差矩阵

#### 自适应机制

AdaptiveVarianceField根据同化质量动态调整方差参数:

- 如果改进比 < 0.85: 增加背景误差尺度
- 如果改进比 > 1.2: 减少背景误差尺度

## 2. LSTM+XGBoost订正模型

### 2.1 功能特性

增强版气象预测与订正模型提供了以下改进:

- **数据预处理**: 支持MinMax、Standard和Robust三种缩放方式
- **训练监控**: 实时监控训练指标,早停机制
- **超参数调优**: 自动搜索最佳超参数配置
- **模型版本管理**: 自动保存模型版本和元数据
- **缓存机制**: 避免重复计算
- **错误处理**: 完善的异常捕获和日志记录

### 2.2 核心组件

#### ModelConfig

模型配置类,包含所有可配置参数:

```python
@dataclass
class ModelConfig:
    look_back: int = 24                    # 回看窗口
    lstm_units: List[int] = [50, 50]      # LSTM层单元数
    dropout_rate: float = 0.2             # Dropout率
    dense_units: int = 25                  # 全连接层单元数
    xgb_n_estimators: int = 100           # XGBoost树数量
    xgb_learning_rate: float = 0.1        # XGBoost学习率
    xgb_max_depth: int = 5                # XGBoost最大深度
    batch_size: int = 32                  # 批次大小
    epochs: int = 50                       # 训练轮数
    validation_split: float = 0.2          # 验证集比例
    early_stopping_patience: int = 10      # 早停耐心值
    reduce_lr_patience: int = 5           # 学习率降低耐心值
    reduce_lr_factor: float = 0.5          # 学习率降低因子
    min_lr: float = 1e-6                  # 最小学习率
    scaler_type: ScalerType = ScalerType.MINMAX  # 缩放器类型
```

#### DataPreprocessor

数据预处理器,负责数据标准化:

```python
class DataPreprocessor:
    def __init__(self, scaler_type: ScalerType = ScalerType.MINMAX)
    def fit_transform(self, data: np.ndarray) -> np.ndarray
    def transform(self, data: np.ndarray) -> np.ndarray
    def inverse_transform(self, data: np.ndarray) -> np.ndarray
```

#### TrainingMonitor

训练监控器,跟踪训练过程:

```python
class TrainingMonitor:
    def start_training()
    def record_epoch(epoch, train_loss, val_loss, train_mae, val_mae, lr)
    def get_best_epoch() -> int
    def get_best_loss() -> float
    def should_stop_early(patience: int) -> bool
```

### 2.3 训练流程

#### 基础训练

```python
from meteor_forecast_enhanced import MeteorForecast, ModelConfig

# 创建模型
model = MeteorForecast(
    model_path='./models',
    config=ModelConfig(
        look_back=24,
        lstm_units=[50, 50],
        batch_size=32
    )
)

# 准备数据
data = [...]  # 时间序列数据
result = model.self_improve(
    new_data=data,
    epochs=20,
    batch_size=32
)

print(f"训练成功, RMSE: {result['rmse']:.4f}")
```

#### 超参数调优

```python
# 执行超参数搜索
tune_result = model.tune_hyperparameters(
    training_data=data,
    n_configs=10  # 测试10种配置
)

print(f"最佳配置: {tune_result['best_config']}")
print(f"最佳验证分数: {tune_result['best_score']:.6f}")
```

#### 模型预测

```python
# 单步预测
predictions = model.predict(input_data)

# 误差订正
corrected_data = model.correct(
    forecast_data=forecast,
    observed_data=observed
)

# 融合预测
fused_predictions = model.fusion_forecast(input_data)
```

### 2.4 训练监控

#### TensorBoard集成

模型训练支持TensorBoard日志:

```python
from tensorflow.keras.callbacks import TensorBoard

tb_callback = TensorBoard(
    log_dir='./logs',
    histogram_freq=1,
    write_graph=True
)

model.train_lstm(
    X_train, y_train,
    X_val, y_val,
    callbacks=[tb_callback]
)
```

#### 自定义回调

```python
class CustomCallback(Callback):
    def on_epoch_end(self, epoch, logs=None):
        print(f"Epoch {epoch}: loss={logs['loss']:.4f}")
```

### 2.5 模型持久化

#### 模型保存

```python
# 保存模型(自动保存版本)
model._save_model('lstm')
model._save_model('xgb')

# 保存元数据
model._save_metadata()
```

#### 模型加载

```python
# 自动加载最新模型
model = MeteorForecast(model_path='./models')

# 检查模型版本
print(f"当前模型版本: {model.model_version}")
```

#### 模型版本文件

```
models/
├── lstm_model_20240115_143022.h5
├── lstm_model.h5                    # 最新版本
├── xgb_model_20240115_143022.json
├── xgb_model.json                   # 最新版本
├── metadata_20240115_143022.json    # 版本元数据
└── ...
```

## 3. 单元测试

### 3.1 方差场模块测试

运行测试:

```bash
cd data-assimilation-platform/service_python
pytest tests/test_variance_field.py -v
```

测试覆盖:

- 优化器初始化
- 参数优化
- 方差场生成
- 稀疏矩阵操作
- 自适应调整
- 边界情况处理

### 3.2 LSTM+XGBoost模型测试

运行测试:

```bash
cd meteor-forecast-service
pytest tests/test_meteor_forecast_enhanced.py -v
```

测试覆盖:

- 数据预处理
- 训练监控
- 模型配置
- 预测功能
- 订正功能
- 模型保存加载
- 风险热力图生成
- 边界情况处理

## 4. 性能优化

### 4.1 方差场计算优化

1. **稀疏矩阵**: 使用CSR格式减少内存占用
2. **并行计算**: 多线程加速目标函数评估
3. **早停机制**: 避免不必要的迭代

### 4.2 模型训练优化

1. **批次处理**: 使用合适的批次大小
2. **早停**: 监控验证损失,防止过拟合
3. **学习率调度**: ReduceLROnPlateau回调
4. **GPU加速**: TensorFlow自动使用GPU

### 4.3 缓存策略

- **预测缓存**: 避免重复计算
- **融合缓存**: 多预报引擎结果缓存
- **风险热力图缓存**: 可视化结果缓存

## 5. 使用示例

### 5.1 完整工作流

```python
from meteor_forecast_enhanced import MeteorForecast, ModelConfig
import numpy as np

# 1. 初始化模型
config = ModelConfig(
    look_back=48,
    lstm_units=[100, 100],
    dropout_rate=0.3,
    batch_size=64
)
model = MeteorForecast(model_path='./models', config=config)

# 2. 准备训练数据
data = np.random.randn(1000) * 10 + 20

# 3. 超参数调优(可选)
tune_result = model.tune_hyperparameters(data, n_configs=5)

# 4. 训练模型
train_result = model.self_improve(
    new_data=data,
    epochs=50,
    batch_size=64
)

# 5. 评估模型
eval_result = model.evaluate(X_val, y_val)
print(f"验证RMSE: {eval_result['rmse']:.4f}")

# 6. 进行预测
predictions = model.predict(new_data[:100])

# 7. 误差订正
corrected = model.correct(
    forecast_data=predictions,
    observed_data=actual_values
)
```

### 5.2 方差场计算工作流

```python
import numpy as np
from bayesian_assimilation.models.variance_field_optimizer import VarianceFieldOptimizer

# 1. 初始化优化器
optimizer = VarianceFieldOptimizer(use_sparse=True)
optimizer.set_parallel_jobs(4)

# 2. 准备数据
nx, ny, nz = 20, 20, 5
background = np.random.rand(nx, ny, nz) * 10

# 生成观测数据
obs_count = 30
obs_locations = np.random.rand(obs_count, 3) * [nx, ny, nz]
observations = np.array([
    background[
        int(loc[0]) % nx,
        int(loc[1]) % ny,
        int(loc[2]) % nz
    ] + np.random.normal(0, 0.1)
    for loc in obs_locations
])

# 3. 优化参数
result = optimizer.optimize(
    background=background,
    observations=observations,
    obs_locations=obs_locations,
    method='L-BFGS-B',
    verbose=1
)

# 4. 获取优化结果
print(f"最佳分数: {result['best_score']:.6f}")
print(f"最佳参数: {result['best_params']}")

# 5. 生成方差场
variance_field = optimizer.get_variance_field((nx, ny, nz))
print(f"方差场范围: [{variance_field.min():.4f}, {variance_field.max():.4f}]")

# 6. 使用自适应调整(可选)
adaptive = AdaptiveVarianceField()
adaptive.adapt(
    analysis=background + np.random.randn(*background.shape) * 0.5,
    background=background,
    observations=observations,
    obs_locations=obs_locations
)
print(f"自适应后背景误差尺度: {adaptive.background_error_scale:.4f}")
```

## 6. 注意事项

### 6.1 数据要求

- 时间序列数据长度应大于 `look_back * 2`
- 观测位置应在网格范围内
- 数据应包含足够的变异性以支持模型学习

### 6.2 参数选择

- `look_back`: 通常取24-48(1-2天的数据)
- `lstm_units`: 根据数据复杂度调整
- `dropout_rate`: 0.1-0.3防止过拟合
- `batch_size`: 根据GPU内存调整

### 6.3 故障排除

1. **模型加载失败**: 检查模型文件是否存在
2. **训练收敛慢**: 调整学习率或增加训练轮数
3. **预测结果异常**: 检查数据预处理是否正确
4. **内存不足**: 减小网格大小或批次大小

## 7. 更新日志

### v2.0 (2024-01)

- 增强版模型架构
- 超参数自动调优
- 训练监控系统
- 模型版本管理
- 完善的单元测试

### v1.0 (初始版本)

- 基础LSTM+XGBoost预测
- 基本订正功能
- 融合预报支持

## 8. 联系方式

如有问题,请联系开发团队或提交Issue。
