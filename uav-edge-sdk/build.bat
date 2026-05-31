@echo off
REM UAV Edge SDK - Windows Build Script (Auto-Detect VS Version)
setlocal enabledelayedexpansion

echo ============================================
echo   UAV Edge SDK - Windows Build
echo ============================================
echo.

REM Check if CMake is installed
where cmake >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] CMake not found!
    echo Please install CMake from: https://cmake.org/download/
    echo Or use: winget install Kitware.CMake
    pause
    exit /b 1
)

echo [INFO] CMake found: 
cmake --version | findstr /i "version"

REM Auto-detect available Visual Studio generator
echo [INFO] Detecting Visual Studio...
set "VS_GENERATOR="

REM List available VS generators and pick the latest
for /f "delims=" %%G in ('cmake --help ^| findstr /R /C:"Visual Studio 1[6-9] 20[12][0-9]"') do (
    set "VS_GENERATOR=%%G"
)

REM Trim leading spaces and asterisks
for /f "tokens=*" %%G in ("!VS_GENERATOR!") do set "VS_GENERATOR=%%G"
set "VS_GENERATOR=!VS_GENERATOR:  =!"
set "VS_GENERATOR=!VS_GENERATOR:* =!"
set "VS_GENERATOR=!VS_GENERATOR: =!"

if "!VS_GENERATOR!"=="" (
    echo [WARN] No Visual Studio generator found via cmake.
    echo [INFO] Trying MSBuild detection...
    where msbuild >nul 2>&1
    if !errorlevel! neq 0 (
        echo [ERROR] MSBuild not found either.
        echo Please install Visual Studio 2022+ with "Desktop development with C++" workload.
        pause
        exit /b 1
    )
    echo [INFO] MSBuild found. Letting CMake auto-select generator...
    set "CMAKE_GEN_ARG="
) else (
    echo [INFO] Detected: !VS_GENERATOR!
    set "CMAKE_GEN_ARG=-G "!VS_GENERATOR!" -A x64"
    REM Also verify MSBuild
    where msbuild >nul 2>&1 || (
        echo [WARN] MSBuild not in PATH, but continuing with CMake...
    )
)

echo.

REM Create build directory
if not exist build (
    echo [INFO] Creating build directory...
    mkdir build
)

cd build

echo [INFO] Configuring CMake...
if "!CMAKE_GEN_ARG!"=="" (
    cmake .. -DCMAKE_BUILD_TYPE=Release
) else (
    cmake .. !CMAKE_GEN_ARG! -DCMAKE_BUILD_TYPE=Release
)

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] CMake configuration failed!
    echo.
    echo Troubleshooting:
    echo   1. Ensure Visual Studio with C++ workload is installed
    echo   2. Try running from "Developer Command Prompt for VS"
    echo   3. Or build via WSL: bash build.sh
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] Building C++ module...
cmake --build . --config Release

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Build failed! See logs above.
    pause
    exit /b 1
)

echo.
echo [INFO] Installing to python directory...
cmake --install . --config Release

echo.
echo ============================================
echo   Build Complete!
echo ============================================
echo.
echo Usage in Python:
echo   from edge_sdk import EdgeSDK
echo   sdk = EdgeSDK()
echo.
echo Run tests:
echo   cd ..\tests
echo   python test_edge_sdk.py
echo ============================================
endlocal
pause
