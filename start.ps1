#!/usr/bin/env pwsh
<#
.SYNOPSIS
    UAV Platform V2 - 一键启动脚本 (PowerShell)
.DESCRIPTION
    自动检查环境、初始化配置、构建并启动所有服务。
.PARAMETER SkipBuild
    跳过 Maven 构建和 Docker 镜像构建，直接 docker compose up。
.PARAMETER InfraOnly
    仅启动基础设施 (MySQL, Redis, Nacos, Kafka, Zookeeper)。
.PARAMETER Down
    停止所有服务。
.PARAMETER Status
    查看服务状态。
.PARAMETER Logs
    查看所有服务日志 (Ctrl+C 退出)。
.EXAMPLE
    .\start.ps1                    # 完整启动
    .\start.ps1 -SkipBuild         # 跳过构建，直接启动
    .\start.ps1 -InfraOnly         # 仅基础设施
    .\start.ps1 -Down              # 停止
    .\start.ps1 -Status            # 状态
    .\start.ps1 -Logs              # 日志
#>

param(
    [switch]$SkipBuild,
    [switch]$InfraOnly,
    [switch]$Down,
    [switch]$Status,
    [switch]$Logs
)

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$EnvFile = Join-Path $ProjectDir '.env'
$EnvExample = Join-Path $ProjectDir '.env.example'
$ComposeFile = Join-Path $ProjectDir 'docker-compose.yml'

# 颜色函数
function Write-Info($msg) { Write-Host "[INFO] $(Get-Date -Format 'HH:mm:ss') $msg" -ForegroundColor Blue }
function Write-Ok($msg)   { Write-Host "[OK]   $(Get-Date -Format 'HH:mm:ss') $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $(Get-Date -Format 'HH:mm:ss') $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERR]  $(Get-Date -Format 'HH:mm:ss') $msg" -ForegroundColor Red }

# 检查前置条件
function Test-Prerequisites {
    $missing = @()

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        $missing += 'docker'
    }
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue) -and
        -not (docker compose version 2>$null)) {
        $missing += 'docker-compose'
    }
    if (-not $SkipBuild -and -not (Get-Command mvn -ErrorAction SilentlyContinue)) {
        $missing += 'mvn (Java Maven)'
    }

    if ($missing.Count -gt 0) {
        Write-Err "缺少必要工具: $($missing -join ', ')"
        Write-Host "请先安装: $($missing -join ', ')"
        exit 1
    }
    Write-Ok "前置条件检查通过"
}

# 初始化 .env
function Initialize-Env {
    if (-not (Test-Path $EnvFile)) {
        if (Test-Path $EnvExample) {
            Copy-Item $EnvExample $EnvFile
            Write-Info "已从 .env.example 创建 .env 文件"
            Write-Warn "请编辑 .env 填入实际密码，然后重新运行此脚本"
            Write-Host ""
            Write-Host "  编辑命令: notepad $EnvFile" -ForegroundColor Cyan
            exit 0
        } else {
            Write-Err "未找到 .env.example，无法初始化"
            exit 1
        }
    }
    Write-Ok ".env 已就绪"
}

# Maven 构建
function Build-Maven {
    Write-Info "Maven 打包 Java 服务 (跳过测试)..."
    Push-Location $ProjectDir
    mvn package '-Dmaven.test.skip=true' -q
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Maven 构建失败"
        Pop-Location
        exit 1
    }
    Pop-Location
    Write-Ok "Maven 构建完成"
}

# Docker Compose 操作
function Invoke-Compose {
    param([string]$Action, [string[]]$Services, [switch]$Build)
    Push-Location $ProjectDir
    $cmd = "docker compose -f `"$ComposeFile`" --env-file .env"
    if ($Build) { $cmd += " build" }
    $cmd += " $Action"
    if ($Services) { $cmd += " $($Services -join ' ')" }
    Invoke-Expression $cmd
    $result = $LASTEXITCODE
    Pop-Location
    return $result
}

# 等待服务健康
function Wait-Healthy {
    param(
        [string[]]$Containers,
        [int]$TimeoutSeconds = 120
    )

    $elapsed = 0
    $interval = 5

    foreach ($container in $Containers) {
        $done = $false
        $timer = 0
        while (-not $done -and $timer -lt $TimeoutSeconds) {
            $health = docker inspect --format='{{.State.Health.Status}}' $container 2>$null
            if ($health -eq 'healthy') {
                Write-Ok "$container 就绪"
                $done = $true
            } elseif ($health -eq 'unhealthy') {
                Write-Warn "$container unhealthy，查看日志: docker logs $container --tail 20"
                $done = $true
            } else {
                Start-Sleep -Seconds $interval
                $timer += $interval
            }
        }
        if (-not $done) {
            Write-Warn "$container 启动超时 (${TimeoutSeconds}s)"
        }
    }
}

# 打印访问地址
function Show-Endpoints {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  UAV Platform V2 服务已启动" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  业务服务:" -ForegroundColor White
    Write-Host "    API 网关:       http://localhost:8258" -ForegroundColor Green
    Write-Host "    前端控制台:     http://localhost:3002" -ForegroundColor Green
    Write-Host "    算法引擎:       http://localhost:9095" -ForegroundColor Green
    Write-Host ""
    Write-Host "  微服务:" -ForegroundColor White
    Write-Host "    Platform API:   http://localhost:8251" -ForegroundColor DarkGray
    Write-Host "    Weather API:    http://localhost:8252" -ForegroundColor DarkGray
    Write-Host "    Assimilation:   http://localhost:8253" -ForegroundColor DarkGray
    Write-Host "    Risk:           http://localhost:8254" -ForegroundColor DarkGray
    Write-Host "    Observation:    http://localhost:8255" -ForegroundColor DarkGray
    Write-Host "    Planning:       http://localhost:8256" -ForegroundColor DarkGray
    Write-Host "    UTM:            http://localhost:8259" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  基础设施:" -ForegroundColor White
    Write-Host "    MySQL:          localhost:3307" -ForegroundColor DarkGray
    Write-Host "    Redis:          localhost:6380" -ForegroundColor DarkGray
    Write-Host "    Nacos:          http://localhost:8950/nacos" -ForegroundColor DarkGray
    Write-Host "    Kafka:          localhost:19092" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  监控:" -ForegroundColor White
    Write-Host "    Prometheus:     http://localhost:19091" -ForegroundColor DarkGray
    Write-Host "    Grafana:        http://localhost:3001" -ForegroundColor DarkGray
    Write-Host "    Alertmanager:  http://localhost:19093" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  常用命令:" -ForegroundColor White
    Write-Host "    查看日志:   docker compose logs -f" -ForegroundColor DarkGray
    Write-Host "    停止服务:   .\start.ps1 -Down" -ForegroundColor DarkGray
    Write-Host "    查看状态:   .\start.ps1 -Status" -ForegroundColor DarkGray
    Write-Host "============================================================" -ForegroundColor Cyan
}

# ============================================================
# 主逻辑
# ============================================================

if ($Down) {
    Write-Info "停止所有服务..."
    Invoke-Compose -Action 'down --volumes'
    Write-Ok "所有服务已停止"
    exit 0
}

if ($Status) {
    Push-Location $ProjectDir
    docker compose -f $ComposeFile ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    Pop-Location
    exit 0
}

if ($Logs) {
    Push-Location $ProjectDir
    docker compose -f $ComposeFile logs -f --tail 50
    Pop-Location
    exit 0
}

# 正常启动流程
Write-Host ""
Write-Host "  _    _       ____  _       _ _    " -ForegroundColor Cyan
Write-Host " | |  | |     / __ \| |     (_) |   " -ForegroundColor Cyan
Write-Host " | |__| | ___| |  | | |_ __  _| | __" -ForegroundColor Cyan
Write-Host " |  __  |/ _ \ |  | | | '_ \| | |/ /" -ForegroundColor Cyan
Write-Host " | |  | |  __/ |__| | | | | |   < " -ForegroundColor Cyan
Write-Host " |_|  |_|\___|\____/|_|_| |_|_|\_\" -ForegroundColor Cyan
Write-Host ""
Write-Host "  UAV Platform V2 - 一键启动" -ForegroundColor White
Write-Host ""

Test-Prerequisites
Initialize-Env

if (-not $SkipBuild) {
    Build-Maven
}

if ($InfraOnly) {
    Write-Info "启动基础设施..."
    Invoke-Compose -Action 'up -d' -Services @('mysql', 'redis', 'nacos', 'zookeeper', 'kafka') -Build
    Write-Info "等待基础设施就绪..."
    Wait-Healthy -Containers @('uav-mysql', 'uav-redis', 'uav-nacos') -TimeoutSeconds 120
    Write-Ok "基础设施已启动"
    exit 0
}

# 启动所有服务
Write-Info "启动所有服务..."
Invoke-Compose -Action 'up -d --build' -Build
if ($LASTEXITCODE -ne 0) {
    Write-Err "Docker Compose 启动失败"
    exit 1
}

Write-Info "等待核心服务就绪..."
Wait-Healthy -Containers @(
    'uav-mysql', 'uav-redis', 'uav-nacos',
    'uav-gateway', 'uav-platform-api',
    'uav-algorithm-engine', 'uav-console'
) -TimeoutSeconds 180

Show-Endpoints
