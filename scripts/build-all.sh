#!/bin/bash
# Build All - Bash Script

echo "========================================"
echo "Building UAV Platform Docker Images"
echo "========================================"
echo ""

# Build base images
echo "[1/9] Building uav-base image..."
docker build -t uav-base:latest -f docker/base/Dockerfile .

echo "[2/9] Building uav-python image..."
docker build -t uav-python:latest -f docker/base/python/Dockerfile .

echo ""
echo "Building service images..."
echo ""

# Build service images
services=(
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
docker build -t uav-edge-sdk:latest -f uav-edge-sdk/Dockerfile uav-edge-sdk

index=3
for service in "${services[@]}"; do
    echo "[$index/11] Building $service..."
    docker build -t "uav-$service:latest" -f "$service/Dockerfile.runtime" "$service"
    index=$((index + 1))
done

echo ""
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
