# 贝叶斯数据同化平台文档

欢迎访问贝叶斯数据同化平台文档。本文档集提供了平台的完整说明。

## 文档导航

| 文档 | 说明 |
|------|------|
| [架构说明](architecture.md) | 系统架构、模块划分与技术选型 |
| [开发指南](development.md) | 本地开发环境搭建与编码规范 |
| [API 参考](api.md) | 算法核心 REST API 接口说明 |
| [教程](tutorials.md) | 从入门到高级的使用教程 |
| [无人机集成](uav_integration.md) | 与无人机路径规划系统的集成方案 |

## 平台概述

本平台实现了一套完整的贝叶斯数据同化系统，主要功能包括：

- **多算法同化**：支持 3D-VAR、4D-VAR、EnKF 及混合同化算法
- **多源数据融合**：卫星、雷达、地面站等多源观测数据融合
- **并行计算**：支持 Dask、MPI、Ray 等多种并行框架
- **硬件加速**：支持 CPU、GPU(CUDA)、JAX 加速
- **质量管控**：数据质量控制与风险评估
- **可视化**：同化结果可视化与仪表盘

## 快速链接

- [算法核心库文档](../algorithm_core/README.md)
- [Docker 部署指南](../algorithm_core/docker/README.md)
- [项目主 README](../../README.md)
- [共享协议定义](../shared/protos/README.md)
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
