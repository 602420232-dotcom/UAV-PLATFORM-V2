# 数据适配器测试指南

## 概述

本指南介绍如何运行数据适配器测试、解读测试结果以及集成到CI/CD流水线中。

## 运行测试

### 基本运行

在 `algorithm_core/examples` 目录下运行：

```bash
python test_adapters.py
```

### CI模式运行

在CI环境中运行，减少日志输出：

```bash
python test_adapters.py --ci
```

### 仅运行性能测试

```bash
python test_adapters.py --performance-only
```

## 依赖项

- **必要依赖**：
  - numpy

- **可选依赖**：
  - psutil (用于内存监控)
  - pytest (用于测试框架)
  - requests (用于Slack通知)

## 测试报告

测试完成后，会在 `test_output` 目录下生成以下报告：

1. **test_report.json** - JSON格式的测试报告
2. **test_report.html** - HTML格式的测试报告，包含详细的性能指标
3. **test_report.xml** - JUnit XML格式的测试报告，用于CI系统集成

## 性能基线

性能测试会检查以下基线指标：

| 指标 | 基线值 | 说明 |
|------|--------|------|
| 处理速度 | ≥ 100万点/秒 | 数据处理的最小速度要求 |
| 内存使用 | ≤ 1GB | 最大内存使用限制 |
| 网格插值时间 | ≤ 1秒 | 网格插值操作的最大时间 |

## CI/CD集成

### GitHub Actions

已配置 `.github/workflows/test.yml` 流水线，会在以下情况自动运行：
- 推送到 `main` 或 `dev` 分支
- 对 `main` 分支的拉取请求

### Jenkins

已配置 `Jenkinsfile` 流水线，可直接在Jenkins中使用。

## 通知系统

测试完成后，可通过以下方式发送通知：

### Slack通知

设置环境变量 `SLACK_WEBHOOK_URL` 即可启用Slack通知。

### 邮件通知

设置以下环境变量启用邮件通知：
- `SMTP_SERVER` - SMTP服务器地址
- `SMTP_USER` - SMTP用户名
- `SMTP_PASSWORD` - SMTP密码
- `TEST_EMAIL` - 接收通知的邮箱

## 测试结果解读

### 成功状态

- **✅ 全部通过** - 所有测试都通过，性能达到基线要求

### 失败状态

- **❌ 部分失败** - 部分测试失败或性能未达到基线要求

### 性能指标

HTML报告中包含以下性能指标：
- 处理数据点 - 测试处理的数据总量
- 处理时间 - 总处理时间（秒）
- 处理速度 - 数据处理速度（点/秒）
- 内存使用 - 内存使用量（MB）
- 网格插值耗时 - 网格插值操作的时间
- 数据转换耗时 - 数据格式转换的时间
- 观测数据适配耗时 - 观测数据适配的时间
- 网格转点耗时 - 网格数据转点数据的时间

## 故障排除

### 常见错误

1. **ModuleNotFoundError: No module named 'numpy'**
   - 解决方案：安装numpy `pip install numpy`

2. **生成HTML测试报告失败: unsupported format character**
   - 解决方案：确保HTML模板文件格式正确，无格式错误

3. **性能基线检查失败**
   - 解决方案：检查系统资源使用情况，考虑优化代码或增加硬件资源

## 自定义测试

### 修改测试数据量

在 `test_performance()` 函数中修改 `large_data` 的大小：

```python
large_data = {
    'wind_speed': np.random.rand(300, 300, 120),  # 10,800,000 points
    # ...
}
```

### 修改性能基线

在 `check_performance_baseline()` 函数中修改基线值：

```python
baselines = {
    'min_speed': 1000000,      # 最小处理速度：100万点/秒
    'max_memory': 1024,        # 最大内存使用：1GB
    'max_grid_interpolate': 1.0 # 网格插值最大时间：1秒
}
```
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
