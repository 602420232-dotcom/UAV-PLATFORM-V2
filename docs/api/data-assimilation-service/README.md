# data-assimilation-service

本目录包含数据同化服务（Data Assimilation Service）的 API 文档。数据同化服务负责将多源气象观测数据（如 UAV 采集数据、卫星数据、地面站数据等）与数值天气预报模型（如 WRF）进行融合，生成高精度的初始场和分析场，为后续气象预报和路径规划提供可靠的数据基础。

| 文件 | 描述 |
|------|------|
| [assimilation.md](assimilation.md) | 数据同化服务 API 接口文档，包含同化任务创建、执行状态查询、同化结果获取等接口定义 |

---
> **最后更新**: 2026-06-01  
> **版本**: 1.0  
> **维护者**: DITHIOTHREITOL
