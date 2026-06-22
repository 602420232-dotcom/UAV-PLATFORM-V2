# UAV Platform V2 生产就绪与科研完善实施计划（修订版 v1.1）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 3 个工作日内修复安全高危漏洞并打通风乌气象数据源，1 周内完成全链路真实数据算法实验验证，7 月上旬启动灰度发布，7 月下旬全量生产上线。毕设专项（WRF模式驱动、地形分析）采用"设计+服务器方案"方式推进。

**Architecture:** 以"安全加固 → 数据对接 → 科研可复现 → 算法验证 → 环境切换 → 毕设专项设计"六阶段推进。前端功能分离为 **科研功能模块** 和 **API运营管理模块** 两大独立入口。

**Tech Stack:** Spring Boot 4.1.0/3.4.0, Vue 3 + Element Plus, Python 3.11 + ONNX Runtime, FengWu-GHR Torch, MySQL 8.4, Redis 7.2, Kafka 7.8

---

## 文件结构总览

### 后端（Java）
| 文件 | 职责 |
|------|------|
| `services/platform-api/src/main/resources/application.yml` | 主配置：JWT、DB、Redis、Actuator |
| `common/common-security/src/main/java/com/uav/common/security/filter/JwtAuthenticationFilter.java` | JWT认证过滤器：Token解析、角色提取 |
| `services/platform-api/src/main/java/com/uav/platform/controller/AuthController.java` | 认证接口：登录、刷新、重置密码 |
| `services/platform-api/src/main/java/com/uav/platform/controller/DashboardController.java` | 仪表盘：添加@PreAuthorize |
| `services/weather-api/...` | 气象服务：风乌/风雷数据源对接 |
| `services/assimilation-api/...` | 同化服务：3D/4D/5D-VAR实验验证 |
| `services/planning-api/...` | 规划服务：VRPTW/DE-RRT*/A*/DWA/MPC |
| `services/risk-api/...` | 风险服务：四维风险场、五维适航 |
| `gateway/api-gateway/src/main/resources/application.yml` | 网关配置：UTM双环境开关 |

### 后端（Python）
| 文件 | 职责 |
|------|------|
| `python/algorithm-engine/app/adapters/fengwu_adapter.py` | 风乌模型适配器：ONNX/Torch推理封装 |
| `python/algorithm-engine/app/adapters/fengle_adapter.py` | 风雷模型适配器（预留） |
| `python/algorithm-engine/app/core/experiment_logger.py` | 实验日志：结构化记录、指标收集 |
| `python/algorithm-engine/app/core/snapshot_manager.py` | 实验快照：输入/输出/参数/环境序列化 |
| `python/algorithm-engine/app/core/report_generator.py` | 对比报告：标准化图表、LaTeX模板 |
| `python/algorithm-engine/app/api/routes.py` | FastAPI路由：实验执行、状态查询、报告导出 |
| `python/algorithm-engine/app/adapters/wrf_model_driver.py` | **【毕设专项】** WRF模式运行驱动（设计阶段） |
| `python/algorithm-engine/app/adapters/wrf_namelist_manager.py` | **【毕设专项】** namelist配置管理（设计阶段） |
| `python/algorithm-engine/app/adapters/wrf_terrain_analyzer.py` | **【毕设专项】** 盆地地形机理分析（设计阶段） |

### 前端（Vue）— 科研功能模块
| 文件 | 职责 |
|------|------|
| `console/src/views/research/SandboxView.vue` | 科研沙箱：算法描述、参数调整、实验日志 |
| `console/src/views/research/AlgorithmLab.vue` | 算法实验室：单算法运行、参数调优、结果可视化 |
| `console/src/views/research/ExperimentManager.vue` | 实验管理：历史实验、快照恢复、对比分析 |
| `console/src/views/research/ReportCenter.vue` | 报告中心：报告生成、导出、模板管理 |
| `console/src/components/research/AlgorithmParamsPanel.vue` | 参数调整面板：动态表单、验证、预设 |
| `console/src/components/research/ExperimentLogViewer.vue` | 实验日志查看器：实时流、筛选、导出 |
| `console/src/components/research/ReportExporter.vue` | 报告导出：PDF/PNG/CSV/LaTeX格式 |
| `console/src/components/research/AlgorithmDescription.vue` | 算法描述：原理说明、公式展示、参考文献 |
| `console/src/components/research/WRFTerrainAnalysis.vue` | **【毕设专项】** WRF地形分析可视化 |
| `console/src/components/research/PBLSchemeSelector.vue` | **【毕设专项】** PBL方案选择与对比 |
| `console/src/api/weather-source.ts` | 气象数据源API：风乌/风雷配置 |
| `console/src/api/experiment.ts` | 实验管理API：快照、日志、报告 |

### 前端（Vue）— API运营管理模块
| 文件 | 职责 |
|------|------|
| `console/src/views/api/DashboardView.vue` | 运营仪表盘：调用量、成功率、延迟 |
| `console/src/views/api/ApiKeyManager.vue` | API密钥管理：创建、限流、统计 |
| `console/src/views/api/TenantManager.vue` | 租户管理：配额、计费、监控 |
| `console/src/views/api/UsageAnalytics.vue` | 用量分析：趋势、分布、预测 |
| `console/src/views/api/ServiceHealth.vue` | 服务健康：状态、告警、拓扑 |
| `console/src/views/api/AlertRules.vue` | 告警规则：阈值、通知、历史 |
| `console/src/components/api/MetricChart.vue` | 指标图表：实时/历史数据可视化 |
| `console/src/components/api/ServiceTopology.vue` | 服务拓扑图：依赖关系、流量路径 |
| `console/src/components/settings/EnvironmentSwitcher.vue` | 环境切换：开发/测试/灰度/生产 |
| `console/src/components/settings/WeatherSourceConfig.vue` | 气象数据源配置 |

---

## Phase 1: P0 安全高危漏洞修复（第 1 天）

### Task 1.1: 移除 JWT 硬编码默认密钥

**Files:**
- Modify: `services/platform-api/src/main/resources/application.yml:45-52`
- Modify: `common/common-security/src/main/java/com/uav/common/security/service/JwtService.java`

- [ ] **Step 1: 修改 application.yml 移除默认值**

```yaml
jwt:
  secret: ${JWT_SECRET}  # 移除默认值，强制环境变量配置
  expiration: 1800000    # 30分钟（从24小时缩短）
  refresh-expiration: 604800000  # 7天
  issuer: uav-platform
```

- [ ] **Step 2: 添加启动时密钥校验**

在 `JwtService.java` 构造函数中添加：

```java
@PostConstruct
public void validateConfig() {
    if (!StringUtils.hasText(secretKey)) {
        throw new IllegalStateException(
            "JWT_SECRET must be configured via environment variable. " +
            "Please set JWT_SECRET to a secure random string (min 256 bits)."
        );
    }
    if (secretKey.length() < 32) {
        throw new IllegalStateException(
            "JWT_SECRET must be at least 256 bits (32 characters). " +
            "Current length: " + secretKey.length()
        );
    }
}
```

- [ ] **Step 3: 更新 docker-compose 环境变量**

```yaml
platform-api:
  environment:
    - JWT_SECRET=${JWT_SECRET:?JWT_SECRET is required}
```

使用 `${VAR:?message}` 语法确保启动时若未设置则报错。

- [ ] **Step 4: 生成开发环境密钥脚本**

Create: `scripts/generate-jwt-secret.sh`

```bash
#!/bin/bash
# Generate a secure JWT secret for development
SECRET=$(openssl rand -base64 48)
echo "JWT_SECRET=$SECRET"
echo ""
echo "Add to your .env file:"
echo "JWT_SECRET=$SECRET"
```

- [ ] **Step 5: 更新部署文档**

在 `docs/deployment-guide.md` 中添加 JWT 配置章节，强调生产环境必须使用环境变量。

---

### Task 1.2: 修复 JWT 过滤器角色解析

**Files:**
- Modify: `common/common-security/src/main/java/com/uav/common/security/filter/JwtAuthenticationFilter.java:74-76`

- [ ] **Step 1: 修改 Token 生成逻辑（JwtService）**

在生成 Token 时嵌入用户角色：

```java
public String generateToken(UserDetails userDetails, String tokenType) {
    Map<String, Object> claims = new HashMap<>();
    claims.put("type", tokenType);
    claims.put("roles", userDetails.getAuthorities().stream()
        .map(GrantedAuthority::getAuthority)
        .collect(Collectors.toList()));
    claims.put("username", userDetails.getUsername());
    
    return Jwts.builder()
        .setClaims(claims)
        .setSubject(userDetails.getUsername())
        .setIssuedAt(new Date())
        .setExpiration(new Date(System.currentTimeMillis() + expiration))
        .setIssuer(issuer)
        .signWith(getSigningKey(), SignatureAlgorithm.HS256)
        .compact();
}
```

- [ ] **Step 2: 修改 Token 解析逻辑（JwtAuthenticationFilter）**

```java
@Override
protected void doFilterInternal(HttpServletRequest request, 
                                HttpServletResponse response, 
                                FilterChain filterChain) throws ServletException, IOException {
    String token = extractToken(request);
    if (token != null && validateToken(token)) {
        Claims claims = parseToken(token);
        String username = claims.getSubject();
        
        // 从Token中提取角色
        @SuppressWarnings("unchecked")
        List<String> roles = claims.get("roles", List.class);
        List<SimpleGrantedAuthority> authorities = roles != null 
            ? roles.stream().map(SimpleGrantedAuthority::new).collect(Collectors.toList())
            : Collections.singletonList(new SimpleGrantedAuthority("ROLE_USER"));
        
        UsernamePasswordAuthenticationToken authentication = 
            new UsernamePasswordAuthenticationToken(username, null, authorities);
        authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
        SecurityContextHolder.getContext().setAuthentication(authentication);
    }
    filterChain.doFilter(request, response);
}
```

- [ ] **Step 3: 验证角色权限生效**

测试用例：
- SUPER_ADMIN 访问 `/api/v1/users` → 200
- OPERATOR 访问 `/api/v1/users` → 403
- OBSERVER 访问 `/api/v1/roles` → 403

---

### Task 1.3: 修复 reset-password 权限控制

**Files:**
- Modify: `services/platform-api/src/main/java/com/uav/platform/controller/AuthController.java:154`

- [ ] **Step 1: 添加权限注解**

```java
@PostMapping("/reset-password")
@PreAuthorize("hasRole('SUPER_ADMIN') or hasRole('TENANT_ADMIN')")
public Result<Void> resetPassword(@RequestBody @Valid ResetPasswordRequest request) {
    // 只允许重置同租户下的用户密码
    String currentTenantId = TenantContext.getCurrentTenant();
    userService.resetPassword(request.getUserId(), request.getNewPassword(), currentTenantId);
    return Result.success();
}
```

- [ ] **Step 2: 添加租户隔离校验**

在 `UserService.resetPassword()` 中：

```java
public void resetPassword(Long userId, String newPassword, String operatorTenantId) {
    User user = userRepository.findById(userId)
        .orElseThrow(() -> new BusinessException("用户不存在"));
    
    // 租户隔离：只能重置同租户用户密码
    if (!user.getTenantId().equals(operatorTenantId)) {
        throw new AccessDeniedException("无权重置其他租户用户密码");
    }
    
    String encodedPassword = passwordEncoder.encode(newPassword);
    user.setPassword(encodedPassword);
    userRepository.updateById(user);
    
    log.info("密码已重置: userId={}, tenantId={}, operator={}", 
        userId, operatorTenantId, SecurityContextHolder.getContext().getAuthentication().getName());
}
```

- [ ] **Step 3: 移除调试日志**

删除 `AuthController` 中记录密码哈希的调试日志：

```java
// 删除以下代码：
// log.info("登录调试: username={}, storedHash={}, inputLength={}, matches={}", ...)
```

---

### Task 1.4: DashboardController 添加权限注解

**Files:**
- Modify: `services/platform-api/src/main/java/com/uav/platform/controller/DashboardController.java`

- [ ] **Step 1: 添加类级权限注解**

```java
@RestController
@RequestMapping("/api/v1/dashboard")
@PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR', 'ALGORITHM_ADMIN')")
public class DashboardController {
    
    @GetMapping("/stats")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN')")
    public Result<DashboardStats> getStats() { ... }
    
    @GetMapping("/api-trend")
    public Result<ApiTrendData> getApiCallTrend() { ... }
    
    @GetMapping("/service-distribution")
    public Result<ServiceDistributionData> getServiceDistribution() { ... }
    
    @GetMapping("/service-health")
    public Result<ServiceHealthData> getServiceHealth() { ... }
}
```

同时移除 `SecurityConfig` 中 `/api/v1/dashboard/**` 的 `permitAll()` 配置。

---

## Phase 2: P0 风乌气象数据源对接（第 1-2 天）

### Task 2.1: 风乌 ONNX 模型适配器

**Files:**
- Create: `python/algorithm-engine/app/adapters/fengwu_adapter.py`
- Create: `python/algorithm-engine/app/adapters/__init__.py`

- [ ] **Step 1: 创建 FengWu ONNX 适配器**

```python
"""
FengWu 气象模型适配器
支持 FengWu v1 (ERA5) 和 v2 (Operational Analysis) 两种模型
数据格式：69x721x1440 (变量x纬度x经度)
"""
import os
import numpy as np
import onnxruntime as ort
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger


@dataclass
class FengWuConfig:
    """风乌模型配置"""
    model_path: str              # ONNX模型路径
    data_mean_path: str          # 数据均值路径
    data_std_path: str           # 数据标准差路径
    input_shape: Tuple = (69, 721, 1440)  # 输入形状
    forecast_steps: int = 56     # 预报步数（每步6小时）
    version: str = "v2"          # v1=ERA5, v2=Operational


class FengWuAdapter:
    """风乌气象预报模型适配器"""
    
    # 变量顺序（与论文一致）
    SURFACE_VARS = ['u10', 'v10', 't2m', 'msl']
    PRESSURE_LEVELS = [50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000]
    UPPER_VARS = ['z', 'q', 'u', 'v', 't']
    
    def __init__(self, config: FengWuConfig):
        self.config = config
        self.session = None
        self.data_mean = None
        self.data_std = None
        self._init_model()
        
    def _init_model(self):
        """初始化ONNX运行时"""
        options = ort.SessionOptions()
        options.enable_cpu_mem_arena = False
        options.enable_mem_pattern = False
        options.enable_mem_reuse = False
        options.intra_op_num_threads = 4
        
        cuda_options = {'arena_extend_strategy': 'kSameAsRequested'}
        providers = [
            ('CUDAExecutionProvider', cuda_options),
            'CPUExecutionProvider'
        ]
        
        self.session = ort.InferenceSession(
            self.config.model_path,
            sess_options=options,
            providers=providers
        )
        
        # 加载归一化参数
        self.data_mean = np.load(self.config.data_mean_path)[:, np.newaxis, np.newaxis]
        self.data_std = np.load(self.config.data_std_path)[:, np.newaxis, np.newaxis]
        
        logger.info(f"FengWu {self.config.version} 模型加载完成: {self.config.model_path}")
        
    def normalize(self, data: np.ndarray) -> np.ndarray:
        """数据归一化"""
        return (data - self.data_mean) / self.data_std
        
    def denormalize(self, data: np.ndarray) -> np.ndarray:
        """数据反归一化"""
        return data * self.data_std + self.data_mean
        
    def predict(self, input1: np.ndarray, input2: np.ndarray, 
                steps: Optional[int] = None) -> List[Dict]:
        """
        执行气象预报
        
        Args:
            input1: 第一时刻大气状态 [69, 721, 1440]
            input2: 第二时刻大气状态（6小时后）[69, 721, 1440]
            steps: 预报步数，默认56步（14天）
            
        Returns:
            预报结果列表，每步包含时间戳和各变量场
        """
        steps = steps or self.config.forecast_steps
        
        # 归一化并拼接输入
        input1_norm = self.normalize(input1.astype(np.float32))
        input2_norm = self.normalize(input2.astype(np.float32))
        model_input = np.concatenate((input1_norm, input2_norm), axis=0)[np.newaxis, :, :, :]
        
        results = []
        current_time = datetime.now()
        
        for step in range(steps):
            # ONNX推理
            output = self.session.run(None, {'input': model_input})[0]
            
            # 更新输入：滑动窗口，用后69个变量+新输出
            model_input = np.concatenate((model_input[:, 69:], output[:, :69]), axis=1)
            
            # 反归一化
            forecast = self.denormalize(output[0, :69])
            
            # 计算预报时间（每步6小时）
            forecast_time = current_time + timedelta(hours=6 * (step + 1))
            
            results.append({
                'step': step,
                'forecast_time': forecast_time.isoformat(),
                'lead_time_hours': 6 * (step + 1),
                'data': forecast,
                'variables': self._extract_variables(forecast)
            })
            
            logger.debug(f"FengWu 预报步 {step+1}/{steps} 完成")
            
        return results
        
    def _extract_variables(self, data: np.ndarray) -> Dict:
        """提取各变量场"""
        variables = {}
        
        # 地面变量
        for i, var in enumerate(self.SURFACE_VARS):
            variables[var] = data[i]
            
        # 高空变量
        idx = 4
        for var in self.UPPER_VARS:
            variables[var] = {}
            for level in self.PRESSURE_LEVELS:
                variables[var][f'{level}hPa'] = data[idx]
                idx += 1
                
        return variables
        
    def get_variable_at_level(self, result: Dict, var_name: str, 
                              level: Optional[str] = None) -> np.ndarray:
        """获取指定变量在指定气压层的场"""
        variables = result['variables']
        
        if var_name in self.SURFACE_VARS:
            return variables[var_name]
            
        if level and var_name in variables:
            return variables[var_name].get(level)
            
        raise ValueError(f"变量 {var_name} 或气压层 {level} 不存在")
```

- [ ] **Step 2: 创建 FengWu-GHR Torch 适配器**

Create: `python/algorithm-engine/app/adapters/fengwu_ghr_adapter.py`

```python
"""
FengWu-GHR 高分辨率气象模型适配器
支持 0.25° 和 0.09° 两种分辨率
基于 PyTorch 推理
"""
import os
import sys
import torch
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

# 添加 FengWu-GHR 路径
FENGWU_GHR_PATH = os.environ.get('FENGWU_GHR_PATH', 'D:/Developer/FengWu_All/FengWu-GHR')
if FENGWU_GHR_PATH not in sys.path:
    sys.path.insert(0, FENGWU_GHR_PATH)

from fengwu_ghr_inference_torch import FengWu_GHR_Inference
from mmengine.config import Config


@dataclass
class FengWuGHRConfig:
    """FengWu-GHR 配置"""
    config_path: str             # 配置文件路径
    checkpoint_dir: str          # 模型检查点目录
    save_path: str               # 输出保存路径
    resolution: str = "0.25"     # 0.25 或 0.09
    version: str = "v2"          # v1 或 v2
    inference_steps: int = 40    # 预报步数
    device: str = "cuda"         # cuda 或 cpu


class FengWuGHRAdapter:
    """FengWu-GHR 高分辨率气象模型适配器"""
    
    def __init__(self, config: FengWuGHRConfig):
        self.config = config
        self.inference = None
        self._init_model()
        
    def _init_model(self):
        """初始化 FengWu-GHR 推理引擎"""
        cfg = Config.fromfile(self.config.config_path)
        cfg.checkpoint_dir = self.config.checkpoint_dir
        cfg.save_cfg.save_path = self.config.save_path
        cfg.inference_steps = self.config.inference_steps
        cfg.fp16 = True
        
        self.inference = FengWu_GHR_Inference(cfg)
        logger.info(f"FengWu-GHR {self.config.resolution}° 模型加载完成")
        
    def predict(self, timestamp: str) -> Dict:
        """
        执行高分辨率气象预报
        
        Args:
            timestamp: 初始场时间戳 (ISO格式)
            
        Returns:
            预报结果路径和元数据
        """
        try:
            self.inference.inference(timestamp)
            
            return {
                'status': 'success',
                'timestamp': timestamp,
                'resolution': self.config.resolution,
                'output_path': self.config.save_path,
                'variables': self.inference.cfg.save_cfg.variables_list
            }
        except Exception as e:
            logger.error(f"FengWu-GHR 推理失败: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': timestamp
            }
```

---

### Task 2.2: 气象数据源配置与管理

**Files:**
- Create: `python/algorithm-engine/app/core/weather_source_manager.py`
- Modify: `python/algorithm-engine/app/config.py`

- [ ] **Step 1: 创建气象数据源管理器**

```python
"""
气象数据源管理器
支持多数据源切换：风乌(FengWu)、风雷(FengLei)、天资(TianZi)、WRF
"""
import os
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class WeatherSourceType(Enum):
    FENGWU = "fengwu"           # 风乌全球预报
    FENGWU_GHR = "fengwu_ghr"   # 风乌高分辨率
    FENGLEI = "fenglei"         # 风雷短临预报
    TIANZI = "tianzi"           # 天资区域AI
    WRF = "wrf"                 # WRF数值模式
    MOCK = "mock"               # 模拟数据（开发测试）


@dataclass
class WeatherSourceConfig:
    """气象数据源配置"""
    source_type: WeatherSourceType
    name: str
    enabled: bool = True
    priority: int = 0           # 优先级（数值越小优先级越高）
    config: Dict = field(default_factory=dict)
    
    # 风乌特定配置
    model_path: Optional[str] = None
    data_mean_path: Optional[str] = None
    data_std_path: Optional[str] = None
    
    # FengWu-GHR 特定配置
    ghr_config_path: Optional[str] = None
    checkpoint_dir: Optional[str] = None
    
    # 通用配置
    forecast_hours: int = 72    # 预报时效（小时）
    resolution: str = "0.25"    # 分辨率（度）


class WeatherSourceManager:
    """气象数据源管理器"""
    
    def __init__(self):
        self.sources: Dict[str, WeatherSourceConfig] = {}
        self.adapters: Dict[str, object] = {}
        self._init_default_sources()
        
    def _init_default_sources(self):
        """初始化默认数据源配置"""
        # 风乌（本地部署）
        fengwu_base = os.environ.get('FENGWU_PATH', 'D:/Developer/FengWu_All/FengWu')
        self.register_source(WeatherSourceConfig(
            source_type=WeatherSourceType.FENGWU,
            name="风乌全球预报",
            priority=1,
            model_path=os.path.join(fengwu_base, 'fengwu_v2.onnx'),
            data_mean_path=os.path.join(fengwu_base, 'data_mean.npy'),
            data_std_path=os.path.join(fengwu_base, 'data_std.npy'),
            forecast_hours=336,  # 14天
            resolution="0.25"
        ))
        
        # 风乌-GHR（本地部署）
        fengwu_ghr_base = os.environ.get('FENGWU_GHR_PATH', 'D:/Developer/FengWu_All/FengWu-GHR')
        self.register_source(WeatherSourceConfig(
            source_type=WeatherSourceType.FENGWU_GHR,
            name="风乌高分辨率",
            priority=2,
            ghr_config_path=os.path.join(fengwu_ghr_base, 'config/fengwu_ghr_cfg_74v_0.25_torch.py'),
            checkpoint_dir=os.path.join(fengwu_ghr_base, 'onnx/meta_model_0.25'),
            forecast_hours=240,  # 10天
            resolution="0.25"
        ))
        
        # 风雷（预留API配置）
        self.register_source(WeatherSourceConfig(
            source_type=WeatherSourceType.FENGLEI,
            name="风雷短临预报",
            enabled=False,  # 默认禁用，等待API
            priority=3,
            config={
                'api_endpoint': os.environ.get('FENGLEI_API_URL', ''),
                'api_key': os.environ.get('FENGLEI_API_KEY', ''),
                'forecast_hours': 3
            },
            resolution="0.01"
        ))
        
        # 天资（预留API配置）
        self.register_source(WeatherSourceConfig(
            source_type=WeatherSourceType.TIANZI,
            name="天资区域AI",
            enabled=False,
            priority=4,
            config={
                'api_endpoint': os.environ.get('TIANZI_API_URL', ''),
                'api_key': os.environ.get('TIANZI_API_KEY', ''),
                'forecast_hours': 12
            },
            resolution="0.01"
        ))
        
        # WRF（本地模式）
        self.register_source(WeatherSourceConfig(
            source_type=WeatherSourceType.WRF,
            name="WRF数值模式",
            enabled=False,
            priority=5,
            config={
                'wrf_path': os.environ.get('WRF_PATH', ''),
                'namelist_path': ''
            },
            resolution="0.03"
        ))
        
        # 模拟数据（开发测试）
        self.register_source(WeatherSourceConfig(
            source_type=WeatherSourceType.MOCK,
            name="模拟数据",
            enabled=True,
            priority=99,
            forecast_hours=72,
            resolution="0.25"
        ))
        
    def register_source(self, config: WeatherSourceConfig):
        """注册数据源"""
        self.sources[config.source_type.value] = config
        logger.info(f"注册气象数据源: {config.name} ({config.source_type.value})")
        
    def get_active_sources(self) -> List[WeatherSourceConfig]:
        """获取启用的数据源（按优先级排序）"""
        return sorted(
            [s for s in self.sources.values() if s.enabled],
            key=lambda x: x.priority
        )
        
    def get_source(self, source_type: str) -> Optional[WeatherSourceConfig]:
        """获取指定数据源配置"""
        return self.sources.get(source_type)
        
    def update_source_config(self, source_type: str, **kwargs):
        """更新数据源配置"""
        if source_type in self.sources:
            for key, value in kwargs.items():
                setattr(self.sources[source_type], key, value)
            logger.info(f"更新数据源配置: {source_type}")
            
    def get_adapter(self, source_type: str):
        """获取或创建数据源适配器"""
        if source_type not in self.adapters:
            config = self.sources.get(source_type)
            if not config:
                raise ValueError(f"未知数据源: {source_type}")
                
            if config.source_type == WeatherSourceType.FENGWU:
                from ..adapters.fengwu_adapter import FengWuAdapter, FengWuConfig
                self.adapters[source_type] = FengWuAdapter(FengWuConfig(
                    model_path=config.model_path,
                    data_mean_path=config.data_mean_path,
                    data_std_path=config.data_std_path
                ))
            elif config.source_type == WeatherSourceType.FENGWU_GHR:
                from ..adapters.fengwu_ghr_adapter import FengWuGHRAdapter, FengWuGHRConfig
                self.adapters[source_type] = FengWuGHRAdapter(FengWuGHRConfig(
                    config_path=config.ghr_config_path,
                    checkpoint_dir=config.checkpoint_dir,
                    save_path=os.environ.get('FENGWU_OUTPUT_PATH', '/tmp/fengwu_output')
                ))
                
        return self.adapters.get(source_type)
```

---

### Task 2.3: 前端气象数据源配置界面

**Files:**
- Create: `console/src/api/weather-source.ts`
- Create: `console/src/components/settings/WeatherSourceConfig.vue`

- [ ] **Step 1: 创建气象数据源 API**

```typescript
import { get, post } from './request'

export interface WeatherSource {
  sourceType: string
  name: string
  enabled: boolean
  priority: number
  forecastHours: number
  resolution: string
  config: Record<string, unknown>
}

export interface WeatherSourceUpdateRequest {
  enabled?: boolean
  priority?: number
  config?: Record<string, unknown>
}

export const weatherSourceApi = {
  /** 获取所有气象数据源配置 */
  list(): Promise<WeatherSource[]> {
    return get<WeatherSource[]>('/v1/weather/sources')
  },

  /** 获取指定数据源详情 */
  getDetail(sourceType: string): Promise<WeatherSource> {
    return get<WeatherSource>(`/v1/weather/sources/${sourceType}`)
  },

  /** 更新数据源配置 */
  update(sourceType: string, data: WeatherSourceUpdateRequest): Promise<void> {
    return post<void>(`/v1/weather/sources/${sourceType}/config`, data)
  },

  /** 测试数据源连接 */
  testConnection(sourceType: string): Promise<{ success: boolean; message: string }> {
    return post<{ success: boolean; message: string }>(`/v1/weather/sources/${sourceType}/test`)
  },

  /** 获取数据源状态 */
  getStatus(): Promise<Record<string, { status: string; lastUpdate: string }>> {
    return get<Record<string, { status: string; lastUpdate: string }>>('/v1/weather/sources/status')
  }
}
```

- [ ] **Step 2: 创建气象数据源配置组件**

```vue
<template>
  <div class="weather-source-config">
    <h3>气象数据源配置</h3>
    
    <el-alert
      v-if="hasUnconfiguredSources"
      type="warning"
      :closable="false"
      show-icon
    >
      <template #title>
        以下数据源尚未配置API密钥，将在获取权限后自动启用：
        <span v-for="s in unconfiguredSources" :key="s.sourceType" class="source-tag">
          {{ s.name }}
        </span>
      </template>
    </el-alert>
    
    <el-table :data="sources" style="width: 100%; margin-top: 16px">
      <el-table-column prop="name" label="数据源" width="150" />
      <el-table-column prop="sourceType" label="类型" width="120" />
      <el-table-column prop="resolution" label="分辨率" width="100">
        <template #default="{ row }">
          {{ row.resolution }}°
        </template>
      </el-table-column>
      <el-table-column prop="forecastHours" label="预报时效" width="100">
        <template #default="{ row }">
          {{ row.forecastHours }}h
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-switch
            v-model="row.enabled"
            :disabled="isSourceDisabled(row)"
            @change="handleToggle(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="优先级" width="100">
        <template #default="{ row }">
          <el-input-number
            v-model="row.priority"
            :min="1"
            :max="99"
            size="small"
            @change="handlePriorityChange(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button
            size="small"
            type="primary"
            @click="handleTest(row)"
            :loading="testing[row.sourceType]"
          >
            测试连接
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 风雷API配置弹窗 -->
    <el-dialog v-model="fengleiDialogVisible" title="风雷API配置" width="500px">
      <el-form :model="fengleiConfig" label-width="120px">
        <el-form-item label="API地址">
          <el-input v-model="fengleiConfig.apiEndpoint" placeholder="https://api.fenglei.com/v1" />
        </el-form-item>
        <el-form-item label="API密钥">
          <el-input v-model="fengleiConfig.apiKey" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="fengleiDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveFengleiConfig">保存</el-button>
      </template>
    </el-dialog>
    
    <!-- 天资API配置弹窗 -->
    <el-dialog v-model="tianziDialogVisible" title="天资API配置" width="500px">
      <el-form :model="tianziConfig" label-width="120px">
        <el-form-item label="API地址">
          <el-input v-model="tianziConfig.apiEndpoint" placeholder="https://api.tianzi.com/v1" />
        </el-form-item>
        <el-form-item label="API密钥">
          <el-input v-model="tianziConfig.apiKey" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tianziDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTianziConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { weatherSourceApi, type WeatherSource } from '@/api/weather-source'

const sources = ref<WeatherSource[]>([])
const testing = ref<Record<string, boolean>>({})
const fengleiDialogVisible = ref(false)
const tianziDialogVisible = ref(false)
const fengleiConfig = ref({ apiEndpoint: '', apiKey: '' })
const tianziConfig = ref({ apiEndpoint: '', apiKey: '' })

const unconfiguredSources = computed(() => 
  sources.value.filter(s => ['fenglei', 'tianzi'].includes(s.sourceType) && !s.enabled)
)

const hasUnconfiguredSources = computed(() => unconfiguredSources.value.length > 0)

function isSourceDisabled(row: WeatherSource): boolean {
  // 风雷和天资需要API配置才能启用
  if (['fenglei', 'tianzi'].includes(row.sourceType)) {
    return !row.config?.apiKey
  }
  return false
}

async function loadSources() {
  try {
    sources.value = await weatherSourceApi.list()
  } catch (e) {
    ElMessage.error('加载数据源配置失败')
  }
}

async function handleToggle(row: WeatherSource) {
  try {
    await weatherSourceApi.update(row.sourceType, { enabled: row.enabled })
    ElMessage.success(`${row.name} 已${row.enabled ? '启用' : '禁用'}`)
  } catch (e) {
    row.enabled = !row.enabled
    ElMessage.error('更新失败')
  }
}

async function handlePriorityChange(row: WeatherSource) {
  try {
    await weatherSourceApi.update(row.sourceType, { priority: row.priority })
  } catch (e) {
    ElMessage.error('更新优先级失败')
  }
}

async function handleTest(row: WeatherSource) {
  testing.value[row.sourceType] = true
  try {
    const result = await weatherSourceApi.testConnection(row.sourceType)
    ElMessage[result.success ? 'success' : 'error'](result.message)
  } finally {
    testing.value[row.sourceType] = false
  }
}

onMounted(loadSources)
</script>

<style scoped>
.weather-source-config {
  padding: 16px;
}
.source-tag {
  display: inline-block;
  margin: 0 4px;
  padding: 2px 8px;
  background: var(--el-color-warning-light-9);
  border: 1px solid var(--el-color-warning-light-5);
  border-radius: 4px;
  font-size: 12px;
}
</style>
```

---

## Phase 3: P0.5 科研可复现性基础设施（第 2-3 天）

### Task 3.1: 实验快照管理器

**Files:**
- Create: `python/algorithm-engine/app/core/snapshot_manager.py`

- [ ] **Step 1: 创建快照管理器**

```python
"""
实验快照管理器
实现实验完整状态的序列化与恢复，确保科研可复现性
"""
import os
import json
import hashlib
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from loguru import logger
import pickle


@dataclass
class ExperimentSnapshot:
    """实验快照"""
    snapshot_id: str           # 快照ID（哈希生成）
    experiment_id: str         # 实验ID
    algorithm_name: str        # 算法名称
    algorithm_version: str     # 算法版本
    timestamp: str             # 快照时间
    
    # 输入数据
    input_data: Dict[str, Any]  # 输入数据路径/摘要
    input_data_hash: str        # 输入数据哈希（用于校验）
    
    # 参数配置
    parameters: Dict[str, Any]  # 完整参数配置
    
    # 环境信息
    environment: Dict[str, str] # 环境信息（Python版本、库版本等）
    
    # 输出数据
    output_data: Dict[str, Any] # 输出数据路径/摘要
    output_data_hash: str       # 输出数据哈希
    
    # 指标
    metrics: Dict[str, float]   # 评估指标
    
    # 随机种子
    random_seed: Optional[int]  # 随机种子
    
    # 备注
    notes: Optional[str]        # 实验备注


class SnapshotManager:
    """实验快照管理器"""
    
    def __init__(self, base_path: str = "./experiments/snapshots"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def create_snapshot(self, 
                       experiment_id: str,
                       algorithm_name: str,
                       algorithm_version: str,
                       input_data: Dict[str, Any],
                       parameters: Dict[str, Any],
                       output_data: Dict[str, Any],
                       metrics: Dict[str, float],
                       random_seed: Optional[int] = None,
                       notes: Optional[str] = None) -> ExperimentSnapshot:
        """创建实验快照"""
        
        timestamp = datetime.now().isoformat()
        
        # 计算数据哈希
        input_hash = self._compute_hash(input_data)
        output_hash = self._compute_hash(output_data)
        
        # 生成快照ID
        snapshot_content = f"{experiment_id}:{algorithm_name}:{timestamp}:{input_hash}"
        snapshot_id = hashlib.sha256(snapshot_content.encode()).hexdigest()[:16]
        
        # 收集环境信息
        environment = self._collect_environment()
        
        snapshot = ExperimentSnapshot(
            snapshot_id=snapshot_id,
            experiment_id=experiment_id,
            algorithm_name=algorithm_name,
            algorithm_version=algorithm_version,
            timestamp=timestamp,
            input_data=input_data,
            input_data_hash=input_hash,
            parameters=parameters,
            environment=environment,
            output_data=output_data,
            output_data_hash=output_hash,
            metrics=metrics,
            random_seed=random_seed,
            notes=notes
        )
        
        # 保存快照
        self._save_snapshot(snapshot)
        
        logger.info(f"实验快照已创建: {snapshot_id} (实验: {experiment_id})")
        return snapshot
        
    def load_snapshot(self, snapshot_id: str) -> Optional[ExperimentSnapshot]:
        """加载实验快照"""
        snapshot_path = self.base_path / f"{snapshot_id}.json"
        
        if not snapshot_path.exists():
            logger.warning(f"快照不存在: {snapshot_id}")
            return None
            
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return ExperimentSnapshot(**data)
        
    def verify_snapshot(self, snapshot_id: str) -> bool:
        """验证快照完整性"""
        snapshot = self.load_snapshot(snapshot_id)
        if not snapshot:
            return False
            
        # 验证输入数据哈希
        input_data = self._load_data(snapshot.input_data)
        current_input_hash = self._compute_hash(input_data)
        
        if current_input_hash != snapshot.input_data_hash:
            logger.error(f"输入数据哈希不匹配: {snapshot_id}")
            return False
            
        # 验证输出数据哈希
        output_data = self._load_data(snapshot.output_data)
        current_output_hash = self._compute_hash(output_data)
        
        if current_output_hash != snapshot.output_data_hash:
            logger.error(f"输出数据哈希不匹配: {snapshot_id}")
            return False
            
        logger.info(f"快照验证通过: {snapshot_id}")
        return True
        
    def list_snapshots(self, experiment_id: Optional[str] = None) -> list:
        """列出快照"""
        snapshots = []
        
        for snapshot_file in self.base_path.glob("*.json"):
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if experiment_id is None or data.get('experiment_id') == experiment_id:
                snapshots.append(data)
                
        return sorted(snapshots, key=lambda x: x['timestamp'], reverse=True)
        
    def _compute_hash(self, data: Any) -> str:
        """计算数据哈希"""
        if isinstance(data, np.ndarray):
            return hashlib.sha256(data.tobytes()).hexdigest()[:16]
        elif isinstance(data, dict):
            content = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(content.encode()).hexdigest()[:16]
        else:
            content = str(data)
            return hashlib.sha256(content.encode()).hexdigest()[:16]
            
    def _collect_environment(self) -> Dict[str, str]:
        """收集环境信息"""
        import platform
        import sys
        
        return {
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'numpy_version': np.__version__,
            'timestamp': datetime.now().isoformat()
        }
        
    def _save_snapshot(self, snapshot: ExperimentSnapshot):
        """保存快照到文件"""
        snapshot_path = self.base_path / f"{snapshot.snapshot_id}.json"
        
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(snapshot), f, indent=2, ensure_ascii=False, default=str)
            
    def _load_data(self, data_info: Dict[str, Any]) -> Any:
        """加载数据"""
        if 'path' in data_info:
            path = data_info['path']
            if path.endswith('.npy'):
                return np.load(path)
            elif path.endswith('.pkl'):
                with open(path, 'rb') as f:
                    return pickle.load(f)
        return data_info
```

---

### Task 3.2: 实验日志与指标收集

**Files:**
- Create: `python/algorithm-engine/app/core/experiment_logger.py`
- Create: `python/algorithm-engine/app/core/report_generator.py`

- [ ] **Step 1: 创建实验日志记录器**

```python
"""
实验日志记录器
结构化记录算法实验过程，支持实时监控和事后分析
"""
import os
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from loguru import logger
import threading


@dataclass
class ExperimentLogEntry:
    """实验日志条目"""
    timestamp: str
    level: str           # INFO, WARNING, ERROR, PROGRESS
    stage: str           # 实验阶段（初始化/预处理/计算/后处理）
    message: str
    metrics: Optional[Dict[str, float]] = None
    elapsed_ms: Optional[int] = None


class ExperimentLogger:
    """实验日志记录器"""
    
    def __init__(self, experiment_id: str, algorithm_name: str, 
                 base_path: str = "./experiments/logs"):
        self.experiment_id = experiment_id
        self.algorithm_name = algorithm_name
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.base_path / f"{experiment_id}.jsonl"
        self.start_time = time.time()
        self.entries: List[ExperimentLogEntry] = []
        self._lock = threading.Lock()
        self._stage_start_times: Dict[str, float] = {}
        
        # 初始化日志
        self.info("experiment_start", "实验开始", {
            'experiment_id': experiment_id,
            'algorithm': algorithm_name,
            'start_time': datetime.now().isoformat()
        })
        
    def info(self, stage: str, message: str, metrics: Optional[Dict] = None):
        """记录信息日志"""
        self._log("INFO", stage, message, metrics)
        
    def warning(self, stage: str, message: str, metrics: Optional[Dict] = None):
        """记录警告日志"""
        self._log("WARNING", stage, message, metrics)
        
    def error(self, stage: str, message: str, metrics: Optional[Dict] = None):
        """记录错误日志"""
        self._log("ERROR", stage, message, metrics)
        
    def progress(self, stage: str, current: int, total: int, message: str = ""):
        """记录进度"""
        percentage = (current / total * 100) if total > 0 else 0
        self._log("PROGRESS", stage, 
                  f"{message} [{current}/{total}] {percentage:.1f}%",
                  {'progress_current': current, 'progress_total': total, 'progress_pct': percentage})
        
    def metric(self, stage: str, metrics: Dict[str, float]):
        """记录指标"""
        self._log("METRIC", stage, "指标更新", metrics)
        
    def stage_start(self, stage: str):
        """阶段开始"""
        self._stage_start_times[stage] = time.time()
        self._log("INFO", stage, f"阶段开始: {stage}")
        
    def stage_end(self, stage: str):
        """阶段结束"""
        elapsed = 0
        if stage in self._stage_start_times:
            elapsed = int((time.time() - self._stage_start_times[stage]) * 1000)
        self._log("INFO", stage, f"阶段完成: {stage}", elapsed_ms=elapsed)
        
    def experiment_end(self, final_metrics: Optional[Dict] = None):
        """实验结束"""
        total_elapsed = int((time.time() - self.start_time) * 1000)
        self._log("INFO", "experiment_end", "实验完成", 
                  metrics=final_metrics, elapsed_ms=total_elapsed)
        
    def get_summary(self) -> Dict:
        """获取实验摘要"""
        total_time = int((time.time() - self.start_time) * 1000)
        
        # 统计各阶段耗时
        stage_times = {}
        for entry in self.entries:
            if entry.elapsed_ms and entry.stage not in stage_times:
                stage_times[entry.stage] = entry.elapsed_ms
                
        return {
            'experiment_id': self.experiment_id,
            'algorithm': self.algorithm_name,
            'total_entries': len(self.entries),
            'total_time_ms': total_time,
            'stage_times': stage_times,
            'error_count': sum(1 for e in self.entries if e.level == 'ERROR'),
            'warning_count': sum(1 for e in self.entries if e.level == 'WARNING')
        }
        
    def export_to_json(self) -> str:
        """导出为JSON文件"""
        output_path = self.base_path / f"{self.experiment_id}_full.json"
        
        data = {
            'experiment_id': self.experiment_id,
            'algorithm': self.algorithm_name,
            'entries': [asdict(e) for e in self.entries],
            'summary': self.get_summary()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
        return str(output_path)
        
    def _log(self, level: str, stage: str, message: str, 
             metrics: Optional[Dict] = None, elapsed_ms: Optional[int] = None):
        """内部日志记录"""
        entry = ExperimentLogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            stage=stage,
            message=message,
            metrics=metrics,
            elapsed_ms=elapsed_ms
        )
        
        with self._lock:
            self.entries.append(entry)
            
            # 写入JSONL文件
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(entry), ensure_ascii=False, default=str) + '\n')
                
        # 同时输出到标准日志
        logger.log(level, f"[{self.experiment_id}] [{stage}] {message}")
```

- [ ] **Step 2: 创建报告生成器**

```python
"""
标准化对比报告生成器
生成符合期刊论文要求的图表和表格
"""
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from loguru import logger


@dataclass
class ReportConfig:
    """报告配置"""
    title: str
    author: str
    institution: str
    output_dir: str = "./experiments/reports"
    figure_dpi: int = 300
    figure_format: str = "png"  # png, pdf, svg
    table_format: str = "csv"   # csv, latex


class ReportGenerator:
    """标准化对比报告生成器"""
    
    def __init__(self, config: ReportConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置matplotlib中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
    def generate_comparison_report(self, 
                                   experiment_results: List[Dict],
                                   metrics: List[str],
                                   output_name: Optional[str] = None) -> str:
        """
        生成算法对比报告
        
        Args:
            experiment_results: 多个实验的结果列表
            metrics: 需要对比的指标名称
            output_name: 输出文件名（不含扩展名）
            
        Returns:
            生成的报告文件路径
        """
        output_name = output_name or f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        report_dir = self.output_dir / output_name
        report_dir.mkdir(exist_ok=True)
        
        # 1. 生成对比表格
        self._generate_comparison_table(experiment_results, metrics, report_dir)
        
        # 2. 生成雷达图
        self._generate_radar_chart(experiment_results, metrics, report_dir)
        
        # 3. 生成柱状图
        self._generate_bar_chart(experiment_results, metrics, report_dir)
        
        # 4. 生成折线图（时序指标）
        self._generate_line_chart(experiment_results, report_dir)
        
        # 5. 生成LaTeX报告模板
        self._generate_latex_template(experiment_results, metrics, report_dir)
        
        logger.info(f"对比报告已生成: {report_dir}")
        return str(report_dir)
        
    def _generate_comparison_table(self, results: List[Dict], metrics: List[str], 
                                   report_dir: Path):
        """生成对比表格"""
        # CSV格式
        csv_path = report_dir / "comparison_table.csv"
        with open(csv_path, 'w', encoding='utf-8') as f:
            # 表头
            headers = ['算法', '版本'] + metrics + ['运行时间(s)', '时间戳']
            f.write(','.join(headers) + '\n')
            
            # 数据行
            for result in results:
                row = [
                    result.get('algorithm_name', ''),
                    result.get('algorithm_version', ''),
                ]
                for metric in metrics:
                    value = result.get('metrics', {}).get(metric, 'N/A')
                    row.append(f"{value:.4f}" if isinstance(value, float) else str(value))
                row.append(f"{result.get('execution_time', 0):.2f}")
                row.append(result.get('timestamp', ''))
                f.write(','.join(row) + '\n')
                
        # LaTeX格式
        latex_path = report_dir / "comparison_table.tex"
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write('\\begin{table}[htbp]\n')
            f.write('\\centering\n')
            f.write('\\caption{算法性能对比}\n')
            f.write('\\begin{tabular}{l' + 'c' * len(metrics) + '}\n')
            f.write('\\hline\n')
            f.write('算法 & ' + ' & '.join(metrics) + ' \\\\n')
            f.write('\\hline\n')
            
            for result in results:
                row = [result.get('algorithm_name', '')]
                for metric in metrics:
                    value = result.get('metrics', {}).get(metric, 'N/A')
                    row.append(f"{value:.4f}" if isinstance(value, float) else str(value))
                f.write(' & '.join(row) + ' \\\\n')
                
            f.write('\\hline\n')
            f.write('\\end{tabular}\n')
            f.write('\\end{table}\n')
            
    def _generate_radar_chart(self, results: List[Dict], metrics: List[str], 
                              report_dir: Path):
        """生成雷达图"""
        if len(metrics) < 3:
            return
            
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]  # 闭合
        
        colors = plt.cm.tab10(np.linspace(0, 1, len(results)))
        
        for idx, result in enumerate(results):
            values = []
            for metric in metrics:
                value = result.get('metrics', {}).get(metric, 0)
                # 归一化到0-1范围（假设指标越大越好）
                max_val = max(r.get('metrics', {}).get(metric, 1) for r in results)
                values.append(value / max_val if max_val > 0 else 0)
            values += values[:1]  # 闭合
            
            ax.plot(angles, values, 'o-', linewidth=2, 
                   label=result.get('algorithm_name', ''), color=colors[idx])
            ax.fill(angles, values, alpha=0.15, color=colors[idx])
            
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics)
        ax.set_ylim(0, 1)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        ax.set_title('算法性能雷达图', pad=20)
        
        plt.tight_layout()
        plt.savefig(report_dir / f"radar_chart.{self.config.figure_format}", 
                   dpi=self.config.figure_dpi, bbox_inches='tight')
        plt.close()
        
    def _generate_bar_chart(self, results: List[Dict], metrics: List[str], 
                           report_dir: Path):
        """生成柱状图"""
        fig, axes = plt.subplots(1, len(metrics), figsize=(5 * len(metrics), 5))
        
        if len(metrics) == 1:
            axes = [axes]
            
        algorithm_names = [r.get('algorithm_name', f'Algo_{i}') 
                          for i, r in enumerate(results)]
        
        for idx, metric in enumerate(metrics):
            values = [r.get('metrics', {}).get(metric, 0) for r in results]
            
            axes[idx].bar(algorithm_names, values, color=plt.cm.tab10(np.linspace(0, 1, len(results))))
            axes[idx].set_title(f'{metric}')
            axes[idx].set_ylabel('数值')
            axes[idx].tick_params(axis='x', rotation=45)
            
        plt.tight_layout()
        plt.savefig(report_dir / f"bar_chart.{self.config.figure_format}", 
                   dpi=self.config.figure_dpi, bbox_inches='tight')
        plt.close()
        
    def _generate_line_chart(self, results: List[Dict], report_dir: Path):
        """生成折线图（时序指标）"""
        # 如果结果包含时序数据，生成折线图
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for result in results:
            if 'time_series' in result:
                ts_data = result['time_series']
                ax.plot(ts_data.get('timestamps', []), 
                       ts_data.get('values', []),
                       label=result.get('algorithm_name', ''),
                       linewidth=2)
                
        ax.set_xlabel('时间')
        ax.set_ylabel('指标值')
        ax.set_title('算法时序性能对比')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(report_dir / f"line_chart.{self.config.figure_format}", 
                   dpi=self.config.figure_dpi, bbox_inches='tight')
        plt.close()
        
    def _generate_latex_template(self, results: List[Dict], metrics: List[str], 
                                 report_dir: Path):
        """生成LaTeX报告模板"""
        latex_path = report_dir / "report_template.tex"
        
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write('\\documentclass{article}\n')
            f.write('\\usepackage{graphicx}\n')
            f.write('\\usepackage{booktabs}\n')
            f.write('\\usepackage{geometry}\n')
            f.write('\\geometry{a4paper, margin=1in}\n')
            f.write('\\begin{document}\n\n')
            
            f.write(f'\\title{{{self.config.title}}}\n')
            f.write(f'\\author{{{self.config.author}}}\n')
            f.write(f'\\date{{{datetime.now().strftime("%Y-%m-%d")}}}\n')
            f.write('\\maketitle\n\n')
            
            f.write('\\section{实验概述}\n')
            f.write(f'本实验对比了 {len(results)} 种算法的性能表现。\n\n')
            
            f.write('\\section{性能对比}\n')
            f.write('\\input{comparison_table}\n\n')
            
            f.write('\\section{可视化结果}\n')
            f.write('\\begin{figure}[htbp]\n')
            f.write('\\centering\n')
            f.write(f'\\includegraphics[width=0.8\\textwidth]{{radar_chart.{self.config.figure_format}}}\n')
            f.write('\\caption{算法性能雷达图}\n')
            f.write('\\end{figure}\n\n')
            
            f.write('\\begin{figure}[htbp]\n')
            f.write('\\centering\n')
            f.write(f'\\includegraphics[width=0.8\\textwidth]{{bar_chart.{self.config.figure_format}}}\n')
            f.write('\\caption{算法性能柱状图}\n')
            f.write('\\end{figure}\n\n')
            
            f.write('\\end{document}\n')
```

---

## Phase 4: P0 全链路真实数据算法验证（第 3-5 天）

### Task 4.1: 同化算法真实数据验证

**Files:**
- Modify: `python/algorithm-engine/app/algorithms/assimilation/...`
- Create: `python/algorithm-engine/app/algorithms/assimilation/var_3d.py`
- Create: `python/algorithm-engine/app/algorithms/assimilation/var_4d.py`
- Create: `python/algorithm-engine/app/algorithms/assimilation/var_5d.py`

- [ ] **Step 1: 创建 3D-VAR 同化算法（真实数据版）**

```python
"""
3D-VAR 数据同化算法
使用真实 FengWu 气象数据作为背景场和观测
"""
import numpy as np
from typing import Dict, Any, Optional
from loguru import logger
from ..core.experiment_logger import ExperimentLogger
from ..core.snapshot_manager import SnapshotManager


class ThreeDVarAssimilation:
    """3D-VAR 数据同化"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.experiment_logger = None
        self.snapshot_manager = SnapshotManager()
        
    def assimilate(self, 
                   background_field: np.ndarray,      # 背景场 (FengWu预报)
                   observations: np.ndarray,          # 观测数据
                   observation_error: np.ndarray,     # 观测误差协方差
                   background_error: np.ndarray,      # 背景误差协方差
                   experiment_id: Optional[str] = None) -> Dict[str, Any]:
        """
        执行3D-VAR同化
        
        代价函数: J(x) = 1/2[(x-xb)^T B^-1 (x-xb) + (y-Hx)^T R^-1 (y-Hx)]
        
        Args:
            background_field: 背景场 [nvar, nlat, nlon]
            observations: 观测数据 [nobs]
            observation_error: 观测误差协方差矩阵 [nobs, nobs]
            background_error: 背景误差协方差矩阵 [nvar, nvar]
            
        Returns:
            同化结果和分析场
        """
        experiment_id = experiment_id or f"3dvar_{int(time.time())}"
        self.experiment_logger = ExperimentLogger(experiment_id, "3D-VAR")
        
        self.experiment_logger.stage_start("initialization")
        
        # 初始化参数
        max_iterations = self.config.get('max_iterations', 50)
        convergence_threshold = self.config.get('convergence_threshold', 1e-6)
        
        self.experiment_logger.info("initialization", 
                                   f"初始化完成: max_iter={max_iterations}, threshold={convergence_threshold}")
        self.experiment_logger.stage_end("initialization")
        
        # 同化计算
        self.experiment_logger.stage_start("assimilation")
        
        # 简化的3D-VAR实现（实际应使用更高效的优化算法）
        analysis = background_field.copy()
        
        for iteration in range(max_iterations):
            # 计算代价函数梯度（简化版）
            innovation = observations - self._observation_operator(analysis)
            
            # 背景项梯度
            bg_gradient = np.linalg.solve(background_error, analysis - background_field)
            
            # 观测项梯度
            obs_gradient = self._observation_operator_adjoint(
                np.linalg.solve(observation_error, innovation)
            )
            
            # 总梯度
            gradient = bg_gradient + obs_gradient
            
            # 更新分析场（最速下降法，实际应使用共轭梯度或L-BFGS）
            step_size = self._line_search(analysis, gradient, background_field, 
                                         observations, background_error, observation_error)
            analysis = analysis - step_size * gradient
            
            # 计算代价函数值
            cost = self._cost_function(analysis, background_field, observations,
                                      background_error, observation_error)
            
            self.experiment_logger.metric("assimilation", {
                'iteration': iteration,
                'cost': cost,
                'gradient_norm': np.linalg.norm(gradient)
            })
            
            # 检查收敛
            if np.linalg.norm(gradient) < convergence_threshold:
                self.experiment_logger.info("assimilation", 
                                          f"收敛于第 {iteration} 次迭代")
                break
                
            if iteration % 10 == 0:
                self.experiment_logger.progress("assimilation", iteration, max_iterations)
                
        self.experiment_logger.stage_end("assimilation")
        
        # 计算评估指标
        self.experiment_logger.stage_start("evaluation")
        
        rmse = np.sqrt(np.mean((analysis - background_field)**2))
        innovation_norm = np.linalg.norm(observations - self._observation_operator(analysis))
        
        metrics = {
            'rmse': float(rmse),
            'innovation_norm': float(innovation_norm),
            'iterations': iteration + 1,
            'final_cost': float(cost)
        }
        
        self.experiment_logger.metric("evaluation", metrics)
        self.experiment_logger.stage_end("evaluation")
        
        # 创建快照
        snapshot = self.snapshot_manager.create_snapshot(
            experiment_id=experiment_id,
            algorithm_name="3D-VAR",
            algorithm_version="1.0",
            input_data={
                'background_field_shape': background_field.shape,
                'observations_shape': observations.shape
            },
            parameters=self.config,
            output_data={
                'analysis_shape': analysis.shape,
                'metrics': metrics
            },
            metrics=metrics,
            random_seed=self.config.get('random_seed'),
            notes="使用FengWu背景场的3D-VAR同化实验"
        )
        
        self.experiment_logger.experiment_end(metrics)
        
        return {
            'analysis': analysis,
            'background': background_field,
            'metrics': metrics,
            'snapshot_id': snapshot.snapshot_id,
            'log_path': self.experiment_logger.export_to_json()
        }
        
    def _cost_function(self, x, xb, y, B, R):
        """计算3D-VAR代价函数"""
        bg_term = 0.5 * np.dot(x - xb, np.linalg.solve(B, x - xb))
        innovation = y - self._observation_operator(x)
        obs_term = 0.5 * np.dot(innovation, np.linalg.solve(R, innovation))
        return bg_term + obs_term
        
    def _observation_operator(self, x):
        """观测算子（简化：直接采样）"""
        return x.flatten()[:len(x)]  # 简化实现
        
    def _observation_operator_adjoint(self, y):
        """观测算子伴随"""
        return y.reshape(self.config.get('grid_shape', (69, 721, 1440)))
        
    def _line_search(self, x, grad, xb, y, B, R):
        """线搜索（简化：固定步长）"""
        return 0.01
```

---

### Task 4.2: 路径规划算法真实数据验证

**Files:**
- Modify: `python/algorithm-engine/app/algorithms/planning/...`

- [ ] **Step 1: 创建真实气象场感知的路径规划基类**

```python
"""
气象感知路径规划基类
所有路径规划算法继承此类，统一接入真实气象数据
"""
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from loguru import logger


@dataclass
class WeatherField:
    """气象场数据"""
    u10: np.ndarray      # 10米U风分量 [nlat, nlon]
    v10: np.ndarray      # 10米V风分量 [nlat, nlon]
    t2m: np.ndarray      # 2米温度 [nlat, nlon]
    msl: np.ndarray      # 海平面气压 [nlat, nlon]
    lat: np.ndarray      # 纬度网格
    lon: np.ndarray      # 经度网格
    timestamp: str       # 时间戳
    
    @property
    def wind_speed(self) -> np.ndarray:
        """计算风速"""
        return np.sqrt(self.u10**2 + self.v10**2)
        
    @property
    def wind_direction(self) -> np.ndarray:
        """计算风向（度）"""
        return np.degrees(np.arctan2(self.v10, self.u10))


@dataclass
class PathPoint:
    """路径点"""
    lat: float
    lon: float
    altitude: float
    timestamp: str
    weather: Optional[Dict] = None  # 该点的气象条件


class WeatherAwarePlanner(ABC):
    """气象感知路径规划器基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.weather_field: Optional[WeatherField] = None
        
    def set_weather_field(self, weather: WeatherField):
        """设置气象场"""
        self.weather_field = weather
        logger.info(f"气象场已设置: {weather.timestamp}, 网格: {weather.u10.shape}")
        
    def get_weather_at_point(self, lat: float, lon: float) -> Dict[str, float]:
        """获取指定点的气象条件（双线性插值）"""
        if self.weather_field is None:
            return {}
            
        # 找到最近的网格点
        lat_idx = np.argmin(np.abs(self.weather_field.lat - lat))
        lon_idx = np.argmin(np.abs(self.weather_field.lon - lon))
        
        return {
            'u10': float(self.weather_field.u10[lat_idx, lon_idx]),
            'v10': float(self.weather_field.v10[lat_idx, lon_idx]),
            'wind_speed': float(self.weather_field.wind_speed[lat_idx, lon_idx]),
            'wind_direction': float(self.weather_field.wind_direction[lat_idx, lon_idx]),
            't2m': float(self.weather_field.t2m[lat_idx, lon_idx]),
            'msl': float(self.weather_field.msl[lat_idx, lon_idx])
        }
        
    def calculate_wind_cost(self, lat: float, lon: float, 
                           heading: float) -> float:
        """
        计算风阻代价
        
        Args:
            lat, lon: 位置
            heading: 航向（度，正北为0）
            
        Returns:
            风阻代价（0-1，越小越好）
        """
        weather = self.get_weather_at_point(lat, lon)
        if not weather:
            return 0.0
            
        wind_speed = weather['wind_speed']
        wind_dir = weather['wind_direction']
        
        # 计算相对风向
        relative_wind = np.abs(heading - wind_dir)
        relative_wind = min(relative_wind, 360 - relative_wind)
        
        # 逆风代价高，顺风代价低
        headwind_component = wind_speed * np.cos(np.radians(relative_wind))
        
        # 归一化代价
        max_wind = self.config.get('max_wind_speed', 20.0)  # m/s
        cost = max(0, headwind_component / max_wind)
        
        return min(cost, 1.0)
        
    @abstractmethod
    def plan(self, start: Tuple[float, float], 
             goal: Tuple[float, float],
             waypoints: Optional[List[Tuple[float, float]]] = None) -> List[PathPoint]:
        """
        规划路径
        
        Args:
            start: 起点 (lat, lon)
            goal: 终点 (lat, lon)
            waypoints: 途经点列表
            
        Returns:
            路径点列表
        """
        pass
```

---

## Phase 5: P1 环境切换与 UTM 双环境（第 4-5 天）

### Task 5.1: 环境切换检测与配置

**Files:**
- Create: `console/src/components/settings/EnvironmentSwitcher.vue`
- Modify: `console/src/stores/app.ts`

- [ ] **Step 1: 创建环境切换组件**

```vue
<template>
  <div class="environment-switcher">
    <el-dropdown @command="handleEnvChange" trigger="click">
      <el-button :type="envType" size="small">
        <el-icon><Setting /></el-icon>
        {{ currentEnvLabel }}
        <el-icon class="el-icon--right"><ArrowDown /></el-icon>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="dev" :disabled="currentEnv === 'dev'">
            <el-tag size="small" type="info">开发</el-tag>
            <span class="env-desc">模拟数据 + 模拟UTM</span>
          </el-dropdown-item>
          <el-dropdown-item command="test" :disabled="currentEnv === 'test'">
            <el-tag size="small" type="warning">测试</el-tag>
            <span class="env-desc">真实数据 + 模拟UTM</span>
          </el-dropdown-item>
          <el-dropdown-item command="staging" :disabled="currentEnv === 'staging'">
            <el-tag size="small" type="primary">灰度</el-tag>
            <span class="env-desc">真实数据 + 真实UTM</span>
          </el-dropdown-item>
          <el-dropdown-item command="prod" :disabled="currentEnv === 'prod'">
            <el-tag size="small" type="danger">生产</el-tag>
            <span class="env-desc">全量真实环境</span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
    
    <!-- 环境状态指示器 -->
    <div class="env-status">
      <el-tag :type="dataSourceStatus.type" size="small" effect="plain">
        数据源: {{ dataSourceStatus.label }}
      </el-tag>
      <el-tag :type="utmStatus.type" size="small" effect="plain">
        UTM: {{ utmStatus.label }}
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/app'
import { ElMessage, ElMessageBox } from 'element-plus'

const appStore = useAppStore()

const currentEnv = computed(() => appStore.environment)

const envLabels: Record<string, string> = {
  dev: '开发环境',
  test: '测试环境',
  staging: '灰度环境',
  prod: '生产环境'
}

const currentEnvLabel = computed(() => envLabels[currentEnv.value] || '未知环境')

const envType = computed(() => {
  const types: Record<string, string> = {
    dev: 'info',
    test: 'warning',
    staging: 'primary',
    prod: 'danger'
  }
  return types[currentEnv.value] || 'info'
})

const dataSourceStatus = computed(() => {
  const isReal = ['test', 'staging', 'prod'].includes(currentEnv.value)
  return {
    type: isReal ? 'success' : 'info',
    label: isReal ? '真实数据' : '模拟数据'
  }
})

const utmStatus = computed(() => {
  const isReal = ['staging', 'prod'].includes(currentEnv.value)
  return {
    type: isReal ? 'success' : 'info',
    label: isReal ? '真实UTM' : '模拟UTM'
  }
})

async function handleEnvChange(env: string) {
  if (env === 'prod' || env === 'staging') {
    try {
      await ElMessageBox.confirm(
        `切换到${envLabels[env]}将启用真实外部系统，确认继续？`,
        '环境切换确认',
        {
          confirmButtonText: '确认切换',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  }
  
  appStore.setEnvironment(env)
  ElMessage.success(`已切换到${envLabels[env]}`)
  
  // 刷新页面以应用新环境配置
  window.location.reload()
}
</script>

<style scoped>
.environment-switcher {
  display: flex;
  align-items: center;
  gap: 12px;
}
.env-desc {
  margin-left: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.env-status {
  display: flex;
  gap: 8px;
}
</style>
```

---

### Task 5.2: UTM 双环境配置

**Files:**
- Modify: `gateway/api-gateway/src/main/resources/application.yml`
- Create: `services/utm-api/src/main/java/com/uav/utm/config/UtmEnvironmentConfig.java`

- [ ] **Step 1: 添加 UTM 环境配置**

```yaml
# application.yml (gateway)
gateway:
  utm:
    # 环境切换开关
    external:
      enabled: ${UTM_EXTERNAL_ENABLED:false}
    
    # 模拟UTM配置（开发/测试环境）
    mock:
      enabled: true
      response_delay_ms: 100
      failure_rate: 0.0
      
    # 真实UTM配置（灰度/生产环境）
    real:
      base_url: ${UTM_REAL_BASE_URL:https://utm.gov.cn/api}
      api_key: ${UTM_API_KEY:}
      timeout_ms: 5000
      retry_count: 3
      
    # 白名单配置
    whitelist: ${UTM_WHITELIST:127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16}
    secret: ${UTM_SECRET:}
    replay_window: 300
```

- [ ] **Step 2: 创建 UTM 环境配置类**

```java
package com.uav.utm.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "uav.utm")
public class UtmEnvironmentConfig {
    
    private ExternalConfig external = new ExternalConfig();
    private MockConfig mock = new MockConfig();
    private RealConfig real = new RealConfig();
    
    @Data
    public static class ExternalConfig {
        private boolean enabled = false;  // 是否启用真实外部UTM
    }
    
    @Data
    public static class MockConfig {
        private boolean enabled = true;
        private long responseDelayMs = 100;
        private double failureRate = 0.0;
    }
    
    @Data
    public static class RealConfig {
        private String baseUrl;
        private String apiKey;
        private long timeoutMs = 5000;
        private int retryCount = 3;
    }
    
    /**
     * 判断是否使用真实UTM
     */
    public boolean isRealUtmEnabled() {
        return external.isEnabled();
    }
    
    /**
     * 获取当前UTM基础URL
     */
    public String getCurrentBaseUrl() {
        return isRealUtmEnabled() ? real.getBaseUrl() : "http://mock-utm:8080";
    }
}
```

---

## Phase 6: 前端功能分离（科研 vs API运营）

### Task 6.1: 前端路由重构

**Files:**
- Modify: `console/src/router/index.ts`

- [ ] **Step 1: 重构路由结构**

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 科研功能模块路由
const researchRoutes = [
  {
    path: '/research',
    component: () => import('@/views/research/ResearchLayout.vue'),
    meta: { roles: ['SUPER_ADMIN', 'ALGORITHM_ADMIN', 'OPERATOR', 'TENANT_ADMIN'] },
    children: [
      {
        path: 'sandbox',
        name: 'ResearchSandbox',
        component: () => import('@/views/research/SandboxView.vue'),
        meta: { title: '科研沙箱', icon: 'Experiment' }
      },
      {
        path: 'algorithm-lab',
        name: 'AlgorithmLab',
        component: () => import('@/views/research/AlgorithmLab.vue'),
        meta: { title: '算法实验室', icon: 'Cpu' }
      },
      {
        path: 'experiments',
        name: 'ExperimentManager',
        component: () => import('@/views/research/ExperimentManager.vue'),
        meta: { title: '实验管理', icon: 'List' }
      },
      {
        path: 'reports',
        name: 'ReportCenter',
        component: () => import('@/views/research/ReportCenter.vue'),
        meta: { title: '报告中心', icon: 'Document' }
      },
      {
        path: 'wrf-analysis',
        name: 'WRFAnalysis',
        component: () => import('@/views/research/WRFAnalysis.vue'),
        meta: { title: 'WRF地形分析', icon: 'MapLocation' }
      }
    ]
  }
]

// API运营管理模块路由
const apiRoutes = [
  {
    path: '/api-ops',
    component: () => import('@/views/api/ApiOpsLayout.vue'),
    meta: { roles: ['SUPER_ADMIN', 'TENANT_ADMIN'] },
    children: [
      {
        path: 'dashboard',
        name: 'ApiDashboard',
        component: () => import('@/views/api/DashboardView.vue'),
        meta: { title: '运营仪表盘', icon: 'Odometer' }
      },
      {
        path: 'api-keys',
        name: 'ApiKeyManager',
        component: () => import('@/views/api/ApiKeyManager.vue'),
        meta: { title: 'API密钥管理', icon: 'Key' }
      },
      {
        path: 'tenants',
        name: 'TenantManager',
        component: () => import('@/views/api/TenantManager.vue'),
        meta: { title: '租户管理', icon: 'UserFilled' }
      },
      {
        path: 'usage',
        name: 'UsageAnalytics',
        component: () => import('@/views/api/UsageAnalytics.vue'),
        meta: { title: '用量分析', icon: 'TrendCharts' }
      },
      {
        path: 'health',
        name: 'ServiceHealth',
        component: () => import('@/views/api/ServiceHealth.vue'),
        meta: { title: '服务健康', icon: 'FirstAidKit' }
      },
      {
        path: 'alerts',
        name: 'AlertRules',
        component: () => import('@/views/api/AlertRules.vue'),
        meta: { title: '告警规则', icon: 'Bell' }
      }
    ]
  }
]

// 系统管理路由（公共）
const systemRoutes = [
  {
    path: '/system',
    component: () => import('@/views/system/SystemLayout.vue'),
    meta: { roles: ['SUPER_ADMIN', 'TENANT_ADMIN'] },
    children: [
      {
        path: 'users',
        name: 'UserList',
        component: () => import('@/views/system/UserList.vue'),
        meta: { title: '用户管理', icon: 'User' }
      },
      {
        path: 'roles',
        name: 'RoleList',
        component: () => import('@/views/system/RoleList.vue'),
        meta: { title: '角色管理', icon: 'Lock' }
      },
      {
        path: 'database',
        name: 'DatabaseView',
        component: () => import('@/views/system/DatabaseView.vue'),
        meta: { title: '数据库管理', icon: 'Coin' }
      },
      {
        path: 'settings',
        name: 'SystemSettings',
        component: () => import('@/views/system/SettingsView.vue'),
        meta: { title: '系统设置', icon: 'Setting' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/research/sandbox'
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { public: true }
    },
    ...researchRoutes,
    ...apiRoutes,
    ...systemRoutes,
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/NotFound.vue')
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // 公开页面直接放行
  if (to.meta.public) {
    next()
    return
  }
  
  // 检查登录状态
  if (!authStore.isAuthenticated) {
    next('/login')
    return
  }
  
  // 检查角色权限
  if (to.meta.roles && !to.meta.roles.includes(authStore.currentRole)) {
    next('/403')
    return
  }
  
  next()
})

export default router
```

---

### Task 6.2: 科研布局组件

**Files:**
- Create: `console/src/views/research/ResearchLayout.vue`

- [ ] **Step 1: 创建科研布局**

```vue
<template>
  <div class="research-layout">
    <el-container>
      <!-- 左侧菜单 -->
      <el-aside width="220px" class="research-sidebar">
        <div class="sidebar-header">
          <el-icon size="24"><Experiment /></el-icon>
          <span class="title">科研平台</span>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          router
          class="research-menu"
          background-color="transparent"
          text-color="var(--color-text)"
          active-text-color="var(--color-primary)"
        >
          <el-menu-item index="/research/sandbox">
            <el-icon><Monitor /></el-icon>
            <span>科研沙箱</span>
          </el-menu-item>
          
          <el-menu-item index="/research/algorithm-lab">
            <el-icon><Cpu /></el-icon>
            <span>算法实验室</span>
          </el-menu-item>
          
          <el-menu-item index="/research/experiments">
            <el-icon><List /></el-icon>
            <span>实验管理</span>
          </el-menu-item>
          
          <el-menu-item index="/research/reports">
            <el-icon><Document /></el-icon>
            <span>报告中心</span>
          </el-menu-item>
          
          <el-sub-menu index="/research/wrf">
            <template #title>
              <el-icon><MapLocation /></el-icon>
              <span>WRF分析</span>
            </template>
            <el-menu-item index="/research/wrf-analysis">地形分析</el-menu-item>
            <el-menu-item index="/research/pbl-analysis">边界层分析</el-menu-item>
            <el-menu-item index="/research/cu-analysis">积云参数化</el-menu-item>
          </el-sub-menu>
        </el-menu>
        
        <!-- 环境状态 -->
        <div class="env-info">
          <el-divider />
          <EnvironmentSwitcher />
          <WeatherSourceConfig compact />
        </div>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-main class="research-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import EnvironmentSwitcher from '@/components/settings/EnvironmentSwitcher.vue'
import WeatherSourceConfig from '@/components/settings/WeatherSourceConfig.vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.research-layout {
  height: 100vh;
}

.research-sidebar {
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--color-border);
}

.sidebar-header .title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-primary);
}

.research-menu {
  flex: 1;
  border-right: none;
}

.env-info {
  padding: 12px;
}

.research-main {
  background: var(--color-bg);
  padding: 20px;
  overflow-y: auto;
}
</style>
```

---

### Task 6.3: API运营布局组件

**Files:**
- Create: `console/src/views/api/ApiOpsLayout.vue`

- [ ] **Step 1: 创建API运营布局**

```vue
<template>
  <div class="api-ops-layout">
    <el-container>
      <!-- 左侧菜单 -->
      <el-aside width="220px" class="api-sidebar">
        <div class="sidebar-header">
          <el-icon size="24"><Connection /></el-icon>
          <span class="title">API运营</span>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          router
          class="api-menu"
          background-color="transparent"
          text-color="var(--color-text)"
          active-text-color="var(--color-primary)"
        >
          <el-menu-item index="/api-ops/dashboard">
            <el-icon><Odometer /></el-icon>
            <span>运营仪表盘</span>
          </el-menu-item>
          
          <el-menu-item index="/api-ops/api-keys">
            <el-icon><Key /></el-icon>
            <span>API密钥管理</span>
          </el-menu-item>
          
          <el-menu-item index="/api-ops/tenants">
            <el-icon><UserFilled /></el-icon>
            <span>租户管理</span>
          </el-menu-item>
          
          <el-menu-item index="/api-ops/usage">
            <el-icon><TrendCharts /></el-icon>
            <span>用量分析</span>
          </el-menu-item>
          
          <el-menu-item index="/api-ops/health">
            <el-icon><FirstAidKit /></el-icon>
            <span>服务健康</span>
          </el-menu-item>
          
          <el-menu-item index="/api-ops/alerts">
            <el-icon><Bell /></el-icon>
            <span>告警规则</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-main class="api-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.api-ops-layout {
  height: 100vh;
}

.api-sidebar {
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border);
}

.sidebar-header {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--color-border);
}

.sidebar-header .title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-primary);
}

.api-menu {
  border-right: none;
}

.api-main {
  background: var(--color-bg);
  padding: 20px;
  overflow-y: auto;
}
</style>
```

---

## Phase 7: 毕设专项 — WRF模式运行驱动设计（服务器方案）

### Task 7.1: WRF 模式运行驱动架构设计

由于本地设备条件限制（WRF模式需要Linux环境、大量计算资源、WPS前处理链），建议采用**远程服务器方案**。

**推荐服务器配置：**

| 组件 | 最低配置 | 推荐配置 | 说明 |
|------|----------|----------|------|
| CPU | 16核 | 32核+ | WRF并行计算需要多核 |
| 内存 | 64GB | 128GB+ | 3km分辨率模拟需要大内存 |
| 存储 | 500GB SSD | 2TB NVMe | WRF输出文件体积大 |
| GPU | 可选 | NVIDIA A100 | 加速FengWu推理 |
| 网络 | 100Mbps | 1Gbps | 传输GRIB边界条件 |
| 系统 | CentOS 7/Ubuntu 20.04 | Ubuntu 22.04 | WRF官方支持 |

**部署方案选择：**

1. **校内高性能计算中心**（推荐）
   - 联系学校超算中心申请计算资源
   - 优势：免费/低成本、网络延迟低、数据安全
   - 适合：长期毕设使用

2. **云服务器（阿里云/腾讯云/华为云）**
   - 配置：32核128GB + 2TB SSD
   - 成本：约 2000-4000元/月
   - 优势：按需付费、弹性扩展
   - 适合：短期集中计算

3. **课题组服务器**
   - 如果导师有服务器资源可申请使用
   - 优势：免费、数据共享方便

---

### Task 7.2: WRF 模式运行驱动设计

**Files:**
- Create: `python/algorithm-engine/app/adapters/wrf_model_driver.py`（设计文档）

```python
"""
WRF 模式运行驱动设计文档
============================

由于本地设备限制，本模块为设计阶段代码，需在远程服务器上部署运行。

架构设计:
---------
1. 本地平台通过 SSH/API 提交任务到远程WRF服务器
2. WRF服务器执行: WPS前处理 → real.exe → wrf.exe → 后处理
3. 结果通过 SFTP/API 传回本地平台
4. 本地平台进行可视化分析和论文图表生成

四川盆地模拟域设置:
------------------
Domain 1 (d01): 粗网格
  - 分辨率: 9km
  - 范围: 27-35°N, 102-110°E
  - 格点数: ~400x400
  
Domain 2 (d02): 中网格
  - 分辨率: 3km
  - 范围: 29-33°N, 103-108°E
  - 格点数: ~500x500
  
Domain 3 (d03): 细网格（可选）
  - 分辨率: 1km
  - 范围: 30-32°N, 104-106.5°E
  - 格点数: ~600x600

物理参数化方案配置:
------------------
微物理方案: Thompson (mp_physics=8)
长波辐射: RRTMG (ra_lw_physics=4)
短波辐射: RRTMG (ra_sw_physics=4)
边界层方案: YSU (bl_pbl_physics=1) / MYJ (bl_pbl_physics=2) / MYNN (bl_pbl_physics=5)
积云方案: Kain-Fritsch (cu_physics=1) / BMJ (cu_physics=2) / GD (cu_physics=93)
近地面层: MM5 (sf_sfclay_physics=1) / MYJ (sf_sfclay_physics=2)
陆面过程: Noah (sf_surface_physics=2)

边界条件:
---------
- GFS 0.25° 预报场（每6小时更新）
- 或 ECMWF ERA5 再分析资料
- 实时运行需要自动下载GRIB数据

运行流程:
---------
1. 下载GFS/ECMWF边界条件GRIB文件
2. 运行WPS: geogrid → ungrib → metgrid
3. 运行WRF: real.exe → wrf.exe
4. 运行ndown.exe（嵌套域降尺度，可选）
5. 后处理: 提取低空飞行相关变量
6. 传输结果到本地平台

预计计算时间:
------------
- 24小时预报, 9km+3km双域: ~2-4小时（32核）
- 24小时预报, 9km+3km+1km三域: ~6-12小时（32核）
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PBLScheme(Enum):
    """边界层参数化方案"""
    YSU = 1          # Yonsei University
    MYJ = 2          # Mellor-Yamada-Janjić
    MYNN = 5         # Mellor-Yamada-Nakanishi-Niino
    ACM2 = 7         # Asymmetric Convective Model v2
    BOULAC = 8       # Bougeault-Lacarrère
    GBM = 11         # Grenier-Bretherton-McCaa
    MYNN_TKE = 12    # MYNN with TKE
    TEMF = 10        # Total Energy Mass Flux


class CumulusScheme(Enum):
    """积云参数化方案"""
    KAIN_FRITSCH = 1    # Kain-Fritsch
    BETTS_MILLER = 2    # Betts-Miller-Janjic
    GRELL_DEvenyi = 93  # Grell-Devenyi ensemble
    GRELL_FREITAS = 3   # Grell-Freitas
    SAS = 14            # Simplified Arakawa-Schubert
    NSAS = 16           # New SAS
    TIEDTKE = 6         # Tiedtke
    ZHANG_MCFARLANE = 7 # Zhang-McFarlane


@dataclass
class WRFConfig:
    """WRF配置"""
    # 模拟域
    max_dom: int = 2                    # 嵌套域数量
    dx_d01: int = 9000                  # d01分辨率(m)
    dx_d02: int = 3000                  # d02分辨率(m)
    e_we: list = None                   # 东西向格点数
    e_sn: list = None                   # 南北向格点数
    
    # 物理方案
    mp_physics: int = 8                 # 微物理方案
    ra_lw_physics: int = 4              # 长波辐射
    ra_sw_physics: int = 4              # 短波辐射
    bl_pbl_physics: int = 1             # 边界层方案
    cu_physics: int = 1                 # 积云方案
    sf_sfclay_physics: int = 1          # 近地面层
    sf_surface_physics: int = 2         # 陆面过程
    
    # 时间设置
    run_hours: int = 24                 # 预报时长
    time_step: int = 45                 # 时间步长(s)
    
    # 输入输出
    input_from_file: bool = True
    history_interval: int = 60          # 输出间隔(min)
    frames_per_outfile: int = 1
    
    # 边界条件
    boundary_data: str = "GFS"          # GFS/ECMWF/ERA5


class WRFModelDriver(ABC):
    """
    WRF模式运行驱动抽象基类
    
    子类实现:
    - LocalWRFDriver: 本地运行（需要Linux环境）
    - RemoteWRFDriver: 远程服务器运行（SSH+SFTP）
    - CloudWRFDriver: 云平台运行（阿里云/腾讯云API）
    """
    
    def __init__(self, config: WRFConfig):
        self.config = config
        
    @abstractmethod
    def prepare_environment(self) -> bool:
        """准备运行环境"""
        pass
        
    @abstractmethod
    def run_wps(self) -> bool:
        """运行WPS前处理"""
        pass
        
    @abstractmethod
    def run_real(self) -> bool:
        """运行real.exe生成初始场和边界条件"""
        pass
        
    @abstractmethod
    def run_wrf(self) -> bool:
        """运行wrf.exe进行模式积分"""
        pass
        
    @abstractmethod
    def extract_results(self, output_dir: str) -> Dict[str, Any]:
        """提取模拟结果"""
        pass
        
    def run_full_pipeline(self) -> Dict[str, Any]:
        """运行完整流程"""
        results = {
            'wps_success': self.run_wps(),
            'real_success': self.run_real(),
            'wrf_success': self.run_wrf(),
            'output': self.extract_results('/tmp/wrf_output')
        }
        return results


class RemoteWRFDriver(WRFModelDriver):
    """
    远程WRF服务器驱动
    
    通过SSH连接到远程服务器执行WRF模式
    """
    
    def __init__(self, config: WRFConfig, 
                 host: str, username: str, password: Optional[str] = None,
                 key_file: Optional[str] = None):
        super().__init__(config)
        self.host = host
        self.username = username
        self.password = password
        self.key_file = key_file
        self.ssh_client = None
        self.sftp_client = None
        
    def connect(self):
        """建立SSH连接"""
        import paramiko
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if self.key_file:
            self.ssh_client.connect(self.host, username=self.username, 
                                   key_filename=self.key_file)
        else:
            self.ssh_client.connect(self.host, username=self.username, 
                                   password=self.password)
        
        self.sftp_client = self.ssh_client.open_sftp()
        
    def upload_namelist(self, local_path: str, remote_path: str):
        """上传namelist文件"""
        self.sftp_client.put(local_path, remote_path)
        
    def download_results(self, remote_dir: str, local_dir: str):
        """下载模拟结果"""
        import os
        os.makedirs(local_dir, exist_ok=True)
        
        # 获取远程文件列表
        stdin, stdout, stderr = self.ssh_client.exec_command(f'ls {remote_dir}')
        files = stdout.read().decode().split('\n')
        
        for file in files:
            if file.endswith('.nc') or file.endswith('.txt'):
                remote_file = f"{remote_dir}/{file}"
                local_file = f"{local_dir}/{file}"
                self.sftp_client.get(remote_file, local_file)
                
    def run_command(self, command: str) -> tuple:
        """在远程服务器执行命令"""
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()
        
    def prepare_environment(self) -> bool:
        """准备远程环境"""
        # 检查WRF安装
        stdout, stderr = self.run_command('which wrf.exe')
        if not stdout.strip():
            print("WRF未安装，需要手动安装")
            return False
        return True
        
    def run_wps(self) -> bool:
        """运行WPS"""
        commands = [
            'cd /path/to/WPS',
            './geogrid.exe',
            './ungrib.exe',
            './metgrid.exe'
        ]
        for cmd in commands:
            stdout, stderr = self.run_command(cmd)
            if stderr:
                print(f"WPS错误: {stderr}")
                return False
        return True
        
    def run_real(self) -> bool:
        """运行real.exe"""
        stdout, stderr = self.run_command(
            'cd /path/to/WRF/run && mpirun -np 32 ./real.exe'
        )
        return 'SUCCESS' in stdout
        
    def run_wrf(self) -> bool:
        """运行wrf.exe"""
        stdout, stderr = self.run_command(
            'cd /path/to/WRF/run && mpirun -np 32 ./wrf.exe'
        )
        return 'SUCCESS' in stdout
        
    def extract_results(self, output_dir: str) -> Dict[str, Any]:
        """提取结果"""
        # 下载wrfout文件到本地
        local_dir = './wrf_output'
        self.download_results(output_dir, local_dir)
        
        return {
            'output_dir': local_dir,
            'files': os.listdir(local_dir)
        }
```

---

### Task 7.3: 盆地地形机理分析模块设计

**Files:**
- Create: `python/algorithm-engine/app/adapters/wrf_terrain_analyzer.py`（设计文档）

```python
"""
四川盆地地形机理分析模块设计文档
=================================

四川盆地地形特征:
----------------
- 四周环山: 秦岭(北)、大巴山(东北)、巫山(东)、大娄山(南)、横断山脉(西)
- 盆地底部: 成都平原、川中丘陵
- 地形高度差: 从盆地底部~500m到周边山脉~3000m
- 关键地形通道: 秦岭缺口、大巴山缺口、长江三峡

分析内容:
---------
1. 地形坡度与坡向分析
2. 地形粗糙度计算
3. 地形遮蔽效应
4. 山谷风环流识别
5. 地形降水增强效应
6. 背风波检测
"""

import numpy as np
from typing import Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class TerrainMetrics:
    """地形指标"""
    elevation: np.ndarray       # 高程 (m)
    slope: np.ndarray           # 坡度 (度)
    aspect: np.ndarray          # 坡向 (度)
    roughness: np.ndarray       # 粗糙度 (m)
    curvature: np.ndarray       # 曲率
    tpi: np.ndarray             # 地形位置指数
    

class SichuanBasinTerrainAnalyzer:
    """四川盆地地形分析器"""
    
    # 四川盆地范围
    BASIN_BOUNDS = {
        'lat_min': 27.0,
        'lat_max': 35.0,
        'lon_min': 102.0,
        'lon_max': 110.0
    }
    
    # 关键地形通道
    TERRAIN_CHANNELS = {
        'qinling_gap': {'lat': 33.5, 'lon': 106.5, 'width_km': 50},
        'daba_gap': {'lat': 31.5, 'lon': 108.0, 'width_km': 30},
        'three_gorges': {'lat': 30.8, 'lon': 109.5, 'width_km': 20}
    }
    
    def __init__(self, elevation_data: np.ndarray, 
                 lat_grid: np.ndarray, lon_grid: np.ndarray):
        self.elevation = elevation_data
        self.lat = lat_grid
        self.lon = lon_grid
        self.dx = self._calculate_grid_spacing()
        
    def _calculate_grid_spacing(self) -> float:
        """计算网格间距(m)"""
        # 假设等经纬度网格
        lat_mid = (self.lat.max() + self.lat.min()) / 2
        dx_deg = np.abs(self.lon[1] - self.lon[0])
        return dx_deg * 111320 * np.cos(np.radians(lat_mid))
        
    def calculate_slope(self) -> np.ndarray:
        """
        计算地形坡度
        
        使用中心差分:
        slope = arctan(sqrt(dz/dx^2 + dz/dy^2))
        """
        dz_dx, dz_dy = np.gradient(self.elevation, self.dx)
        slope = np.degrees(np.arctan(np.sqrt(dz_dx**2 + dz_dy**2)))
        return slope
        
    def calculate_aspect(self) -> np.ndarray:
        """
        计算坡向
        
        aspect = 180/π * arctan2(dz/dy, -dz/dx)
        """
        dz_dx, dz_dy = np.gradient(self.elevation, self.dx)
        aspect = np.degrees(np.arctan2(dz_dy, -dz_dx))
        aspect = np.where(aspect < 0, aspect + 360, aspect)
        return aspect
        
    def calculate_roughness(self, window_size: int = 5) -> np.ndarray:
        """
        计算地形粗糙度
        
        使用移动窗口内高程标准差
        """
        from scipy.ndimage import uniform_filter
        
        mean_elev = uniform_filter(self.elevation, window_size)
        mean_elev_sq = uniform_filter(self.elevation**2, window_size)
        roughness = np.sqrt(mean_elev_sq - mean_elev**2)
        return roughness
        
    def calculate_tpi(self, window_size: int = 10) -> np.ndarray:
        """
        计算地形位置指数 (Topographic Position Index)
        
        TPI = elevation - mean(elevation in neighborhood)
        
        TPI > 0: 山脊/高地
        TPI < 0: 山谷/低地
        TPI ≈ 0: 斜坡
        """
        from scipy.ndimage import uniform_filter
        
        mean_elev = uniform_filter(self.elevation, window_size)
        tpi = self.elevation - mean_elev
        return tpi
        
    def identify_valley_wind_system(self, 
                                    u_wind: np.ndarray,
                                    v_wind: np.ndarray,
                                    time: str) -> Dict[str, Any]:
        """
        识别山谷风环流
        
        四川盆地典型山谷风:
        - 白天: 谷风 (风从盆地吹向山脉)
        - 夜间: 山风 (风从山脉吹向盆地)
        
        判断依据:
        1. 风向与坡向的关系
        2. 风速的日变化特征
        3. 温度梯度
        """
        slope = self.calculate_slope()
        aspect = self.calculate_aspect()
        
        # 计算风向
        wind_dir = np.degrees(np.arctan2(v_wind, u_wind))
        wind_speed = np.sqrt(u_wind**2 + v_wind**2)
        
        # 判断山谷风类型
        # 如果风向与坡向相反（白天，风上坡）→ 谷风
        # 如果风向与坡向相同（夜间，风下坡）→ 山风
        
        wind_aspect_diff = np.abs(wind_dir - aspect)
        wind_aspect_diff = np.where(wind_aspect_diff > 180, 
                                    360 - wind_aspect_diff, 
                                    wind_aspect_diff)
        
        # 谷风: 风向与坡向差 > 90度 (风从低处吹向高处)
        valley_wind_mask = wind_aspect_diff > 90
        
        # 山风: 风向与坡向差 < 90度 (风从高处吹向低处)
        mountain_wind_mask = wind_aspect_diff <= 90
        
        return {
            'valley_wind_coverage': float(np.mean(valley_wind_mask)),
            'mountain_wind_coverage': float(np.mean(mountain_wind_mask)),
            'mean_valley_wind_speed': float(np.mean(wind_speed[valley_wind_mask])),
            'mean_mountain_wind_speed': float(np.mean(wind_speed[mountain_wind_mask])),
            'wind_direction_analysis': wind_dir.tolist()
        }
        
    def analyze_terrain_channel_effect(self,
                                       wind_u: np.ndarray,
                                       wind_v: np.ndarray) -> Dict[str, Any]:
        """
        分析地形通道效应
        
        四川盆地关键地形通道对气流的影响:
        1. 秦岭缺口: 北方冷空气南下通道
        2. 大巴山缺口: 东北气流进入
        3. 长江三峡: 东西向气流通道
        """
        results = {}
        
        for channel_name, channel_info in self.TERRAIN_CHANNELS.items():
            lat_idx = np.argmin(np.abs(self.lat - channel_info['lat']))
            lon_idx = np.argmin(np.abs(self.lon - channel_info['lon']))
            
            # 提取通道区域风场
            half_width = int(channel_info['width_km'] / 2 / (self.dx / 1000))
            
            u_channel = wind_u[max(0, lat_idx-half_width):lat_idx+half_width,
                              max(0, lon_idx-half_width):lon_idx+half_width]
            v_channel = wind_v[max(0, lat_idx-half_width):lat_idx+half_width,
                              max(0, lon_idx-half_width):lon_idx+half_width]
            
            # 计算通道内平均风速和风向
            mean_u = float(np.mean(u_channel))
            mean_v = float(np.mean(v_channel))
            mean_speed = float(np.sqrt(mean_u**2 + mean_v**2))
            mean_dir = float(np.degrees(np.arctan2(mean_v, mean_u)))
            
            results[channel_name] = {
                'mean_wind_speed': mean_speed,
                'mean_wind_direction': mean_dir,
                'mean_u': mean_u,
                'mean_v': mean_v,
                'location': channel_info
            }
            
        return results
        
    def detect_lee_waves(self, 
                         vertical_velocity: np.ndarray,
                         potential_temperature: np.ndarray) -> Dict[str, Any]:
        """
        检测背风波
        
        背风波特征:
        1. 山地背风侧垂直速度的周期性振荡
        2. 位温面的波动
        3. 波长与地形尺度相关
        """
        # 沿风向的垂直速度剖面
        w_along_flow = np.mean(vertical_velocity, axis=1)
        
        # 检测周期性振荡（简化：寻找零点穿越）
        zero_crossings = np.where(np.diff(np.sign(w_along_flow)))[0]
        
        if len(zero_crossings) > 2:
            # 估算波长
            wavelengths = np.diff(zero_crossings) * self.dx
            mean_wavelength = float(np.mean(wavelengths))
            
            return {
                'lee_waves_detected': True,
                'zero_crossings': len(zero_crossings),
                'mean_wavelength_m': mean_wavelength,
                'wavelength_range_m': [float(np.min(wavelengths)), 
                                       float(np.max(wavelengths))]
            }
        else:
            return {
                'lee_waves_detected': False,
                'zero_crossings': len(zero_crossings)
            }
            
    def calculate_terrain_drag(self,
                               wind_u: np.ndarray,
                               wind_v: np.ndarray,
                               pbl_height: np.ndarray) -> Dict[str, Any]:
        """
        计算地形拖曳效应
        
        地形拖曳公式:
        τ = ρ * Cd * |V| * V
        
        其中Cd为拖曳系数，与地形粗糙度和坡度相关
        """
        slope = self.calculate_slope()
        roughness = self.calculate_roughness()
        
        # 简化拖曳系数
        cd = 0.001 + 0.01 * (slope / 45) + 0.005 * (roughness / 100)
        
        wind_speed = np.sqrt(wind_u**2 + wind_v**2)
        
        # 拖曳力
        rho = 1.225  # 空气密度 kg/m³
        drag_u = rho * cd * wind_speed * wind_u
        drag_v = rho * cd * wind_speed * wind_v
        
        return {
            'drag_coefficient': cd.tolist(),
            'drag_u': drag_u.tolist(),
            'drag_v': drag_v.tolist(),
            'mean_drag_magnitude': float(np.mean(np.sqrt(drag_u**2 + drag_v**2)))
        }
        
    def generate_terrain_report(self) -> Dict[str, Any]:
        """生成完整的地形分析报告"""
        slope = self.calculate_slope()
        aspect = self.calculate_aspect()
        roughness = self.calculate_roughness()
        tpi = self.calculate_tpi()
        
        return {
            'basin_info': self.BASIN_BOUNDS,
            'elevation_stats': {
                'min': float(np.min(self.elevation)),
                'max': float(np.max(self.elevation)),
                'mean': float(np.mean(self.elevation)),
                'std': float(np.std(self.elevation))
            },
            'slope_stats': {
                'min': float(np.min(slope)),
                'max': float(np.max(slope)),
                'mean': float(np.mean(slope))
            },
            'roughness_stats': {
                'min': float(np.min(roughness)),
                'max': float(np.max(roughness)),
                'mean': float(np.mean(roughness))
            },
            'terrain_classification': {
                'ridge_percentage': float(np.mean(tpi > 50)),
                'valley_percentage': float(np.mean(tpi < -50)),
                'slope_percentage': float(np.mean((tpi >= -50) & (tpi <= 50)))
            }
        }
```

---

## Phase 8: 毕设专项 — 前端 WRF 分析可视化

### Task 8.1: WRF 地形分析可视化组件

**Files:**
- Create: `console/src/components/research/WRFTerrainAnalysis.vue`

```vue
<template>
  <div class="wrf-terrain-analysis">
    <h3>四川盆地地形机理分析</h3>
    
    <el-alert type="info" :closable="false" show-icon>
      <template #title>
        本功能需要远程WRF服务器支持。当前为设计预览模式，使用示例数据展示。
      </template>
    </el-alert>
    
    <!-- 地形概览 -->
    <el-row :gutter="16" class="terrain-overview">
      <el-col :span="6">
        <el-statistic title="盆地高程范围" :value="terrainStats.elevationRange" suffix="m" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="平均坡度" :value="terrainStats.meanSlope" suffix="°" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="地形粗糙度" :value="terrainStats.meanRoughness" suffix="m" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="山脊/山谷比例" :value="terrainStats.ridgeValleyRatio" />
      </el-col>
    </el-row>
    
    <!-- 地形分类图 -->
    <el-card class="terrain-map-card">
      <template #header>
        <span>地形分类图</span>
        <el-tag size="small" type="warning">示例数据</el-tag>
      </template>
      <div ref="terrainMapRef" class="terrain-map"></div>
    </el-card>
    
    <!-- 山谷风分析 -->
    <el-card class="valley-wind-card">
      <template #header>
        <span>山谷风环流分析</span>
      </template>
      <el-form :model="valleyWindParams" label-width="120px" size="small">
        <el-form-item label="分析时间">
          <el-time-picker v-model="valleyWindParams.time" format="HH:mm" />
        </el-form-item>
        <el-form-item label="风速阈值">
          <el-slider v-model="valleyWindParams.threshold" :min="0" :max="10" :step="0.5" />
        </el-form-item>
      </el-form>
      <div ref="valleyWindRef" class="valley-wind-map"></div>
    </el-card>
    
    <!-- 地形通道效应 -->
    <el-card class="channel-effect-card">
      <template #header>
        <span>地形通道效应</span>
      </template>
      <el-table :data="channelEffects" style="width: 100%">
        <el-table-column prop="name" label="通道名称" width="150" />
        <el-table-column prop="location" label="位置" width="200" />
        <el-table-column prop="meanWindSpeed" label="平均风速(m/s)" width="120" />
        <el-table-column prop="windDirection" label="风向(°)" width="100" />
        <el-table-column prop="effect" label="效应类型">
          <template #default="{ row }">
            <el-tag :type="row.effect === '加速' ? 'danger' : 'success'">
              {{ row.effect }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- PBL方案对比 -->
    <el-card class="pbl-comparison-card">
      <template #header>
        <span>边界层参数化方案对比</span>
      </template>
      <PBLSchemeSelector />
    </el-card>
    
    <!-- 远程服务器配置 -->
    <el-card class="server-config-card">
      <template #header>
        <span>远程WRF服务器配置</span>
      </template>
      <el-form :model="serverConfig" label-width="120px">
        <el-form-item label="服务器地址">
          <el-input v-model="serverConfig.host" placeholder="192.168.1.100" />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="serverConfig.username" />
        </el-form-item>
        <el-form-item label="认证方式">
          <el-radio-group v-model="serverConfig.authType">
            <el-radio label="password">密码</el-radio>
            <el-radio label="key">密钥</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="WRF路径">
          <el-input v-model="serverConfig.wrfPath" placeholder="/home/user/WRF" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="testConnection">测试连接</el-button>
          <el-button @click="saveConfig">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import PBLSchemeSelector from './PBLSchemeSelector.vue'

const terrainMapRef = ref<HTMLDivElement>()
const valleyWindRef = ref<HTMLDivElement>()

const terrainStats = ref({
  elevationRange: 2500,
  meanSlope: 12.5,
  meanRoughness: 85.3,
  ridgeValleyRatio: 0.35
})

const valleyWindParams = ref({
  time: new Date(2024, 0, 1, 14, 0),
  threshold: 2.0
})

const channelEffects = ref([
  { name: '秦岭缺口', location: '33.5°N, 106.5°E', meanWindSpeed: 8.5, windDirection: 180, effect: '加速' },
  { name: '大巴山缺口', location: '31.5°N, 108.0°E', meanWindSpeed: 6.2, windDirection: 225, effect: '偏转' },
  { name: '长江三峡', location: '30.8°N, 109.5°E', meanWindSpeed: 5.8, windDirection: 90, effect: '通道' }
])

const serverConfig = ref({
  host: '',
  username: '',
  authType: 'password',
  wrfPath: '/home/user/WRF'
})

function initTerrainMap() {
  if (!terrainMapRef.value) return
  
  const chart = echarts.init(terrainMapRef.value)
  
  // 示例地形数据（四川盆地简化）
  const data = []
  for (let lat = 27; lat <= 35; lat += 0.1) {
    for (let lon = 102; lon <= 110; lon += 0.1) {
      // 简化地形：盆地中心低，四周高
      const centerLat = 31.0
      const centerLon = 106.0
      const dist = Math.sqrt((lat - centerLat)**2 + (lon - centerLon)**2)
      const elevation = 500 + 2000 * Math.min(dist / 3, 1)
      data.push([lon, lat, elevation])
    }
  }
  
  chart.setOption({
    title: { text: '四川盆地地形高程', left: 'center' },
    tooltip: { trigger: 'item', formatter: (p: any) => `高程: ${p.data[2].toFixed(0)}m` },
    visualMap: {
      min: 0,
      max: 3000,
      calculable: true,
      inRange: { color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#fee090', '#fdae61', '#f46d43', '#d73027'] }
    },
    xAxis: { type: 'value', name: '经度', min: 102, max: 110 },
    yAxis: { type: 'value', name: '纬度', min: 27, max: 35 },
    series: [{
      type: 'heatmap',
      data: data,
      emphasis: { itemStyle: { borderColor: '#333', borderWidth: 1 } }
    }]
  })
}

function initValleyWindMap() {
  if (!valleyWindRef.value) return
  
  const chart = echarts.init(valleyWindRef.value)
  
  // 示例山谷风数据
  const data = []
  for (let lat = 27; lat <= 35; lat += 0.2) {
    for (let lon = 102; lon <= 110; lon += 0.2) {
      const centerLat = 31.0
      const centerLon = 106.0
      const dist = Math.sqrt((lat - centerLat)**2 + (lon - centerLon)**2)
      
      // 白天谷风：从盆地中心向外
      const u = -(lon - centerLon) * 2
      const v = -(lat - centerLat) * 2
      
      data.push([lon, lat, u, v])
    }
  }
  
  chart.setOption({
    title: { text: '山谷风环流（示例：白天谷风）', left: 'center' },
    tooltip: { trigger: 'item' },
    xAxis: { type: 'value', name: '经度', min: 102, max: 110 },
    yAxis: { type: 'value', name: '纬度', min: 27, max: 35 },
    series: [{
      type: 'scatter',
      data: data.map(d => [d[0], d[1]]),
      symbolSize: 3,
      itemStyle: { color: '#5470c6' }
    }]
  })
}

function testConnection() {
  ElMessage.info('正在测试远程WRF服务器连接...')
  // 实际实现需要调用后端API
}

function saveConfig() {
  ElMessage.success('配置已保存')
  // 实际实现需要调用后端API
}

onMounted(() => {
  initTerrainMap()
  initValleyWindMap()
})
</script>

<style scoped>
.wrf-terrain-analysis {
  padding: 20px;
}

.terrain-overview {
  margin: 20px 0;
}

.terrain-map-card,
.valley-wind-card,
.channel-effect-card,
.pbl-comparison-card,
.server-config-card {
  margin-top: 20px;
}

.terrain-map,
.valley-wind-map {
  width: 100%;
  height: 400px;
}
</style>
```

---

### Task 8.2: PBL 方案选择器组件

**Files:**
- Create: `console/src/components/research/PBLSchemeSelector.vue`

```vue
<template>
  <div class="pbl-scheme-selector">
    <el-row :gutter="16">
      <el-col :span="12">
        <h4>边界层参数化方案</h4>
        <el-checkbox-group v-model="selectedPBL">
          <el-checkbox label="YSU">YSU (Yonsei University)</el-checkbox>
          <el-checkbox label="MYJ">MYJ (Mellor-Yamada-Janjić)</el-checkbox>
          <el-checkbox label="MYNN">MYNN (Nakanishi-Niino)</el-checkbox>
          <el-checkbox label="ACM2">ACM2 (Asymmetric Convective)</el-checkbox>
          <el-checkbox label="BOULAC">BOULAC (Bougeault-Lacarrère)</el-checkbox>
        </el-checkbox-group>
      </el-col>
      
      <el-col :span="12">
        <h4>积云参数化方案</h4>
        <el-checkbox-group v-model="selectedCU">
          <el-checkbox label="KF">Kain-Fritsch</el-checkbox>
          <el-checkbox label="BMJ">Betts-Miller-Janjic</el-checkbox>
          <el-checkbox label="GD">Grell-Devenyi</el-checkbox>
          <el-checkbox label="GF">Grell-Freitas</el-checkbox>
        </el-checkbox-group>
      </el-col>
    </el-row>
    
    <el-divider />
    
    <!-- 方案组合对比 -->
    <el-table :data="schemeCombinations" style="width: 100%">
      <el-table-column prop="pbl" label="PBL方案" width="120" />
      <el-table-column prop="cu" label="积云方案" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === '已完成' ? 'success' : 'info'">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="rmse" label="RMSE" width="100" />
      <el-table-column prop="bias" label="Bias" width="100" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="runScheme(row)">
            运行
          </el-button>
          <el-button size="small" @click="viewResults(row)">
            查看
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-divider />
    
    <!-- 方案说明 -->
    <el-collapse>
      <el-collapse-item title="YSU方案说明" name="1">
        <p>Yonsei University方案，非局地K方案，适用于对流边界层。</p>
        <p>特点：计算效率高，对强对流边界层模拟较好。</p>
      </el-collapse-item>
      <el-collapse-item title="MYJ方案说明" name="2">
        <p>Mellor-Yamada-Janjić方案，TKE闭合方案，适用于稳定边界层。</p>
        <p>特点：对稳定边界层和夜间边界层模拟较好。</p>
      </el-collapse-item>
      <el-collapse-item title="MYNN方案说明" name="3">
        <p>Mellor-Yamada-Nakanishi-Niino方案，改进的TKE方案。</p>
        <p>特点：综合考虑了多种边界层过程，适用范围广。</p>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const selectedPBL = ref(['YSU', 'MYNN'])
const selectedCU = ref(['KF'])

const schemeCombinations = computed(() => {
  const combinations = []
  for (const pbl of selectedPBL.value) {
    for (const cu of selectedCU.value) {
      combinations.push({
        pbl,
        cu,
        status: '待运行',
        rmse: '-',
        bias: '-'
      })
    }
  }
  return combinations
})

function runScheme(row: any) {
  ElMessage.info(`正在运行 ${row.pbl} + ${row.cu} 方案组合...`)
  // 实际实现需要调用后端API提交WRF任务
}

function viewResults(row: any) {
  ElMessage.info(`查看 ${row.pbl} + ${row.cu} 结果`)
  // 实际实现需要跳转到结果页面
}
</script>

<style scoped>
.pbl-scheme-selector {
  padding: 16px;
}

.el-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
```

---

## 附录

### A. 实施时间表

| 阶段 | 任务 | 优先级 | 预计时间 | 依赖 |
|------|------|--------|----------|------|
| Phase 1 | 安全漏洞修复 | P0 | 1天 | 无 |
| Phase 2 | 风乌数据源对接 | P0 | 1-2天 | Phase 1 |
| Phase 3 | 科研可复现性 | P0.5 | 2-3天 | Phase 2 |
| Phase 4 | 算法真实数据验证 | P0 | 3-5天 | Phase 2 |
| Phase 5 | 环境切换/UTM | P1 | 2天 | Phase 1 |
| Phase 6 | 前端功能分离 | P1 | 2-3天 | Phase 5 |
| Phase 7 | WRF驱动设计 | 毕设专项 | 设计阶段 | 无 |
| Phase 8 | WRF前端可视化 | 毕设专项 | 设计阶段 | Phase 7 |

### B. 服务器推荐配置

**WRF远程服务器（四川盆地模拟）**

| 用途 | CPU | 内存 | 存储 | 预估成本 |
|------|-----|------|------|----------|
| 校内超算 | 32核 | 128GB | 1TB | 免费/低费用 |
| 阿里云ECS | 32核 | 128GB | 2TB SSD | ~3000元/月 |
| 腾讯云CVM | 32核 | 128GB | 2TB SSD | ~2800元/月 |

### C. 关键联系人

- 风乌模型：上海AI Lab
- 风雷模型：中国气象局
- UTM对接：民航局空管局
- WRF技术支持：NCAR/MMM

### D. 论文数据需求

**硕士论文（四川盆地地形机理）**
- WRF模拟数据：至少3组PBL方案对比实验
- 观测验证数据：成都、重庆探空站数据
- 地形分析：SRTM 90m高程数据

**5D-VAR期刊论文**
- FengWu同化实验数据
- 对比实验：3D-VAR/4D-VAR/EnKF
- 验证数据：ERA5再分析资料

---

> **注意：** 本计划为动态文档，实施过程中可根据实际情况调整优先级和时间安排。WRF相关功能因设备限制采用"设计先行、服务器部署后实施"策略。
