# Flutter Web 启动脚本 (Windows PowerShell) — 自动检测 WSL2 IP 注入
# 用法: .\run_web.ps1 [chrome|edge]

param([string]$Target = "chrome")

# 从 WSL 获取 IP
$wslIp = (wsl -- ip addr show eth0 2>$null | Select-String "inet " | ForEach-Object { $_ -replace '.*inet (\d+\.\d+\.\d+\.\d+).*', '$1' } | Select-Object -First 1)

if (-not $wslIp) {
    Write-Host "⚠️  未检测到 WSL2 IP，回退到 localhost" -ForegroundColor Yellow
    $apiUrl = "http://localhost:8088"
} else {
    $apiUrl = "http://${wslIp}:8088"
    Write-Host "🌐 WSL2 IP: ${wslIp}" -ForegroundColor Cyan
    Write-Host "📡 API:    ${apiUrl}" -ForegroundColor Cyan
}

Write-Host "🚀 启动 Flutter Web (${Target})..." -ForegroundColor Green
flutter run -d $Target --dart-define=API_BASE_URL=$apiUrl
