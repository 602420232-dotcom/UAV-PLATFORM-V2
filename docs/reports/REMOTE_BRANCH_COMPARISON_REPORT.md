# 远程与本地代码差异对比报告

> **生成日期**: 2026-06-08  
> **对比策略**: 仅对比差异，不执行合并、不修改/覆盖/删除本地任何源码
> **基准分支**: `origin/main`

---

## 一、仓库信息

| 项目 | 值 |
|------|----|
| 远程仓库 | `git@github.com:602420232-dotcom/weather.git` |
| 本地当前分支 | `main` |
| 本地 HEAD | `8fa0a1c` |
| 远程分支 | `origin/main`, `origin/chenlingqian`, `origin/master`, `origin/fix/deploy-bugs` |

---

## 二、本地与远程 main 分支同步状态

**结论：本地 `main` 领先于 `origin/main` 共 4 个提交。**

```
8fa0a1c (HEAD -> main) fix: 修复测试配置文件中的未知属性问题
40949ed fix: 修复UAV配置属性问题
5268ad7 fix: 修复application.yml中文乱码问题
47fc8a4 fix: 统一JWT配置前缀为uav.jwt
60344a9 (origin/main, origin/HEAD) fix: 修复 CI/CD 构建缺少环境变量的问题
```

### 本地领先提交详情

| 提交 | 描述 |
|------|------|
| `8fa0a1c` | 修复测试配置文件中的未知属性问题 |
| `40949ed` | 修复UAV配置属性问题 |
| `5268ad7` | 修复application.yml中文乱码问题 |
| `47fc8a4` | 统一JWT配置前缀为uav.jwt |

---

## 三、本地与远程 main 差异文件清单

本地有以下文件与 `origin/main` 存在差异：

| 文件路径 | 修改类型 | 说明 |
|----------|----------|------|
| `api-gateway/src/main/resources/application.yml` | 修改 | API网关配置 |
| `common-utils/src/main/java/com/uav/common/security/JwtProperties.java` | 修改 | JWT属性配置类 |
| `path-planning-service/src/main/resources/application.yml` | 修改 | 路径规划服务配置 |
| `uav-path-planning-system/backend-spring/src/main/java/com/uav/config/JwtKeyRotationService.java` | 修改 | JWT密钥轮换服务 |
| `uav-path-planning-system/backend-spring/src/main/java/com/uav/config/JwtUtil.java` | 修改 | JWT工具类 |
| `uav-path-planning-system/backend-spring/src/main/java/com/uav/config/UavProperties.java` | 修改 | UAV属性配置 |
| `uav-path-planning-system/backend-spring/src/main/java/com/uav/config/UtmProperties.java` | 修改 | UTM属性配置 |
| `uav-path-planning-system/backend-spring/src/main/resources/application.yml` | 修改 | 后端主配置文件 |
| `uav-path-planning-system/backend-spring/src/test/resources/application-test.yml` | 修改 | 测试配置文件 |
| `uav-path-planning-system/backend-spring/src/test/resources/application.yml` | 修改 | 测试资源配置 |
| `uav-platform-service/src/main/resources/application.yml` | 修改 | 平台服务配置 |
| `uav-weather-collector/src/main/resources/application.yml` | 修改 | 气象采集服务配置 |
| `wrf-processor-service/src/main/resources/application.yml` | 修改 | WRF处理器服务配置 |

### 差异分析总结

**核心改动方向：**
1. **JWT 配置统一**：将所有 JWT 相关配置前缀统一为 `uav.jwt`，解决之前配置键不一致的问题
2. **配置属性修复**：修复 UAV 和 UTM 配置属性问题
3. **编码问题修复**：修复 application.yml 文件中文乱码问题
4. **测试配置优化**：修复测试配置文件中的未知属性问题

---

## 四、新增远程分支

### 4.1 origin/fix/deploy-bugs

| 属性 | 值 |
|------|----|
| 提交 | `632edb0` |
| 描述 | `fix: disable PathPlanningIntegrationTest due to CommonSecurityConfig permission changes` |
| 上游 | `origin/main` |

**评估**：这是一个修复部署问题的临时分支，禁用了路径规划集成测试以解决安全配置变更导致的测试失败。

---

## 五、其他远程分支对比

### 5.1 origin/main vs origin/chenlingqian

| 属性 | 值 |
|------|----|
| 提交 | `79f1fac` |
| 描述 | `fix: docker-compose.dev.yml 环境变量名对齐到项目统一规范` |
| 与 main 差异 | 中等 |

**评估**：该分支包含 docker-compose.dev.yml 环境变量名规范对齐的改动，与当前本地修改方向一致。

### 5.2 origin/main vs origin/master

| 属性 | 值 |
|------|----|
| 提交 | `a283bf8` |
| 描述 | `init one` |
| 与 main 差异 | 大量 |

**评估**：`master` 分支是早期初始化版本，与当前 `main` 分支差异显著，建议确认是否仍在使用。

---

## 六、结论与建议

### 6.1 当前状态总结

| 分支 | 状态 | 与本地 main 关系 |
|------|------|-----------------|
| `origin/main` | 落后 | 本地领先 4 个提交 |
| `origin/fix/deploy-bugs` | 新增 | 基于 main 的修复分支 |
| `origin/chenlingqian` | 活跃 | 包含环境变量规范改动 |
| `origin/master` | 陈旧 | 早期版本，差异显著 |

### 6.2 操作建议

1. **本地变更推送**：建议将本地 4 个提交推送到 `origin/main`
   ```bash
   git push origin main
   ```

2. **分支清理**：`master` 分支与 `main` 差异过大，建议确认是否废弃

3. **新分支关注**：关注 `fix/deploy-bugs` 分支的修复内容，评估是否需要合并到本地

4. **代码审查**：在推送前建议对本地改动进行代码审查，特别是 JWT 配置相关的安全性变更

---

## 七、本地修改详情

### 7.1 JWT 配置统一（关键变更）

**问题背景**：之前发现 `JwtAuthenticationFilter` 使用 `uav.jwt.secret`，而 `JwtUtil` 使用 `jwt.secret`，配置键不一致。

**修复方案**：统一配置前缀为 `uav.jwt`

**影响文件**：
- `common-utils/src/main/java/com/uav/common/security/JwtProperties.java` - 属性类更新
- `uav-path-planning-system/backend-spring/src/main/java/com/uav/config/JwtUtil.java` - 工具类更新
- 各服务 `application.yml` - 配置文件更新

### 7.2 配置文件编码修复

**问题背景**：部分 application.yml 文件存在中文乱码问题

**修复方案**：统一使用 UTF-8 编码并重新保存

**影响文件**：多个服务的 application.yml

---

*此报告仅记录差异，不包含任何代码修改。*