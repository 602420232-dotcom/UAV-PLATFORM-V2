# PowerShell批量修复脚本 - 替换所有print()为logging
# 用法: .\batch_fix_print.ps1

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "批量修复Python print()语句" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$count = 0
$total = 0

# 获取所有Python文件
$pythonFiles = Get-ChildItem -Path "d:\Developer\workplace\py\iteam\trae" -Recurse -Filter "*.py" | Where-Object { $_.FullName -notlike "*__pycache__*" -and $_.FullName -notlike "*test_*" }

Write-Host "找到 $($pythonFiles.Count) 个Python文件" -ForegroundColor Yellow

foreach ($file in $pythonFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    
    # 检查是否有print语句
    if ($content -match '\bprint\s*\(') {
        $original = $content
        
        # 替换 print("...") 为 logger.info("...")
        $content = $content -replace 'print\s*\(\s*"(.*?)"\s*\)', 'logger.info("$1")'
        
        # 替换 print(f"...") 为 logger.info(f"...")
        $content = $content -replace 'print\s*\(\s*f"(.*?)"\s*\)', 'logger.info(f"$1")'
        
        # 替换 print('...') 为 logger.info('...')
        $content = $content -replace "print\s*\(\s*'(.*?)'\s*\)", "logger.info('$1')"
        
        # 替换 print(f'...') 为 logger.info(f'...')
        $content = $content -replace "print\s*\(\s*f'(.*?)'\s*\)", "logger.info(f'$1')"
        
        # 如果有改动，写入文件
        if ($content -ne $original) {
            # 添加logging导入（如果还没有）
            if ($content -notmatch 'import logging') {
                $content = $content -replace '(^import [^\r\n]+)', "`$1`nimport logging"
            }
            
            Set-Content -Path $file.FullName -Value $content -Encoding UTF8
            $count++
            Write-Host "修复: $($file.Name)" -ForegroundColor Green
        }
        $total++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "修复完成!" -ForegroundColor Green
Write-Host "处理文件数: $total" -ForegroundColor Yellow
Write-Host "实际修复数: $count" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
