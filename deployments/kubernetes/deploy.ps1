# Kubernetes部署脚本 (PowerShell版本)
# 用于将无人机路径规划系统部署到生产环境

param(
    [switch]$SkipPreChecks
)

$ErrorActionPreference = "Stop"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "UAV平台K8s部署脚本" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# 前置检查
if (-not $SkipPreChecks) {
    Write-Host "执行前置检查..." -ForegroundColor Yellow
    
    # 检查kubectl是否可用
    try {
        $kubectlVersion = kubectl version --client -o json 2>$null | ConvertFrom-Json
        Write-Host "✓ kubectl 已安装: $($kubectlVersion.clientVersion.gitVersion)" -ForegroundColor Green
    } catch {
        Write-Host "✗ kubectl 未安装或不可用，请先安装 kubectl" -ForegroundColor Red
        exit 1
    }
    
    # 检查是否可以连接集群
    try {
        kubectl cluster-info 2>$null | Out-Null
        Write-Host "✓ 可以连接K8s集群" -ForegroundColor Green
    } catch {
        Write-Host "✗ 无法连接K8s集群，请检查配置" -ForegroundColor Red
        Write-Host "  提示: 对于本地开发，可以使用 Docker Desktop + kind/minikube" -ForegroundColor Gray
        exit 1
    }
    
    Write-Host ""
}

# 1. 创建命名空间
Write-Host "[1/10] 创建命名空间..." -ForegroundColor Yellow
kubectl apply -f namespace.yml
if ($LASTEXITCODE -eq 0) { Write-Host "✓ 命名空间创建成功" -ForegroundColor Green }

# 2. 创建ConfigMap
Write-Host "[2/10] 创建ConfigMap..." -ForegroundColor Yellow
kubectl apply -f configmap.yml
if ($LASTEXITCODE -eq 0) { Write-Host "✓ ConfigMap创建成功" -ForegroundColor Green }

# 3. 创建Secret
Write-Host "[3/10] 创建Secret..." -ForegroundColor Yellow
if (Test-Path "secrets.yml") {
    kubectl apply -f secrets.yml
    if ($LASTEXITCODE -eq 0) { Write-Host "✓ Secret创建成功" -ForegroundColor Green }
} else {
    Write-Host "⚠ 未找到 secrets.yml，请先从 secrets.example.yml 创建并配置！" -ForegroundColor Yellow
    Write-Host "  执行: cp secrets.example.yml secrets.yml 然后编辑" -ForegroundColor Gray
    exit 1
}

# 4. 创建持久卷声明
Write-Host "[4/10] 创建持久卷声明..." -ForegroundColor Yellow
kubectl apply -f persistent-volumes.yml
if ($LASTEXITCODE -eq 0) { Write-Host "✓ PVC创建成功" -ForegroundColor Green }

# 5. 部署数据库服务
Write-Host "[5/10] 部署数据库服务..." -ForegroundColor Yellow
kubectl apply -f database-services.yml
if ($LASTEXITCODE -eq 0) { Write-Host "✓ 数据库服务部署成功" -ForegroundColor Green }

Write-Host "  等待MySQL和Redis就绪..." -ForegroundColor Gray
Start-Sleep -Seconds 10
kubectl wait --for=condition=ready pod -l app=mysql -n uav-platform --timeout=180s
kubectl wait --for=condition=ready pod -l app=redis -n uav-platform --timeout=180s

# 6. 部署后端服务
Write-Host "[6/10] 部署后端服务..." -ForegroundColor Yellow

$services = @(
    "data-assimilation-service.yml",
    "wrf-processor-service.yml",
    "meteor-forecast-service.yml",
    "path-planning-service.yml",
    "uav-platform-service.yml",
    "uav-weather-collector.yml",
    "fengwu-service.yml",
    "edge-cloud-coordinator.yml"
)

foreach ($svc in $services) {
    if (Test-Path $svc) {
        Write-Host "  部署 $svc..." -ForegroundColor Gray
        kubectl apply -f $svc
    }
}
Write-Host "✓ 后端服务部署成功" -ForegroundColor Green

# 7. 部署前端服务
Write-Host "[7/10] 部署前端服务..." -ForegroundColor Yellow
kubectl apply -f frontend-vue.yml
if ($LASTEXITCODE -eq 0) { Write-Host "✓ 前端服务部署成功" -ForegroundColor Green }

# 8. 部署API网关
Write-Host "[8/10] 部署API网关..." -ForegroundColor Yellow
kubectl apply -f api-gateway.yml
if ($LASTEXITCODE -eq 0) { Write-Host "✓ API网关部署成功" -ForegroundColor Green }

# 9. 部署自动扩展配置
Write-Host "[9/10] 部署自动扩展配置..." -ForegroundColor Yellow
if (Test-Path "hpa.yml") {
    kubectl apply -f hpa.yml
    Write-Host "✓ HPA配置部署成功" -ForegroundColor Green
} elseif (Test-Path "autoscaling.yml") {
    kubectl apply -f autoscaling.yml
    Write-Host "✓ 自动扩展配置部署成功" -ForegroundColor Green
} else {
    Write-Host "未找到HPA配置文件" -ForegroundColor Gray
}

# 10. 部署Ingress
Write-Host "[10/10] 部署Ingress..." -ForegroundColor Yellow
kubectl apply -f nginx-ingress.yml
if ($LASTEXITCODE -eq 0) { Write-Host "✓ Ingress部署成功" -ForegroundColor Green }

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "部署完成!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "运行验证脚本检查部署状态:" -ForegroundColor Yellow
Write-Host "  .\validate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "查看部署状态:" -ForegroundColor Yellow
Write-Host "  kubectl get all -n uav-platform" -ForegroundColor White
Write-Host ""
Write-Host "查看服务日志:" -ForegroundColor Yellow
Write-Host "  kubectl logs -n uav-platform <pod-name>" -ForegroundColor White
Write-Host ""
Write-Host "访问应用:" -ForegroundColor Yellow
Write-Host "  需要配置Ingress或使用端口转发" -ForegroundColor Gray
Write-Host "  例如: kubectl port-forward -n uav-platform svc/api-gateway 8088:8088" -ForegroundColor Gray
Write-Host ""
