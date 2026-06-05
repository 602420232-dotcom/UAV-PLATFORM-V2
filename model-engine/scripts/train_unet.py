#!/usr/bin/env python3
"""
U-Net 降尺度器 — 训练脚本

训练: U-Net 3km → 1km 超分辨率 + 多源观测同化
输入: CNN 订正后场 (6ch, 50×50)
输出: 精细场 (6ch, 150×150)


策略:
  1. 预训练: 纯降尺度 (MSE)
  2. 微调: 加入观测同化 (注意力门)
"""
import sys
import logging
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

sys.path.insert(0, str(Path(__file__).parent.parent))
from unet_downscaler.model import UNetDownscaler, UNetConfig
from data_pipeline.dataset import WeatherDataModule


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class UNetTrainer:
    """U-Net 降尺度训练器"""

    def __init__(self, config: UNetConfig = None, device: str = "cuda"):
        self.device = device if torch.cuda.is_available() else "cpu"
        logger.info(f"设备: {self.device}")

        self.config = config or UNetConfig()
        self.model = UNetDownscaler(self.config).to(self.device)
        self.optimizer = optim.AdamW(self.model.parameters(), lr=1e-3, weight_decay=1e-5)
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=100)
        self.writer = SummaryWriter("runs/unet_downscaler")

        self.best_val_loss = float("inf")

    def _loss(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """多尺度损失: 逐像素 + 梯度 + 感知"""
        # MSE
        mse = nn.MSELoss()(pred, target)

        # 梯度损失 (边缘保留)
        gx_pred = pred[:, :, :, 1:] - pred[:, :, :, :-1]
        gy_pred = pred[:, :, 1:, :] - pred[:, :, :-1, :]
        gx_tar = target[:, :, :, 1:] - target[:, :, :, :-1]
        gy_tar = target[:, :, 1:, :] - target[:, :, :-1, :]
        grad_loss = nn.L1Loss()(gx_pred, gx_tar) + nn.L1Loss()(gy_pred, gy_tar)

        # 低频损失 (小波或高斯模糊后)
        blur_pred = nn.functional.avg_pool2d(pred, kernel_size=3, stride=1, padding=1)
        blur_tar = nn.functional.avg_pool2d(target, kernel_size=3, stride=1, padding=1)
        lowfreq_loss = nn.L1Loss()(blur_pred, blur_tar)

        return mse + 0.1 * grad_loss + 0.05 * lowfreq_loss

    def train_epoch(self, loader: DataLoader) -> float:
        self.model.train()
        total_loss = 0.0
        for batch_idx, (coarse, fine, _) in enumerate(loader):
            coarse, fine = coarse.to(self.device), fine.to(self.device)
            # U-Net 输入是已订正场 → 使用 coarse[:, :6] (6通道)
            x = coarse[:, :6].to(self.device)

            self.optimizer.zero_grad()

            # 模拟观测 (训练时 50% 概率注入)
            obs = None
            obs_mask = None
            if self.config.use_attention and torch.rand(1) > 0.5:
                obs = torch.randn_like(fine[:, :4, ::3, ::3]) * 0.1
                obs_mask = (torch.rand_like(obs[:, :1]) > 0.95).float()

            pred = self.model(x, obs, obs_mask)
            loss = self._loss(pred, fine)
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
        for coarse, fine, _ in loader:
            coarse, fine = coarse.to(self.device), fine.to(self.device)
            x = coarse[:, :6]
            pred = self.model(x)
            total_loss += self._loss(pred, fine).item()
        return total_loss / len(loader)

    @torch.no_grad()
    def validate_physical(self, loader: DataLoader) -> dict:
        """物理指标验证"""
        self.model.eval()
        metrics = {"psnr": 0.0, "ssim": 0.0, "rmse": 0.0, "bias": 0.0}
        count = 0
        for coarse, fine, _ in loader:
            coarse, fine = coarse.to(self.device), fine.to(self.device)
            x = coarse[:, :6]
            pred = self.model(x)

            # PSNR-like (气象场专用)
            for b in range(pred.shape[0]):
                for c in range(pred.shape[1]):
                    mse_val = ((pred[b, c] - fine[b, c]) ** 2).mean()
                    max_val = fine[b, c].max() - fine[b, c].min() + 1e-8
                    psnr = 20 * torch.log10(max_val / (torch.sqrt(mse_val) + 1e-8))
                    metrics["psnr"] += psnr.item()
                    metrics["rmse"] += torch.sqrt(mse_val).item()
                    metrics["bias"] += (pred[b, c] - fine[b, c]).mean().item()
                    count += 1

        return {k: v / count for k, v in metrics.items()}

    def train(self, n_epochs: int = 150):
        logger.info(f"开始 U-Net 训练: {n_epochs} epochs")
        dm = WeatherDataModule(batch_size=8, use_generator=True)
        train_loader = dm.train_dataloader()
        val_loader = dm.val_dataloader()

        for epoch in range(n_epochs):
            train_loss = self.train_epoch(train_loader)
            val_loss = self.validate(val_loader)
            self.scheduler.step()

            self.writer.add_scalar("loss/train", train_loss, epoch)
            self.writer.add_scalar("loss/val", val_loss, epoch)

            logger.info(f"Epoch {epoch+1:3d}/{n_epochs}  "
                        f"train={train_loss:.6f}  val={val_loss:.6f}")

            if (epoch + 1) % 20 == 0:
                phys = self.validate_physical(val_loader)
                logger.info(f"  物理指标: PSNR={phys['psnr']:.2f}  "
                            f"RMSE={phys['rmse']:.4f}  Bias={phys['bias']:.4f}")

            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": self.model.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "val_loss": val_loss,
                    "config": self.config,
                }, "model-engine/checkpoints/unet_downscaler_best.pth")
                logger.info(f"  🏆 Best model saved (val_loss={val_loss:.6f})")

        self.writer.close()
        logger.info("U-Net 训练完成!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    cfg = UNetConfig()
    cfg.lr = args.lr
    trainer = UNetTrainer(cfg)
    trainer.train(n_epochs=args.epochs)
