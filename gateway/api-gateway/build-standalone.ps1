<#
.SYNOPSIS
    Build api-gateway as a standalone service with Spring Boot 3.4.x
.DESCRIPTION
    This script temporarily replaces api-gateway/pom.xml with the standalone
    module POM (which inherits from standalone-pom.xml using Spring Boot 3.4.5),
    builds the gateway, then restores the original pom.xml.
.EXAMPLE
    .\build-standalone.ps1
    .\build-standalone.ps1 -SkipTests
    .\build-standalone.ps1 -Clean
#>

param(
    [switch]$SkipTests,
    [switch]$Clean,
    [string]$MavenArgs = ""
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$GatewayDir = Join-Path $ProjectRoot "gateway"
$ApiGatewayDir = Join-Path $GatewayDir "api-gateway"

$OriginalPom = Join-Path $ApiGatewayDir "pom.xml"
$BackupPom = Join-Path $ApiGatewayDir "pom.xml.main-branch"
$StandaloneModulePom = Join-Path $ApiGatewayDir "standalone-module-pom.xml"
$StandaloneParentPom = Join-Path $GatewayDir "standalone-pom.xml"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  UAV Platform - Gateway Standalone Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Validate files exist
if (-not (Test-Path $OriginalPom)) {
    Write-Error "Original pom.xml not found: $OriginalPom"
    exit 1
}
if (-not (Test-Path $StandaloneModulePom)) {
    Write-Error "Standalone module POM not found: $StandaloneModulePom"
    exit 1
}
if (-not (Test-Path $StandaloneParentPom)) {
    Write-Error "Standalone parent POM not found: $StandaloneParentPom"
    exit 1
}

# Step 1: Backup original pom.xml
Write-Host "[1/4] Backing up original pom.xml..." -ForegroundColor Yellow
Copy-Item -Path $OriginalPom -Destination $BackupPom -Force
Write-Host "  -> Backed up to: $BackupPom" -ForegroundColor Gray

# Step 2: Replace with standalone module POM
Write-Host "[2/4] Replacing pom.xml with standalone module POM..." -ForegroundColor Yellow
Copy-Item -Path $StandaloneModulePom -Destination $OriginalPom -Force
Write-Host "  -> Using standalone parent: $StandaloneParentPom" -ForegroundColor Gray

# Step 3: Build
Write-Host "[3/4] Building gateway with Spring Boot 3.4.x..." -ForegroundColor Yellow

$buildArgs = @("clean", "package")
if ($SkipTests) {
    $buildArgs += "-DskipTests"
}
if ($MavenArgs) {
    $buildArgs += $MavenArgs
}

$buildCmd = "mvn $($buildArgs -join ' ') -f `"$StandaloneParentPom`""
Write-Host "  -> Command: $buildCmd" -ForegroundColor Gray
Write-Host ""

try {
    Push-Location $GatewayDir
    & mvn $buildArgs -f $StandaloneParentPom
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

# Step 4: Restore original pom.xml
Write-Host ""
Write-Host "[4/4] Restoring original pom.xml..." -ForegroundColor Yellow
Copy-Item -Path $BackupPom -Destination $OriginalPom -Force
Remove-Item -Path $BackupPom -Force -ErrorAction SilentlyContinue
Write-Host "  -> Original pom.xml restored" -ForegroundColor Gray

# Report result
Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  BUILD SUCCESSFUL" -ForegroundColor Green
    $jarPath = Join-Path $ApiGatewayDir "target" "api-gateway-2.0.0.jar"
    if (Test-Path $jarPath) {
        Write-Host "  JAR: $jarPath" -ForegroundColor Green
    }
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "To run the gateway:" -ForegroundColor Cyan
    Write-Host "  java -jar gateway/api-gateway/target/api-gateway-2.0.0.jar" -ForegroundColor White
    Write-Host "  java -jar gateway/api-gateway/target/api-gateway-2.0.0.jar --spring.profiles.active=local" -ForegroundColor White
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  BUILD FAILED (exit code: $exitCode)" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit $exitCode
}
