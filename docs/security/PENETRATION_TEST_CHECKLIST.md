# 安全渗透测试检查清单

## JWT 认证安全测试

### Token 生成
- [ ] Token 签名算法是否为 HMAC-SHA256 或更强
- [ ] Token 是否包含 jti (Token ID) 用于唯一标识
- [ ] Token 是否包含 iat (签发时间) 和 exp (过期时间)
- [ ] 密钥长度是否 >= 256 bits
- [ ] 密钥是否通过环境变量或 Secrets Manager 注入（非硬编码）

### Token 验证
- [ ] 签名验证失败是否返回 401
- [ ] Token 过期是否返回 401
- [ ] Token 结构异常（非 3 段式）是否返回 401
- [ ] 空 Token / 空 Authorization 头是否返回 401
- [ ] 非 Bearer 类型的 Token 是否被拒绝
- [ ] 篡改的 Token（修改 payload）是否被检测

### Token 黑名单
- [ ] 登出后 Token 是否加入黑名单
- [ ] 已撤销的 Token 再次使用是否被拒绝
- [ ] 黑名单中的 Token 绕过验证尝试
- [ ] 黑名单过期自动清理机制是否正常
- [ ] Redis 中黑名单的 TTL 是否与 Token 剩余有效期一致

### 刷新 Token
- [ ] Refresh Token 是否可以重复使用（应一次有效）
- [ ] Refresh Token 是否包含 jti
- [ ] 无效的 Refresh Token 是否抛出异常
- [ ] 过期 Refresh Token 是否被拒绝

## 网关安全测试

### JwtAuthGatewayFilter
- [ ] Gateway 是否校验所有非公开路径的 Token
- [ ] 白名单路径（/actuator/health, /api/auth/login）是否放行
- [ ] 透传到下游的 X-User-Id, X-User-Roles 头是否正确
- [ ] X-User-Roles 是否可被客户端伪造（下游应信任网关注入的头）
- [ ] 网关层 401 响应格式是否统一

### 限流
- [ ] Demo 用户是否被限制在 5 req/min
- [ ] 超过限流阈值是否返回 429
- [ ] 429 响应是否包含 Retry-After 头
- [ ] IP 限流是否对 1000 req/min 以上的突发有效
- [ ] 计算密集型端点（/api/planning）是否有限流

## 认证事件监控测试

### 日志记录
- [ ] 登录成功是否记录用户、IP、User-Agent
- [ ] 登录失败是否记录原因和 IP
- [ ] Token 刷新是否记录新旧 jti
- [ ] 登出是否记录
- [ ] 日志中是否掩盖敏感信息（IP 最后一段、完整 Token）

### 监控指标
- [ ] /api/admin/auth-events/metrics 是否可访问（需 ADMIN 角色）
- [ ] 指标计数器是否准确递增
- [ ] 活跃用户计数是否正确（同一用户多次登录计为 1）
- [ ] 指标重置功能是否生效

## 常见漏洞测试

### JWT 攻击
- [ ] alg:none 攻击：修改 header 的 alg 为 none
- [ ] 密钥替换攻击：使用自己的公钥签名
- [ ] 暴力破解密钥（短密钥测试）
- [ ] Token 注入（XSS 方式注入 Token）
- [ ] CSRF Token 绕过（如果同时使用 CSRF 保护）

### 会话管理
- [ ] 同一用户是否可以多设备登录（预期行为？）
- [ ] 用户角色变更后，现有 Token 是否立即失效
- [ ] Token 撤销后，是否可以继续使用旧 Token

### 信息泄露
- [ ] Token 中是否包含敏感信息（密码、密钥）
- [ ] 错误响应是否泄露过多信息（堆栈跟踪、密钥片段）
- [ ] 401 响应是否一致（防止用户枚举）

## 自动化工具扫描

### 推荐工具
- [ ] OWASP ZAP - 主动扫描
- [ ] Burp Suite - 手动渗透测试
- [ ] jwt_tool - JWT 安全测试
- [ ] nuclei - 漏洞扫描

### 运行命令
```bash
# JWT 安全测试
python3 jwt_tool.py -t http://localhost:8088/api/drones -rh "Authorization: Bearer <TOKEN>"

# OWASP ZAP 主动扫描
zap-cli quick-scan http://localhost:8088

# Nuclei 扫描
nuclei -u http://localhost:8088 -t ~/nuclei-templates/
```
