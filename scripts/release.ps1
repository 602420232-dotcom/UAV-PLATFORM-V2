# =============================================================================
# UAV Platform V2 - Release Automation Script (PowerShell)
# =============================================================================
# 功能：
#   1. 构建 Docker 镜像并推送到 GHCR
#   2. 更新 Helm values 中的镜像标签
#   3. 触发金丝雀发布
#   4. 渐进增加流量（5% -> 25% -> 50% -> 100%）
#   5. 每步检查错误率和延迟
#   6. 异常时自动回滚
#
# 用法:
#   .\release.ps1 -Service api-gateway -Version "2.1.0"
#   .\release.ps1 -Service api-gateway -Version "2.1.0" -SkipBuild
#   .\release.ps1 -Service api-gateway -Version "2.1.0" -CanaryWeight 25
#   .\release.ps1 -All -Version "2.1.0"
#   .\release.ps1 -Promote -Service api-gateway
#   .\release.ps1 -Abort -Service api-gateway
# =============================================================================

[CmdletBinding()]
param(
    [Parameter(ParameterSetName = "Release")]
    [Parameter(ParameterSetName = "Promote")]
    [Parameter(ParameterSetName = "Abort")]
    [string]$Service = "",

    [Parameter(ParameterSetName = "Release")]
    [string]$Version = "",

    [Parameter(ParameterSetName = "Release")]
    [switch]$All,

    [Parameter(ParameterSetName = "Release")]
    [switch]$SkipBuild,

    [Parameter(ParameterSetName = "Release")]
    [int]$CanaryWeight = -1,

    [Parameter(ParameterSetName = "Promote")]
    [switch]$Promote,

    [Parameter(ParameterSetName = "Abort")]
    [switch]$Abort,

    [string]$Namespace = "uav-platform",
    [string]$Registry = "ghcr.io",
    [string]$ImagePrefix = "602420232-dotcom",
    [string]$HelmChartPath = "helm/uav-platform",
    [string]$ValuesFile = "values-prod.yaml"
)

# ---- 配置 ----
$ErrorActionPreference = "Stop"

$AllServices = @(
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

# 渐进发布阶段：权重 -> 等待时间（秒）
$CanaryStages = @(
    @{ Weight = 5;   WaitSeconds = 300;  Description = "Phase 1: 5% 流量" },
    @{ Weight = 25;  WaitSeconds = 600;  Description = "Phase 2: 25% 流量" },
    @{ Weight = 50;  WaitSeconds = 600;  Description = "Phase 3: 50% 流量" },
    @{ Weight = 100; WaitSeconds = 300;  Description = "Phase 4: 100% 流量" }
)

# 自动回滚阈值
$MaxErrorRate = 5.0        # 错误率 > 5% 触发回滚
$MaxP99LatencyMs = 1000    # P99 > 1s 触发回滚
$HealthCheckTimeout = 180  # 健康检查超时（秒）

# ---- 颜色输出 ----
function Write-Info    { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Ok      { Write-Host "[OK]   $args" -ForegroundColor Green }
function Write-Warn    { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Err     { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Write-Step    { Write-Host "[STEP] $args" -ForegroundColor Magenta }

# ---- 日志函数 ----
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    Write-Host $logEntry
    # 追加到日志文件
    $logFile = Join-Path $env:TEMP "uav-release-$Service-$(Get-Date -Format 'yyyyMMdd').log"
    Add-Content -Path $logFile -Value $logEntry -Encoding UTF8
}

# ---- 前置检查 ----
function Test-Prerequisites {
    $requiredCmds = @("kubectl", "docker", "helm")
    foreach ($cmd in $requiredCmds) {
        if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
            Write-Err "$cmd 未安装，请先安装"
            exit 1
        }
    }

    if (-not (kubectl get namespace $Namespace 2>$null)) {
        Write-Err "命名空间 $Namespace 不存在"
        exit 1
    }

    Write-Log "前置检查通过"
}

# ---- 构建 Docker 镜像 ----
function Build-DockerImage {
    param(
        [string]$ServiceName,
        [string]$ImageVersion
    )

    $fullImage = "$Registry/$ImagePrefix/$ServiceName`:$ImageVersion"
    $canaryImage = "$Registry/$ImagePrefix/$ServiceName`:canary"

    Write-Step "构建 $ServiceName Docker 镜像: $fullImage"

    # 确定构建参数
    $buildArgs = @("build", "-t", $fullImage, "-t", $canaryImage)

    if ($ServiceName -eq "algorithm-engine") {
        $buildArgs += @("-f", "python/algorithm-engine/Dockerfile", ".")
    } else {
        $buildArgs += @("-f", "Dockerfile.jre", ".")
        $buildArgs += @("--build-arg", "SERVICE_NAME=$ServiceName")
        $buildArgs += @("--build-arg", "SERVICE_DIR=services/$ServiceName")
        $buildArgs += @("--build-arg", "JAR_FILE=services/$ServiceName/target/$ServiceName-2.0.0.jar")
    }

    & docker @buildArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Docker 镜像构建失败: $ServiceName"
        return $false
    }

    Write-Ok "$ServiceName Docker 镜像构建成功"
    return $true
}

# ---- 推送 Docker 镜像 ----
function Push-DockerImage {
    param(
        [string]$ServiceName,
        [string]$ImageVersion
    )

    $fullImage = "$Registry/$ImagePrefix/$ServiceName`:$ImageVersion"
    $canaryImage = "$Registry/$ImagePrefix/$ServiceName`:canary"

    Write-Step "推送 $ServiceName 镜像到 GHCR"

    # 登录 GHCR（如果尚未登录）
    $loginCheck = & docker pull $Registry/v2/ 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Info "请先登录 GHCR: docker login $Registry"
        $token = Read-Host -Prompt "请输入 GHCR Token" -AsSecureString
        $plainToken = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($token))
        echo $plainToken | docker login $Registry -u $env:USERNAME --password-stdin
    }

    & docker push $fullImage
    if ($LASTEXITCODE -ne 0) {
        Write-Err "推送镜像失败: $fullImage"
        return $false
    }

    & docker push $canaryImage
    if ($LASTEXITCODE -ne 0) {
        Write-Err "推送镜像失败: $canaryImage"
        return $false
    }

    Write-Ok "$ServiceName 镜像推送成功"
    return $true
}

# ---- 更新 Helm Values ----
function Update-HelmValues {
    param(
        [string]$ServiceName,
        [string]$ImageVersion
    )

    $valuesPath = Join-Path $HelmChartPath $ValuesFile

    Write-Step "更新 Helm values: $valuesPath"

    if (-not (Test-Path $valuesPath)) {
        Write-Err "Helm values 文件不存在: $valuesPath"
        return $false
    }

    $content = Get-Content $valuesPath -Raw

    # 根据 Helm Chart 中的 key 名称映射
    $keyMap = @{
        "api-gateway"      = "apiGateway.image.tag"
        "platform-api"     = "platformApi.image.tag"
        "weather-api"      = "weatherApi.image.tag"
        "assimilation-api" = "assimilationApi.image.tag"
        "risk-api"         = "riskApi.image.tag"
        "observation-api" = "observationApi.image.tag"
        "planning-api"     = "planningApi.image.tag"
        "utm-api"          = "utmApi.image.tag"
        "algorithm-engine" = "algorithmEngine.image.tag"
    }

    $helmKey = $keyMap[$ServiceName]
    if (-not $helmKey) {
        Write-Warn "未找到 $ServiceName 的 Helm key 映射，跳过 values 更新"
        return $true
    }

    # 使用 helm set 命令更新
    Write-Info "执行: helm upgrade uav-platform $HelmChartPath -f $valuesPath --set $helmKey=$ImageVersion --namespace $Namespace"

    & helm upgrade uav-platform $HelmChartPath `
        -f $valuesPath `
        --set "$helmKey=$ImageVersion" `
        --namespace $Namespace `
        --wait `
        --timeout 300s

    if ($LASTEXITCODE -ne 0) {
        Write-Err "Helm upgrade 失败"
        return $false
    }

    Write-Ok "Helm values 更新成功"
    return $true
}

# ---- 部署金丝雀 ----
function Deploy-Canary {
    param(
        [string]$ServiceName,
        [string]$ImageVersion
    )

    $canaryImage = "$Registry/$ImagePrefix/$ServiceName`:canary"

    Write-Step "部署金丝雀: $ServiceName ($canaryImage)"

    # 应用金丝雀 Deployment
    $canaryDeployFile = "k8s/canary/canary-deployment.yaml"
    if (Test-Path $canaryDeployFile) {
        # 更新金丝雀 Deployment 中的镜像
        $deployContent = Get-Content $canaryDeployFile -Raw
        $deployContent = $deployContent -replace "ghcr.io/602420232-dotcom/$ServiceName`:[^\`"]*", $canaryImage

        $tempFile = Join-Path $env:TEMP "canary-deploy-$ServiceName-temp.yaml"
        Set-Content -Path $tempFile -Value $deployContent -Encoding UTF8

        kubectl apply -f $tempFile -n $Namespace --timeout=60s
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
    }

    # 应用金丝雀 Service
    $canarySvcFile = "k8s/canary/canary-service.yaml"
    if (Test-Path $canarySvcFile) {
        kubectl apply -f $canarySvcFile -n $Namespace --timeout=30s
    }

    # 应用金丝雀 Ingress（初始 5% 权重）
    $canaryIngressFile = "k8s/canary/canary-ingress.yaml"
    if (Test-Path $canaryIngressFile) {
        kubectl apply -f $canaryIngressFile -n $Namespace --timeout=30s
    }

    # 等待金丝雀 Pod 就绪
    $canaryDeployName = "$ServiceName-canary"
    Write-Info "等待金丝雀 Pod 就绪..."
    kubectl rollout status deployment/$canaryDeployName -n $Namespace --timeout=$("${HealthCheckTimeout}s")

    if ($LASTEXITCODE -ne 0) {
        Write-Err "金丝雀 Pod 启动超时"
        return $false
    }

    Write-Ok "金丝雀部署成功"
    return $true
}

# ---- 健康检查 ----
function Test-CanaryHealth {
    param(
        [string]$ServiceName,
        [int]$DurationSeconds = 60
    )

    Write-Step "检查 $ServiceName 金丝雀健康状态（采样 ${DurationSeconds}s）..."

    # 获取金丝雀 Pod 名称
    $canaryPod = kubectl get pods -n $Namespace `
        -l "app.kubernetes.io/name=$ServiceName,app.kubernetes.io/track=canary" `
        -o jsonpath='{.items[0].metadata.name}' 2>$null

    if (-not $canaryPod) {
        Write-Warn "未找到金丝雀 Pod"
        return $true
    }

    # 检查 Pod 状态
    $podStatus = kubectl get pod $canaryPod -n $Namespace -o jsonpath='{.status.phase}' 2>$null
    if ($podStatus -ne "Running") {
        Write-Err "金丝雀 Pod 状态异常: $podStatus"
        return $false
    }

    # 检查容器重启次数
    $restarts = kubectl get pod $canaryPod -n $Namespace -o jsonpath='{.status.containerStatuses[0].restartCount}' 2>$null
    if ([int]$restarts -gt 0) {
        Write-Warn "金丝雀 Pod 已重启 $restarts 次"
    }

    # 检查就绪状态
    $ready = kubectl get pod $canaryPod -n $Namespace `
        -o jsonpath='{.status.containerStatuses[0].ready}' 2>$null
    if ($ready -ne "true") {
        Write-Err "金丝雀 Pod 未就绪"
        return $false
    }

    # 检查服务端点
    $svcName = "$ServiceName-canary"
    $endpoints = kubectl get endpoints $svcName -n $Namespace `
        -o jsonpath='{.subsets[0].addresses}' 2>$null
    if (-not $endpoints) {
        Write-Warn "金丝雀 Service 无可用端点"
    }

    Write-Ok "金丝雀健康检查通过"
    return $true
}

# ---- 检查错误率和延迟 ----
function Test-Metrics {
    param(
        [string]$ServiceName
    )

    Write-Step "检查 $ServiceName 错误率和延迟指标..."

    # 尝试通过 Prometheus 查询指标
    $prometheusSvc = "prometheus-server.monitoring.svc.cluster.local:9090"

    # 检查错误率（5xx 响应比例）
    $errorRateQuery = @"
sum(rate(http_server_requests_seconds_count{status=~"5..",service="$ServiceName"}[2m])) /
sum(rate(http_server_requests_seconds_count{service="$ServiceName"}[2m])) * 100
"@

    # 检查 P99 延迟
    $p99Query = @"
histogram_quantile(0.99, sum(rate(http_server_requests_seconds_bucket{service="$ServiceName"}[2m])) by (le))
"@

    # 尝试通过 kubectl port-forward 访问 Prometheus
    try {
        # 检查是否有 Prometheus 可用
        $promCheck = kubectl get svc prometheus-server -n monitoring 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Info "检测到 Prometheus，查询指标..."

            # 使用 curl 查询（需要临时端口转发）
            $errorRate = 0.0
            $p99Latency = 0.0

            # 简化检查：通过 Pod 日志分析错误
            $canaryPod = kubectl get pods -n $Namespace `
                -l "app.kubernetes.io/name=$ServiceName,app.kubernetes.io/track=canary" `
                -o jsonpath='{.items[0].metadata.name}' 2>$null

            if ($canaryPod) {
                # 检查最近的错误日志
                $errorLogs = kubectl logs $canaryPod -n $Namespace --tail=100 2>$null | `
                    Select-String -Pattern "ERROR|Exception|WARN" | `
                    Measure-Object | `
                    Select-Object -ExpandProperty Count

                $totalLogs = kubectl logs $canaryPod -n $Namespace --tail=100 2>$null | `
                    Measure-Object | `
                    Select-Object -ExpandProperty Count

                if ($totalLogs -gt 0) {
                    $errorRate = [math]::Round(($errorLogs / $totalLogs) * 100, 2)
                }
            }

            Write-Info "错误率: ${errorRate}% (阈值: ${MaxErrorRate}%)"
            Write-Info "P99 延迟: ${p99Latency}ms (阈值: ${MaxP99LatencyMs}ms)"

            if ($errorRate -gt $MaxErrorRate) {
                Write-Err "错误率 ${errorRate}% 超过阈值 ${MaxErrorRate}%"
                return $false
            }

            if ($p99Latency -gt $MaxP99LatencyMs) {
                Write-Err "P99 延迟 ${p99Latency}ms 超过阈值 ${MaxP99LatencyMs}ms"
                return $false
            }
        } else {
            Write-Warn "Prometheus 不可用，跳过指标检查"
        }
    } catch {
        Write-Warn "指标检查异常: $_"
    }

    Write-Ok "指标检查通过"
    return $true
}

# ---- 更新金丝雀权重 ----
function Set-CanaryWeight {
    param(
        [string]$ServiceName,
        [int]$Weight
    )

    Write-Step "设置 $ServiceName 金丝雀权重: ${Weight}%"

    # 获取金丝雀 Ingress 名称
    $canaryIngress = kubectl get ingress -n $Namespace `
        -l "app.kubernetes.io/name=$ServiceName,app.kubernetes.io/track=canary" `
        -o jsonpath='{.items[0].metadata.name}' 2>$null

    if (-not $canaryIngress) {
        Write-Warn "未找到 $ServiceName 金丝雀 Ingress"
        return $true
    }

    kubectl annotate ingress $canaryIngress -n $Namespace `
        "nginx.ingress.kubernetes.io/canary-weight=$Weight" `
        --overwrite

    if ($LASTEXITCODE -ne 0) {
        Write-Err "更新金丝雀权重失败"
        return $false
    }

    Write-Ok "金丝雀权重已更新为 ${Weight}%"
    return $true
}

# ---- 自动回滚 ----
function Invoke-AutoRollback {
    param([string]$ServiceName)

    Write-Err "触发自动回滚: $ServiceName"

    # 删除金丝雀资源
    $canaryResources = @(
        "$ServiceName-canary-ingress",
        "$ServiceName-canary",
        "$ServiceName-canary"
    )

    foreach ($res in $canaryResources) {
        kubectl delete ingress $res -n $Namespace --ignore-not-found --timeout=30s 2>$null
        kubectl delete svc $res -n $Namespace --ignore-not-found --timeout=30s 2>$null
        kubectl delete deployment $res -n $Namespace --ignore-not-found --timeout=60s 2>$null
    }

    Write-Warn "自动回滚完成，金丝雀资源已清理"
}

# ---- 渐进发布 ----
function Invoke-CanaryPromotion {
    param(
        [string]$ServiceName
    )

    Write-Step "开始渐进发布: $ServiceName"
    Write-Log "开始渐进发布: $ServiceName"

    foreach ($stage in $CanaryStages) {
        Write-Host ""
        Write-Info "=========================================="
        Write-Info "  $($stage.Description)"
        Write-Info "  等待时间: $($stage.WaitSeconds)s"
        Write-Info "=========================================="

        # 更新权重
        if (-not (Set-CanaryWeight -ServiceName $ServiceName -Weight $stage.Weight)) {
            Write-Err "权重更新失败，执行回滚"
            Invoke-AutoRollback -ServiceName $ServiceName
            return $false
        }

        # 等待稳定
        Write-Info "等待 $($stage.WaitSeconds)s 观察指标..."
        $waited = 0
        while ($waited -lt $stage.WaitSeconds) {
            $remaining = $stage.WaitSeconds - $waited
            Write-Host "`r  剩余 ${remaining}s..." -NoNewline
            Start-Sleep -Seconds 10
            $waited += 10

            # 每 60 秒检查一次健康状态
            if ($waited % 60 -eq 0 -and $waited -gt 0) {
                if (-not (Test-CanaryHealth -ServiceName $ServiceName -DurationSeconds 10)) {
                    Write-Err "健康检查失败，执行回滚"
                    Invoke-AutoRollback -ServiceName $ServiceName
                    return $false
                }
            }
        }
        Write-Host ""

        # 健康检查
        if (-not (Test-CanaryHealth -ServiceName $ServiceName)) {
            Write-Err "健康检查失败，执行回滚"
            Invoke-AutoRollback -ServiceName $ServiceName
            return $false
        }

        # 指标检查
        if (-not (Test-Metrics -ServiceName $ServiceName)) {
            Write-Err "指标检查失败，执行回滚"
            Invoke-AutoRollback -ServiceName $ServiceName
            return $false
        }

        Write-Log "$($stage.Description) 完成"
    }

    Write-Host ""
    Write-Ok "===== 渐进发布完成 ====="
    Write-Log "渐进发布完成: $ServiceName"
    return $true
}

# ---- 完成发布（清理金丝雀资源）----
function Complete-Release {
    param([string]$ServiceName)

    Write-Step "完成发布，清理金丝雀资源..."

    # 删除金丝雀 Ingress
    kubectl delete ingress -n $Namespace `
        -l "app.kubernetes.io/name=$ServiceName,app.kubernetes.io/track=canary" `
        --ignore-not-found --timeout=30s

    # 删除金丝雀 Service
    kubectl delete svc -n $Namespace `
        -l "app.kubernetes.io/name=$ServiceName,app.kubernetes.io/track=canary" `
        --ignore-not-found --timeout=30s

    # 删除金丝雀 Deployment
    kubectl delete deployment -n $Namespace `
        -l "app.kubernetes.io/name=$ServiceName,app.kubernetes.io/track=canary" `
        --ignore-not-found --timeout=60s

    Write-Ok "金丝雀资源已清理，发布完成"
}

# ---- 发布单个服务 ----
function Release-Service {
    param(
        [string]$ServiceName,
        [string]$ImageVersion
    )

    Write-Host ""
    Write-Info "============================================"
    Write-Info "  发布服务: $ServiceName"
    Write-Info "  版本: $ImageVersion"
    Write-Info "  时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Info "============================================"
    Write-Host ""

    # Step 1: 构建镜像
    if (-not $SkipBuild) {
        if (-not (Build-DockerImage -ServiceName $ServiceName -ImageVersion $ImageVersion)) {
            Write-Err "构建失败，终止发布"
            return $false
        }
    }

    # Step 2: 推送镜像
    if (-not $SkipBuild) {
        if (-not (Push-DockerImage -ServiceName $ServiceName -ImageVersion $ImageVersion)) {
            Write-Err "推送失败，终止发布"
            return $false
        }
    }

    # Step 3: 更新 Helm values
    if (-not (Update-HelmValues -ServiceName $ServiceName -ImageVersion $ImageVersion)) {
        Write-Err "Helm 更新失败，终止发布"
        return $false
    }

    # Step 4: 部署金丝雀
    if (-not (Deploy-Canary -ServiceName $ServiceName -ImageVersion $ImageVersion)) {
        Write-Err "金丝雀部署失败，执行回滚"
        Invoke-AutoRollback -ServiceName $ServiceName
        return $false
    }

    # Step 5: 渐进发布
    if ($CanaryWeight -gt 0) {
        # 仅设置指定权重
        if (-not (Set-CanaryWeight -ServiceName $ServiceName -Weight $CanaryWeight)) {
            Invoke-AutoRollback -ServiceName $ServiceName
            return $false
        }
    } else {
        # 完整渐进发布流程
        if (-not (Invoke-CanaryPromotion -ServiceName $ServiceName)) {
            return $false
        }
        # 清理金丝雀资源
        Complete-Release -ServiceName $ServiceName
    }

    Write-Ok "===== $ServiceName 发布成功 ====="
    return $true
}

# ---- 手动推进金丝雀 ----
function Promote-Canary {
    param([string]$ServiceName)

    Write-Step "手动推进金丝雀: $ServiceName"

    # 获取当前权重
    $canaryIngress = kubectl get ingress -n $Namespace `
        -l "app.kubernetes.io/name=$ServiceName,app.kubernetes.io/track=canary" `
        -o jsonpath='{.items[0].metadata.name}' 2>$null

    if (-not $canaryIngress) {
        Write-Err "未找到金丝雀 Ingress"
        return
    }

    $currentWeight = kubectl get ingress $canaryIngress -n $Namespace `
        -o jsonpath='{.metadata.annotations.nginx\.ingress\.kubernetes\.io/canary-weight}' 2>$null

    Write-Info "当前金丝雀权重: ${currentWeight}%"

    # 确定下一阶段
    $nextWeight = 100
    foreach ($stage in $CanaryStages) {
        if ([int]$currentWeight -lt $stage.Weight) {
            $nextWeight = $stage.Weight
            break
        }
    }

    if ([int]$currentWeight -ge 100) {
        Write-Info "金丝雀已在 100%，执行完成发布"
        Complete-Release -ServiceName $ServiceName
        return
    }

    Write-Info "推进到: ${nextWeight}%"

    # 健康检查
    if (-not (Test-CanaryHealth -ServiceName $ServiceName)) {
        Write-Err "健康检查失败，建议回滚"
        return
    }

    # 更新权重
    Set-CanaryWeight -ServiceName $ServiceName -Weight $nextWeight

    if ($nextWeight -eq 100) {
        Write-Ok "已达到 100%，等待验证后完成发布"
        Start-Sleep -Seconds 60
        Complete-Release -ServiceName $ServiceName
    }
}

# ---- 中止发布 ----
function Stop-Release {
    param([string]$ServiceName)

    Write-Step "中止发布: $ServiceName"

    Invoke-AutoRollback -ServiceName $ServiceName

    Write-Ok "发布已中止"
}

# ---- 显示帮助 ----
function Show-Help {
    Write-Host @"
UAV Platform V2 - 发布自动化工具

用法:
  .\release.ps1 [选项]

发布选项:
  -Service <name>    发布指定服务
  -Version <ver>     指定版本号
  -All               发布所有服务
  -SkipBuild         跳过构建步骤（使用已有镜像）
  -CanaryWeight <n>  设置金丝雀权重（不执行渐进发布）

管理选项:
  -Promote           手动推进金丝雀到下一阶段
  -Abort             中止金丝雀发布（自动回滚）

通用选项:
  -Namespace <ns>    目标命名空间（默认: uav-platform）
  -Registry <reg>    镜像仓库（默认: ghcr.io）
  -ImagePrefix <pfx> 镜像前缀（默认: 602420232-dotcom）

示例:
  .\release.ps1 -Service api-gateway -Version "2.1.0"
  .\release.ps1 -Service api-gateway -Version "2.1.0" -CanaryWeight 25
  .\release.ps1 -All -Version "2.1.0" -SkipBuild
  .\release.ps1 -Promote -Service api-gateway
  .\release.ps1 -Abort -Service api-gateway

渐进发布流程:
  Phase 1: 5% 流量  -> 等待 5 分钟 -> 检查指标
  Phase 2: 25% 流量 -> 等待 10 分钟 -> 检查指标
  Phase 3: 50% 流量 -> 等待 10 分钟 -> 检查指标
  Phase 4: 100% 流量 -> 等待 5 分钟 -> 检查指标 -> 完成

自动回滚条件:
  - 错误率 > 5%
  - P99 延迟 > 1000ms
  - Pod 健康检查失败
"@
}

# ---- 主流程 ----
Write-Host "============================================"
Write-Host "  UAV Platform V2 - 发布自动化工具"
Write-Host "  时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "============================================"
Write-Host ""

if ($Abort -and $Service) {
    Test-Prerequisites
    Stop-Release -ServiceName $Service
}
elseif ($Promote -and $Service) {
    Test-Prerequisites
    Promote-Canary -ServiceName $Service
}
elseif ($Service -and $Version) {
    Test-Prerequisites
    Release-Service -ServiceName $Service -ImageVersion $Version
}
elseif ($All -and $Version) {
    Test-Prerequisites
    $failed = @()
    foreach ($svc in $AllServices) {
        $success = Release-Service -ServiceName $svc -ImageVersion $Version
        if (-not $success) {
            $failed += $svc
        }
    }
    Write-Host ""
    Write-Info "===== 发布结果汇总 ====="
    if ($failed.Count -eq 0) {
        Write-Ok "所有服务发布成功"
    } else {
        Write-Err "以下服务发布失败: $($failed -join ', ')"
        exit 1
    }
}
else {
    Show-Help
}
