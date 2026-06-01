# UAV Path Planning System - 无人机路径规划系统

## 📋 项目概述

基于 WRF 气象驱动的无人机 VRP（车辆路径问题）智能路径规划系统。

**核心特性**:
- 🌦️ **气象驱动**: 集成 WRF 气象模型，实时获取风场、温度、降水等数据
- 🛤️ **智能规划**: 融合 VRPTW、DE-RRT*、DWA 等算法
- ☁️ **数据同化**: 贝叶斯数据同化技术，融合多源气象观测
- 📊 **实时监控**: 可视化监控无人机状态和任务进度
- 🔄 **联邦学习**: Edge-Cloud 协同，支持端侧离线路径规划

**技术栈**:
- **前端**: Vue 3 + Vite + Element Plus
- **后端**: Spring Boot 3.2 + Java 17
- **数据库**: MySQL 8.0 + Redis
- **算法**: Python 3.8+ (NumPy, SciPy, TensorFlow)
- **容器**: Docker + Kubernetes
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
