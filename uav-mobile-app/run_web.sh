#!/bin/bash
# Flutter Web 启动脚本 — 自动检测 WSL2 IP 注入
# 用法: bash run_web.sh [chrome|edge|web-server]

TARGET=${1:-chrome}

# 检测 WSL2 IP
WSL_IP=$(ip addr show eth0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)

if [ -z "$WSL_IP" ]; then
  echo "⚠️  未检测到 WSL2 IP，回退到 localhost"
  API_URL="http://localhost:8088"
else
  API_URL="http://${WSL_IP}:8088"
  echo "🌐 WSL2 IP: ${WSL_IP}"
  echo "📡 API:    ${API_URL}"
fi

echo "🚀 启动 Flutter Web (${TARGET})..."
cd "$(dirname "$0")"
flutter run -d ${TARGET} --dart-define=API_BASE_URL=${API_URL}
