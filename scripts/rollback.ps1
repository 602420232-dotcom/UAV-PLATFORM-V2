# =============================================================================
# UAV Platform V2 - Rollback Script (PowerShell)
# =============================================================================
# 用法:
#   .\rollback.ps1                          # 显示帮助
#   .\rollback.ps1 -Service api-gateway     # 回滚指定服务到上一个版本
#   .\rollback.ps1 -Service api-gateway -Revision 2  # 回滚到指定版本
#   .\rollback.ps1 -All                     # 批量回滚所有服务
#   .\rollback.ps1 -Canary                  # 回滚金丝雀发布
#   .\rollback.ps1 -Auto                    # 跳过确认提示
# =============================================================================

[CmdletBinding()]
param(
    [string]$Service = "",
    [int]$Revision = -1,
    [switch]$All,
    [switch]$Auto,
    [switch]$Canary,
    [string]$Namespace = "uav-platform"
)

# ---- 配置 ----
$ErrorActionPreference = "Stop"

$Services = @(
    "api-gateway",
    "platform-api",
    "weather-api",
    "assimilation-api",
    "risk-api",
    "observation-api",
    "planning-api",
    "utm-api",
    "algorithm-engine"
)

# ---- 颜色输出函数 ----
function Write-Info    { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Ok      { Write-Host "[OK]   $args" -ForegroundColor Green }
function Write-Warn    { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Err     { Write-Host "[ERROR] $args" -ForegroundColor Red }

# ---- 前置检查 ----
function Test-Prerequisites {
    $kubectlCmd = Get-Command kubectl -ErrorAction SilentlyContinue
    if (-not $kubectlCmd) {
        Write-Err "kubectl 未安装，请先安装 Kubernetes CLI"
        exit 1
    }

    $ns = kubectl get namespace $Namespace 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Err "命名空间 $Namespace 不存在"
        exit 1
    }

    Write-Info "命名空间: $Namespace"
}

# ---- 健康检查 ----
function Wait-Healthy {
    param(
        [string]$ServiceName,
        [int]$MaxWaitSeconds = 120
    )

    Write-Info "等待 $ServiceName 健康检查通过（最长 ${MaxWaitSeconds}s）..."

    $elapsed = 0
    while ($elapsed -lt $MaxWaitSeconds) {
        $readyJson = kubectl get deployment $ServiceName `
            -n $Namespace `
            -o jsonpath='{.status.readyReplicas}' 2>$null

        $desiredJson = kubectl get deployment $ServiceName `
            -n $Namespace `
            -o jsonpath='{.spec.replicas}' 2>$null

        $ready = if ($readyJson) { [int]$readyJson } else { 0 }
        $desired = if ($desiredJson) { [int]$desiredJson } else { 0 }

        if ($ready -eq $desired -and $ready -gt 0) {
            Write-Ok "$ServiceName 健康检查通过 ($ready/$desired ready)"
            return $true
        }

        Write-Host "`r  已等待 ${elapsed}s ($ready/$desired ready)..." -NoNewline
        Start-Sleep -Seconds 5
        $elapsed += 5
    }

    Write-Host ""
    Write-Warn "$ServiceName 健康检查超时（${MaxWaitSeconds}s），请手动检查"
    return $false
}

# ---- 确认提示 ----
function Confirm-Action {
    param([string]$Message)

    if ($Auto) {
        return $true
    }

    $title = "确认操作"
    $yes = New-Object System.Management.Automation.Host.ChoiceDescription "&Yes", "执行操作"
    $no  = New-Object System.Management.Automation.Host.ChoiceDescription "&No",  "取消操作"
    $options = [System.Management.Automation.Host.ChoiceDescription[]]($yes, $no)

    $result = $Host.UI.PromptForChoice($title, $Message, $options, 1)
    return $result -eq 0
}

# ---- 显示版本历史 ----
function Show-RevisionHistory {
    param([string]$ServiceName)

    Write-Info "$ServiceName 部署版本历史:"
    kubectl rollout history deployment/$ServiceName -n $Namespace 2>$null
    Write-Host ""
}

# ---- 回滚单个服务 ----
function Rollback-Service {
    param(
        [string]$ServiceName,
        [int]$TargetRevision = -1
    )

    Write-Info "===== 回滚服务: $ServiceName ====="

    # 显示当前镜像
    $currentImage = kubectl get deployment $ServiceName `
        -n $Namespace `
        -o jsonpath='{.spec.template.spec.containers[0].image}' 2>$null
    Write-Info "当前镜像: $currentImage"

    # 显示版本历史
    Show-RevisionHistory $ServiceName

    # 执行回滚
    if ($TargetRevision -gt 0) {
        Write-Info "回滚 $ServiceName 到版本 revision $TargetRevision ..."
        kubectl rollout undo deployment/$ServiceName `
            -n $Namespace `
            --to-revision=$TargetRevision
    } else {
        Write-Info "回滚 $ServiceName 到上一个版本 ..."
        kubectl rollout undo deployment/$ServiceName -n $Namespace
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Err "$ServiceName 回滚命令执行失败"
        return $false
    }

    # 等待回滚完成
    Write-Info "等待回滚完成..."
    kubectl rollout status deployment/$ServiceName `
        -n $Namespace `
        --timeout=180s

    if ($LASTEXITCODE -ne 0) {
        Write-Err "$ServiceName 回滚等待超时"
        return $false
    }

    # 健康检查
    $healthy = Wait-Healthy -ServiceName $ServiceName -MaxWaitSeconds 120
    if (-not $healthy) {
        Write-Warn "$ServiceName 健康检查未通过"
    }

    # 验证回滚后镜像
    $newImage = kubectl get deployment $ServiceName `
        -n $Namespace `
        -o jsonpath='{.spec.template.spec.containers[0].image}' 2>$null
    Write-Info "回滚后镜像: $newImage"

    if ($currentImage -ne $newImage) {
        Write-Ok "$ServiceName 回滚成功"
        return $true
    } else {
        Write-Warn "$ServiceName 镜像未变化，请确认回滚是否生效"
        return $true
    }
}

# ---- 金丝雀回滚 ----
function Rollback-Canary {
    Write-Info "===== 回滚金丝雀发布 ====="

    if (-not (Confirm-Action "确认删除所有金丝雀资源？这将把 100% 流量切回稳定版本")) {
        Write-Info "操作已取消"
        return
    }

    # 删除金丝雀 Ingress
    $canaryIngresses = kubectl get ingress -n $Namespace `
        -l "app.kubernetes.io/track=canary" `
        -o jsonpath='{.items[*].metadata.name}' 2>$null

    if ($canaryIngresses) {
        foreach ($ing in $canaryIngresses -split ' ') {
            if ($ing) {
                Write-Info "删除金丝雀 Ingress: $ing"
                kubectl delete ingress $ing -n $Namespace --timeout=30s
            }
        }
    }

    # 删除金丝雀 Service
    $canaryServices = kubectl get svc -n $Namespace `
        -l "app.kubernetes.io/track=canary" `
        -o jsonpath='{.items[*].metadata.name}' 2>$null

    if ($canaryServices) {
        foreach ($svc in $canaryServices -split ' ') {
            if ($svc) {
                Write-Info "删除金丝雀 Service: $svc"
                kubectl delete svc $svc -n $Namespace --timeout=30s
            }
        }
    }

    # 删除金丝雀 Deployment
    $canaryDeployments = kubectl get deployment -n $Namespace `
        -l "app.kubernetes.io/track=canary" `
        -o jsonpath='{.items[*].metadata.name}' 2>$null

    if ($canaryDeployments) {
        foreach ($deploy in $canaryDeployments -split ' ') {
            if ($deploy) {
                Write-Info "删除金丝雀 Deployment: $deploy"
                kubectl delete deployment $deploy -n $Namespace --timeout=60s
            }
        }
    }

    Write-Ok "金丝雀资源已全部删除，流量已切回稳定版本"
}

# ---- 批量回滚 ----
function Rollback-AllServices {
    Write-Info "===== 批量回滚所有服务 ====="

    if (-not (Confirm-Action "确认回滚所有 $($Services.Count) 个服务？")) {
        Write-Info "操作已取消"
        return
    }

    $failed = @()

    foreach ($svc in $Services) {
        $exists = kubectl get deployment $svc -n $Namespace 2>$null
        if ($LASTEXITCODE -eq 0) {
            $success = Rollback-Service -ServiceName $svc -TargetRevision $Revision
            if (-not $success) {
                $failed += $svc
            }
        } else {
            Write-Warn "服务 $svc 不存在，跳过"
        }
    }

    Write-Host ""
    Write-Info "===== 回滚结果汇总 ====="
    if ($failed.Count -eq 0) {
        Write-Ok "所有服务回滚成功"
    } else {
        Write-Err "以下服务回滚失败: $($failed -join ', ')"
        exit 1
    }
}

# ---- 显示帮助 ----
function Show-Help {
    Write-Host @"
UAV Platform V2 - 回滚工具

用法:
  .\rollback.ps1 [选项]

选项:
  -Service <name>    回滚指定服务到上一个版本
  -Revision <num>    回滚到指定版本号（需配合 -Service 使用）
  -All               批量回滚所有服务
  -Canary            回滚金丝雀发布（删除金丝雀资源）
  -Auto              跳过确认提示
  -Namespace <ns>    指定命名空间（默认: uav-platform）
  -Help              显示帮助信息

示例:
  .\rollback.ps1 -Service api-gateway
  .\rollback.ps1 -Service api-gateway -Revision 2
  .\rollback.ps1 -All -Auto
  .\rollback.ps1 -Canary
"@
}

# ---- 主流程 ----
Write-Host "============================================"
Write-Host "  UAV Platform V2 - 回滚工具"
Write-Host "  时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "============================================"
Write-Host ""

Test-Prerequisites

if ($Canary) {
    Rollback-Canary
}
elseif ($All) {
    Rollback-AllServices
}
elseif ($Service) {
    if (-not (Confirm-Action "确认回滚服务 $Service ？")) {
        Write-Info "操作已取消"
        exit 0
    }
    Rollback-Service -ServiceName $Service -TargetRevision $Revision
}
else {
    Show-Help
    exit 0
}
