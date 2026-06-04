# 模型权重目录

训练好的模型权重文件存放在此目录。

## 文件命名规范

| 文件 | 模型 | 来源 |
|------|------|------|
| `cnn_corrector.pth` | CNN 气象订正器 | `scripts/train_cnn.py` |
| `unet_downscaler.pth` | U-Net 降尺度 | `scripts/train_unet.py` |
| `xgboost_u10.json` | XGBoost 风场 U 订正 | XGBoost 训练 |
| `xgboost_v10.json` | XGBoost 风场 V 订正 | XGBoost 训练 |
| `xgboost_t2m.json` | XGBoost 温度订正 | XGBoost 训练 |

## 训练方式

```bash
# 自动训练所有模型
./scripts/auto_train.sh

# 或单独训练
python scripts/train_cnn.py --epochs 100
python scripts/train_unet.py --epochs 100
```

权重文件生成后，API 服务会自动加载它们进行推理。
