# UAV Path Planning - Windows Desktop Build Script
# This script builds and packages the Windows desktop application

param(
    [switch]$Build,
    [switch]$Package,
    [switch]$Clean,
    [string]$OutputDir = ".\dist"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$AppName = "uav_path_planning_app"
$Version = "1.0.0"

function Write-Step($message) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $message -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Clear-Build {
    Write-Step "Cleaning previous build artifacts..."
    if (Test-Path "build\windows") {
        Remove-Item -Path "build\windows" -Recurse -Force
        Write-Host "✓ Build directory cleaned" -ForegroundColor Green
    } else {
        Write-Host "✓ No previous build found" -ForegroundColor Green
    }
}

function Build-WindowsApp {
    Write-Step "Building Windows Desktop Application..."
    
    # Ensure Flutter is available
    try {
        $flutterVersion = flutter --version 2>&1
        Write-Host "Flutter Version: $flutterVersion" -ForegroundColor Gray
    } catch {
        Write-Error "Flutter is not installed or not in PATH"
        exit 1
    }
    
    # Get dependencies
    Write-Host "Getting dependencies..." -ForegroundColor Yellow
    flutter pub get
    
    # Build release
    Write-Host "Building release..." -ForegroundColor Yellow
    flutter build windows --release
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed with exit code $LASTEXITCODE"
        exit 1
    }
    
    Write-Host "✓ Build completed successfully!" -ForegroundColor Green
}

function Package-Application {
    Write-Step "Packaging Application..."
    
    $ReleasePath = "build\windows\x64\runner\Release"
    $PackageDir = "$OutputDir\windows-$Version"
    
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir | Out-Null
    }
    
    if (Test-Path $PackageDir) {
        Remove-Item -Path $PackageDir -Recurse -Force
    }
    
    New-Item -ItemType Directory -Path $PackageDir | Out-Null
    
    Write-Host "Copying build files..." -ForegroundColor Yellow
    Copy-Item -Path "$ReleasePath\*" -Destination $PackageDir -Recurse
    
    # Create ZIP archive
    $ZipPath = "$OutputDir\$AppName-windows-$Version.zip"
    Compress-Archive -Path $PackageDir -DestinationPath $ZipPath -Force
    
    Write-Host "✓ Package created: $ZipPath" -ForegroundColor Green
    Write-Host "✓ Package directory: $PackageDir" -ForegroundColor Green
    
    # Display package contents
    Write-Host "`nPackage contents:" -ForegroundColor Cyan
    Get-ChildItem $PackageDir | Select-Object Name, Length | Format-Table -AutoSize
}

function Show-BuildInfo {
    Write-Step "Build Information"
    
    $ExePath = "build\windows\x64\runner\Release\$AppName.exe"
    
    if (Test-Path $ExePath) {
        $FileInfo = Get-Item $ExePath
        $VersionInfo = $FileInfo.VersionInfo
        
        Write-Host "Executable: $($FileInfo.FullName)" -ForegroundColor Yellow
        Write-Host "Size: $([math]::Round($FileInfo.Length / 1KB, 2)) KB" -ForegroundColor Yellow
        Write-Host "File Version: $($VersionInfo.FileVersion)" -ForegroundColor Yellow
        Write-Host "Product Version: $($VersionInfo.ProductVersion)" -ForegroundColor Yellow
        Write-Host "Product Name: $($VersionInfo.ProductName)" -ForegroundColor Yellow
        Write-Host "Company: $($VersionInfo.CompanyName)" -ForegroundColor Yellow
        Write-Host "Description: $($VersionInfo.FileDescription)" -ForegroundColor Yellow
        
        # Calculate total package size
        $ReleasePath = "build\windows\x64\runner\Release"
        $TotalSize = (Get-ChildItem $ReleasePath -Recurse | Measure-Object -Property Length -Sum).Sum
        Write-Host "`nTotal Package Size: $([math]::Round($TotalSize / 1MB, 2)) MB" -ForegroundColor Cyan
    } else {
        Write-Warning "Executable not found. Run with -Build flag first."
    }
}

# Main execution
Write-Host "UAV Path Planning - Windows Build Script" -ForegroundColor Magenta
Write-Host "=========================================`n" -ForegroundColor Magenta

if ($Clean) {
    Clear-Build
}

if ($Build) {
    if ($Clean) {
        # Clean already happened, so just build
        Build-WindowsApp
    } else {
        # Ask to clean
        $cleanChoice = Read-Host "Clean previous build? (y/N)"
        if ($cleanChoice -eq 'y' -or $cleanChoice -eq 'Y') {
            Clear-Build
        }
        Build-WindowsApp
    }
}

if ($Package) {
    Package-Application
}

if ($Build -and $Package) {
    # Already built above
} elseif (-not $Build -and -not $Package -and -not $Clean) {
    # Show build info by default
    Show-BuildInfo
    
    Write-Host "`nUsage:" -ForegroundColor Yellow
    Write-Host "  -Build    Build the Windows application" -ForegroundColor Gray
    Write-Host "  -Package  Create distribution package" -ForegroundColor Gray
    Write-Host "  -Clean    Clean previous build artifacts" -ForegroundColor Gray
    Write-Host "`nExamples:" -ForegroundColor Yellow
    Write-Host "  .\build_windows.ps1 -Build -Package" -ForegroundColor Gray
    Write-Host "  .\build_windows.ps1 -Build -Clean -Package" -ForegroundColor Gray
    Write-Host "  .\build_windows.ps1 -Show" -ForegroundColor Gray
}

Write-Host "`nBuild script completed!" -ForegroundColor Green
