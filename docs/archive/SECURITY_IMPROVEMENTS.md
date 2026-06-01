# 项目安全改进记录

**更新日期**: 2026-05-08
**版本**: 1.0.1

---

## 一、本次修复的安全问题

### 1. ProcessBuilder白名单验证 ✅

#### 问题描述
原有代码中ProcessBuilder调用Python脚本时缺少严格的脚本白名单验证，存在潜在的安全风险。

#### 受影响文件
- `wrf-processor-service/src/main/java/com/wrf/processor/controller/WrfController.java`
- `uav-path-planning-system/backend-spring/src/main/java/com/uav/utils/PythonAlgorithmUtil.java`

#### 修复方案

**WrfController.java 增强措施:**
```java
// 1. 添加脚本白名单
private static final Set<String> ALLOWED_SCRIPT_NAMES = Set.of(
    "wrf_processor.py",
    "wrf_parser.py",
    "wrf_converter.py"
);

// 2. 文件类型验证
if (!originalName.endsWith(".nc") && !originalName.endsWith(".netcdf")) {
    return Map.of("success", false, "error", "仅支持NetCDF格式文件");
}

// 3. 路径遍历防护
if (!tempFile.startsWith(Paths.get(dataPath).normalize())) {
    return Map.of("success", false, "error", "路径遍历攻击检测");
}

// 4. 脚本路径验证
private void validateScriptPath(String scriptPath) {
    if (!ALLOWED_SCRIPT_NAMES.contains(scriptName)) {
        throw new SecurityException("未授权的脚本: " + scriptName);
    }
}

// 5. 超时控制
Future<String> future = executorService.submit(() -> {...});
String result = future.get(timeout, TimeUnit.MILLISECONDS);
```

**PythonAlgorithmUtil.java 增强措施:**
```java
// 1. 允许的脚本列表
private static final Set<String> ALLOWED_SCRIPTS = Set.of(
    "wrf/wrf_parser.py",
    "assimilation/bayesian_assimilation.py",
    "prediction/meteor_forecast.py",
    "path-planning/three_layer_planner.py",
    "vrp/optimize_routes.py"
);

// 2. 脚本名称验证
private void validateScriptName(String scriptName) {
    if (!ALLOWED_SCRIPTS.contains(scriptName)) {
        throw new SecurityException("未授权的脚本: " + scriptName);
    }
}

// 3. 安全路径解析
private String getSecureScriptPath(String scriptName) {
    Path fullPath = Paths.get(scriptPath, scriptName).normalize();
    if (!fullPath.startsWith(basePath)) {
        throw new SecurityException("路径遍历攻击检测");
    }
    return fullPath.toString();
}
```

#### 验证方法
1. 尝试执行白名单外的脚本应返回安全错误
2. 尝试路径遍历攻击应被拦截
3. 处理超时应该正常工作

---

### 2. 异常处理规范化 ✅

#### 问题描述
部分代码使用了过于宽泛的Exception捕获，可能掩盖具体错误。

#### 受影响文件
- `uav-path-planning-system/backend-spring/src/main/java/com/uav/controller/AuthController.java`

#### 修复方案

**修复前:**
```java
} catch (Exception e) {
    SecurityAuditConfig.logAuthenticationFailure(username, "认证失败", httpRequest);
    throw new BusinessException("AUTH_ERROR", "登录失败，请稍后重试");
}
```

**修复后:**
```java
} catch (BadCredentialsException e) {
    SecurityAuditConfig.logAuthenticationFailure(username, "密码错误", httpRequest);
    return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("用户名或密码错误");
} catch (DisabledException e) {
    SecurityAuditConfig.logAuthenticationFailure(username, "账户已禁用", httpRequest);
    return ResponseEntity.status(HttpStatus.FORBIDDEN).body("账户已被禁用");
} catch (LockedException e) {
    SecurityAuditConfig.logAuthenticationFailure(username, "账户已锁定", httpRequest);
    return ResponseEntity.status(HttpStatus.FORBIDDEN).body("账户已被锁定");
} catch (UsernameNotFoundException e) {
    SecurityAuditConfig.logAuthenticationFailure(username, "用户不存在", httpRequest);
    return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("用户名或密码错误");
} catch (AuthenticationException e) {
    SecurityAuditConfig.logAuthenticationFailure(username, "认证失败", httpRequest);
    throw new BusinessException("AUTH_ERROR", "登录失败，请稍后重试");
}
```

#### 改进点
1. 细分异常类型，提供精确的错误信息
2. 增加输入验证（用户名/密码非空检查）
3. 记录详细的审计日志

---

## 二、其他安全最佳实践

### 1. 输入验证
- 所有用户输入都经过验证
- 文件上传限制类型和大小
- 参数使用类型安全的绑定

### 2. 超时控制
- Python脚本执行设置超时
- 避免无限期阻塞

### 3. 日志审计
- 认证成功/失败详细记录
- 安全异常单独记录

### 4. 错误处理
- 不向用户暴露内部错误细节
- 使用通用错误消息
- 记录完整错误到日志

---

## 三、安全配置建议

### 1. 生产环境
```yaml
# application-prod.yml
wrf:
  python-script: /opt/wrf/scripts/wrf_processor.py
  data-path: /var/wrf/data
  timeout: 60000  # 生产环境可以适当增加

uav:
  python:
    script-path: /opt/uav/python
    timeout: 60000
```

### 2. 环境变量
```bash
# 生产环境应通过环境变量配置
export WRf_PYTHON_SCRIPT=/opt/wrf/scripts/wrf_processor.py
export WRf_DATA_PATH=/var/wrf/data
export UAV_PYTHON_SCRIPT_PATH=/opt/uav/python
```

---

## 四、测试验证

### 1. 单元测试建议
```java
@Test
void testValidateScriptPath_ValidScript() {
    assertDoesNotThrow(() -> validateScriptPath("wrf_processor.py"));
}

@Test
void testValidateScriptPath_InvalidScript() {
    assertThrows(SecurityException.class,
        () -> validateScriptPath("malicious.py"));
}

@Test
void testValidateScriptPath_PathTraversal() {
    assertThrows(SecurityException.class,
        () -> validateScriptPath("../etc/passwd"));
}
```

### 2. 集成测试建议
```java
@Test
void testProcessWrfFile_ValidInput() {
    // 测试正常文件处理
}

@Test
void testProcessWrfFile_InvalidType() {
    // 测试文件类型验证
}

@Test
void testProcessWrfFile_Timeout() {
    // 测试超时处理
}
```

---

## 五、合规检查清单

| 检查项 | 状态 | 说明 |
|--------|------|------|
| ProcessBuilder白名单 | ✅ 已实现 | WrfController, PythonAlgorithmUtil |
| 路径遍历防护 | ✅ 已实现 | validateScriptPath |
| 输入验证 | ✅ 已实现 | 文件类型、参数验证 |
| 超时控制 | ✅ 已实现 | ExecutorService + Future |
| 异常处理 | ✅ 已实现 | 具体异常类型 |
| 日志审计 | ✅ 已实现 | SecurityAuditConfig |
| 错误消息 | ✅ 已实现 | 不暴露内部细节 |

---

## 六、后续改进计划

### 短期 (1-2周)
1. 为更多Controller添加输入验证
2. 增加单元测试覆盖率
3. 统一日志格式

### 中期 (1个月)
1. 实现API限流
2. 增加Web应用防火墙(WAF)
3. 安全扫描集成到CI

### 长期 (3个月)
1. 渗透测试
2. 安全培训
3. 合规审计

---

**报告生成时间**: 2026-05-08
**下次审查**: 2026-06-08
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
