# ============================================================
# UAV Platform V2 - 部署脚本 (PowerShell)
# ============================================================
# 用法:
#   .\scripts\deploy.ps1              # 构建并启动所有服务
#   .\scripts\deploy.ps1 -BuildOnly   # 仅构建镜像
#   .\scripts\deploy.ps1 -Push        # 构建并推送到镜像仓库
#   .\scripts\deploy.ps1 -Down        # 停止所有服务
#   .\scripts\deploy.ps1 -Clean       # 停止并清除所有容器和镜像
#   .\scripts\deploy.ps1 -Status       # 显示服务状态
# ============================================================

param(
    [switch]$BuildOnly,
    [switch]$Push,
    [switch]$Down,
    [switch]$Clean,
    [switch]$Status
)

$ErrorActionPreference = "Stop"

# 配置
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ComposeFile = Join-Path $ProjectDir "docker-compose.yml"
$ImageRegistry = if ($env:IMAGE_REGISTRY) { $env:IMAGE_REGISTRY } else { "ghcr.io/uav-platform" }
$ImageTag = if ($env:IMAGE_TAG) { $env:IMAGE_TAG } else { "latest" }

# 服务列表
$JavaServices = @(
    "api-gateway",
    "platform-api",
    "weather-api",
    "assimilation-api",
    "risk-api",
    "observation-api",
    "planning-api",
    "utm-api"
)
$PythonServices = @("algorithm-engine")
$AllServices = $JavaServices + $PythonServices + @("console")

# ============================================================
# 工具函数
# ============================================================
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Message" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Message)
    Write-Host "[ERROR] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Message" -ForegroundColor Red
}

# ============================================================
# 构建函数
# ============================================================
function Build-JavaServices {
    Write-Info "开始构建 Java 微服务..."
    Push-Location $ProjectDir

    # Maven 打包
    Write-Info "执行 Maven 打包..."
    mvn package -DskipTests -q

    foreach ($service in $JavaServices) {
        $image = "$ImageRegistry/$service`:$ImageTag"
        Write-Info "构建镜像: $image"

        if ($service -eq "api-gateway") {
            docker build -t $image `
                -f gateway/api-gateway/Dockerfile . `
                --build-arg SERVICE_NAME=$service `
                --build-arg SERVICE_DIR=gateway/api-gateway
        } else {
            docker build -t $image `
                -f services/$service/Dockerfile . `
                --build-arg SERVICE_NAME=$service `
                --build-arg SERVICE_DIR=services/$service
        }

        Write-Success "镜像构建完成: $image"
    }

    Pop-Location
}

function Build-PythonServices {
    Write-Info "开始构建 Python 服务..."
    Push-Location $ProjectDir

    foreach ($service in $PythonServices) {
        $image = "$ImageRegistry/$service`:$ImageTag"
        Write-Info "构建镜像: $image"
        docker build -t $image -f python/$service/Dockerfile python/$service/
        Write-Success "镜像构建完成: $image"
    }

    Pop-Location
}

function Build-Frontend {
    Write-Info "开始构建前端控制台..."
    Push-Location $ProjectDir
    $image = "$ImageRegistry/console`:$ImageTag"
    docker build -t $image -f console/Dockerfile console/
    Write-Success "镜像构建完成: $image"
    Pop-Location
}

function Build-All {
    Write-Info "========== 开始构建所有 Docker 镜像 =========="
    Build-JavaServices
    Build-PythonServices
    Build-Frontend
    Write-Success "========== 所有镜像构建完成 =========="
}

# ============================================================
# 推送函数
# ============================================================
function Push-Images {
    Write-Info "========== 开始推送镜像到仓库 =========="
    foreach ($service in $AllServices) {
        $image = "$ImageRegistry/$service`:$ImageTag"
        Write-Info "推送镜像: $image"
        try {
            docker push $image
        } catch {
            Write-Warn "推送失败: $service"
        }
    }
    Write-Success "========== 镜像推送完成 =========="
}

# ============================================================
# 部署函数
# ============================================================
function Deploy {
    Write-Info "========== 开始部署 UAV Platform V2 =========="
    Push-Location $ProjectDir

    # 启动基础设施
    Write-Info "启动基础设施服务 (MySQL, Redis, Nacos, Kafka)..."
    docker compose -f $ComposeFile up -d mysql redis zookeeper kafka nacos

    # 等待基础设施就绪
    Write-Info "等待基础设施服务就绪..."
    Wait-Service "uav-mysql" 60
    Wait-Service "uav-redis" 30
    Wait-Service "uav-nacos" 60

    # 启动业务服务
    Write-Info "启动业务微服务..."
    docker compose -f $ComposeFile up -d `
        api-gateway `
        platform-api `
        weather-api `
        assimilation-api `
        risk-api `
        observation-api `
        planning-api `
        utm-api `
        algorithm-engine `
        console

    # 等待所有服务就绪
    Write-Info "等待所有服务就绪..."
    $services = @(
        "uav-gateway",
        "uav-platform-api",
        "uav-weather-api",
        "uav-assimilation-api",
        "uav-risk-api",
        "uav-observation-api",
        "uav-planning-api",
        "uav-utm-api",
        "uav-algorithm-engine",
        "uav-console"
    )

    foreach ($service in $services) {
        Wait-Service $service 120
    }

    # 显示服务状态
    Show-Status

    Pop-Location

    Write-Success "========== UAV Platform V2 部署完成 =========="
    Write-Host ""
    Write-Host "服务访问地址:"
    Write-Host "  - API 网关:    http://localhost:8088"
    Write-Host "  - 前端控制台:  http://localhost:3000"
    Write-Host "  - Nacos 控制台: http://localhost:8848/nacos"
    Write-Host "  - Grafana:      http://localhost:3001"
    Write-Host "  - Prometheus:   http://localhost:9091"
}

# ============================================================
# 健康检查
# ============================================================
function Wait-Service {
    param(
        [string]$ContainerName,
        [int]$TimeoutSeconds = 60
    )

    $elapsed = 0
    while ($elapsed -lt $TimeoutSeconds) {
        try {
            $status = docker inspect --format='{{.State.Health.Status}}' $ContainerName 2>$null
            if ($status -eq "healthy") {
                Write-Success "$ContainerName is healthy"
                return $true
            } elseif ($status -eq "unhealthy") {
                Write-Err "$ContainerName is unhealthy"
                return $false
            }
        } catch {
            # 容器可能还没有健康检查配置
        }

        Start-Sleep -Seconds 5
        $elapsed += 5
    }

    Write-Warn "$ContainerName health check timed out after ${TimeoutSeconds}s"
    return $false
}

# ============================================================
# 状态显示
# ============================================================
function Show-Status {
    Write-Host ""
    Write-Host "============================================================"
    Write-Host "  UAV Platform V2 - 服务状态"
    Write-Host "============================================================"
    docker compose -f $ComposeFile ps
    Write-Host "============================================================"
}

# ============================================================
# 主逻辑
# ============================================================
if ($BuildOnly) {
    Build-All
} elseif ($Push) {
    Build-All
    Push-Images
} elseif ($Down) {
    Write-Info "停止所有服务..."
    docker compose -f $ComposeFile down
    Write-Success "所有服务已停止"
} elseif ($Clean) {
    Write-Info "停止并清除所有容器、网络和镜像..."
    docker compose -f $ComposeFile down --volumes --rmi local
    Write-Success "清理完成"
} elseif ($Status) {
    Show-Status
} else {
    Build-All
    Deploy
}
