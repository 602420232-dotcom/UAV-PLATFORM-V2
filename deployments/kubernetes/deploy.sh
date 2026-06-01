#!/bin/bash

# Kubernetes部署脚本
# 用于将无人机路径规划系统部署到生产环境

set -e

echo "=== 开始部署无人机路径规划系统 ==="

# 创建命名空间
echo "1. 创建命名空间..."
kubectl apply -f namespace.yml

# 创建Secret
echo "2. 创建Secret..."
kubectl apply -f secrets.yml

# 创建持久卷声明
echo "3. 创建持久卷声明..."
kubectl apply -f persistent-volumes.yml

# 部署数据库服务
echo "4. 部署数据库服务..."
kubectl apply -f database-services.yml

# 部署后端服务
echo "5. 部署WRF处理服务..."
kubectl apply -f wrf-processor-service.yml

echo "6. 部署气象预测服务..."
kubectl apply -f meteor-forecast-service.yml

echo "7. 部署路径规划服务..."
kubectl apply -f path-planning-service.yml

echo "8. 部署平台服务..."
kubectl apply -f uav-platform-service.yml

# 部署前端服务
echo "9. 部署前端服务..."
kubectl apply -f frontend-vue.yml

# 部署自动扩展配置
echo "10. 部署自动扩展配置..."
kubectl apply -f autoscaling.yml

echo "=== 部署完成 ==="
echo "查看部署状态: kubectl get all -n uav-path-planning"
echo "查看服务日志: kubectl logs -n uav-path-planning <pod-name>"
echo "查看自动扩展状态: kubectl get hpa -n uav-path-planning"
