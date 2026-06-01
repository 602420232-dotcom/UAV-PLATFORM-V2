# Kubernetes部署验证脚本
# 用于验证UAV平台在K8s集群中的部署状态
# PowerShell版本

$ErrorActionPreference = "Continue"
$namespace = "uav-platform"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "UAV平台K8s部署验证脚本" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查命名空间
Write-Host "[1/8] 检查命名空间..." -ForegroundColor Yellow
try {
    $ns = kubectl get namespace $namespace -o name 2>$null
    if ($ns) {
        Write-Host "✓ 命名空间 '$namespace' 存在" -ForegroundColor Green
    } else {
        Write-Host "✗ 命名空间 '$namespace' 不存在" -ForegroundColor Red
        Write-Host "  请先运行: kubectl apply -f namespace.yml" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ 检查命名空间失败: $_" -ForegroundColor Red
}
Write-Host ""

# 2. 检查ConfigMap
Write-Host "[2/8] 检查ConfigMap..." -ForegroundColor Yellow
try {
    $cm = kubectl get configmap uav-platform-config -n $namespace -o name 2>$null
    if ($cm) {
        Write-Host "✓ ConfigMap 'uav-platform-config' 存在" -ForegroundColor Green
        kubectl get configmap uav-platform-config -n $namespace -o jsonpath='{.data}' | ConvertFrom-Json | Get-Member -MemberType NoteProperty | Select-Object -First 10 Name | ForEach-Object { Write-Host "  - $($_.Name)" }
    } else {
        Write-Host "✗ ConfigMap 'uav-platform-config' 不存在" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ 检查ConfigMap失败: $_" -ForegroundColor Red
}
Write-Host ""

# 3. 检查Secret
Write-Host "[3/8] 检查Secret..." -ForegroundColor Yellow
try {
    $secret = kubectl get secret uav-platform-secrets -n $namespace -o name 2>$null
    if ($secret) {
        Write-Host "✓ Secret 'uav-platform-secrets' 存在" -ForegroundColor Green
    } else {
        Write-Host "✗ Secret 'uav-platform-secrets' 不存在" -ForegroundColor Red
        Write-Host "  请先从 secrets.example.yml 创建: cp secrets.example.yml secrets.yml 然后配置" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ 检查Secret失败: $_" -ForegroundColor Red
}
Write-Host ""

# 4. 检查Pod状态
Write-Host "[4/8] 检查Pod状态..." -ForegroundColor Yellow
try {
    Write-Host "Pod状态概览:" -ForegroundColor White
    kubectl get pods -n $namespace -o wide
    Write-Host ""
    
    $pods = kubectl get pods -n $namespace -o jsonpath='{.items[*].metadata.name}' 2>$null
    if ($pods) {
        $allReady = $true
        foreach ($pod in $pods.Split(' ')) {
            if ($pod) {
                $phase = kubectl get pod $pod -n $namespace -o jsonpath='{.status.phase}'
                if ($phase -eq "Running") {
                    Write-Host "✓ Pod '$pod' 运行中" -ForegroundColor Green
                } else {
                    Write-Host "✗ Pod '$pod' 状态: $phase" -ForegroundColor Red
                    $allReady = $false
                    # 显示事件
                    Write-Host "  最近事件:" -ForegroundColor Gray
                    kubectl get events -n $namespace --field-selector involvedObject.name=$pod --sort-by='.lastTimestamp' | Select-Object -Last 5
                }
            }
        }
    } else {
        Write-Host "✗ 未发现Pod" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ 检查Pod失败: $_" -ForegroundColor Red
}
Write-Host ""

# 5. 检查服务
Write-Host "[5/8] 检查服务..." -ForegroundColor Yellow
try {
    Write-Host "服务列表:" -ForegroundColor White
    kubectl get svc -n $namespace
} catch {
    Write-Host "✗ 检查服务失败: $_" -ForegroundColor Red
}
Write-Host ""

# 6. 检查部署状态
Write-Host "[6/8] 检查部署/StatefulSet状态..." -ForegroundColor Yellow
try {
    Write-Host "部署状态:" -ForegroundColor White
    kubectl get deploy,sts -n $namespace
} catch {
    Write-Host "✗ 检查部署失败: $_" -ForegroundColor Red
}
Write-Host ""

# 7. 检查HPA
Write-Host "[7/8] 检查HPA..." -ForegroundColor Yellow
try {
    $hpas = kubectl get hpa -n $namespace -o name 2>$null
    if ($hpas) {
        Write-Host "HPA状态:" -ForegroundColor White
        kubectl get hpa -n $namespace
    } else {
        Write-Host "未发现HPA资源" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ 检查HPA失败: $_" -ForegroundColor Red
}
Write-Host ""

# 8. 提供调试命令
Write-Host "[8/8] 有用的调试命令:" -ForegroundColor Yellow
Write-Host "  - 查看Pod日志: kubectl logs -n $namespace <pod-name>" -ForegroundColor Gray
Write-Host "  - 查看Pod详情: kubectl describe pod -n $namespace <pod-name>" -ForegroundColor Gray
Write-Host "  - 进入Pod: kubectl exec -it -n $namespace <pod-name> -- /bin/sh" -ForegroundColor Gray
Write-Host "  - 查看事件: kubectl get events -n $namespace --sort-by='.lastTimestamp'" -ForegroundColor Gray
Write-Host "  - 查看资源使用: kubectl top pods -n $namespace" -ForegroundColor Gray
Write-Host ""

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "验证完成" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
