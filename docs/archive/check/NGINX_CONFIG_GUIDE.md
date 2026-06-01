# Nginx配置统一与安全加固

## 概述

本项目包含移动端(Flutter)和Vue前端两个Nginx配置文件。本次更新统一了API代理行为，并增强了安全配置。

## 主要改进

### 1. API代理行为统一 ✅

**问题**: 移动端和Vue前端的API代理配置不一致，导致请求转发行为不同。

**解决**: 统一采用Vue方式（保留`/api/`前缀）

修改前后对比：

| 配置 | 修改前 | 修改后 |
|------|--------|--------|
| **移动端** | `proxy_pass http://uav-gateway:8088/;` | `proxy_pass http://uav-gateway:8088/api/;` |
| **Vue前端** | `proxy_pass http://uav-gateway:8088/api/;` | 保持不变 |

**效果**: `/api/v1/foo` 统一转发到 `http://uav-gateway:8088/api/v1/foo`

### 2. 安全头配置 ✅

为两个配置文件添加了完整的安全响应头：

```nginx
# X-Frame-Options
add_header X-Frame-Options "SAMEORIGIN" always;

# X-Content-Type-Options
add_header X-Content-Type-Options "nosniff" always;

# X-XSS-Protection
add_header X-XSS-Protection "1; mode=block" always;

# Referrer-Policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Content-Security-Policy
add_header Content-Security-Policy "..." always;
```

#### CSP配置说明

**移动端 (Flutter)**:
```
default-src 'self' data: blob: https:;
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com;
style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
img-src 'self' data: https:;
connect-src 'self' https://cdn.jsdelivr.net https://unpkg.com;
font-src 'self' data:;
```

**Vue前端**:
```
default-src 'self' data: blob: https:;
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com;
style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
img-src 'self' data: https:;
connect-src 'self' ws: wss: https://cdn.jsdelivr.net https://unpkg.com;  # 支持WebSocket
font-src 'self' data: https:;
frame-ancestors 'self';
```

### 3. 代理头完善 ✅

为所有代理请求添加了完整的请求头：

```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

### 4. Gzip压缩优化 ✅

增强了Gzip压缩配置：

```nginx
gzip on;
gzip_vary on;                    # 添加Vary头
gzip_min_length 1024;            # 最小压缩长度
gzip_proxied any;                # 代理请求也压缩
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
gzip_disable "MSIE [1-6]\.";     # 禁用旧IE压缩
```

### 5. 超时配置优化 ✅

为代理请求添加了连接超时配置：

```nginx
proxy_connect_timeout 60s;       # 连接超时
proxy_read_timeout 120s;         # 读取超时
```

## 文件位置

- **移动端**: `uav-mobile-app/nginx.conf`
- **Vue前端**: `uav-path-planning-system/frontend-vue/nginx.conf`

## 安全头说明

### X-Frame-Options
- **值**: `SAMEORIGIN`
- **作用**: 防止页面被嵌入到iframe中，避免点击劫持攻击

### X-Content-Type-Options
- **值**: `nosniff`
- **作用**: 防止浏览器MIME类型嗅探，确保浏览器遵守Content-Type头

### X-XSS-Protection
- **值**: `1; mode=block`
- **作用**: 启用浏览器XSS过滤器，阻止XSS攻击

### Referrer-Policy
- **值**: `strict-origin-when-cross-origin`
- **作用**: 控制Referer头的发送策略，保护用户隐私

### Content-Security-Policy (CSP)
- **作用**: 限制资源加载来源，防止XSS和数据注入攻击
- 移动端包含cdn.jsdelivr.net和unpkg.com（用于Flutter Web依赖）
- Vue前端额外支持WebSocket（wss:）用于实时通信

## 部署注意事项

### 1. 验证配置

测试Nginx配置语法：
```bash
# 本地测试
nginx -t -c /path/to/nginx.conf

# Docker容器中测试
docker exec <container-name> nginx -t
```

### 2. 应用配置

**Docker Compose环境**:
配置文件已在docker-compose.yml中挂载，无需手动操作。

**独立部署**:
```bash
# 复制配置
cp nginx.conf /etc/nginx/conf.d/uav-frontend.conf

# 测试并重载
nginx -t && nginx -s reload
```

### 3. 验证安全头

使用curl验证响应头：
```bash
curl -I https://your-domain.com
```

检查响应中是否包含：
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `Content-Security-Policy: ...`

## CSP调试

如果遇到CSP阻止脚本或样式的问题：

1. **检查浏览器控制台**: 会显示被阻止的资源
2. **临时禁用CSP进行测试**: 添加meta标签 `httpEquiv="Content-Security-Policy-Report-Only"`
3. **使用Report-URI**: 配置CSP报告端点收集违规报告

## 维护建议

### 定期更新CDN域名白名单
如果使用了新的CDN域名，需要更新CSP配置。

### 监控安全事件
配置CSP violation报告：
```nginx
Content-Security-Policy-Report-URI /csp-violation-report;
```

### 日志分析
定期检查Nginx错误日志，排查CSP违规：
```bash
grep "csp" /var/log/nginx/error.log
```

## 更新历史

- **2026-06-01**: 初始版本
  - 统一API代理行为为保留前缀方式
  - 添加完整安全响应头
  - 完善代理请求头配置
  - 优化Gzip压缩设置
  - 添加连接超时配置

## 参考资料

- [MDN: Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [OWASP Security Headers](https://owasp.org/www-project-secure-headers/)
- [Nginx Gzip Module](http://nginx.org/en/docs/http/ngx_http_gzip_module.html)
