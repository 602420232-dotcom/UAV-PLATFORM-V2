#!/bin/bash
# model-engine 依赖安装脚本
pip install \
    numpy==1.26.0 \
    pandas==2.1.0 \
    xarray==2024.1.0 \
    cfgrib==0.9.10 \
    netCDF4==1.6.5 \
    torch==2.2.0 \
    torchvision==0.17.0 \
    pytorch-lightning==2.1.0 \
    gpytorch==1.11 \
    scikit-learn==1.3.0 \
    scipy==1.11.4 \
    fastapi==0.109.0 \
    uvicorn==0.27.0 \
    pydantic==2.5.0 \
    httpx==0.26.0 \
    requests==2.31.0 \
    matplotlib==3.8.2
