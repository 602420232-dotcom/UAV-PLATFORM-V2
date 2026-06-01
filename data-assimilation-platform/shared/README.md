# Shared Resources - 共享资源

## 📋 概述

共享资源模块，包含 Protocol Buffers 定义、JSON Schema、共享配置等跨服务共用资源。

---

## 📁 目录结构

```
shared/
├── protos/                    # Protocol Buffers 定义
│   ├── common/               # 公共消息类型
│   │   ├── common.proto
│   │   ├── types.proto
│   │   └── README.md
│   ├── assimilation/         # 数据同化消息
│   │   ├── request.proto
│   │   └── response.proto
│   └── README.md
│
├── schemas/                 # JSON Schema 定义
│   ├── assimilation/
│   └── validation/
│
└── README.md                # 本文档
```

---

## 📦 Protos 子模块

### Protocol Buffers 定义

**位置**: `protos/`

**包含文件**:

- `common/common.proto` - 公共消息类型
- `common/types.proto` - 通用类型定义
- `assimilation/request.proto` - 同化请求
- `assimilation/response.proto` - 同化响应

### 编译 Proto 文件

#### Python 编译

```bash
# 安装 protoc 插件
pip install grpcio grpcio-tools

# 编译 Proto 文件
cd protos
protoc --python_out=. -I. assimilation/*.proto common/*.proto

# 生成文件
ls -la assimilation/*.py
ls -la common/*.py
```

#### Java 编译

```bash
# 安装 protoc 插件 (Maven)
mvn protobuf:compile

# 或使用命令行
protoc --java_out=. -I. assimilation/*.proto common/*.proto
```

### Proto 使用示例

**Python**:
```python
import grpc
from protos.assimilation import request_pb2, request_pb2_grpc
from protos.common import types_pb2

# 创建请求
request = request_pb2.AssimilationRequest(
    algorithm=request_pb2.AlgorithmType.VAR_3D,
    observations=[...],
    background=types_pb2.GridData(...)
)

# 调用服务
channel = grpc.insecure_channel('localhost:8084')
stub = request_pb2_grpc.AssimilationServiceStub(channel)
response = stub.Assimilate(request)
```

**Java**:
```java
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import com.uav.assimilation.*;

ManagedChannel channel = ManagedChannelBuilder
    .forAddress("localhost", 8084)
    .usePlaintext()
    .build();

AssimilationServiceGrpc.AssimilationServiceBlockingStub stub = 
    AssimilationServiceGrpc.newBlockingStub(channel);

AssimilationRequest request = AssimilationRequest.newBuilder()
    .setAlgorithm(AlgorithmType.VAR_3D)
    .addAllObservations(observations)
    .build();

AssimilationResponse response = stub.assimilate(request);
```

---

## 📋 JSON Schema

### 位置

**目录**: `schemas/`

**包含文件**:
- `assimilation/request.schema.json`
- `assimilation/response.schema.json`
- `validation/validator.py`

### Schema 验证示例

**Python**:
```python
import json
from jsonschema import validate, ValidationError

# 加载 Schema
with open('schemas/assimilation/request.schema.json') as f:
    schema = json.load(f)

# 验证数据
data = {
    "algorithm": "3D-VAR",
    "observations": [...],
    "background": {...}
}

try:
    validate(instance=data, schema=schema)
    print("Validation passed!")
except ValidationError as e:
    print(f"Validation error: {e.message}")
```

**Java**:
```java
import com.fasterxml.jackson.databind.JsonNode;
import com.networknt.schema.JsonSchema;
import com.networknt.schema.JsonSchemaFactory;
import com.networknt.schema.SpecVersion;
import com.networknt.schema.ValidationMessage;

String schemaPath = "schemas/assimilation/request.schema.json";
JsonSchemaFactory factory = JsonSchemaFactory.getInstance(SpecVersion.VersionFlag.V7);
JsonSchema schema = factory.getSchema(new File(schemaPath).toURI().toURL());

Set<ValidationMessage> errors = schema.validate(jsonNode);
if (errors.isEmpty()) {
    System.out.println("Validation passed!");
} else {
    errors.forEach(e -> System.out.println(e.getMessage()));
}
```

---

## 🔧 共享配置

### 配置格式

**支持格式**:
- YAML (`.yml`, `.yaml`)
- JSON (`.json`)
- Properties (`.properties`)

### 配置示例

**database.yml**:
```yaml
development:
  host: localhost
  port: 3306
  database: uav_assimilation
  
production:
  host: ${DB_HOST}
  port: ${DB_PORT}
  database: ${DB_NAME}
```

**features.json**:
```json
{
  "3D-VAR": {
    "enabled": true,
    "maxIterations": 100
  },
  "4D-VAR": {
    "enabled": true,
    "maxIterations": 200
  },
  "EnKF": {
    "enabled": true,
    "ensembleSize": 50
  }
}
```

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [Protos README](protos/README.md) | Protocol Buffers 详细说明 |
| [Common Types README](protos/common/README.md) | 公共类型说明 |
| [Algorithm Core](../algorithm_core/README.md) | 核心算法库 |
| [Service Spring](../service_spring/README.md) | Spring Boot 服务 |

---

## 🚀 快速开始

### 1. 克隆项目

```bash
cd shared
```

### 2. 安装依赖

```bash
# Python
pip install grpcio grpcio-tools jsonschema

# Java (Maven)
mvn clean install
```

### 3. 编译 Proto 文件

```bash
# Python
protoc --python_out=. -I. protos/**/*.proto

# Java
mvn protobuf:compile
```

---

## 🔄 版本管理

### Proto 版本控制

**版本号规则**:
```
major.minor.patch
```

**示例**:
- `v1.0.0` - 初始版本
- `v1.1.0` - 添加新字段
- `v2.0.0` - 不兼容更改

### 向后兼容

**添加字段** (向后兼容):
```protobuf
message DataRequest {
    string id = 1;
    int32 timeout = 2;
    // 添加新字段（必须添加默认值）
    string new_field = 3 [default = ""];
}
```

**不兼容更改** (需要新版本):
- 重命名字段
- 更改字段类型
- 修改字段编号

---

## 🧪 测试

### Proto 单元测试

```bash
# Python
python -m pytest tests/protos/

# Java
mvn test -Dtest=*ProtoTest
```

### Schema 验证测试

```bash
# Python
python -m pytest tests/schemas/

# Java
mvn test -Dtest=*SchemaTest
```

---

## 📦 发布

### 发布流程

1. **更新版本号**
   ```bash
   # 修改 proto 文件中的 version 注释
   ```

2. **编译代码**
   ```bash
   # Python
   make build-python
   
   # Java
   mvn clean install
   ```

3. **运行测试**
   ```bash
   make test
   ```

4. **提交更改**
   ```bash
   git add protos/
   git commit -m "feat: update proto definitions v1.1.0"
   git tag v1.1.0
   ```

---

## 🤝 贡献指南

### 添加新的 Proto 定义

1. **创建 Proto 文件**:
   ```protobuf
   syntax = "proto3";
   package your_package;
   
   message YourMessage {
       // 消息定义
   }
   ```

2. **遵循命名规范**:
   - 使用 snake_case
   - 消息类型使用 PascalCase
   - 字段使用 snake_case

3. **添加文档注释**:
   ```protobuf
   // 这是一个示例消息
   message ExampleMessage {
       // 字段说明
       string id = 1;
   }
   ```

4. **创建测试**:
   ```bash
   # Python
   touch tests/protos/test_your_message.py
   
   # Java
   touch src/test/java/TestYourMessage.java
   ```

---

## 📄 许可证

本目录遵循项目整体许可证。


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
