#!/bin/bash
# UAV Edge SDK - Build Script
# Builds the C++ pybind11 module for maximum performance
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  UAV Edge SDK Build Script"
echo "============================================"
echo ""

# Check prerequisites
echo "[1/5] Checking prerequisites..."

command -v cmake >/dev/null 2>&1 || { echo "ERROR: cmake is required but not installed."; exit 1; }
echo "  ✓ cmake: $(cmake --version | head -1)"

command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required but not installed."; exit 1; }
echo "  ✓ python3: $(python3 --version)"

# Check pybind11
python3 -c "import pybind11" 2>/dev/null || {
    echo "  Installing pybind11..."
    pip3 install pybind11
}
echo "  ✓ pybind11: $(python3 -c 'import pybind11; print(pybind11.__version__)')"

# Check numpy
python3 -c "import numpy" 2>/dev/null || {
    echo "  Installing numpy..."
    pip3 install numpy
}

# Create build directory
echo ""
echo "[2/5] Creating build directory..."
mkdir -p build

# Configure
echo ""
echo "[3/5] Configuring with CMake..."
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release

# Build
echo ""
echo "[4/5] Building C++ module..."
cmake --build build --config Release -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)

# Copy module
echo ""
echo "[5/5] Installing Python module..."
if [ -f "build/edge_sdk_cpp.pyd" ]; then
    cp build/edge_sdk_cpp.pyd edge_sdk/
    echo "  ✓ Installed edge_sdk_cpp.pyd (Windows)"
elif [ -f "build/edge_sdk_cpp.so" ]; then
    cp build/edge_sdk_cpp.so edge_sdk/
    echo "  ✓ Installed edge_sdk_cpp.so (Linux)"
else
    # Try to find in subdirectories
    find build -name "edge_sdk_cpp.*" -exec cp {} edge_sdk/ \;
    echo "  ✓ C++ module built and installed"
fi

# Verify
echo ""
echo "Verifying build..."
python3 -c "
from edge_sdk._core import HAS_CPP_MODULE
if HAS_CPP_MODULE:
    print('  ✓ C++ module loaded successfully!')
    from edge_sdk import create_sdk
    sdk = create_sdk()
    print('  ✓ EdgeSDK initialized with C++ acceleration')
else:
    print('  ⚠ C++ module not loaded. Check build output above.')
"

echo ""
echo "============================================"
echo "  Build complete!"
echo "============================================"
echo ""
echo "To run tests:"
echo "  cd tests && python test_edge_sdk.py"
echo ""
