#!/usr/bin/env python3
"""
自动应用部署审计修复脚本
对 docker-compose.yml, Dockerfile, K8s YAML 等应用修复
"""
import os
import re
import shutil

PROJECT = "/mnt/d/Developer/workplace/py/iteam/trae"


def fix_docker_compose():
    """修复 docker-compose.yml: 替换硬编码密码 + 添加健康检查 + 修复kafka"""
    path = os.path.join(PROJECT, "docker-compose.yml")
    with open(path, 'r') as f:
        content = f.read()

    # 1. 替换所有硬编码密码为环境变量
    secrets_map = {
        '"uav-jwt-production-secret-change-me"': '${JWT_SECRET_KEY}',
        '"uav-aes256-encryption-key-change-me"': '${ENCRYPTION_KEY}',
        '"admin123"': '${SECURITY_USER_PASSWORD:-admin123}',
        '"uav_ploy_2026_secure"': '${DB_PASSWORD}',
    }
    for old, new in secrets_map.items():
        content = content.replace(old, new)

    # 2. 修复 MYSQL_ROOT_PASSWORD
    content = content.replace(
        'MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}',
        'MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-${DB_PASSWORD}}'
    )

    # 3. 修复 Kafka advertised listener
    content = content.replace(
        'KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092,PLAINTEXT_INTERNAL://kafka:29092',
        'KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://${KAFKA_HOST:-localhost}:9092,PLAINTEXT_INTERNAL://kafka:29092'
    )

    # 4. 添加 Zookeeper healthcheck
    zk_section_old = """      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    deploy:"""
    zk_section_new = """      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    healthcheck:
      test: ["CMD", "bash", "-c", "echo ruok | nc -w 2 localhost 2181 | grep imok"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s
    deploy:"""
    content = content.replace(zk_section_old, zk_section_new)

    # 5. 添加 Kafka healthcheck
    kafka_section_old = """      KAFKA_JMX_PORT: 9999
    deploy:"""
    kafka_section_new = """      KAFKA_JMX_PORT: 9999
    healthcheck:
      test: ["CMD", "bash", "-c", "kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1"]
      interval: 15s
      timeout: 10s
      retries: 5
      start_period: 30s
    deploy:"""
    content = content.replace(kafka_section_old, kafka_section_new)

    # 6. 添加 edge-cloud-coordinator healthcheck
    edge_section_old = """      REDIS_HOST: redis
      REDIS_PORT: 6379
    restart: always
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    security_opt:
      - no-new-privileges:true
    networks:
      - uav-network"""
    edge_section_new = """      REDIS_HOST: redis
      REDIS_PORT: 6379
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-", "http://localhost:8000/health"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 20s
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    security_opt:
      - no-new-privileges:true
    networks:
      - uav-network"""
    content = content.replace(edge_section_old, edge_section_new)

    # 7. 添加 version
    if not content.startswith('version:'):
        content = 'version: \'3.8\'\n\n' + content

    with open(path, 'w') as f:
        f.write(content)
    print(f"✅ docker-compose.yml 已修复 ({len(secrets_map)} 处密码替换 + 3 处健康检查)")


def fix_dockerfiles():
    """修复所有 runtime Dockerfile: 添加非root用户; 修复 pip 静默错误"""
    runtime_dockerfiles = [
        "api-gateway/Dockerfile.runtime",
        "uav-platform-service/Dockerfile.runtime",
        "wrf-processor-service/Dockerfile.runtime",
        "meteor-forecast-service/Dockerfile.runtime",
        "path-planning-service/Dockerfile.runtime",
        "data-assimilation-service/Dockerfile.runtime",
        "uav-weather-collector/Dockerfile.runtime",
    ]

    user_block = """# Security: create non-root user
RUN addgroup -g 1001 -S appgroup && \\
    adduser -u 1001 -S appuser -G appgroup && \\
    chown -R appuser:appgroup /app
USER appuser

"""

    for df in runtime_dockerfiles:
        path = os.path.join(PROJECT, df)
        if not os.path.exists(path):
            print(f"  ⚠️ 跳过不存在的文件: {df}")
            continue
        with open(path, 'r') as f:
            content = f.read()

        if 'USER appuser' not in content:
            # Insert before HEALTHCHECK
            content = content.replace('HEALTHCHECK', user_block + 'HEALTHCHECK')
            with open(path, 'w') as f:
                f.write(content)
            print(f"✅ {df} 已添加非root用户")
        else:
            print(f"  ⏭️ {df} 已有非root用户，跳过")

    # Fix fengwu-service/Dockerfile
    fengwu_path = os.path.join(PROJECT, "fengwu-service/Dockerfile")
    if os.path.exists(fengwu_path):
        with open(fengwu_path, 'r') as f:
            content = f.read()
        if 'USER' not in content:
            fengwu_user = """# Security: create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -m -s /sbin/nologin appuser && \\
    chown -R appuser:appgroup /app
USER appuser


"""
            content = content.replace('HEALTHCHECK', fengwu_user + 'HEALTHCHECK')
            # Also remove unnecessary mkdir (model mounted as volume)
            content = content.replace("RUN mkdir -p /app/model\n\n", "")
            with open(fengwu_path, 'w') as f:
                f.write(content)
            print("✅ fengwu-service/Dockerfile 已添加非root用户")

    # Fix pip error suppression in standalone Dockerfiles
    standalone_dfs = [
        "wrf-processor-service/Dockerfile",
        "meteor-forecast-service/Dockerfile",
        "path-planning-service/Dockerfile",
        "edge-cloud-coordinator/Dockerfile",
    ]
    for df in standalone_dfs:
        path = os.path.join(PROJECT, df)
        if not os.path.exists(path):
            continue
        with open(path, 'r') as f:
            content = f.read()

        # Remove 2>/dev/null || true from pip commands
        old_pattern = re.sub(r'2>/dev/null\s*\|\|\s*true', '', content)
        if old_pattern != content:
            # Also fix: pip install without --break-system-packages on older pip
            with open(path, 'w') as f:
                f.write(old_pattern)
            print(f"✅ {df} 已移除pip错误静默抑制")
        else:
            print(f"  ⏭️ {df} 无需pip修复")

def fix_env_files():
    """修复 .env 和 docker-compose.dev.yml"""
    # Fix .env
    env_path = os.path.join(PROJECT, ".env")
    with open(env_path, 'r') as f:
        content = f.read()

    # Add missing variables
    if 'MYSQL_ROOT_PASSWORD' not in content:
        content += '\n# ===== MySQL Root Password =====\nMYSQL_ROOT_PASSWORD=your-secure-root-password\n'
    if 'SECURITY_USER_PASSWORD' not in content:
        content += '\n# ===== Security Default Password =====\nSECURITY_USER_PASSWORD=admin123\n'
    if 'REDIS_PASSWORD' not in content:
        content += '\n# ===== Redis Password =====\nREDIS_PASSWORD=\n'
    if 'WEATHER_API_KEY' not in content:
        content += '\n# ===== Weather API Key =====\nWEATHER_API_KEY=\n'
    if 'KAFKA_HOST' not in content:
        content += '\n# ===== Kafka Host (external) =====\nKAFKA_HOST=localhost\n'

    with open(env_path, 'w') as f:
        f.write(content)
    print("✅ .env 已补充缺失变量")

    # Fix docker-compose.dev.yml - add MYSQL_ROOT_PASSWORD, healthcheck for nacos
    dev_path = os.path.join(PROJECT, "docker-compose.dev.yml")
    with open(dev_path, 'r') as f:
        dev_content = f.read()

    # Add nacos healthcheck
    if 'healthcheck' not in dev_content.split('nacos:')[1].split('uav-nacos-dev')[0] if 'nacos:' in dev_content else True:
        nacos_old = """    environment:
      - MODE=standalone
    ports:
      - "8848:8848"
    deploy:"""
        nacos_new = """    environment:
      - MODE=standalone
      - JVM_XMS=256m
      - JVM_XMX=512m
    ports:
      - "8848:8848"
    healthcheck:
      test: ["CMD", "curl", "-", "http://localhost:8848/nacos/"]
      interval: 15s
      timeout: 5s
      retries: 10
      start_period: 60s
    deploy:"""
        dev_content = dev_content.replace(nacos_old, nacos_new)

    # Use same image versions as prod
    dev_content = dev_content.replace('redis:6.2\n', 'redis:6.2-alpine\n')

    with open(dev_path, 'w') as f:
        f.write(dev_content)
    print("✅ docker-compose.dev.yml 已修复 (Nacos健康检查 + Redis版本)")


def fix_k8s_namespace():
    """统一 K8s 命名空间为 uav-platform"""
    # Fix namespace.yml
    ns_path = os.path.join(PROJECT, "deployments/kubernetes/namespace.yml")
    with open(ns_path, 'r') as f:
        content = f.read()
    content = content.replace('uav-path-planning', 'uav-platform')
    with open(ns_path, 'w') as f:
        f.write(content)
    print("✅ namespace.yml 命名空间已统一为 uav-platform")

    # Fix deploy.sh
    deploy_sh = os.path.join(PROJECT, "deployments/kubernetes/deploy.sh")
    with open(deploy_sh, 'r') as f:
        content = f.read()
    content = content.replace('uav-path-planning', 'uav-platform')
    # Add missing services
    if 'api-gateway' not in content:
        old_end = 'echo "=== 部署完成 ==="'
        new_deploy = '''echo "11. 部署API网关..."
kubectl apply -f api-gateway.yml

echo "12. 部署天气采集服务..."
kubectl apply -f uav-weather-collector.yml

echo "13. 部署边云协同服务..."
kubectl apply -f edge-cloud-coordinator.yml

echo "14. 部署Ingress..."
kubectl apply -f nginx-ingress.yml

echo "15. 部署监控..."
kubectl apply -f monitoring.yml


echo "=== 部署完成 ==="'''
        content = content.replace(old_end, new_deploy)
    with open(deploy_sh, 'w') as f:
        f.write(content)
    print("✅ deploy.sh 已修复 (命名空间 + 补全服务)")


def fix_monitoring_dns():
    """修正 monitoring.yml 中的 DNS 引用"""
    mon_path = os.path.join(PROJECT, "deployments/kubernetes/monitoring.yml")
    with open(mon_path, 'r') as f:
        content = f.read()
    content = content.replace('uav-path-planning.svc.cluster.local', 'uav-platform.svc.cluster.local')
    with open(mon_path, 'w') as f:
        f.write(content)
    print("✅ monitoring.yml DNS引用已修正")


def fix_k8s_pvc_and_secrets():
    """添加缺失的 PVC 和 Secrets"""
    # Add backup-pvc to persistent-volumes.yml
    pv_path = os.path.join(PROJECT, "deployments/kubernetes/persistent-volumes.yml")
    with open(pv_path, 'r') as f:
        content = f.read()
    if 'backup-pvc' not in content:
        backup_pvc = """
---
# 备份存储
apiVersion: v1
kind: PersistentVolumeClaim


metadata:
  name: backup-pvc
  namespace: uav-platform


spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: standard


"""
        content += backup_pvc
        with open(pv_path, 'w') as f:
            f.write(content)
        print("✅ persistent-volumes.yml 已添加 backup-pvc")

    # Add missing secrets
    sec_path = os.path.join(PROJECT, "deployments/kubernetes/secrets.yml")
    with open(sec_path, 'r') as f:
        content = f.read()

    if 'mysql-secrets' not in content:
        mysql_sec = """
---
apiVersion: v1
kind: Secret


metadata:
  name: mysql-secrets
  namespace: uav-platform
type: Opaque


data:
  username: ${MYSQL_USER_BASE64:-dWF2}
  password: ${MYSQL_PASSWORD_BASE64}


"""
        content += mysql_sec

    if 'uav-platform-tls' not in content:
        tls_sec = """
---
# TLS Certificate Secret (use cert-manager or manually create)
apiVersion: v1
kind: Secret


metadata:
  name: uav-platform-tls
  namespace: uav-platform
type: kubernetes.io/tls


data:
  tls.crt: ${TLS_CRT_BASE64}
  tls.key: ${TLS_KEY_BASE64}


"""
        content += tls_sec

    if 'uav-secrets' not in content:
        uav_sec = """
---
apiVersion: v1
kind: Secret


metadata:
  name: uav-secrets
  namespace: uav-platform
type: Opaque


data:
  db-password: ${DB_PASSWORD_BASE64}


"""
        content += uav_sec

    with open(sec_path, 'w') as f:
        f.write(content)
    print("✅ secrets.yml 已添加缺失Secrets (mysql-secrets, tls, uav-secrets)")

def fix_k8s_resources():
    """修正 K8s 资源限制与 docker-compose 对齐"""
    # data-assimilation-service.yml: 512Mi → 2Gi
    da_svc = os.path.join(PROJECT, "deployments/kubernetes/data-assimilation-service.yml")
    with open(da_svc, 'r') as f:
        content = f.read()
    old_res = """          resources:
            limits: { memory: 512Mi, cpu: 500m }
            requests: { memory: 256Mi, cpu: 200m }"""
    new_res = """          resources:
            limits: { memory: 2Gi, cpu: 2000m }
            requests: { memory: 1Gi, cpu: 500m }"""
    content = content.replace(old_res, new_res)
    with open(da_svc, 'w') as f:
        f.write(content)

    # data-assimilation.yml
    da_path = os.path.join(PROJECT, "deployments/kubernetes/data-assimilation.yml")
    if os.path.exists(da_path):
        with open(da_path, 'r') as f:
            content = f.read()
        content = content.replace(old_res, new_res)
        with open(da_path, 'w') as f:
            f.write(content)

    # uav-platform-service.yml: 512Mi → 1.5Gi
    plat_svc = os.path.join(PROJECT, "deployments/kubernetes/uav-platform-service.yml")
    with open(plat_svc, 'r') as f:
        content = f.read()
    old_plat_res = """          resources:
          requests:
            cpu: "100m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi\""""
    new_plat_res = """          resources:
          requests:
            cpu: "500m"
            memory: "768Mi"
          limits:
            cpu: "2000m"
            memory: "1536Mi\""""
    content = content.replace(old_plat_res, new_plat_res)
    with open(plat_svc, 'w') as f:
        f.write(content)

    # uav-platform.yml
    plat_path = os.path.join(PROJECT, "deployments/kubernetes/uav-platform.yml")
    if os.path.exists(plat_path):
        with open(plat_path, 'r') as f:
            content = f.read()
        content = content.replace(old_plat_res, new_plat_res)
        with open(plat_path, 'w') as f:
            f.write(content)

    print("✅ K8s 资源限制已与 docker-compose 对齐 (data-assimilation: 2Gi, uav-platform: 1.5Gi)")


def archive_duplicate_k8s():
    """归档重复的 K8s YAML 文件"""
    duplicates = [
        "wrf-processor.yml",
        "meteor-forecast.yml",
        "path-planning.yml",
        "data-assimilation.yml",
        "uav-platform.yml",
    ]
    k8s_dir = os.path.join(PROJECT, "deployments/kubernetes")
    for f in duplicates:
        path = os.path.join(k8s_dir, f)
        if os.path.exists(path):
            dep_path = path + ".deprecated"
            shutil.move(path, dep_path)
            print(f"✅ {f} → {f}.deprecated (已归档)")


def fix_build_scripts():
    """补全构建脚本"""
    # Fix build-all.sh
    build_sh = os.path.join(PROJECT, "scripts/build-all.sh")
    with open(build_sh, 'r') as f:
        content = f.read()

    if 'fengwu' not in content:
        old_services = '''services=(
    "api-gateway"
    "data-assimilation-service"
    "meteor-forecast-service"
    "path-planning-service"
    "wrf-processor-service"
    "uav-platform-service"
    "uav-weather-collector"
)'''
        new_services = '''services=(
    "api-gateway"
    "data-assimilation-service"
    "meteor-forecast-service"
    "path-planning-service"
    "wrf-processor-service"
    "uav-platform-service"
    "uav-weather-collector"
    "fengwu-service"
    "edge-cloud-coordinator"
)

# Build frontend separately (non-Java)
echo "[10/11] Building uav-frontend..."
docker build -t uav-frontend:latest -f uav-path-planning-system/frontend-vue/Dockerfile uav-path-planning-system/frontend-vue

# Build edge SDK
echo "[11/11] Building uav-edge-sdk..."
docker build -t uav-edge-sdk:latest -f uav-edge-sdk/Dockerfile uav-edge-sdk'''

        old_total = 'index=3\nfor service in "${services[@]}"; do\n    echo "[$index/9] Building $service..."'
        new_total = 'index=3\nfor service in "${services[@]}"; do\n    echo "[$index/11] Building $service..."'

        content = content.replace(old_services, new_services)
        content = content.replace(old_total, new_total)

        with open(build_sh, 'w') as f:
            f.write(content)
        print("✅ build-all.sh 已补全 (添加 fengwu, edge-cloud, frontend)")

def fix_hpa_conflicts():
    """解决 HPA 冲突：保留 hpa.yml 为主配置"""
    k8s_dir = os.path.join(PROJECT, "deployments/kubernetes")

    # Archive autoscaling.yml (conflicts with hpa.yml)
    auto_path = os.path.join(k8s_dir, "autoscaling.yml")
    if os.path.exists(auto_path):
        shutil.move(auto_path, auto_path + ".deprecated")
        print("✅ autoscaling.yml → autoscaling.yml.deprecated (已归档)")

    # Remove inline HPA from service YAMLs (meteor-forecast-service.yml and path-planning-service.yml)
    for svc_file in ["meteor-forecast-service.yml", "path-planning-service.yml"]:
        svc_path = os.path.join(k8s_dir, svc_file)
        if os.path.exists(svc_path):
            with open(svc_path, 'r') as f:
                content = f.read()
            # Remove HPA section (from ---\napiVersion: autoscaling to end)
            pattern = r'\n---\napiVersion: autoscaling.*$'
            new_content = re.sub(pattern, '', content, flags=re.DOTALL)
            if new_content != content:
                with open(svc_path, 'w') as f:
                    f.write(new_content)
                print(f"✅ {svc_file} 已移除内联HPA")

    print("   ℹ️ HPA统一使用 hpa.yml + hpa-supplement.yml")


def fix_sonarqube_postgres():
    """为 SonarQube 添加 PostgreSQL 部署"""
    sq_path = os.path.join(PROJECT, "deployments/kubernetes/sonarqube.yml")
    with open(sq_path, 'r') as f:
        content = f.read()

    if 'postgres-sonar' not in content or 'kind: Deployment' not in content.split('sonarqube\n')[0] if len(content.split('sonarqube\n')) > 1 else True:
        postgres_block = """---
# PostgreSQL for SonarQube
apiVersion: v1
kind: PersistentVolumeClaim


metadata:
  name: postgres-sonar-pvc
  namespace: uav-platform


spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: apps/v1
kind: Deployment


metadata:
  name: postgres-sonar
  namespace: uav-platform


spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres-sonar
  template:
    metadata:
      labels:
        app: postgres-sonar
    spec:
      containers:
        - name: postgres
          image: postgres:15-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: sonar
            - name: POSTGRES_USER
              value: sonar
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: sonar-secrets
                  key: password
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
      volumes:
        - name: postgres-data
          persistentVolumeClaim:
            claimName: postgres-sonar-pvc
---
apiVersion: v1
kind: Service


metadata:
  name: postgres-sonar
  namespace: uav-platform


spec:
  selector:
    app: postgres-sonar
  ports:
    - port: 5432
      targetPort: 5432


"""
        content = postgres_block + "\n" + content
        with open(sq_path, 'w') as f:
            f.write(content)
        print("✅ sonarqube.yml 已添加 PostgreSQL 部署")


def create_docker_override():
    """创建 docker-compose.override.yml 开发覆盖"""
    override_path = os.path.join(PROJECT, "docker-compose.override.yml")
    override = """# Docker Compose Override - 本地开发覆盖
# docker compose -f docker-compose.yml -f docker-compose.override.yml up


services:
  api-gateway:
    ports:
      - "8088:8088"
      - "5005:5005"  # Remote debug
    environment:
      - JAVA_OPTS=-agentlib:jdwp=transport=dt_socket, server=y, suspend=n, address=*:5005 -Xms256m -Xmx512m -XX:+UseG1GC
      - LOG_LEVEL=DEBUG
    volumes:
      - ./api-gateway/target:/app:ro

  uav-platform:
    ports:
      - "8080:8080"
      - "5006:5005"
    environment:
      - JAVA_OPTS=-agentlib:jdwp=transport=dt_socket, server=y, suspend=n, address=*:5005 -Xms256m -Xmx512m -XX:+UseG1GC
      - LOG_LEVEL=DEBUG

  wrf-processor:
    ports:
      - "8081:8081"
      - "5007:5005"
    environment:
      - JAVA_OPTS=-agentlib:jdwp=transport=dt_socket, server=y, suspend=n, address=*:5005 -Xms256m -Xmx512m -XX:+UseG1GC
      - LOG_LEVEL=DEBUG

  meteor-forecast:
    ports:
      - "8082:8082"
      - "5008:5005"
    environment:
      - JAVA_OPTS=-agentlib:jdwp=transport=dt_socket, server=y, suspend=n, address=*:5005 -Xms256m -Xmx512m -XX:+UseG1GC
      - LOG_LEVEL=DEBUG

  path-planning:
    ports:
      - "8083:8083"
      - "5009:5005"
    environment:
      - JAVA_OPTS=-agentlib:jdwp=transport=dt_socket, server=y, suspend=n, address=*:5005 -Xms256m -Xmx512m -XX:+UseG1GC
      - LOG_LEVEL=DEBUG

  data-assimilation:
    ports:
      - "8084:8084"
      - "5010:5005"
    environment:
      - JAVA_OPTS=-agentlib:jdwp=transport=dt_socket, server=y, suspend=n, address=*:5005 -Xms256m -Xmx512m -XX:+UseG1GC
      - LOG_LEVEL=DEBUG

  uav-weather-collector:
    ports:
      - "8086:8086"
      - "5011:5005"
    environment:
      - JAVA_OPTS=-agentlib:jdwp=transport=dt_socket, server=y, suspend=n, address=*:5005 -Xms256m -Xmx256m -XX:+UseG1GC
      - LOG_LEVEL=DEBUG
"""
    if not os.path.exists(override_path):
        with open(override_path, 'w') as f:
            f.write(override)
        print("✅ docker-compose.override.yml 已创建 (开发调试覆盖)")


def main():
    print("=" * 60)
    print("🔧 开始应用部署审计自动修复...")
    print("=" * 60)
    print()

    fix_docker_compose()
    fix_dockerfiles()
    fix_env_files()
    fix_k8s_namespace()
    fix_monitoring_dns()
    fix_k8s_pvc_and_secrets()
    fix_k8s_resources()
    archive_duplicate_k8s()
    fix_build_scripts()
    fix_hpa_conflicts()
    fix_sonarqube_postgres()
    create_docker_override()

    print()
    print("=" * 60)
    print("✅ 所有自动修复已完成！")
    print(f"📄 审计报告: {PROJECT}/docs/audit/deploy-audit.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
