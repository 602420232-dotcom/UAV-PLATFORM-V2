# Spring版本自动修复脚本
# 用途: 将不兼容的Spring版本降级到稳定版本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Spring Framework 版本自动修复工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$pomPath = "pom.xml"
$backupPath = "pom.xml.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# 备份原文件
Write-Host "[1/5] 正在备份原配置文件..." -ForegroundColor Yellow
if (Test-Path $pomPath) {
    Copy-Item $pomPath $backupPath -Force
    Write-Host "✅ 备份完成: $backupPath" -ForegroundColor Green
} else {
    Write-Host "❌ pom.xml 文件不存在!" -ForegroundColor Red
    exit 1
}

# 读取pom.xml内容
Write-Host "`n[2/5] 正在读取配置文件..." -ForegroundColor Yellow
$content = Get-Content $pomPath -Raw

# 检查当前版本
if ($content -match '<spring-boot\.version>([^<]+)</spring-boot\.version>') {
    $currentSpringBoot = $matches[1]
    Write-Host "当前 Spring Boot 版本: $currentSpringBoot" -ForegroundColor Cyan
}

if ($content -match '<spring-cloud\.version>([^<]+)</spring-cloud\.version>') {
    $currentSpringCloud = $matches[1]
    Write-Host "当前 Spring Cloud 版本: $currentSpringCloud" -ForegroundColor Cyan
}

# 执行版本替换
Write-Host "`n[3/5] 正在更新Spring版本..." -ForegroundColor Yellow

$replacements = @{
    '<spring-boot\.version>.*?</spring-boot\.version>' = '<spring-boot.version>3.2.5</spring-boot.version>'
    '<spring-cloud\.version>.*?</spring-cloud\.version>' = '<spring-cloud.version>2023.0.3</spring-cloud.version>'
    '<spring-cloud-alibaba\.version>.*?</spring-cloud-alibaba\.version>' = '<spring-cloud-alibaba.version>2023.0.1.0</spring-cloud-alibaba.version>'
    '<spring-cloud-bootstrap\.version>.*?</spring-cloud-bootstrap\.version>' = '<spring-cloud-bootstrap.version>4.2.0</spring-cloud-bootstrap.version>'
    '<spring-cloud-starters\.version>.*?</spring-cloud-starters\.version>' = '<spring-cloud-starters.version>4.2.0</spring-cloud-starters.version>'
}

foreach ($pattern in $replacements.Keys) {
    if ($content -match $pattern) {
        $oldVersion = $matches[1]
        $content = $content -replace $pattern, $replacements[$pattern]
        Write-Host "  ✅ $pattern -> $($replacements[$pattern])" -ForegroundColor Green
    }
}

# 保存修改后的文件
Write-Host "`n[4/5] 正在保存修改..." -ForegroundColor Yellow
Set-Content $pomPath -Value $content -NoNewline
Write-Host "✅ 配置文件已更新" -ForegroundColor Green

# 清理Maven缓存
Write-Host "`n[5/5] 正在清理Maven缓存..." -ForegroundColor Yellow
Write-Host "  (这可能需要几分钟,请耐心等待...)" -ForegroundColor Gray

try {
    mvn clean dependency:purge-local-repository -DactTransitively=false -DreResolve=false -ErrorAction SilentlyContinue
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "✅ 修复完成!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "修改内容:" -ForegroundColor Yellow
    Write-Host "  • Spring Boot: $currentSpringBoot -> 3.2.5" -ForegroundColor White
    Write-Host "  • Spring Cloud: $currentSpringCloud -> 2023.0.3" -ForegroundColor White
    Write-Host ""
    Write-Host "下一步操作:" -ForegroundColor Yellow
    Write-Host "  1. 刷新IDE中的Maven项目" -ForegroundColor White
    Write-Host "  2. 或者重启IDE" -ForegroundColor White
    Write-Host "  3. 运行: mvn clean install -DskipTests" -ForegroundColor White
    Write-Host ""
    Write-Host "备份文件位置: $backupPath" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "⚠️ Maven清理过程中出现错误,但配置文件已更新" -ForegroundColor Yellow
    Write-Host "请手动运行: mvn clean install -DskipTests" -ForegroundColor Yellow
}

# 等待用户确认
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
