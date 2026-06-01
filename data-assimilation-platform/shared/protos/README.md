# Protocol Buffers 版本管理策略

## 目录结构
- `common/v1/` - 基础类型（永久冻结，向后兼容）
- `request/v1/`, `response/v1/` - 当前稳定版本
- `request/v2/`, `response/v2/` - 开发中版本

## 版本规则

1. common/v1 永不修改，确保所有版本兼容
2. v1 只能新增 optional 字段，不能删除或修改现有字段
3. v2 可以重构，但需通过 import common/v1 复用基础类型
4. 服务升级时，同时支持 v1 和 v2 至少 3 个月
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
