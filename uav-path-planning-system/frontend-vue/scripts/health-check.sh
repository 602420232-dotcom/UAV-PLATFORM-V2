#!/bin/bash
# 后端服务健康检查脚本

echo "============================================"
echo "  18个后端服务健康检查"
echo "============================================"
echo ""

# 服务配置
declare -A services=(
  ["mysql"]="tcp://localhost:3306"
  ["redis"]="tcp://localhost:6379"
  ["nacos"]="http://localhost:8848/nacos/health"
  ["api-gateway"]="http://localhost:8088/actuator/health"
  ["wrf-processor"]="http://localhost:8081/actuator/health"
  ["data-assimilation"]="http://localhost:8084/actuator/health"
  ["meteor-forecast"]="http://localhost:8082/actuator/health"
  ["path-planning"]="http://localhost:8083/actuator/health"
  ["uav-platform"]="http://localhost:8080/actuator/health"
  ["uav-weather-collector"]="http://localhost:8086/actuator/health"
  ["edge-cloud-coordinator"]="http://localhost:8000/actuator/health"
  ["fengwu-service"]="http://localhost:8085/actuator/health"
  ["model-engine"]="http://localhost:8087/actuator/health"
  ["tianzi-service"]="http://localhost:8090/actuator/health"
  ["fenglei-service"]="http://localhost:8091/actuator/health"
  ["kafka"]="tcp://localhost:9092"
  ["zookeeper"]="tcp://localhost:2181"
  ["frontend"]="http://localhost:3000/api/health"
)

success_count=0
failed_count=0
total=${#services[@]}

for name in "${!services[@]}"; do
  url=${services[$name]}
  echo -n "[$name] "
  
  if [[ $url == http* ]]; then
    # HTTP服务检查
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null)
    if [ "$response" = "200" ] || [ "$response" = "204" ] || [ "$response" = "302" ]; then
      echo -e "\033[32m✅ 正常\033[0m ($response)"
      ((success_count++))
    else
      echo -e "\033[31m❌ 异常\033[0m ($response)"
      ((failed_count++))
    fi
  else
    # TCP服务检查
    timeout 5 bash -c "echo > /dev/tcp/localhost/${url##*:}" 2>/dev/null
    if [ $? -eq 0 ]; then
      echo -e "\033[32m✅ 正常\033[0m"
      ((success_count++))
    else
      echo -e "\033[31m❌ 异常\033[0m"
      ((failed_count++))
    fi
  fi
done

echo ""
echo "============================================"
echo "  检查结果汇总"
echo "============================================"
echo "  服务总数: $total"
echo -e "  ✅ 正常: \033[32m$success_count\033[0m"
echo -e "  ❌ 异常: \033[31m$failed_count\033[0m"
echo ""

if [ $failed_count -gt 0 ]; then
  echo "⚠️  警告: 部分服务异常，请检查容器运行状态后再进行前端对接"
  exit 1
else
  echo "🎉 所有服务正常，可以开始前端对接工作"
  exit 0
fi