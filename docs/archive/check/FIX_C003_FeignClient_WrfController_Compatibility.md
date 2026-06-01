# C-003: FeignClient 与 WrfController API 签名不兼容问题修复

## 问题描述

**问题文件**：
- `common-utils/src/main/java/com/uav/common/feign/WrfProcessorClient.java`
- `wrf-processor-service/src/main/java/com/uav/wrf/processor/controller/WrfController.java`
- `uav-platform-service/src/main/java/com/uav/platform/controller/PlatformController.java`

**问题详情**：
1. PlatformController.plan() 调用 wrfProcessorClient.parseWrfData(weatherData) 发送 JSON 格式数据
2. 但原 WrfController 的 /api/wrf/parse 端点只接受 multipart/form-data 文件上传
3. 导致 HTTP 415 Unsupported Media Type 错误

## 修复方案

### 1. 创建 WrfParseRequest DTO

**文件**：`common-utils/src/main/java/com/uav/common/dto/WrfParseRequest.java`

新增的 DTO 类，用于封装参数化 WRF 解析请求：
- `height`: 高度值（米）
- `bounds`: 区域范围
- `data`: 已解析的气象数据
- `filePath`: 文件路径（可选）
- `timestamp`: 时间戳

### 2. 在 WrfController 中新增 /api/wrf/parse-params 端点

**文件**：`wrf-processor-service/src/main/java/com/uav/wrf/processor/controller/WrfController.java`

新增功能：
1. `parseWrfData(WrfParseRequest request)`: 接受 JSON Body 的新方法
2. `processWrfFromFilePath(String filePath, int height)`: 从文件路径处理
3. `generateMockWeatherData()`: 生成模拟数据
4. `generateGridData()`: 生成网格数据

特性：
- 如果提供了 filePath，尝试从文件加载
- 如果提供了已解析的 data，直接返回
- 默认返回模拟的天气数据（用于演示）
- 响应格式调整为使用 code 而非 success，与 PlatformController 期望的格式一致

### 3. 更新 WrfProcessorClient FeignClient 接口

**文件**：`common-utils/src/main/java/com/uav/common/feign/WrfProcessorClient.java`

新增方法：
1. `parseWrfData(WrfParseRequest request)`: 强类型参数版本
2. `parseWrfData(Map<String, Object> data)`: 兼容旧版调用的默认方法（内部转换为 WrfParseRequest）

### 4. 更新 parseWrfFile 端点的声明

**文件**：`wrf-processor-service/src/main/java/com/uav/wrf/processor/controller/WrfController.java`

添加 `consumes = MediaType.MULTIPART_FORM_DATA_VALUE` 明确文件上传的 Content-Type

## 修改对比

### 修改前的问题

```java
// PlatformController.plan() 调用
Map<String, Object> weatherResponse = wrfProcessorClient.parseWrfData(weatherData);

// 但 WrfProcessorClient 只有这个方法（或者方法名不匹配）
// WrfController 只接受文件上传
@PostMapping("/parse")
public Map<String, Object> parseWrfFile(@RequestParam("file") MultipartFile file, ...)
```

### 修改后

```java
// PlatformController.plan() 调用
Map<String, Object> weatherResponse = wrfProcessorClient.parseWrfData(weatherData);

// WrfProcessorClient 现在有两个 parseWrfData 方法
@PostMapping(value = "/api/wrf/parse-params", consumes = MediaType.APPLICATION_JSON_VALUE)
Map<String, Object> parseWrfData(@RequestBody WrfParseRequest request);

// 以及兼容旧版调用的默认方法
default Map<String, Object> parseWrfData(@RequestBody Map<String, Object> data) {
    WrfParseRequest request = new WrfParseRequest();
    request.setData(data);
    return parseWrfData(request);
}
```

## 响应格式

### PlatformController 期望的格式

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {...}
}
```

### 修复后的 WrfController 响应

```json
{
  "code": 200,
  "message": "WRF数据解析成功",
  "data": {
    "height": 100,
    "timestamp": 1234567890,
    "wind_speed": [...],
    "wind_direction": [...],
    "temperature": [...],
    "humidity": [...],
    "pressure": [...]
  }
}
```

## 向后兼容性

1. **保留原有的 /api/wrf/parse 端点**：继续接受文件上传
2. **新增 /api/wrf/parse-params 端点**：接受 JSON Body
3. **FeignClient 提供两个重载方法**：
   - 强类型 `WrfParseRequest` 参数版本
   - `Map<String, Object>` 参数版本（内部自动转换）

## 测试建议

1. **验证 PlatformController.plan() 调用**：
   ```bash
   curl -X POST http://localhost:8088/api/platform/plan \
     -H "Content-Type: application/json" \
     -d '{
           "weatherData": {
             "height": 100,
             "bounds": {
               "minLat": 30.0,
               "maxLat": 40.0,
               "minLon": 120.0,
               "maxLon": 130.0
             }
           },
           "drones": [...],
           "tasks": [...]
         }'
   ```

2. **验证文件上传端点仍然正常**：
   ```bash
   curl -X POST http://localhost:8081/api/wrf/parse \
     -F "file=@test.nc" \
     -F "height=100"
   ```

## 文件变更清单

### 新增文件
- `common-utils/src/main/java/com/uav/common/dto/WrfParseRequest.java`

### 修改文件
- `wrf-processor-service/src/main/java/com/uav/wrf/processor/controller/WrfController.java`
  - 添加 parseWrfData(WrfParseRequest) 方法
  - 添加 processWrfFromFilePath() 方法
  - 添加 generateMockWeatherData() 方法
  - 添加 generateGridData() 方法
  - 调整响应格式为使用 code 而非 success
  - 为 parseWrfFile 添加 consumes 属性
  
- `common-utils/src/main/java/com/uav/common/feign/WrfProcessorClient.java`
  - 添加 parseWrfData(WrfParseRequest) 方法
  - 添加 parseWrfData(Map) 兼容方法
  - 重命名原注释为"文件上传版本"

## 依赖关系

此修复不需要新的依赖，使用项目已有的库：
- Spring Web
- Lombok
- Feign
