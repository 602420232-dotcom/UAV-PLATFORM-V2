# 部署配置

## 目录说明

```
deployments/
├── kubernetes/          # Kubernetes 部署配置
│   ├── namespace.yml    # 命名空间
│   ├── secrets.yml      # 敏感信息
│   ├── configmap.yml    # 配置映射
│   ├── *.yml            # 各服务部署配置
│   └── ingress.yml      # 入口配置
├── database/            # 数据库相关
│   └── optimize.sql     # 数据库优化脚本
└── monitoring/          # 监控配置
    ├── prometheus-config.yml  # Prometheus 配置
    └── alert-rules.yml        # 告警规则
```

## 使用

```bash
# Kubernetes 部署
kubectl apply -f kubernetes/namespace.yml
kubectl apply -f kubernetes/
```


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
