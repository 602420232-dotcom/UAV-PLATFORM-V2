#!/bin/bash

# Kubernetes部署脚本
# 用于将无人机路径规划系统部署到生产环境

set -e

echo "=== 开始部署无人机路径规划系统 ==="

# 创建命名空间
echo "1. 创建命名空间..."
kubectl apply -f namespace.yml

# 创建ConfigMap (必须在其他资源之前创建)
echo "2. 创建ConfigMap..."
kubectl apply -f configmap.yml

# 创建Secret
echo "3. 创建Secret..."
if [ -f secrets.yml ]; then
    kubectl apply -f secrets.yml
else
    echo "警告: 未找到 secrets.yml 文件，请先从 secrets.example.yml 复制并配置!"
    exit 1
fi

# 创建持久卷声明
echo "4. 创建持久卷声明..."
kubectl apply -f persistent-volumes.yml

# 部署数据库服务
echo "5. 部署数据库服务..."
kubectl apply -f database-services.yml

# 部署后端服务
echo "6. 部署数据同化服务..."
kubectl apply -f data-assimilation-service.yml

echo "7. 部署WRF处理服务..."
kubectl apply -f wrf-processor-service.yml

echo "8. 部署气象预测服务..."
kubectl apply -f meteor-forecast-service.yml

echo "9. 部署路径规划服务..."
kubectl apply -f path-planning-service.yml

echo "10. 部署平台服务..."
kubectl apply -f uav-platform-service.yml

echo "11. 部署天气采集服务..."
kubectl apply -f uav-weather-collector.yml

echo "12. 部署FengWu服务..."
kubectl apply -f fengwu-service.yml

echo "13. 部署边云协同服务..."
kubectl apply -f edge-cloud-coordinator.yml

# 部署前端服务
echo "14. 部署前端服务..."
kubectl apply -f frontend-vue.yml

echo "15. 部署API网关..."
kubectl apply -f api-gateway.yml

# 部署自动扩展配置
echo "16. 部署自动扩展配置..."
if [ -f hpa.yml ]; then
    kubectl apply -f hpa.yml
elif [ -f autoscaling.yml ]; then
    kubectl apply -f autoscaling.yml
fi

echo "17. 部署Ingress..."
kubectl apply -f nginx-ingress.yml

echo "18. 部署监控 Secrets..."
if [ -f monitoring-secrets.yml ]; then
    kubectl apply -f monitoring-secrets.yml
fi

echo "19. 部署监控..."
if [ -f monitoring.yml ]; then
    kubectl apply -f monitoring.yml
fi

echo "=== 部署完成 ==="
echo "查看部署状态: kubectl get all -n uav-platform"
echo "查看服务日志: kubectl logs -n uav-platform <pod-name>"
echo "查看自动扩展状态: kubectl get hpa -n uav-platform"
echo "验证ConfigMap: kubectl describe configmap uav-platform-config -n uav-platform"

