# UAV Path Planning System - 自动化脚本集

## 📋 概述

本目录包含 UAV Path Planning System 的各种自动化脚本，用于代码质量提升、安全修复、测试生成等任务。

---

## 📁 脚本分类

### 🔧 代码质量工具

#### 1. 类型注解相关

| 脚本 | 功能 | 使用方法 |
|------|------|---------|
| `auto_add_type_annotations.py` | 自动分析并生成类型注解建议 | `python auto_add_type_annotations.py` |
| `apply_type_annotations.py` | 应用类型注解到代码 | `python apply_type_annotations.py` |

**功能说明**:
- 扫描所有 Python 文件
- 分析函数签名和返回值
- 生成类型注解建议报告
- 支持批量应用

**使用示例**:
```bash
cd scripts

# 分析项目，生成类型注解报告
python auto_add_type_annotations.py

# 应用类型注解到代码
python apply_type_annotations.py
```

---

#### 2. 代码格式化

| 脚本 | 功能 | 使用方法 |
|------|------|---------|
| `fix_print_statements.py` | 替换 print 为 logging | `python fix_print_statements.py` |
| `batch_fix_print.ps1` | PowerShell 批量替换脚本 | `./batch_fix_print.ps1` |

**功能说明**:
- 替换 `print()` 为 `logging.getLogger().debug/info/warning/error()`
- 保留调试信息，便于生产环境排查问题
- 支持批量处理多个文件

**使用示例**:
```bash
# 单个文件
python fix_print_statements.py path/to/file.py

# PowerShell 批量处理
./batch_fix_print.ps1

# Bash 批量处理
bash fix_print_statements.sh
```

---

### 🧪 测试相关

#### 1. 单元测试生成

| 脚本 | 功能 | 使用方法 |
|------|------|---------|
| `auto_generate_tests.py` | 自动生成单元测试框架 | `python auto_generate_tests.py` |
| `complete_unit_tests.py` | 补充单元测试逻辑 | `python complete_unit_tests.py` |

**功能说明**:
- 分析源代码结构和函数签名
- 自动生成 pytest 测试框架
- 包含 mock 和 fixture
- 支持补充 TODO 标记

**使用示例**:
```bash
# 生成测试框架
python auto_generate_tests.py

# 补充测试逻辑
python complete_unit_tests.py

# 运行测试
pytest test_*.py -v
```

**生成文件示例**:
```python
import pytest
from your_module import your_function

class TestYourFunction:
    """测试类: YourFunction"""
    
    @pytest.fixture
    def setup(self):
        """初始化测试环境"""
        # TODO: 替换为实际的初始化代码
        return {}
    
    def test_your_function_success(self, setup):
        """测试函数: your_function 成功场景"""
        # TODO: 实现测试逻辑
        assert True  # TODO: 替换为实际断言
```

---

### 🔍 代码质量检查

#### 1. 代码质量分析

| 脚本 | 功能 | 使用方法 |
|------|------|---------|
| `code_quality_checker.py` | 检查代码质量指标 | `python code_quality_checker.py` |
| `config_checker.py` | 检查配置文件安全性 | `python config_checker.py` |
| `config_checker_simple.py` | 简化版配置检查 | `python config_checker_simple.py` |

**检查项**:
- 代码重复率
- 函数复杂度
- 注释覆盖率
- 命名规范
- 安全漏洞检测

**使用示例**:
```bash
# 代码质量检查
python code_quality_checker.py

# 输出示例
======================== Code Quality Report ========================
Files scanned: 350
Total warnings: 27
  - High: 5
  - Medium: 12
  - Low: 10
================================================================
```

---

#### 2. 安全配置检查

**检查项**:
- 硬编码密码检测
- SQL 注入风险
- XSS 漏洞检测
- API 密钥暴露
- CORS 配置错误

**使用示例**:
```bash
# 检查所有配置文件
python config_checker_simple.py

# 输出示例
======================== Config Check Report ======================
Files scanned: 88
Issues found: 4
  - Hardcoded password: 2
  - Missing CSRF protection: 1
  - CORS misconfiguration: 1
================================================================
```

---

### 🔐 安全修复工具

#### 1. 生产密钥生成

| 脚本 | 功能 | 使用方法 |
|------|------|---------|
| `generate_secrets.py` | 生成强密钥和配置 | `python generate_secrets.py` |

**功能说明**:
- 生成强随机密钥（JWT、数据库、Redis等）
- 支持 Base64 编码
- 生成 `.env.example` 模板
- 提供安全警告和使用指南

**使用示例**:
```bash
python generate_secrets.py

# 输出示例
======================== Secret Generation =======================
JWT_SECRET=your-jwt-secret-here
DB_PASSWORD=your-db-password-here
REDIS_PASSWORD=your-redis-password-here
================================================================
WARNING: Please configure these secrets in production immediately!
```

---

### 🚀 综合工具

#### 1. 全自动修复工具

| 脚本 | 功能 | 使用方法 |
|------|------|---------|
| `comprehensive_auto_fixer.py` | 综合自动化修复 | `python comprehensive_auto_fixer.py` |

**功能说明**:
- 自动修复代码质量问题
- 应用所有改进建议
- 生成修复报告
- 支持增量修复

**使用示例**:
```bash
# 执行所有自动修复
python comprehensive_auto_fixer.py

# 生成修复报告
cat fix_report_2026-05-08.md
```

---

### 🛠️ 构建和部署脚本

#### 1. Maven 依赖修复

| 脚本 | 功能 | 使用方法 |
|------|------|---------|
| `fix-maven-deps.sh` | Linux/Mac Maven 依赖修复 | `bash fix-maven-deps.sh` |
| `fix-maven-deps.bat` | Windows Maven 依赖修复 | `fix-maven-deps.bat` |

**功能说明**:
- 清理 Maven 缓存
- 重新下载依赖
- 修复损坏的依赖
- 支持离线模式

**使用示例**:
```bash
# Linux/Mac
bash fix-maven-deps.sh

# Windows
fix-maven-deps.bat
```

---

## 📊 使用指南

### 推荐的执行顺序

#### 1. 新项目初始化

```bash
# 1. 生成生产密钥
python generate_secrets.py

# 2. 检查代码质量
python code_quality_checker.py

# 3. 生成测试框架
python auto_generate_tests.py

# 4. 应用类型注解
python apply_type_annotations.py
```

#### 2. 代码审查前

```bash
# 1. 代码质量检查
python code_quality_checker.py

# 2. 安全配置检查
python config_checker_simple.py

# 3. 生成报告
python comprehensive_auto_fixer.py --dry-run
```

#### 3. CI/CD 集成

```bash
# 在 CI 管道中运行
python code_quality_checker.py --fail-on-high
python config_checker_simple.py
```

---

## 🔧 环境要求

### Python 环境

```bash
# Python 版本要求
Python >= 3.8

# 必需依赖
pip install pytest pylint black flake8

# 可选依赖
pip install mypy typescript
```

### PowerShell 环境 (Windows)

```powershell
# PowerShell 版本
PowerShell >= 5.1

# 执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📝 输出报告

### 生成的文件

| 报告文件 | 内容 | 位置 |
|---------|------|------|
| `type_annotations_report.txt` | 类型注解建议 | scripts/ |
| `test_generation_report.txt` | 测试生成报告 | scripts/ |
| `config_check_report.txt` | 配置检查报告 | scripts/ |
| `code_quality_report.txt` | 代码质量报告 | scripts/ |
| `fix_report_*.md` | 综合修复报告 | scripts/ |

### 报告示例

**code_quality_report.txt**:
```
======================== Code Quality Report ========================
Generated: 2026-05-08 16:30:15
Files scanned: 350

Metrics:
  - Average function length: 15 lines
  - Code coverage: 72%
  - Comment ratio: 25%
  - Naming violations: 8

Recommendations:
  - Consider adding type hints to 580 functions
  - Simplify 12 complex functions
  - Add docstrings to 45 functions
================================================================
```

---

## ⚙️ 配置文件

### 脚本配置

某些脚本支持通过环境变量或配置文件自定义：

```bash
# .env 文件示例
LOG_LEVEL=INFO
REPORT_FORMAT=markdown
ENABLE_PARALLEL=true
MAX_WORKERS=4
```

### 忽略文件

脚本使用 `.scriptignore` 文件排除不需要处理的文件和目录。

**已创建的配置文件**: `.scriptignore`

**文件位置**: `scripts/.scriptignore`

**主要排除内容**:

```bash
# Python 虚拟环境
venv/
env/
.venv/

# Python 缓存
__pycache__/
*.py[cod]

# Node.js 依赖
node_modules/

# Maven/Gradle 构建
target/
build/
.gradle/

# 日志和临时文件
*.log
logs/

# 测试文件
test_*.py
*_test.py

# 文档
*.md
*.txt

# 大文件和二进制
*.zip
*.tar.gz
*.png
*.jpg

# 第三方库
vendor/
*.a
*.so

# Git
.git/
.gitignore
```

**使用方式**:

脚本会自动读取 `.scriptignore` 文件并排除匹配的文件。

**添加自定义规则**:

编辑 `scripts/.scriptignore` 文件添加自定义规则：

```bash
# 添加排除规则
echo "custom_dir/" >> .scriptignore
echo "*.custom" >> .scriptignore
```

**规则说明**:

| 规则 | 说明 | 示例 |
|------|------|------|
| `dir/` | 排除目录 | `venv/` |
| `*.ext` | 排除文件 | `*.py` |
| `**/pattern` | 递归匹配 | `**/__pycache__` |
| `# comment` | 注释 | `# 这是注释` |
| `!pattern` | 取反（包含） | `!important.py` |

---

## 🚨 故障排查

### 常见问题

#### 1. Python 依赖缺失

```bash
# 安装必需依赖
pip install pytest pylint black

# 验证安装
python -c "import pytest; print(pytest.__version__)"
```

#### 2. PowerShell 执行策略错误

```powershell
# 查看当前策略
Get-ExecutionPolicy

# 修改策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 3. 脚本执行权限

```bash
# Linux/Mac 添加执行权限
chmod +x *.sh
chmod +x *.py

# Windows 使用 PowerShell
.\script.ps1
```

---

## 🤝 贡献指南

### 添加新脚本

1. **遵循命名规范**:
   - Python 脚本: `snake_case.py`
   - Shell 脚本: `kebab-case.sh`
   - PowerShell: `PascalCase.ps1`

2. **添加文档注释**:
   ```python
   """
   脚本名称: example_script.py
   功能: 简短的脚本功能描述
   作者: Your Name
   日期: 2026-05-08
   """
   ```

3. **创建测试**:
   ```bash
   pytest test_example_script.py
   ```

4. **更新本文档**:
   - 添加脚本到相应的分类
   - 提供使用示例
   - 说明输出格式

---

## 📄 许可证

本目录下的脚本遵循项目整体许可证。


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
