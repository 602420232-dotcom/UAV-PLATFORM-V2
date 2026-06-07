#!/usr/bin/env python3
"""
CNN 空间订正器 — 训练脚本

训练: CNN 订正粗网格预报 (3km → 3km 误差订正)
输入: 粗网格场 (11ch) + DEM (1ch) → 输出: 订正后场 (6ch)


用法:
  python scripts/train_cnn.py                    # 模拟数据训练
  python scripts/train_cnn.py --real-data ./data  # 真实数据
"""
from data_pipeline.dataset import WeatherDataModule
from cnn_corrector.model import CNNCorrector, CNNConfig
import sys
import logging
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard.writer import SummaryWriter

sys.path.insert(0, str(Path(__file__).parent.parent))


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class Trainer:
    """CNN 订正器训练器"""

    def __init__(self, config: Optional[CNNConfig] = None, device: str = "cuda"):
        self.device = device if torch.cuda.is_available() else "cpu"
        logger.info(f"设备: {self.device}")

        self.config = config or CNNConfig()
        self.model = CNNCorrector(self.config).to(self.device)
        self.optimizer = optim.AdamW(self.model.parameters(), lr=1e-3, weight_decay=1e-4)
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=50)
        self.criterion = nn.MultiScaleLoss() if hasattr(nn, 'MultiScaleLoss') else self._combined_loss  # pyright: ignore[reportAttributeAccessIssue]
        self.writer = SummaryWriter("runs/cnn_corrector")

        self.best_val_loss = float("inf")

    @staticmethod
    def _combined_loss(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """MSE + MAE 混合损失"""
        mse = nn.MSELoss()(pred, target)
        mae = nn.L1Loss()(pred, target)
        return 0.7 * mse + 0.3 * mae

    def train_epoch(self, loader: DataLoader) -> float:
        self.model.train()
        total_loss = 0.0
        for batch_idx, (coarse, fine, dem) in enumerate(loader):
            coarse, fine, dem = coarse.to(self.device), fine.to(self.device), dem.to(self.device)

            self.optimizer.zero_grad()
            pred = self.model(coarse, dem)
            loss = self.criterion(pred, fine)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()

            total_loss += loss.item()
            if batch_idx % 10 == 0:
                logger.info(f"  batch {batch_idx:4d}/{len(loader)}  loss={loss.item():.6f}")
        return total_loss / len(loader)

    @torch.no_grad()
    def validate(self, loader: DataLoader) -> float:
        self.model.eval()
        total_loss = 0.0
        for coarse, fine, dem in loader:
            coarse, fine, dem = coarse.to(self.device), fine.to(self.device), dem.to(self.device)
            pred = self.model(coarse, dem)
            total_loss += self.criterion(pred, fine).item()
        return total_loss / len(loader)

    @torch.no_grad()
    def validate_physical(self, loader: DataLoader) -> dict:
        """物理指标验证"""
        self.model.eval()
        metrics = {"rmse_u": 0.0, "rmse_v": 0.0, "rmse_t": 0.0,
                   "bias_u": 0.0, "bias_v": 0.0, "bias_t": 0.0}
        count = 0
        for coarse, fine, dem in loader:
            coarse, fine, dem = coarse.to(self.device), fine.to(self.device), dem.to(self.device)
            pred = self.model(coarse, dem)
            for i, key in enumerate(["rmse_u", "rmse_v", "rmse_t"]):
                diff = pred[:, i] - fine[:, i]
                metrics[key] += torch.sqrt((diff ** 2).mean()).item()
            for i, key in enumerate(["bias_u", "bias_v", "bias_t"]):
                metrics[key] += (pred[:, i] - fine[:, i]).mean().item()
            count += 1
        return {k: v / count for k, v in metrics.items()}

    def train(self, n_epochs: int = 100):
        logger.info(f"开始训练: {n_epochs} epochs")
        dm = WeatherDataModule(batch_size=16, use_generator=True)
        train_loader = dm.train_dataloader()
        val_loader = dm.val_dataloader()

        for epoch in range(n_epochs):
            train_loss = self.train_epoch(train_loader)
            val_loss = self.validate(val_loader)
            self.scheduler.step()

            self.writer.add_scalar("loss/train", train_loss, epoch)
            self.writer.add_scalar("loss/val", val_loss, epoch)
            self.writer.add_scalar("lr", self.optimizer.param_groups[0]["lr"], epoch)

            logger.info(f"Epoch {epoch + 1:3d}/{n_epochs}  "
                        f"train={train_loss:.6f}  val={val_loss:.6f}")

            if (epoch + 1) % 10 == 0:
                phys = self.validate_physical(val_loader)
                logger.info(f"  物理指标: {phys}")

            # 保存 best
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": self.model.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "val_loss": val_loss,
                    "config": self.config,
                }, "model-engine/checkpoints/cnn_corrector_best.pth")
                logger.info(f"  🏆 Best model saved (val_loss={val_loss:.6f})")

        self.writer.close()
        logger.info("训练完成!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--real-data", type=str, default=None)
    args = parser.parse_args()

    cfg = CNNConfig()
    cfg.lr = args.lr

    trainer = Trainer(cfg)
    trainer.train(n_epochs=args.epochs)
