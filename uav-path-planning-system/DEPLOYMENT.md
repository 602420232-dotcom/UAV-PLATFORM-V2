# 无人机路径规划系统部署文档

## 系统架构

### 技术栈
- **后端**：Spring Boot 2.7.0, Java 11
- **前端**：Vue 3, Ant Design Vue, Leaflet, ECharts
- **算法**：Python 3.8+, TensorFlow, XGBoost, NumPy, Pandas
- **数据库**：MySQL 8.0
- **缓存**：Redis 6.2
- **部署**：Docker, Docker Compose

### 系统模块
1. **算法核心**：
   - WRF气象数据解析与处理
   - 贝叶斯同化与不确定性评估
   - LSTM+XGBoost气象预测与订正
   - VRPTW+A*+DWA三层路径规划

2. **后端服务**：
   - 用户认证与权限管理
   - 任务管理
   - 无人机管理
   - 气象数据管理
   - 路径规划服务
   - Python算法集成

3. **前端界面**：
   - 地图可视化
   - 任务配置
   - 路径展示
   - 气象数据展示
   - 历史记录管理

## 部署方式

### 方式一：Docker Compose部署（推荐）

#### 前提条件
- 安装 Docker 和 Docker Compose
- 确保 8080, 3306, 6379 端口未被占用

#### 部署步骤
1. **克隆项目**
   ```bash
   git clone <项目地址>
   cd uav-path-planning-system
   ```

2. **启动服务**
   ```bash
   docker-compose up -d
   ```

3. **验证部署**
   - 访问后端API：http://localhost:8080/api
   - 访问前端界面：http://localhost:3000（需要单独启动前端）

### 方式二：本地部署

#### 前提条件
- JDK 11+
- Python 3.8+
- MySQL 8.0+
- Redis 6.2+
- Node.js 16+

#### 后端部署
1. **配置数据库**
   - 创建数据库：`uav_path_planning`
   - 执行 `database/create_tables.sql` 初始化表结构

2. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **构建并运行后端**
   ```bash
   cd backend-spring
   ./mvnw clean package -DskipTests
   java -jar target/uav-path-planning-0.0.1-SNAPSHOT.jar
   ```

#### 前端部署
1. **安装依赖**
   ```bash
   cd frontend-vue
   npm install
   ```

2. **开发模式运行**
   ```bash
   npm run dev
   ```

3. **生产构建**
   ```bash
   npm run build
   ```

## 配置说明

### 后端配置
- **数据库配置**：`backend-spring/src/main/resources/application.yml`
- **Redis配置**：`backend-spring/src/main/resources/application.yml`
- **Python脚本路径**：`backend-spring/src/main/resources/application.yml`

### 前端配置
- **API地址**：`frontend-vue/vite.config.js`
- **地图配置**：`frontend-vue/src/views/PathPlanningView.vue`

## 系统使用

### 初始账号
- **管理员**：admin / admin
- **调度员**：dispatcher / admin
- **操作员**：operator / admin
- **普通用户**：user / admin

### 核心功能
1. **路径规划**：
   - 添加任务点
   - 选择无人机
   - 设置气象数据
   - 执行路径规划
   - 查看规划结果

2. **气象数据**：
   - 查看实时气象数据
   - 查看气象热力图
   - 查看气象趋势

3. **任务管理**：
   - 创建任务
   - 编辑任务
   - 分配任务
   - 查看任务状态

4. **无人机管理**：
   - 查看无人机状态
   - 管理无人机信息
   - 监控无人机电池

5. **历史记录**：
   - 查看历史任务
   - 查看任务详情
   - 导出历史记录

## 故障排查

### 常见问题
1. **数据库连接失败**
   - 检查 MySQL 服务是否运行
   - 检查数据库配置是否正确
   - 检查数据库用户权限

2. **Python算法调用失败**
   - 检查 Python 环境是否正确
   - 检查依赖是否安装
   - 检查脚本路径是否正确

3. **前端无法访问后端**
   - 检查后端服务是否运行
   - 检查前端API配置是否正确
   - 检查网络连接

4. **Docker 部署失败**
   - 检查 Docker 服务是否运行
   - 检查端口是否被占用
   - 查看容器日志

## 性能优化

1. **缓存优化**：
   - 使用 Redis 缓存气象数据
   - 缓存路径规划结果
   - 缓存频繁访问的配置

2. **数据库优化**：
   - 添加适当的索引
   - 优化查询语句
   - 定期清理数据

3. **算法优化**：
   - 预计算气象数据
   - 增量更新路径规划
   - 并行计算

4. **部署优化**：
   - 使用容器编排
   - 负载均衡
   - 自动扩缩容

## 安全建议

1. **认证与授权**：
   - 使用 HTTPS
   - 定期更新密码
   - 限制API访问

2. **数据安全**：
   - 加密敏感数据
   - 定期备份数据库
   - 防SQL注入

3. **系统安全**：
   - 定期更新依赖
   - 扫描漏洞
   - 配置防火墙

## 联系与支持

- **文档**：本部署文档
- **代码**：项目源代码
- **问题**：提交 Issue

---

**版本**：1.0.0
**更新日期**：2024-01-01
