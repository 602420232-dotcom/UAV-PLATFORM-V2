# Contributing to UAV Edge SDK

Thank you for your interest in contributing to UAV Edge SDK!

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Style Guides](#style-guides)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/uav-edge-sdk.git
   cd uav-edge-sdk
   ```

3. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.8+
- CMake 3.10+
- C++ compiler (MSVC/GCC/Clang)
- Git

### Setup Development Environment

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Build C++ module
./build.sh  # Linux/macOS
.\build.bat  # Windows

# Run tests
cd tests
python test_edge_sdk.py
```

## Making Changes

1. **Keep your changes focused**
   - Work on one feature or fix at a time
   - Keep commits small and focused

2. **Write meaningful commit messages**
   ```
   feat: add new path planning algorithm
   
   - Implemented Dijkstra's algorithm as alternative to A*
   - Added comprehensive tests
   - Updated documentation
   ```

3. **Add tests**
   - Add tests for new features
   - Ensure all tests pass

4. **Update documentation**
   - Update README.md if needed
   - Add docstrings to new functions
   - Update CHANGELOG.md

## Pull Request Process

1. **Before submitting**
   - Run all tests
   - Check code style: `flake8 python/`
   - Run type checking: `mypy python/`

2. **Submit Pull Request**
   - Fill out the PR template
   - Link to any related issues
   - Request review from maintainers

3. **After review**
   - Address feedback
   - Keep branch updated with main
   - Squash commits if needed

## Style Guides

### Python Code

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints where possible
- Write docstrings in Google style

```python
def example_function(param1: int, param2: str) -> bool:
    """
    Brief description of the function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong
    """
    pass
```

### C++ Code

- Follow [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- Use C++14 standard
- Add comments for complex logic

### Git Commit Messages

- Use present tense: "add feature" not "added feature"
- Use imperative mood: "fix bug" not "fixes bug"
- Keep first line under 72 characters
- Add detailed description after blank line

## 🙏 Thank You!

Every contribution is appreciated. Thank you for making UAV Edge SDK better!
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
