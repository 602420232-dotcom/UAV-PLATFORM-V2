#!/bin/bash
# FengWu ONNX 模型自动下载脚本
# 模型来源: Shanghai AI Lab (OpenEarthLab/FengWu)
# 论文: https://arxiv.org/abs/2304.02948
# GitHub: https://github.com/OpenEarthLab/FengWu
# HuggingFace: https://huggingface.co/OpenEarthLab/FengWu

set -e

MODEL_DIR="${1:-/mnt/d/Developer/FengWu_All/FengWu}"
MODEL_DIR_WIN="D:\\Developer\\FengWu_All\\FengWu"

echo "============================================"
echo "  FengWu ONNX 模型下载"
echo "============================================"
echo ""
echo "目标目录: $MODEL_DIR"
echo ""

# --- 方式选择 ---
echo "选择下载方式:"
echo "  1) HuggingFace (推荐，需要 huggingface_hub)"
echo "  2) ModelScope (国内镜像，更快)"
echo "  3) wget 直链下载"
echo "  4) 仅显示手动下载地址"
echo ""
read -p "请输入 [1-4, 默认 4]: " choice
choice=${choice:-4}

mkdir -p "$MODEL_DIR"

download_hf() {
    echo "[INFO] 通过 HuggingFace 下载..."
    pip install -q huggingface_hub
    python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(
    'OpenEarthLab/FengWu',
    local_dir='$MODEL_DIR',
    allow_patterns=['*.onnx', 'data_mean.npy', 'data_std.npy'],
    resume_download=True,
)
"
}

download_ms() {
    echo "[INFO] 通过 ModelScope 下载..."
    pip install -q modelscope
    python3 -c "
from modelscope import snapshot_download
snapshot_download(
    'OpenEarthLab/FengWu',
    cache_dir='$MODEL_DIR',
)
"
}

download_wget() {
    echo "[INFO] 通过 wget 直链下载..."
    BASE_URL="https://huggingface.co/OpenEarthLab/FengWu/resolve/main"

    for f in fengwu_v2.onnx fengwu_v1.onnx data_mean.npy data_std.npy; do
        if [ -f "$MODEL_DIR/$f" ]; then
            echo "  [SKIP] $f 已存在"
        else
            echo "  [DOWNLOAD] $f (约 1.8GB)..."
            wget -c --show-progress "$BASE_URL/$f" -O "$MODEL_DIR/$f"
        fi
    done
}

show_manual() {
    echo ""
    echo "============================================"
    echo "  手动下载地址"
    echo "============================================"
    echo ""
    echo "HuggingFace (推荐):"
    echo "  https://huggingface.co/OpenEarthLab/FengWu"
    echo ""
    echo "ModelScope (国内):"
    echo "  https://www.modelscope.cn/models/OpenEarthLab/FengWu"
    echo ""
    echo "需要下载的文件:"
    echo "  - fengwu_v2.onnx   (1.8 GB) — 实时预报用"
    echo "  - fengwu_v1.onnx   (1.8 GB) — ERA5 评估用 (可选)"
    echo "  - data_mean.npy    (680 B)  — 归一化均值"
    echo "  - data_std.npy     (680 B)  — 归一化标准差"
    echo ""
    echo "下载后放到: $MODEL_DIR"
    echo "       或: $MODEL_DIR_WIN"
    echo ""
}

case $choice in
    1) download_hf ;;
    2) download_ms ;;
    3) download_wget ;;
    4) show_manual ;;
    *) show_manual ;;
esac

echo ""
echo "============================================"
echo "  验证模型文件"
echo "============================================"
echo ""

for f in fengwu_v2.onnx data_mean.npy data_std.npy; do
    if [ -f "$MODEL_DIR/$f" ]; then
        size=$(du -h "$MODEL_DIR/$f" | cut -f1)
        echo "  ✅ $f ($size)"
    else
        echo "  ❌ $f — 未下载"
    fi
done

echo ""
echo "Docker Compose 已配置挂载:"
echo "  $MODEL_DIR → /app/model (ro)"
echo ""
echo "启动服务: docker compose up -d fengwu"
