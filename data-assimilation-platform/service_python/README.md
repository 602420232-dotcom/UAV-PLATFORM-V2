# Data Assimilation Python Service

## 📋 服务概述

Python 微服务，提供数据同化算法的独立 API 接口。

**技术栈**:
- Python 3.8+
- Flask/FastAPI
- NumPy, SciPy
- Pandas

**服务端口**: 5000

---

## 📁 项目结构

```
service_python/
├── api/
│   ├── routes/         # API 路由
│   ├── schemas/        # 数据模式
│   └── main.py        # 应用入口
├── models/            # 数据模型
├── utils/             # 工具函数
├── config.py          # 配置
├── requirements.txt    # 依赖
└── README.md          # 本文档
```

---

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行服务

```bash
python -m api.main
# 或
flask run --port 5000
```

---

## 🔌 API 接口

### 同化接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/assimilate` | POST | 执行同化 |
| `/api/v1/variance` | POST | 计算方差 |
| `/health` | GET | 健康检查 |

---

## 🧪 测试

```bash
pytest tests/ -v
```

---

**最后更新**: 2026-05-08
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
