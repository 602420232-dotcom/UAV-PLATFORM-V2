#!/usr/bin/env python3
"""
XGBoost 残差订正器 — 训练脚本

训练: 轻量级梯度提升树，对 CNN 订正后的结果进一步订正
输入: 粗网格特征 → 输出: 残差场


用法:
  python scripts/train_xgboost.py
"""
from scripts.train_config import CONFIG
import sys
import logging
from pathlib import Path

import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parent.parent))


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_training_data(data_dir: Path, limit: int = 2000):
    """加载训练数据"""
    X_list, y_u_list, y_v_list, y_t_list = [], [], [], []

    files = sorted(data_dir.glob("coarse_*.npy"))[:limit]

    if not files:
        logger.warning("未找到训练数据，将使用合成数据")
        return None, None, None, None

    logger.info(f"加载 {len(files)} 组数据")

    for coarse_file in files:
        coarse = np.load(coarse_file)
        fine_file = data_dir / coarse_file.name.replace("coarse_", "fine_")
        fine = np.load(fine_file)

        # 展平为特征向量 (每个像素点一个样本)
        _H, _W = coarse.shape[1], coarse.shape[2]
        X = coarse[:6].reshape(6, -1).T

        y_u = fine[0].reshape(-1)
        y_v = fine[1].reshape(-1)
        y_t = fine[2].reshape(-1)

        X_list.append(X)
        y_u_list.append(y_u)
        y_v_list.append(y_v)
        y_t_list.append(y_t)

    X = np.concatenate(X_list, axis=0)
    y_u = np.concatenate(y_u_list, axis=0)
    y_v = np.concatenate(y_v_list, axis=0)
    y_t = np.concatenate(y_t_list, axis=0)

    logger.info(f"特征矩阵形状: {X.shape}")
    return X, y_u, y_v, y_t


def train_single_model(X, y, variable_name: str, model_dir: Path):
    """训练单个变量的 XGBoost 模型"""
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = xgb.XGBRegressor(
        n_estimators=CONFIG.xgboost_n_estimators,
        max_depth=CONFIG.xgboost_max_depth,
        learning_rate=CONFIG.xgboost_lr,
        random_state=42,
        n_jobs=-1
    )

    logger.info(f"训练 {variable_name} 模型")
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    val_score = model.score(X_val, y_val)
    logger.info(f"{variable_name} R² = {val_score:.4f}")

    model_path = model_dir / f"xgboost_{variable_name}.json"
    model.save_model(str(model_path))
    logger.info(f"保存模型: {model_path}")

    return model


def main():
    model_dir = Path("model-engine/weights")
    data_dir = Path("model-engine/data/training")
    model_dir.mkdir(parents=True, exist_ok=True)

    X, y_u, y_v, y_t = load_training_data(data_dir)

    if X is None:
        logger.info("生成合成数据")
        n_samples = 10000
        X = np.random.randn(n_samples, 6)
        y_u = np.random.randn(n_samples)
        y_v = np.random.randn(n_samples)
        y_t = np.random.randn(n_samples)

    train_single_model(X, y_u, "u10", model_dir)
    train_single_model(X, y_v, "v10", model_dir)
    train_single_model(X, y_t, "t2m", model_dir)

    logger.info("✅ XGBoost 训练完成！")


if __name__ == "__main__":
    main()
