# Quick Spring Version Fix Script
# Run this to automatically fix Spring version issues

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Spring Version Quick Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# Backup
$backup = "pom.xml.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item pom.xml $backup
Write-Host "Backup created: $backup" -ForegroundColor Green

# Read and fix
$content = Get-Content pom.xml -Raw

$content = $content -replace '<spring-boot\.version>.*?</spring-boot\.version>', '<spring-boot.version>3.2.5</spring-boot.version>'
$content = $content -replace '<spring-cloud\.version>.*?</spring-cloud\.version>', '<spring-cloud.version>2023.0.3</spring-cloud.version>'
$content = $content -replace '<spring-cloud-alibaba\.version>.*?</spring-cloud-alibaba\.version>', '<spring-cloud-alibaba.version>2023.0.1.0</spring-cloud-alibaba.version>'

Set-Content pom.xml -Value $content -NoNewline

Write-Host ""
Write-Host "Updated versions:" -ForegroundColor Yellow
Write-Host "  Spring Boot: 3.5.14 -> 3.2.5" -ForegroundColor White
Write-Host "  Spring Cloud: 2025.0.2 -> 2023.0.3" -ForegroundColor White
Write-Host "  Spring Cloud Alibaba: 2025.0.0.0 -> 2022.0.0.0" -ForegroundColor White
Write-Host ""
Write-Host "Now run: mvn clean install -DskipTests" -ForegroundColor Green
Write-Host ""
