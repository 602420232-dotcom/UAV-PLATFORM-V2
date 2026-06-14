# 模型量化评估报告

> 生成时间: 2026-06-13 23:51:03 UTC

---

## 1. 量化概览

| 模型名称 | 描述 | 参数量 | 原始大小 (MB) | INT8 大小 (MB) | FP16 大小 (MB) | INT8 压缩比 | FP16 压缩比 |
|:---------|:-----|-------:|-------------:|--------------:|--------------:|-----------:|-----------:|
| PathPlanner-CNN | 路径规划卷积神经网络 | 32,768 | 0.12 | 0.03 | 0.06 | 4.00x | 2.00x |
| RiskEstimator-LSTM | 风险评估LSTM循环网络 | 131,072 | 0.50 | 0.12 | 0.25 | 4.00x | 2.00x |
| WeatherPredictor-UNet | 气象预测U-Net网络 | 524,288 | 2.00 | 0.50 | 1.00 | 4.00x | 2.00x |
| ObstacleDetector-YOLO | 障碍物检测YOLO模型 | 2,097,152 | 8.00 | 2.00 | 4.00 | 4.00x | 2.00x |
| DecisionAgent-PPO | 决策智能体PPO强化学习模型 | 8,192 | 0.03 | 0.01 | 0.02 | 4.00x | 2.00x |

## 2. 推理延迟对比

| 模型名称 | FP32 延迟 (ms) | INT8 延迟 (ms) | FP16 延迟 (ms) | INT8 延迟降低 | FP16 延迟降低 |
|:---------|-------------:|-------------:|-------------:|-----------:|-----------:|
| PathPlanner-CNN | 0.062 | 0.021 | 0.032 | 60.4% | 43.9% |
| RiskEstimator-LSTM | 0.067 | 0.023 | 0.037 | 71.6% | 50.7% |
| WeatherPredictor-UNet | 0.109 | 0.045 | 0.050 | 60.5% | 62.4% |
| ObstacleDetector-YOLO | 0.237 | 0.073 | 0.111 | 71.7% | 62.2% |
| DecisionAgent-PPO | 0.065 | 0.001 | 0.002 | 98.7% | 96.1% |

## 3. 精度损失评估

| 模型名称 | INT8 RMSE | INT8 MAE | INT8 Cosine Sim | FP16 RMSE | FP16 MAE | FP16 Cosine Sim |
|:---------|----------:|---------:|---------------:|----------:|---------:|---------------:|
| PathPlanner-CNN | 0.001272 | 0.001102 | 0.999948 | 0.000026 | 0.000018 | 1.000000 |
| RiskEstimator-LSTM | 0.000899 | 0.000778 | 0.999948 | 0.000018 | 0.000012 | 1.000000 |
| WeatherPredictor-UNet | 0.000686 | 0.000594 | 0.999939 | 0.000013 | 0.000009 | 1.000000 |
| ObstacleDetector-YOLO | 0.000485 | 0.000420 | 0.999939 | 0.000009 | 0.000006 | 0.999999 |
| DecisionAgent-PPO | 0.001591 | 0.001382 | 0.999960 | 0.000038 | 0.000025 | 1.000000 |

## 4. 量化感知训练 (QAT) 效果

| 模型名称 | INT8 QAT 恢复率 | FP16 QAT 恢复率 | QAT 轮数 |
|:---------|---------------:|---------------:|--------:|
| PathPlanner-CNN | 0.0000 | 0.0000 | 10 |
| RiskEstimator-LSTM | 0.0000 | 0.0000 | 10 |
| WeatherPredictor-UNet | 0.0000 | 0.0000 | 10 |
| ObstacleDetector-YOLO | 0.0000 | 0.0000 | 10 |
| DecisionAgent-PPO | 0.0000 | 0.0000 | 10 |

## 5. 综合推荐

- **PathPlanner-CNN**: 推荐 **INT8** (高压缩比，精度损失可忽略)
- **RiskEstimator-LSTM**: 推荐 **INT8** (高压缩比，精度损失可忽略)
- **WeatherPredictor-UNet**: 推荐 **INT8** (高压缩比，精度损失可忽略)
- **ObstacleDetector-YOLO**: 推荐 **INT8** (高压缩比，精度损失可忽略)
- **DecisionAgent-PPO**: 推荐 **INT8** (高压缩比，精度损失可忽略)

## 6. 详细量化报告

### PathPlanner-CNN

**描述**: 路径规划卷积神经网络
**参数量**: 32,768
**权重形状**: (256, 128)

#### INT8 量化

```json
{
  "model_name": "PathPlanner-CNN",
  "quantization_type": "int8",
  "original_size_bytes": 131072,
  "quantized_size_bytes": 32768,
  "compression_ratio": 4.0,
  "original_latency_ms": 0.053,
  "quantized_latency_ms": 0.021,
  "latency_reduction_pct": 60.38,
  "mse": 2e-06,
  "rmse": 0.001272,
  "max_absolute_error": 0.002204,
  "mean_absolute_error": 0.001102,
  "qat_applied": true,
  "qat_epochs": 10,
  "qat_accuracy_recovery": 0.0
}
```

#### FP16 量化

```json
{
  "model_name": "PathPlanner-CNN",
  "quantization_type": "fp16",
  "original_size_bytes": 131072,
  "quantized_size_bytes": 65536,
  "compression_ratio": 2.0,
  "original_latency_ms": 0.057,
  "quantized_latency_ms": 0.032,
  "latency_reduction_pct": 43.86,
  "mse": 0.0,
  "rmse": 2.6e-05,
  "max_absolute_error": 0.000173,
  "mean_absolute_error": 1.8e-05,
  "qat_applied": true,
  "qat_epochs": 10,
  "qat_accuracy_recovery": 0.0
}
```

### RiskEstimator-LSTM

**描述**: 风险评估LSTM循环网络
**参数量**: 131,072
**权重形状**: (512, 256)

#### INT8 量化

```json
{
  "model_name": "RiskEstimator-LSTM",
  "quantization_type": "int8",
  "original_size_bytes": 524288,
  "quantized_size_bytes": 131072,
  "compression_ratio": 4.0,
  "original_latency_ms": 0.081,
  "quantized_latency_ms": 0.023,
  "latency_reduction_pct": 71.6,
  "mse": 1e-06,
  "rmse": 0.000899,
  "max_absolute_error": 0.001559,
  "mean_absolute_error": 0.000778,
  "qat_applied": true,
  "qat_epochs": 10,
  "qat_accuracy_recovery": 0.0
}
```

#### FP16 量化

```json
{
  "model_name": "RiskEstimator-LSTM",
  "quantization_type": "fp16",
  "original_size_bytes": 524288,
  "quantized_size_bytes": 262144,
  "compression_ratio": 2.0,
  "original_latency_ms": 0.075,
  "quantized_latency_ms": 0.037,
  "latency_reduction_pct": 50.67,
  "mse": 0.0,
  "rmse": 1.8e-05,
  "max_absolute_error": 0.000122,
  "mean_absolute_error": 1.2e-05,
  "qat_applied": true,
  "qat_epochs": 10,
  "qat_accuracy_recovery": 0.0
}
```

### WeatherPredictor-UNet

**描述**: 气象预测U-Net网络
**参数量**: 524,288
**权重形状**: (1024, 512)

#### INT8 量化

```json
{
  "model_name": "WeatherPredictor-UNet",
  "quantization_type": "int8",
  "original_size_bytes": 2097152,
  "quantized_size_bytes": 524288,
  "compression_ratio": 4.0,
  "original_latency_ms": 0.114,
  "quantized_latency_ms": 0.045,
  "latency_reduction_pct": 60.53,
  "mse": 0.0,
  "rmse": 0.000686,
  "max_absolute_error": 0.001188,
  "mean_absolute_error": 0.000594,
  "qat_applied": true,
  "qat_epochs": 10,
  "qat_accuracy_recovery": 0.0
}
```

#### FP16 量化

```json
{
  "model_name": "WeatherPredictor-UNet",
  "quantization_type": "fp16",
  "original_size_bytes": 2097152,
  "quantized_size_bytes": 1048576,
  "compression_ratio": 2.0,
  "original_latency_ms": 0.133,
  "quantized_latency_ms": 0.05,
  "latency_reduction_pct": 62.41,
  "mse": 0.0,
  "rmse": 1.3e-05,
  "max_absolute_error": 0.00012,
  "mean_absolute_error": 9e-06,
  "qat_applied": true,
  "qat_epochs": 10,
  "qat_accuracy_recovery": 0.0
}
```

### ObstacleDetector-YOLO

**描述**: 障碍物检测YOLO模型
**参数量**: 2,097,152
**权重形状**: (2048, 1024)

#### INT8 量化

```json
{
  "model_name": "ObstacleDetector-YOLO",
  "quantization_type": "int8",
  "original_size_bytes": 8388608,
  "quantized_size_bytes": 2097152,
  "compression_ratio": 4.0,
  "original_latency_ms": 0.258,
  "quantized_latency_ms": 0.073,
  "latency_reduction_pct": 71.71,
  "mse": 0.0,
  "rmse": 0.000485,
  "max_absolute_error": 0.00084,
  "mean_absolute_error": 0.00042,
  "qat_applied": true,
  "qat_epochs": 10,
  "qat_accuracy_recovery": 0.0
}
```

#### FP16 量化

```json
{
  "model_name": "ObstacleDetector-YOLO",
  "quantization_type": "fp16",
  "original_size_bytes": 8388608,
  "quantized_size_bytes": 4194304,
  "compression_ratio": 2.0,
  "original_latency_ms": 0.294,
  "quantized_latency_ms": 0.111,
  "latency_reduction_pct": 62.24,
  "mse": 0.0,
  "rmse": 9e-06,
  "max_absolute_error": 6.1e-05,
  "mean_absolute_error": 6e-06,
  "qat_applied": true,
  "qat_epochs": 10,
  "qat_accuracy_recovery": 0.0
}
```

### DecisionAgent-PPO

**描述**: 决策智能体PPO强化学习模型
**参数量**: 8,192
**权重形状**: (128, 64)

#### INT8 量化

```json
{
  "model_name": "DecisionAgent-PPO",
  "quantization_type": "int8",
  "original_size_bytes": 32768,
  "quantized_size_bytes": 8192,
  "compression_ratio": 4.0,
  "original_latency_ms": 0.075,
  "quantized_latency_ms": 0.001,
  "latency_reduction_pct": 98.67,
  "mse": 3e-06,
  "rmse": 0.001591,
  "max_absolute_error": 0.002732,
  "mean_absolute_error": 0.001382,
  "qat_applied": true,
  "qat_epochs": 10,
  "qat_accuracy_recovery": 0.0
}
```

#### FP16 量化

```json
{
  "model_name": "DecisionAgent-PPO",
  "quantization_type": "fp16",
  "original_size_bytes": 32768,
  "quantized_size_bytes": 16384,
  "compression_ratio": 2.0,
  "original_latency_ms": 0.051,
  "quantized_latency_ms": 0.002,
  "latency_reduction_pct": 96.08,
  "mse": 0.0,
  "rmse": 3.8e-05,
  "max_absolute_error": 0.000243,
  "mean_absolute_error": 2.5e-05,
  "qat_applied": true,
  "qat_epochs": 10,
  "qat_accuracy_recovery": 0.0
}
```

---

*报告由 model-quantization-report.py 自动生成*