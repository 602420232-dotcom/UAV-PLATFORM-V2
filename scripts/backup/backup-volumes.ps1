# ============================================================
# Docker 数据卷备份脚本 (Windows PowerShell)
# ============================================================

$BackupDir = if ($args[0]) { $args[0] } else { ".\backups" }
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupPath = Join-Path $BackupDir $Timestamp
$RetentionDays = if ($env:RETENTION_DAYS) { [int]$env:RETENTION_DAYS } else { 30 }
$LogFile = Join-Path $BackupDir "backup.log"

New-Item -ItemType Directory -Force -Path $BackupPath | Out-Null

function Write-Log {
    param([string]$Message)
    $time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$time $Message" | Tee-Object -FilePath $LogFile -Append
}

Write-Log "=== 开始数据卷备份: $Timestamp ==="

# 1. 备份 Docker 数据卷
Write-Log "[1/3] 备份 Docker 数据卷..."
$volumes = docker volume ls --format "{{.Name}}" | Where-Object { $_ -match '^(uav|trae|mysql|redis)' }
foreach ($volume in $volumes) {
    Write-Log "  正在备份: $volume"
    $outFile = Join-Path $BackupPath "volume-$volume.tar.gz"
    $null = docker run --rm -v "${volume}:/source" -v "${BackupPath}:/backup" alpine:3.18 tar czf "/backup/volume-$volume.tar.gz" -C /source . 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "  ✅ $volume 备份成功"
    } else {
        Write-Log "  ⚠️ $volume 备份失败"
    }
}

# 2. MySQL 逻辑备份
Write-Log "[2/3] MySQL 逻辑备份..."
$mysqlContainer = docker ps --filter "name=uav-mysql" --format "{{.Names}}" 2>$null
if ($mysqlContainer) {
    $databases = @("uav_platform", "path_planning", "wrf_processor", "meteor_forecast", "data_assimilation", "uav_weather")
    foreach ($db in $databases) {
        $outFile = Join-Path $BackupPath "mysql-$db.sql"
        $null = docker exec $mysqlContainer mysqldump --single-transaction -u root -p"${env:MYSQL_ROOT_PASSWORD}" $db 2>$null > $outFile
        if ($LASTEXITCODE -eq 0 -and (Get-Item $outFile).Length -gt 0) {
            Write-Log "  ✅ $db 备份成功"
        } else {
            Write-Log "  ⚠️ $db 备份失败"
        }
    }
} else {
    Write-Log "  ⚠️ MySQL 容器未运行"
}

# 3. 生成备份报告
Write-Log "生成备份报告..."
Get-ChildItem $BackupPath | ForEach-Object {
    "$($_.Name) ($( [math]::Round($_.Length / 1KB) ) KB)"
} | Out-File (Join-Path $BackupPath "MANIFEST.txt")

Write-Log "=== 备份完成 ==="
