# Installation Guide

This guide will help you install UAV Edge SDK on your system.

## 📋 Prerequisites

Before installing, make sure you have the following:

### Required

- **Python**: 3.8 or higher
  - Download from: https://www.python.org/downloads/
  - Verify: `python --version`

- **Git**: For version control
  - Download from: https://git-scm.com/download

### Build Tools

#### Windows

1. **Visual Studio** with "Desktop development with C++" workload
   - Download: https://visualstudio.microsoft.com/downloads/
   - Select: "Desktop development with C++"

2. **CMake** 3.10 or higher
   ```bash
   # Using winget (recommended)
   winget install Kitware.CMake
   
   # Or download from: https://cmake.org/download/
   ```

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    python3-dev \
    python3-pip \
    git
```

#### macOS

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install CMake
brew install cmake
```

## 🚀 Installation Methods

### Method 1: From Source (Recommended)

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/uav-edge-sdk.git
cd uav-edge-sdk
```

#### 2. Install Python Dependencies

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

#### 3. Build C++ Module

**Windows:**
```bash
.\build.bat
```

**Linux/macOS:**
```bash
chmod +x build.sh
./build.sh
```

#### 4. Verify Installation

```bash
cd tests
python test_edge_sdk.py
```

### Method 2: Using Make (Linux/macOS)

```bash
# Install dependencies
make dev

# Build C++ module
make build

# Run tests
make test
```

### Method 3: pip install (Coming Soon)

```bash
pip install uav-edge-sdk
```

## 🔧 Troubleshooting

### CMake not found

**Windows:**
```powershell
winget install Kitware.CMake
```

**Linux:**
```bash
sudo apt-get install cmake
```

**macOS:**
```bash
brew install cmake
```

### MSVC not found (Windows)

1. Open Visual Studio Installer
2. Click "Modify"
3. Select "Desktop development with C++"
4. Click "Install"

### Build fails with "pybind11 not found"

The CMakeLists.txt will automatically download pybind11. If you have issues:

```bash
pip install pybind11
```

### Python version mismatch

Make sure you're using Python 3.8 or higher:

```bash
python --version  # Should show 3.8+
```

### Permission denied (Linux/macOS)

```bash
chmod +x build.sh
./build.sh
```

## ✅ Verification

After installation, verify everything works:

```bash
python
>>> from edge_sdk import EdgeSDK
>>> sdk = EdgeSDK()
>>> path = sdk.plan_path((0, 0), (10, 10), [])
>>> print(f"Path length: {len(path)}")
>>> print("✅ Installation successful!")
```

## 📦 Optional Dependencies

### For Flight Controller Support

```bash
pip install pyserial
```

### For Development

```bash
pip install -r requirements-dev.txt
```

## 🎯 Next Steps

1. Read the [README.md](README.md)
2. Check out the [examples](tests/)

## 🔄 Updating

To update to the latest version:

```bash
git pull origin main
# Rebuild if needed
./build.sh  # or .\build.bat
```

## 📊 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Any 64-bit | Multi-core |
| RAM | 2 GB | 4 GB+ |
| Storage | 500 MB | 1 GB+ |
| OS | Windows 10, macOS 10.14, Ubuntu 18.04 | Latest versions |

---

**Happy coding! 🚀**
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
