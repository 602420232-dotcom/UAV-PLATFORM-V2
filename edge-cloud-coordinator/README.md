# 边云协同计算框架

## 概述

边云协同计算框架（edge-cloud-coordinator）实现无人机与云端之间的分布式智能计算，支持任务编排、实时流处理、联邦学习、WebSocket同步和AI推理。

## 模块说明

| 模块 | 文件 | 说明 |
|------|------|------|
| 边云协调器 | [coordinator.py](coordinator.py) | 任务编排、云端/边缘分流、增量学习 |
| 实时流处理 | [realtime_stream.py](realtime_stream.py) | Kafka/RabbitMQ流处理、秒级风险评估 |
| 边缘AI推理 | [edge_ai_inference.py](edge_ai_inference.py) | TensorRT/ONNX INT8量化、推理基准 |
| 联邦学习 | [federated_learning.py](federated_learning.py) | FedAvg/FedProx多无人机协同学习 |
| WebSocket同步 | [websocket_sync.py](websocket_sync.py) | 实时双向状态同步 |
| 安全增强 | [security.py](security.py) | mTLS服务间通信、JWT认证、数据加密 |
| 知识图谱 | [knowledge_graph.py](knowledge_graph.py) | 气象+路径知识图谱推理 |
| AI决策 | [ai_decision.py](ai_decision.py) | LLM辅助决策、智能问答 |
| V2X协同 | [v2x_cooperative.py](v2x_cooperative.py) | 协同感知、蜂群共识 |
| 气象采集 | [uav_weather_collector.py](uav_weather_collector.py) | 多源气象数据采集 |
| 流处理器 | [stream_processor.py](stream_processor.py) | Flink SQL作业管理 |

## 架构

```
云端 ──────────────┬──────────────┐
                  │              │
          全局路径规划        批量计算
                  │              │
    ┌─────────────┴──────────────┘
    │  WebSocket 实时同步
    │  Kafka/RabbitMQ 流处理
    │  mTLS 安全通道
    ▼
边缘 ──────────────┬──────────────┐
                  │              │
          实时避障        传感器融合
                  │              │
          联邦学习         INT8推理
```

## 数据流

```
气象传感器 → Kafka(weather-raw) → Flink流处理 → 风险评估 → 动态路径调整
                                              ↓
                                         告警通知
```

## 快速开始

```bash
pip install kafka-python websockets pika  # 可选中间件
python -m edge-cloud-coordinator.coordinator
```


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
