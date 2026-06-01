@echo off
REM UAV Edge SDK - Windows Build Script

echo ============================================
echo   UAV Edge SDK - Windows Build
echo ============================================
echo.

REM Check if CMake is installed
where cmake >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] CMake not found!
    echo Please install CMake from: https://cmake.org/download/
    echo.
    echo Or use winget:
    echo   winget install Kitware.CMake
    echo.
    pause
    exit /b 1
)

REM Check if Visual Studio is installed
where msbuild >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Visual Studio (MSBuild) not found!
    echo Please install Visual Studio with "Desktop development with C++" workload.
    echo.
    pause
    exit /b 1
)

echo [INFO] CMake found
echo [INFO] MSBuild found
echo.

REM Create build directory
if not exist build (
    echo [INFO] Creating build directory...
    mkdir build
)

cd build

echo [INFO] Configuring CMake...
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] CMake configuration failed!
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] Building C++ module...
cmake --build . --config Release

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    echo.
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
echo You can now use the C++ module in Python:
echo.
echo   from edge_sdk import EdgeSDK
echo   sdk = EdgeSDK()
echo.
echo To run tests:
echo.
echo   cd tests
echo   python test_edge_sdk.py
echo.
echo ============================================
pause
