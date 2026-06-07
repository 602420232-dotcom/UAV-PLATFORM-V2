# 部署与维护方案

## 系统架构

本系统采用微服务架构，由以下核心服务组成：

### 应用服务

1. **API 网关** (`api-gateway`，端口8088)
2. **WRF气象数据处理服务** (`wrf-processor-service`，端口8081)
3. **贝叶斯同化服务** (`data-assimilation-service`，端口8084)
4. **气象预测与订正服务** (`meteor-forecast-service`，端口8082)
5. **路径规划服务** (`path-planning-service`，端口8083)
6. **主平台服务** (`uav-platform-service`，端口8080)
7. **气象收集服务** (`uav-weather-collector`，端口8086)
8. **FengWu 气象大模型** (`fengwu-service`，端口8085)
9. **边云协同框架** (`edge-cloud-coordinator`，端口8000/8765)
10. **前端应用** (`uav-path-planning-system/frontend-vue`，端口3000)

### 基础设施服务

11. **MySQL 数据库** (端口3306)
12. **Redis 缓存** (端口6379)
13. **Nacos 注册中心** (端口8848)
14. **Kafka 消息队列** (端口9092)
15. **Zookeeper 协调服务** (端口2181)

## 部署方式

### 1. Docker Compose部署（开发环境）

#### 前提条件
- Docker Engine 19.03+ 
- Docker Compose 1.25+
- 至少4GB RAM
- 至少50GB磁盘空间

#### 部署步骤

1. **克隆项目**
   ```bash
   git clone <项目地址>
   cd trae
   ```

2. **配置环境变量**
   - 复制 `.env.example` 文件为 `.env`
   - 根据实际情况修改环境变量，如数据库密码、服务端口等

3. **构建并启动服务**
   ```bash
   docker-compose up -d --build
   ```

4. **验证部署**
   - 服务状态：`docker-compose ps`
   - API 网关：http://localhost:8088/actuator/health
   - 主平台服务：http://localhost:8080/actuator/health
   - WRF处理服务：http://localhost:8081/actuator/health
   - 贝叶斯同化服务：http://localhost:8084/actuator/health
   - 气象预测服务：http://localhost:8082/actuator/health
   - 路径规划服务：http://localhost:8083/actuator/health
   - 气象收集服务：http://localhost:8086/actuator/health
   - FengWu 服务：http://localhost:8085/api/fengwu/health
   - Nacos 控制台：http://localhost:8848/nacos
   - Kafka 状态：`docker exec uav-kafka kafka-topics --bootstrap-server localhost:9092 --list`
   - Zookeeper 状态：`docker exec uav-zookeeper bash -c "echo ruok | nc localhost 2181"`

5. **查看日志**
   ```bash
   docker-compose logs -f
   ```

6. **停止服务**
   ```bash
   docker-compose down
   ```

### 2. Kubernetes部署（生产环境）

#### 前提条件
- Kubernetes 1.19+ 集群
- Helm 3.0+（可选）
- Nginx Ingress Controller
- Prometheus 和 Grafana（用于监控）

#### 部署步骤

1. **准备Kubernetes集群**
   - 确保Kubernetes集群已就绪
   - 安装Nginx Ingress Controller：
     ```bash
     kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.1.2/deploy/static/provider/cloud/deploy.yaml
     ```
   - 安装Prometheus和Grafana：
     ```bash
     helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
     helm install prometheus prometheus-community/kube-prometheus-stack
     ```

2. **配置Kubernetes Secrets**
   - 编辑 `deployments/kubernetes/secrets.yaml` 文件
   - 填充敏感信息，如数据库密码、JWT密钥等

3. **部署服务**
   ```bash
   cd deployments/kubernetes
   kubectl apply -f namespace.yml
   kubectl apply -f secrets.yaml
   kubectl apply -f persistent-volumes.yml
   kubectl apply -f database-services.yml
   kubectl apply -f uav-kafka.yml
   kubectl apply -f api-gateway.yml
   kubectl apply -f wrf-processor-service.yml
   kubectl apply -f meteor-forecast-service.yml
   kubectl apply -f path-planning-service.yml
   kubectl apply -f data-assimilation-service.yml
   kubectl apply -f uav-platform-service.yml
   kubectl apply -f uav-weather-collector.yml
   kubectl apply -f fengwu-service.yml
   kubectl apply -f frontend-vue.yml
   kubectl apply -f monitoring.yml
   kubectl apply -f nginx-ingress.yml
   kubectl apply -f autoscaling.yml
   ```

4. **验证部署**
   - 前端应用：http://uav-platform.local
   - API接口：http://uav-platform.local/api
   - 监控面板：http://uav-platform.local/grafana

5. **配置域名和SSL**
   - 在DNS服务器中添加域名解析
   - 配置HTTPS证书：
     ```bash
     kubectl apply -f tls-secret.yml
     ```

### 3. 本地开发部署

#### 前提条件
- Java 17+
- Python 3.8+
- MySQL 8.0+
- Redis 6.2+
- Maven 3.6+
- Node.js 16+

#### 部署步骤

1. **启动数据库和缓存**
   ```bash
   docker-compose up -d mysql redis
   ```

2. **安装依赖**
   - 后端服务：`mvn install`（在各服务目录下执行）
   - 前端服务：`npm install`（在 `uav-path-planning-system/frontend-vue` 目录下执行）
   - Python依赖：`pip install -r requirements.txt`（在相关服务目录下执行）

3. **启动各个服务**
   - WRF处理服务：`cd wrf-processor-service && mvn spring-boot:run`
   - 贝叶斯同化服务：`cd data-assimilation-service && mvn spring-boot:run`
   - 气象预测服务：`cd meteor-forecast-service && mvn spring-boot:run`
   - 路径规划服务：`cd path-planning-service && mvn spring-boot:run`
   - 主平台服务：`cd uav-platform-service && mvn spring-boot:run`
   - 前端开发：`cd uav-path-planning-system/frontend-vue && npm run dev`

## 服务集成说明

### 1. 贝叶斯同化服务集成

我们使用 `data-assimilation-service` 作为贝叶斯同化服务（底层算法库为 `data-assimilation-platform/algorithm_core`），它具有以下优势：

- **功能丰富**：支持3D-VAR、4D-VAR、EnKF和混合方法
- **性能优化**：支持GPU加速和并行计算
- **完善的API**：提供REST和gRPC接口
- **健壮的架构**：包含熔断、监控等生产级特性

#### 集成方式

1. **服务配置**：在 `docker-compose.yml` 中配置 `data-assimilation` 服务，指向 `data-assimilation-service` 目录。

2. **API调用**：主平台服务通过以下API调用贝叶斯同化服务：
   - 执行同化：`POST http://data-assimilation:8084/api/assimilation/execute`
   - 获取方差场：`POST http://data-assimilation:8084/api/assimilation/variance`
   - 批量处理：`POST http://data-assimilation:8084/api/assimilation/batch`

3. **数据格式**：使用共享的ProtoBuf和JSON Schema定义数据格式，确保服务间通信的一致性

### 2. 服务间通信

所有服务通过Docker网络进行通信，使用服务名称作为主机名：

- WRF处理服务：`wrf-processor:8081`
- 贝叶斯同化服务：`data-assimilation:8084`
- 气象预测服务：`meteor-forecast:8082`
- 路径规划服务：`path-planning:8083`
- 主平台服务：`uav-platform:8080`
- 气象收集服务：`uav-weather-collector:8086`
- 边云协调器：`edge-cloud-coordinator:8000`
- FengWu 模型服务：`fengwu-service:8085`
- Kafka 消息队列：`kafka:9092`
- Zookeeper 协调服务：`zookeeper:2181`
- Nacos 注册中心：`nacos:8848`
- 数据库服务：`mysql:3306`
- 缓存服务：`redis:6379`

## 运行与维护

### 日常运行

1. **服务状态监控**
   - 使用Prometheus和Grafana监控服务健康状态
   - 查看服务日志：`docker-compose logs <service-name>`
   - 检查服务状态：`kubectl get pods`（Kubernetes环境）

2. **数据管理**
   - 定期备份数据库：`docker exec -it <mysql-container> mysqldump -u root -p uav_path_planning > backup.sql`
   - 清理过期数据：设置定时任务清理过期的气象数据和路径规划结果
   - 数据验证：定期验证数据一致性和完整性

3. **性能优化**
   - 监控系统资源使用情况
   - 调整服务资源分配：`docker-compose up -d --scale path-planning-service=3`
   - 优化算法参数：根据实际运行情况调整算法参数

### 维护与故障处理

1. **常见问题与解决方案**

   | 问题 | 症状 | 解决方案 |
   |------|------|----------|
   | 服务启动失败 | 服务容器启动后立即退出 | 查看服务日志：`docker-compose logs <service-name>` |
   | API调用失败 | 服务间API调用返回错误 | 检查服务间网络连接和配置 |
   | Kafka 不工作 | 消息无法收发 | 检查 Zookeeper 是否健康：`docker exec uav-zookeeper bash -c "echo ruok \| nc localhost 2181"` |
   | Zookeeper 异常 | Kafka 无法连接 | 检查端口 2181 是否监听；重启 `docker compose restart zookeeper kafka` |
   | 性能问题 | 系统响应缓慢 | 检查系统资源使用情况，优化算法参数 |
   | 数据一致性问题 | 不同服务间数据不一致 | 确保服务间使用相同的数据格式，实现数据同步机制 |

2. **服务恢复**
   - 重启服务：`docker-compose restart <service-name>`
   - 重建服务：`docker-compose up -d --build <service-name>`
   - 从备份恢复数据：`docker exec -i <mysql-container> mysql -u root -p uav_path_planning < backup.sql`

3. **安全维护**
   - 定期更新依赖：`mvn dependency:update`（后端）和 `npm update`（前端）
   - 检查安全漏洞：使用安全扫描工具定期检查依赖包漏洞
   - 更新SSL证书：确保HTTPS证书及时更新

4. **版本管理**
   - 服务版本：每个服务独立版本管理
   - 依赖版本：使用固定版本的依赖，确保系统稳定性
   - 配置版本：配置文件版本管理，便于回滚

### 扩展与升级

1. **水平扩展**
   - 增加服务实例数量：`kubectl scale deployment <deployment-name> --replicas=5`
   - 负载均衡：使用Nginx或Kubernetes内置负载均衡

2. **垂直扩展**
   - 增加硬件资源：提升CPU、内存等配置
   - 优化算法：改进核心算法，提高计算效率

3. **功能扩展**
   - 集成新算法：添加新的气象预测和路径规划算法
   - 支持新数据源：集成更多类型的气象数据源
   - 添加新功能：如飞行模拟、任务调度优化等

## 监控与告警

### 1. 监控指标

- **服务健康**：各服务的健康状态和响应时间
- **系统资源**：CPU、内存、磁盘使用情况
- **业务指标**：同化计算时间、路径规划时间、预测准确率

### 2. 告警机制

- **服务异常**：服务不可用或响应时间过长时告警
- **资源不足**：系统资源使用超过阈值时告警
- **业务异常**：同化失败或路径规划失败时告警

### 3. 日志管理

- **集中化日志**：使用ELK Stack或类似工具集中管理日志
- **日志分析**：定期分析日志，识别潜在问题
- **日志保留**：设置合理的日志保留策略

## 安全配置

### 1. 网络安全

- **网络隔离**：使用Docker网络隔离不同服务
- **防火墙**：配置防火墙规则，限制外部访问
- **HTTPS**：使用HTTPS加密传输数据

### 2. 认证与授权

- **API认证**：为所有API接口添加认证机制
- **权限控制**：基于角色的权限控制
- **审计日志**：记录所有操作日志，便于审计

### 3. 数据安全

- **数据加密**：对敏感数据进行加密存储
- **数据脱敏**：在日志和监控中脱敏敏感信息
- **访问控制**：限制数据访问权限

## 部署检查清单

### 部署前
- [ ] 检查Docker和Docker Compose版本
- [ ] 检查系统资源（CPU、内存、磁盘）
- [ ] 配置环境变量和数据库连接
- [ ] 确保所有依赖已安装

### 部署中
- [ ] 构建并启动所有服务
- [ ] 检查服务启动状态
- [ ] 验证API接口可用性
- [ ] 测试完整路径规划流程

### 部署后
- [ ] 监控服务运行状态
- [ ] 检查系统资源使用情况
- [ ] 测试故障恢复能力
- [ ] 文档更新和维护

## 结论

本部署与维护方案提供了一种灵活、可扩展的方式来部署和管理无人机路径规划系统。通过集成 `data-assimilation-service`（配合 `data-assimilation-platform` 核心算法库），我们获得了更强大的贝叶斯同化能力，同时保持了系统的模块化和可维护性。

通过合理的资源分配、缓存策略和监控机制，我们可以确保系统在生产环境中的稳定运行。同时，扩展方案和故障处理机制为系统的长期发展和可靠性提供了保障。

系统的部署和维护流程已经标准化，确保了系统的可重复性和可靠性，为用户提供了一个稳定、高效的无人机路径规划平台。

### Kafka 与 Zookeeper 运维

**Kafka 常用运维命令**:

```bash
# 查看所有 Topic
docker exec uav-kafka kafka-topics --bootstrap-server localhost:9092 --list

# 创建 Topic
docker exec uav-kafka kafka-topics --create --topic weather-data --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# 查看消费者组
docker exec uav-kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list

# 消费测试消息
docker exec uav-kafka kafka-console-consumer --topic weather-data --from-beginning --bootstrap-server localhost:9092
```

**Zookeeper 健康检查**:

```bash
# 检查 Zookeeper 是否存活
docker exec uav-zookeeper bash -c "echo ruok | nc localhost 2181"
# 期望输出：imok

# 查看 Zookeeper 状态
docker exec uav-zookeeper bash -c "echo stat | nc localhost 2181"
```

**Kafka 常见问题**:

| 问题 | 症状 | 解决方案 |
|------|------|----------|
| Kafka 无法启动 | 容器反复重启 | 确认 Zookeeper 先于 Kafka 启动且健康 |
| 消息堆积 | 消费者跟不上生产者 | 增加消费者实例；调整 partitions 数量 |
| 磁盘满 | Kafka 日志占满磁盘 | 配置 log.retention.hours 自动清理 |
| 内存不足 OOM | 容器被 kill (exit 137) | 增加 Kafka 内存限制至 2G+（docker-compose.yml 已配置） |

---

> **最后更新**: 2026-06-06  
> **版本**: 2.2  
> **维护者**: DITHIOTHREITOL