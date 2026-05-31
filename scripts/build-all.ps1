# Build All - Windows PowerShell Script

# Navigate to project root (one level up from scripts/)
Set-Location $PSScriptRoot\..

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building UAV Platform Docker Images" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Build base images
Write-Host "[1/9] Building uav-base image..." -ForegroundColor Green
docker build -t uav-base:latest -f docker/base/Dockerfile .

Write-Host "[2/9] Building uav-python image..." -ForegroundColor Green
docker build -t uav-python:latest -f docker/base/python/Dockerfile .

Write-Host ""
Write-Host "Building service images..." -ForegroundColor Yellow
Write-Host ""

# Build service images
$services = @(
    @{name="api-gateway"; port="8088"},
    @{name="data-assimilation-service"; port="8084"},
    @{name="meteor-forecast-service"; port="8082"},
    @{name="path-planning-service"; port="8083"},
    @{name="wrf-processor-service"; port="8081"},
    @{name="uav-platform-service"; port="8080"},
    @{name="uav-weather-collector"; port="8086"}
)

$index = 3
foreach ($service in $services) {
    $tagName = $service.name -replace '^uav-', ''
    Write-Host "[$index/9] Building uav-$tagName..." -ForegroundColor Green
    docker build -t "uav-$tagName:latest" -f "$($service.name)/Dockerfile.runtime" "$($service.name)"
    $index++
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build completed successfully!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
