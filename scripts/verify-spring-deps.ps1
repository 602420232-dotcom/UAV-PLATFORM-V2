# Spring Dependency Verification Script
# Purpose: Verify Spring dependencies are correctly resolved

param(
    [switch]$Verbose
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Spring Dependency Verification Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0

# Check 1: pom.xml versions
Write-Host "[Check 1/6] Verifying Spring versions in pom.xml..." -ForegroundColor Yellow
$pomContent = Get-Content pom.xml -Raw

if ($pomContent -match '<spring-boot\.version>([^<]+)</spring-boot\.version>') {
    $springBootVersion = $matches[1]
} else {
    $springBootVersion = "NOT FOUND"
}

if ($pomContent -match '<spring-cloud\.version>([^<]+)</spring-cloud\.version>') {
    $springCloudVersion = $matches[1]
} else {
    $springCloudVersion = "NOT FOUND"
}

Write-Host "  Spring Boot version: $springBootVersion" -ForegroundColor Cyan
Write-Host "  Spring Cloud version: $springCloudVersion" -ForegroundColor Cyan

# Check version compatibility
$compatible = @("3.2.5", "3.2.4", "3.2.3", "3.1.5", "3.0.9")
if ($compatible -contains $springBootVersion) {
    Write-Host "  [OK] Spring Boot version is compatible" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Spring Boot $springBootVersion may not be stable" -ForegroundColor Yellow
    $WarningCount++
}

# Check 2: Maven repository connection
Write-Host "`n[Check 2/6] Checking Maven repository connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://repo.maven.apache.org/maven2/org/springframework/boot/spring-boot-starter/2.7.18/spring-boot-starter-2.7.18.jar" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host "  [OK] Maven Central repository is accessible" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Maven repository connection failed: $($_.Exception.Message)" -ForegroundColor Red
    $ErrorCount++
}

# Check 3: Local Maven repository
Write-Host "`n[Check 3/6] Checking local Maven repository..." -ForegroundColor Yellow
$m2Repo = "$env:USERPROFILE\.m2\repository\org\springframework\boot"
if (Test-Path $m2Repo) {
    $springBootVersions = Get-ChildItem $m2Repo -Directory | Select-Object -First 5
    Write-Host "  Local Spring Boot versions:"
    foreach ($version in $springBootVersions) {
        Write-Host "    - $($version.Name)" -ForegroundColor Cyan
    }
    Write-Host "  [OK] Local repository exists" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Local repository not found, dependencies need to be downloaded" -ForegroundColor Yellow
    $WarningCount++
}

# Check 4: Maven dependency resolution
Write-Host "`n[Check 4/6] Verifying Maven dependency resolution..." -ForegroundColor Yellow
Write-Host "  (This may take a few minutes...)" -ForegroundColor Gray

try {
    $depOutput = mvn dependency:resolve -B 2>&1 | Out-String
    if ($depOutput -match "BUILD SUCCESS") {
        Write-Host "  [OK] All dependencies resolved successfully" -ForegroundColor Green
    } elseif ($depOutput -match "BUILD FAILURE") {
        Write-Host "  [ERROR] Dependency resolution failed" -ForegroundColor Red
        $ErrorCount++

        if ($depOutput -match "Could not resolve") {
            $matchesFound = [regex]::Matches($depOutput, "Could not resolve (.*)")
            Write-Host "  Missing dependencies:" -ForegroundColor Yellow
            $count = 0
            foreach ($match in $matchesFound) {
                if ($count -lt 3) {
                    Write-Host "    - $($match.Groups[1].Value)" -ForegroundColor Red
                    $count++
                }
            }
        }
    } else {
        Write-Host "  [WARN] Unable to determine build status" -ForegroundColor Yellow
        $WarningCount++
    }
} catch {
    Write-Host "  [ERROR] Maven command failed: $($_.Exception.Message)" -ForegroundColor Red
    $ErrorCount++
}

# Check 5: Project modules
Write-Host "`n[Check 5/6] Checking project modules..." -ForegroundColor Yellow
$modules = @(
    "api-gateway\pom.xml",
    "common-utils\pom.xml",
    "uav-platform-service\pom.xml"
)

foreach ($module in $modules) {
    if (Test-Path $module) {
        $moduleContent = Get-Content $module -Raw
        if ($moduleContent -match "org\.springframework") {
            Write-Host "  [OK] $module - Contains Spring dependencies" -ForegroundColor Green
        } else {
            Write-Host "  [INFO] $module - No Spring dependencies found" -ForegroundColor Gray
        }
    }
}

# Check 6: IDE configuration
Write-Host "`n[Check 6/6] Checking IDE configuration..." -ForegroundColor Yellow

if (Test-Path ".idea") {
    Write-Host "  [OK] IntelliJ IDEA configuration found" -ForegroundColor Green
    Write-Host "  TIP: Restart IDE and refresh Maven project" -ForegroundColor Cyan
} elseif (Test-Path ".vscode") {
    Write-Host "  [OK] VS Code configuration found" -ForegroundColor Green
    Write-Host "  TIP: Restart VS Code and wait for Maven indexing" -ForegroundColor Cyan
} else {
    Write-Host "  [INFO] No IDE configuration detected" -ForegroundColor Gray
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Errors: $ErrorCount" -ForegroundColor $(if ($ErrorCount -eq 0) { "Green" } else { "Red" })
Write-Host "Warnings: $WarningCount" -ForegroundColor $(if ($WarningCount -eq 0) { "Green" } else { "Yellow" })
Write-Host ""

if ($ErrorCount -eq 0 -and $WarningCount -eq 0) {
    Write-Host "[SUCCESS] All checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your Spring configuration appears to be correct." -ForegroundColor White
    Write-Host "If IDE still shows errors, try:" -ForegroundColor Yellow
    Write-Host "  1. Restart IDE" -ForegroundColor Gray
    Write-Host "  2. Clear IDE cache (Ctrl+Shift+Alt+/ -> Invalidate Caches)" -ForegroundColor Gray
    Write-Host "  3. Re-import Maven project" -ForegroundColor Gray
} elseif ($ErrorCount -eq 0) {
    Write-Host "[WARNING] Has warnings, but configuration is basically correct" -ForegroundColor Yellow
    Write-Host "Please make appropriate adjustments based on warnings" -ForegroundColor White
} else {
    Write-Host "[FAILURE] Errors found, need to fix" -ForegroundColor Red
    Write-Host ""
    Write-Host "Recommended action: Run fix script" -ForegroundColor Yellow
    Write-Host "  .\scripts\fix-spring-version.ps1" -ForegroundColor White
}

Write-Host ""
Write-Host "Documentation: docs/troubleshooting/SPRING_IMPORT_FIX.md" -ForegroundColor Gray
Write-Host ""
