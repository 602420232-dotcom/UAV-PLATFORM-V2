# UAV Platform V2 重构实施计划 V2.0

> 基于用户反馈的修正版：微服务清单修正、API版本统一、异步任务标准化、UTM双向通信、实时接口防护、命名规范、MVP分阶段、算法层边界、场景化约束

---

## 一、气象模块拓展点（基于 docs_ref 分析）

### 1.1 多模型融合架构（长短时效全覆盖）

```
时效维度    0-3h          3-12h         12-72h        72h+
           ┌─────────────┬─────────────┬─────────────┬─────────────┐
数据源     │ 风雷NowcastNet │ 天资成渝AI    │ 风乌GHR      │ 风乌GHR      │
           │ (逐10min)    │ (1km区域)    │ (9km全球)    │ (全球环流)   │
           ├─────────────┼─────────────┼─────────────┼─────────────┤
WRF基准    │ SWC-WRF 3km  │ SWC-WRF 3km  │ SWC-WRF 3km  │ -            │
           │ (论文真值)   │ (论文真值)   │ (论文真值)   │              │
           └─────────────┴─────────────┴─────────────┴─────────────┘
                    ↓ 动态权重融合（基于历史RMSE自适应调整）
           ┌─────────────────────────────────────────────────────────┐
           │  融合后气象场 → CNN空间订正 → LSTM时序订正 → U-Net降尺度  │
           │  (3km → 1km精细化，含多源观测同化)                        │
           └─────────────────────────────────────────────────────────┘
```

**动态权重融合规则**：
- 0-3h：风雷权重最高（短临突发天气）
- 3-12h：天资权重最高（区域精细化）
- 12h+：风乌GHR权重最高（全球大背景场）

### 1.2 AI+物理耦合订正体系

| 层级 | 模型 | 功能 | 创新点 |
|------|------|------|--------|
| 空间订正 | 浅层CNN | 替代XGBoost，提取地形特征进行空间残差订正 | 精度提升25% |
| 时序订正 | LSTM | 时序残差订正 | 捕捉时间演变规律 |
| 降尺度同化 | 物理约束U-Net | 3km→1km + 多源观测同化 | 替代WRF 1km嵌套，解决OOM |
| 不确定性 | 概率U-Net | 输出mean+log_var，负对数似然损失 | 同时优化预报和不确定性 |

### 1.3 贝叶斯不确定性量化链路

```
概率U-Net(mean, log_var)
    ↓
EnKF集合生成（~20个成员）
    ↓
集合前向传播 → 分析更新
    ↓
稀疏GPR风险方差场（计算速度提升10倍）
    ↓
风险感知代价重构（α·距离 + β·能耗 + γ·风险方差）
    ↓
三层路径规划（VRPTW→A*→DWA）
```

### 1.4 主动观测决策闭环

```
GPR方差场 → 信息增益决策器 → 选择方差最大前N格点
    ↑                                    ↓
同化更新 ← 无人机探空观测 ← 临时调整路径飞过去
```

**触发条件**：区域风险方差超过阈值时自动决策

### 1.5 5D-VAR扩展维度（已实现）

| 维度 | 代价项 | 含义 |
|------|--------|------|
| D1-D4 | J_b + J_o | 标准4D-VAR（背景+观测约束） |
| D5a 风险 | J_risk = α_r · ∫C_risk(x,t)dt | 飞行风险嵌入同化代价函数 |
| D5b 动态扰动 | B_5D = [B_WRF, C^T; C, P_ensemble] | 无人机集合观测扩展背景协方差 |
| D5c AI参数化 | J_param = λ · ‖H_AI(α) - y_obs‖² | AI模型修正量参与同化 |

### 1.6 新数据源接入

| 数据源 | 类型 | 用途 | 接入优先级 |
|--------|------|------|-----------|
| ERA5再分析数据 | 全球再分析 | 训练U-Net基线模型 | P1 |
| 气象雷达 | 观测数据 | 多源同化，提升初始场精度 | P0 |
| 无人机探空 | 移动观测 | 主动观测决策 | P0 |
| 地面微型气象站 | 定点观测 | 多源同化 | P0 |
| 北斗/GNSS | 定位+气象 | 多源同化，风场反演 | P1 |
| 激光雷达测风 | 机载传感器 | 联邦学习聚合局部观测 | P1 |
| IMU惯导 | 机载传感器 | 推算湍流 | P1 |

---

## 二、微服务清单（修正版：8个标准服务）

### 2.1 服务拆分原则

- **单一职责**：每个服务只负责一个业务域
- **耦合内聚**：强耦合业务合并（risk + airworthiness），避免跨服务调用和数据冗余
- **边界清晰**：Java微服务仅做流程编排/鉴权/租户隔离，Python承载算法计算

### 2.2 8个标准微服务

| 服务名 | 职责 | 核心功能 | 技术栈 |
|--------|------|----------|--------|
| **gateway** | 网关 | 路由、鉴权、版本解析、限流、API Key校验、跨域、HMAC签名验证 | Spring Cloud Gateway |
| **platform-api** | 平台中心 | 多租户管理、用量统计、速率限制、签名管理、开发者控制台后端 | Spring Boot + MyBatis-Plus |
| **weather-api** | 气象服务 | 多源数据融合、AI降尺度、实时气象流（WebSocket） | Spring Boot + Python算法 |
| **assimilation-api** | 数据同化 | 多算法数据同化（3D-VAR/4D-VAR/5D-VAR/EnKF等）、任务状态管理 | Spring Boot + Python算法 |
| **risk-api** | 风险与适航 | 风险场计算 + 全维度适航评估（合并原airworthiness） | Spring Boot + Python算法 |
| **observation-api** | 主动观测 | 观测位置推荐、观测数据上报、闭环更新 | Spring Boot + Python算法 |
| **planning-api** | 路径规划 | 路径规划、MPC滚动重规划、结果查询 | Spring Boot + Python算法 |
| **utm-api** | 低空交通管理 | 空域申请、冲突检测/消解、外部UTM双向对接 | Spring Boot + Resilience4j |

### 2.3 服务依赖关系

```
gateway
  ├── platform-api（用户/租户/用量）
  ├── weather-api（气象数据）
  │     └── 调用 Python: 数据融合/降尺度
  ├── assimilation-api（同化计算）
  │     └── 调用 Python: 3DVAR/4DVAR/5DVAR/EnKF
  ├── risk-api（风险+适航）
  │     └── 调用 Python: GPR风险场/适航评估
  ├── observation-api（主动观测）
  │     └── 调用 Python: 贝叶斯决策器
  ├── planning-api（路径规划）
  │     ├── 依赖: weather-api, assimilation-api, risk-api
  │     └── 调用 Python: VRPTW/DE-RRT*/A*/DWA/MPC
  └── utm-api（UTM对接）
        ├── 外部: 真实UTM系统（双向）
        └── 内部: planning-api（冲突消解协同）
```

---

## 三、API版本规则统一

### 3.1 双版本体系

| 版本类型 | 载体 | 用途 | 生命周期 |
|----------|------|------|----------|
| **架构大版本** | URL路径 `/api/v1` | 整体架构迭代、不兼容重构 | 长（1-2年） |
| **接口小版本** | 请求头 `X-API-Version: 1.2` | 功能迭代、灰度发布、兼容切换 | 短（数周-数月） |

### 3.2 强制请求规范

所有HTTP接口、WebSocket流式接口、UTM双向回调接口，必须携带：

```
# HTTP请求头
X-Tenant-Id: tenant_001          # 租户标识
X-API-Key: uk_xxxxxxxxxxxx        # API Key
X-API-Version: 1.2               # 接口小版本
X-Request-Id: req_xxxxxxxx        # 请求追踪ID（幂等用）
Authorization: HMAC-SHA256 ...    # HMAC签名

# WebSocket连接参数
/ws/v1/weather/realtime?tenant_id=xxx&api_key=xxx&api_version=1.2
```

### 3.3 网关版本解析逻辑

```java
// GatewayFilter 伪代码
public class VersionFilter implements GatewayFilter {
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        // 1. 解析URL大版本
        String majorVersion = extractMajorVersion(exchange.getRequest().getPath());
        
        // 2. 解析Header小版本
        String minorVersion = exchange.getRequest().getHeaders().getFirst("X-API-Version");
        
        // 3. 组合版本路由
        String routeVersion = majorVersion + "." + minorVersion;
        
        // 4. 灰度判断：根据tenant_id + api_key哈希决定是否路由到新版本
        boolean isGray = grayRule.match(tenantId, apiKey, routeVersion);
        
        // 5. 设置路由标记
        exchange.getAttributes().put("routeVersion", isGray ? "v1.2" : "v1.1");
        
        return chain.filter(exchange);
    }
}
```

---

## 四、异步任务标准化

### 4.1 幂等设计

```java
// 任务提交接口
@PostMapping("/assimilation/compute")
public ResponseEntity<TaskResponse> submitAssimilation(
    @RequestHeader("X-Request-Id") String requestId,  // 幂等键
    @RequestBody AssimilationRequest request
) {
    // 1. 检查是否已存在相同requestId的任务
    Task existing = taskRepository.findByRequestId(requestId);
    if (existing != null) {
        return ResponseEntity.ok(new TaskResponse(existing.getJobId(), existing.getStatus()));
    }
    
    // 2. 创建新任务
    String jobId = taskService.createTask(requestId, request);
    return ResponseEntity.ok(new TaskResponse(jobId, TaskStatus.QUEUED));
}
```

### 4.2 统一任务状态枚举

```java
public enum TaskStatus {
    QUEUED("排队中", 100),
    RUNNING("运行中", 200),
    SUCCESS("成功", 300),
    FAILED("失败", 400),
    TIMEOUT("超时", 500),
    CANCELLED("已取消", 600);
    
    private final String displayName;
    private final int code;  // 全平台统一状态码
}
```

### 4.3 统一返回格式

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "job_id": "job_20240612_001",
    "status": "RUNNING",
    "status_code": 200,
    "progress": 65,
    "created_at": "2026-06-12T10:00:00Z",
    "updated_at": "2026-06-12T10:05:30Z",
    "estimated_complete_at": "2026-06-12T10:08:00Z",
    "result_url": "/api/v1/assimilation/job_20240612_001/result",
    "tenant_id": "tenant_001"
  },
  "request_id": "req_xxxxxxxx"
}
```

### 4.4 Redis任务缓存与过期清理

```java
@Configuration
public class TaskCacheConfig {
    
    @Bean
    public RedisTemplate<String, Task> taskRedisTemplate(RedisConnectionFactory factory) {
        RedisTemplate<String, Task> template = new RedisTemplate<>();
        template.setConnectionFactory(factory);
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(new Jackson2JsonRedisSerializer<>(Task.class));
        return template;
    }
}

@Service
public class TaskService {
    @Autowired
    private RedisTemplate<String, Task> taskRedisTemplate;
    
    // 任务缓存：按租户隔离key
    private String getTaskKey(String tenantId, String jobId) {
        return String.format("task:%s:%s", tenantId, jobId);
    }
    
    public void cacheTask(Task task) {
        String key = getTaskKey(task.getTenantId(), task.getJobId());
        taskRedisTemplate.opsForValue().set(key, task, Duration.ofHours(24));
    }
    
    // 定时清理：每天凌晨清理已完成超过7天的任务
    @Scheduled(cron = "0 0 3 * * ?")
    public void cleanupExpiredTasks() {
        // 扫描所有租户的任务key，删除过期数据
    }
}
```

---

## 五、UTM双向通信边界与容错

### 5.1 双向通信架构

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  平台主动调用    │         │   utm-api       │         │  外部UTM系统    │
│  (Resilience4j) │ ──────→ │  (Spring Boot)  │ ←────── │  (政府/军方)    │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                    ↑
                                    │ 回调
                                    ↓
                           ┌─────────────────┐
                           │  网关层校验      │
                           │  - 来源IP白名单  │
                           │  - HMAC签名验证  │
                           │  - 防重放拦截    │
                           │  - 时间戳校验    │
                           └─────────────────┘
```

### 5.2 平台主动调用外部UTM（Resilience4j配置）

```java
@Configuration
public class UtmResilienceConfig {
    
    @Bean
    public CircuitBreaker utmCircuitBreaker() {
        return CircuitBreaker.of("utm-cb", CircuitBreakerConfig.custom()
            .failureRateThreshold(50)           // 失败率阈值50%
            .slowCallRateThreshold(80)          // 慢调用阈值80%
            .slowCallDurationThreshold(Duration.ofSeconds(5))
            .waitDurationInOpenState(Duration.ofSeconds(30))
            .permittedNumberOfCallsInHalfOpenState(5)
            .slidingWindowSize(100)
            .build());
    }
    
    @Bean
    public Retry utmRetry() {
        return Retry.of("utm-retry", RetryConfig.custom()
            .maxAttempts(3)
            .waitDuration(Duration.ofMillis(500))
            .retryExceptions(IOException.class, TimeoutException.class)
            .build());
    }
    
    @Bean
    public TimeLimiter utmTimeLimiter() {
        return TimeLimiter.of("utm-tl", TimeLimiterConfig.custom()
            .timeoutDuration(Duration.ofSeconds(10))
            .cancelRunningFuture(true)
            .build());
    }
}
```

### 5.3 外部UTM回调平台（网关安全校验）

```java
@Component
public class UtmCallbackFilter implements GlobalFilter {
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String path = exchange.getRequest().getPath().value();
        
        // 仅对UTM回调路径生效
        if (!path.startsWith("/api/v1/utm/callback")) {
            return chain.filter(exchange);
        }
        
        // 1. 来源IP白名单校验
        String clientIp = getClientIp(exchange);
        if (!utmIpWhitelist.contains(clientIp)) {
            return reject(exchange, "Unauthorized IP: " + clientIp);
        }
        
        // 2. HMAC签名验证
        String signature = exchange.getRequest().getHeaders().getFirst("X-UTM-Signature");
        String timestamp = exchange.getRequest().getHeaders().getFirst("X-UTM-Timestamp");
        String body = getBody(exchange);
        
        if (!verifyHmac(signature, timestamp, body, utmSecretKey)) {
            return reject(exchange, "Invalid signature");
        }
        
        // 3. 防重放：时间戳必须在5分钟内
        long ts = Long.parseLong(timestamp);
        if (Math.abs(System.currentTimeMillis() - ts) > 5 * 60 * 1000) {
            return reject(exchange, "Request expired");
        }
        
        // 4. 防重放：nonce去重（Redis缓存5分钟）
        String nonce = exchange.getRequest().getHeaders().getFirst("X-UTM-Nonce");
        if (redisTemplate.hasKey("utm:nonce:" + nonce)) {
            return reject(exchange, "Duplicate request");
        }
        redisTemplate.opsForValue().set("utm:nonce:" + nonce, "1", Duration.ofMinutes(5));
        
        return chain.filter(exchange);
    }
}
```

### 5.4 紧急空域申请优先级队列

```java
@Configuration
public class UtmPriorityConfig {
    
    @Bean
    public PriorityBlockingQueue<UtmRequest> emergencyQueue() {
        return new PriorityBlockingQueue<>(100, (a, b) -> {
            // 紧急请求优先
            if (a.isEmergency() && !b.isEmergency()) return -1;
            if (!a.isEmergency() && b.isEmergency()) return 1;
            return Long.compare(a.getTimestamp(), b.getTimestamp());
        });
    }
}
```

---

## 六、全实时接口资源防护

### 6.1 双层限流策略

```java
@Configuration
public class RateLimitConfig {
    
    // 第一层：租户级QPS限流
    @Bean
    public RateLimiter tenantRateLimiter() {
        return RateLimiter.of("tenant-rl", RateLimiterConfig.custom()
            .limitForPeriod(100)        // 每租户每秒100请求
            .limitRefreshPeriod(Duration.ofSeconds(1))
            .timeoutDuration(Duration.ofMillis(100))
            .build());
    }
    
    // 第二层：API Key级QPS限流
    @Bean
    public RateLimiter apiKeyRateLimiter() {
        return RateLimiter.of("apikey-rl", RateLimiterConfig.custom()
            .limitForPeriod(20)         // 每API Key每秒20请求
            .limitRefreshPeriod(Duration.ofSeconds(1))
            .timeoutDuration(Duration.ofMillis(50))
            .build());
    }
    
    // 第三层：WebSocket长连接数限制
    @Bean
    public WebSocketConnectionLimiter wsConnectionLimiter() {
        return new WebSocketConnectionLimiter(
            10,     // 每租户最大10个长连接
            100     // 每API Key最大100个长连接
        );
    }
}
```

### 6.2 飞行核心接口单独阈值

```yaml
# application.yml
rate-limit:
  rules:
    # 普通接口默认阈值
    default:
      tenant-qps: 100
      api-key-qps: 20
    
    # 飞行核心接口（MPC、实时风险、UTM冲突检测）
    flight-critical:
      paths:
        - "/api/v1/planning/mpc/**"
        - "/api/v1/risk/realtime/**"
        - "/api/v1/utm/conflict/**"
      tenant-qps: 500        # 提升5倍
      api-key-qps: 100       # 提升5倍
      ws-connections: 50     # 提升5倍
      
    # 同化计算接口（重计算，降低阈值保护集群）
    heavy-computation:
      paths:
        - "/api/v1/assimilation/compute"
        - "/api/v1/assimilation/5d-var"
      tenant-qps: 10         # 降低10倍
      api-key-qps: 2         # 降低10倍
```

---

## 七、命名风格统一

### 7.1 REST接口路径规范

| 规则 | 示例 | 说明 |
|------|------|------|
| 全小写 | `/api/v1/planning/optimize` | 禁止驼峰 |
| 中横线分隔 | `/api/v1/assimilation/5d-var` | 原`/5dvar`已修正 |
| 资源名词复数 | `/api/v1/assimilation/jobs` | 集合操作用复数 |
| 动作动词放最后 | `/api/v1/planning/jobs/{id}/cancel` | 子资源操作 |

### 7.2 WebSocket流式接口前缀

```
/ws/v1/weather/realtime          # 实时气象流
/ws/v1/risk/realtime             # 实时风险流
/ws/v1/planning/mpc/stream       # MPC滚动优化流
/ws/v1/utm/conflict/alerts       # UTM冲突告警流
```

### 7.3 与HTTP接口物理区分

| 类型 | 前缀 | 用途 |
|------|------|------|
| HTTP REST | `/api/v1/` | 请求-响应模式 |
| WebSocket | `/ws/v1/` | 流式推送模式 |
| UTM回调 | `/api/v1/utm/callback/` | 外部系统回调 |

---

## 八、MVP功能分阶段

### 8.1 MVP一期（P0，必须上线）

**目标**：覆盖业务主干、实时能力、UTM对接、多租户、基础算法，满足商用基础需求

| 模块 | 功能 | 算法范围 |
|------|------|----------|
| 气象 | 多源数据融合、AI降尺度、WebSocket实时气象流 | 动态权重融合、CNN+LSTM订正、U-Net降尺度 |
| 同化 | 核心算法 | **3D-VAR / 4D-VAR / 5D-VAR**（3种主力） |
| 风险+适航 | 基础风险场、全维度适航评估 | GPR风险场、适航规则引擎 |
| 规划 | VRPTW + DE-RRT* + A* + DWA核心组合、MPC基础滚动重规划 | 4种核心算法 |
| 主动观测 | 基础观测位置推荐、观测数据上报 | 贝叶斯决策器 |
| UTM | 空域申请、冲突检测、冲突消解（对接真实外部UTM） | Resilience4j容错 |
| 平台 | 独立Schema多租户、API Key+HMAC签名、用量统计、速率限制 | - |
| SDK | Java/Python SDK基础封装、核心接口文档 | - |
| 运维 | 全链路监控、日志、链路追踪、基础告警 | SkyWalking+Prometheus+Grafana+ELK |

### 8.2 二期迭代（P1，MVP上线后）

**目标**：面向科研、高阶场景、边云协同，逐步放量

| 模块 | 功能 | 算法范围 |
|------|------|----------|
| 同化 | 补足剩余10种算法 | **合计13种全集**（EnKF/Hybrid/AdaptiveHybrid/MultiScaleHybrid/EnhancedBayesian/AdaptiveAssimilator/VarianceFieldOptimizer/AdaptiveVarianceField/BayesianAssimilator/CompatibleAssimilator） |
| 规划 | 补齐全部算法、算法智能调度器 | **28种算法全集** + 智能调度 |
| 风险 | GPR不确定性量化、概率输出、置信区间、方差场、代价分解 | 科研专项能力 |
| 边云协同 | 联邦学习、边缘INT8推理、V2X通信、离线缓存 | C++ Edge SDK完整发布 |
| 前端 | 高级可视化图表、数据大盘、算法实验管理 | 开发者控制台增强 |
| 场景 | 科研沙箱隔离、应急特权通道 | 租户级算力隔离 |

---

## 九、算法层架构边界

### 9.1 明确分工

| 层级 | 职责 | 禁止行为 |
|------|------|----------|
| **Java微服务** | 流程编排、鉴权、租户隔离、流量治理、监控告警、任务状态管理 | 不参与具体算法计算 |
| **Python服务** | 全部算法逻辑、模型推理、数值计算、同化求解、路径搜索 | 不直接对外暴露HTTP |
| **跨进程通信** | 常规请求：内部HTTP；大计算/异步任务：Kafka解耦 | 禁止同步阻塞大计算 |

### 9.2 通信模式

```
┌─────────────────────────────────────────────────────────────┐
│                      Java微服务层                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │weather  │ │assimila-│ │  risk   │ │planning │ ...       │
│  │  -api   │ │tion-api │ │  -api   │ │  -api   │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       │           │           │           │                 │
│       └───────────┴───────────┴───────────┘                 │
│                   │                                         │
│              流程编排层                                      │
│       ┌─────────┴─────────┐                                │
│       │  内部HTTP (同步)   │  < 100ms响应                   │
│       │  Kafka (异步)     │  > 100ms或大数据量              │
│       └─────────┬─────────┘                                │
└─────────────────┼───────────────────────────────────────────┘
                  │
┌─────────────────┼───────────────────────────────────────────┐
│                 ↓                                             │
│              Python算法层                                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  algo-orchestration/                                 │    │
│  │  ├── registry.py      # 算法注册中心                  │    │
│  │  ├── scheduler.py     # 智能调度器                    │    │
│  │  ├── pipeline.py      # 管线编排                     │    │
│  │  └── adapter.py       # 统一接口适配器                │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  算法实现（93个组件）                                 │    │
│  │  ├── assimilation/   # 13种同化算法                   │    │
│  │  ├── model-engine/   # 21个AI模型                    │    │
│  │  ├── path-planning/  # 28种规划算法                   │    │
│  │  ├── edge-cloud/     # 20个边云算法                   │    │
│  │  └── edge-sdk/       # 11个嵌入式算法                 │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 9.3 Kafka消息规范

```java
// 异步任务消息格式
public class AlgorithmTaskMessage {
    private String jobId;           // 任务ID
    private String tenantId;        // 租户隔离
    private String algorithmType;   // 算法类型
    private String algorithmName;   // 具体算法名
    private Map<String, Object> input;   // 输入数据
    private long timeoutMs;         // 超时时间
    private String callbackTopic;   // 完成回调Topic
}

// Topic命名规范
// task:{tenantId}:{algorithmType}  → 如 task:tenant_001:assimilation
// result:{tenantId}:{jobId}        → 如 result:tenant_001:job_xxx
```

---

## 十、场景化补充约束

### 10.1 科研场景：算法任务沙箱隔离

```java
@Service
public class ResearchSandboxService {
    
    // 科研租户专用资源池
    @Autowired
    private ThreadPoolExecutor researchExecutor;
    
    public Task submitResearchTask(String tenantId, AlgorithmTask task) {
        // 1. 校验科研租户标识
        if (!tenantService.isResearchTenant(tenantId)) {
            throw new ForbiddenException("Research sandbox only");
        }
        
        // 2. 分配独立算力配额
        ResourceQuota quota = quotaService.getResearchQuota(tenantId);
        
        // 3. 提交到隔离线程池
        Future<?> future = researchExecutor.submit(() -> {
            Thread.currentThread().setName("research-" + tenantId + "-" + task.getJobId());
            algorithmService.execute(task);
        });
        
        // 4. 监控资源使用，防止单租户独占
        resourceMonitor.watch(tenantId, quota);
        
        return new Task(task.getJobId(), TaskStatus.QUEUED);
    }
}
```

**科研租户特性**：
- 独立算法实验空间（算法参数可调、A/B测试）
- 算力配额隔离（CPU/内存/GPU独立限制）
- 任务队列隔离（不影响商业租户）
- 完整代价分解和方差场输出（科研级详细数据）

### 10.2 应急救灾场景：特权通道

```java
@Service
public class EmergencyPriorityService {
    
    // 应急请求标识
    private static final String EMERGENCY_HEADER = "X-Emergency-Level";
    
    public void handleEmergencyRequest(ServerWebExchange exchange, EmergencyRequest request) {
        String emergencyLevel = exchange.getRequest().getHeaders().getFirst(EMERGENCY_HEADER);
        
        if ("CRITICAL".equals(emergencyLevel)) {
            // 1. 临时放宽限流
            rateLimitService.bypass(exchange);
            
            // 2. 提升队列优先级
            taskQueue.promoteToFront(request.getJobId());
            
            // 3. 预留应急算力
            resourcePool.reserveEmergencyCapacity();
            
            // 4. UTM紧急空域申请（最高优先级）
            utmService.submitEmergencyAirspace(request);
            
            // 5. 通知运维（人工介入准备）
            alertService.sendEmergencyAlert(request);
        }
    }
}
```

**应急特权规则**：
- 限流阈值临时提升10倍
- 任务队列插队（最高优先级）
- 预留20%集群算力给应急请求
- UTM空域申请走绿色通道
- 自动触发运维告警（人工兜底）

---

## 十一、实施时间线（更新版）

```
Phase 1: 骨架搭建（已完成）
├── 2026-06  根POM、CI/CD、Docker Compose、文档规范
└── 2026-06  5D-VAR算法实现与测试

Phase 2: MVP一期核心（P0）
├── 2026-07  common模块 + gateway + platform-api
├── 2026-08  weather-api + assimilation-api（3D/4D/5D-VAR）
├── 2026-09  risk-api（风险+适航合并） + observation-api
├── 2026-10  planning-api（核心4算法+MPC） + utm-api（UTM对接）
└── 2026-11  SDK + 开发者控制台 + E2E测试

MVP一期验收（2026-11底）
├── 端到端管线通（WRF→融合→同化→风险→规划→UTM）
├── 多租户隔离验证
├── 全实时接口压力测试
└── 外部UTM对接联调

Phase 3: 二期迭代（P1）
├── 2026-12  补齐10种同化算法 + 智能调度器
├── 2027-01  补齐28种规划算法 + GPR不确定性量化
├── 2027-02  联邦学习 + 边缘INT8推理 + V2X
├── 2027-03  C++ Edge SDK完整发布
└── 2027-04  前端控制台增强 + 科研沙箱 + 应急特权

Phase 4: 生产就绪
├── 2027-05  性能压测 + 安全审计
├── 2027-06  K8s生产部署 + 监控告警体系
└── 2027-07  灰度发布 + 全量上线
```

---

## 十二、风险管控（更新版）

| 风险 | 等级 | 应对措施 | 责任人 |
|------|------|----------|--------|
| Spring Boot 4.0生态不成熟 | 高 | 提前验证关键依赖兼容性，准备降级方案（Spring Boot 3.4） | 架构组 |
| 93个算法迁移工作量大 | 高 | MVP一期只迁移核心算法，其余二期逐步放量 | 算法组 |
| 外部UTM对接延迟 | 中 | 预留模拟UTM接口，支持内部测试 | UTM组 |
| 全实时性能不达标 | 中 | 预留Kafka异步降级方案，流式接口可切换为轮询 | 性能组 |
| 多租户Schema隔离复杂 | 中 | 使用MyBatis Plus动态数据源，自动化Schema管理 | 数据组 |
| 联邦学习收敛困难 | 低 | 先实现单机联邦学习模拟，再扩展到多机 | 边缘组 |

---

*文档版本：V2.0*
*更新日期：2026-06-12*
*更新内容：微服务清单修正、API版本统一、异步任务标准化、UTM双向通信、实时接口防护、命名规范、MVP分阶段、算法层边界、场景化约束*
