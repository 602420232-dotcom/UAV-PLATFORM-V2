# 公共类型定义

## 目录

`common/v1/` 目录包含所有 Protocol Buffers 服务的共享基础类型定义。

## 内容

| 文件 | 说明 |
|------|------|
| `types.proto` | 基础数据类型（时间、位置等） |
| `geometry.proto` | 几何类型（点、矩形、多边形等） |
| `metadata.proto` | 元数据定义 |
| `variance_field.proto` | 方差场数据结构 |

## 版本规则

- `common/v1/` 永久冻结，向后兼容
- 所有版本的 service 都引用此目录的类型
- 如需新增字段，必须标记为 `optional`
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
