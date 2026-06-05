"""
PyTorch 数据集和 DataLoader
支持: 模拟数据 / WRF 输出 / 在线生成
"""
import logging
from pathlib import Path
from typing import Optional, Callable, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

from .training_data import PhysicsConstrainedGenerator
from .config import CONFIG

logger = logging.getLogger(__name__)


class WeatherDataset(Dataset):
    """
    气象降尺度配对数据集

    返回:
        coarse: (11, Hc, Wc) — 粗网格输入
        fine: (6, Hf, Wf) — 细网格真值
        dem: (1, Hc, Wc) — DEM
    """

    def __init__(self, data_dir: Optional[Path] = None,
                 mode: str = "file",  # "file" | "generator"
                 n_samples: int = 1000,
                 transform: Optional[Callable] = None):
        """
        Args:
            data_dir: 数据目录 (含 coarse_*.npy 和 fine_*.npy)
            mode: "file" 从文件读 | "generator" 在线生成
            n_samples: 样本数 (仅 generator 模式)
            transform: 数据增强
        """
        self.mode = mode
        self.transform = transform
        self.n_samples = n_samples

        if mode == "file":
            self.data_dir = Path(data_dir)
            self.coarse_files = sorted(self.data_dir.glob("coarse_*.npy"))
            self.fine_files = sorted(self.data_dir.glob("fine_*.npy"))
            self.n_samples = len(self.coarse_files)
            logger.info(f"加载 {self.n_samples} 个样本 from {data_dir}")

        elif mode == "generator":
            self.generator = PhysicsConstrainedGenerator()
            self.patterns = ["plain_winter", "summer_heat", "rain_event",
                             "mountain_wave", "city_heat_island"]
            logger.info(f"在线生成模式: {n_samples} 样本")

        else:
            raise ValueError(f"Unknown mode: {mode}")

    def __len__(self) -> int:
        return self.n_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        if self.mode == "file":
            coarse = np.load(self.coarse_files[idx])
            fine = np.load(self.fine_files[idx])
        else:
            pattern = self.patterns[idx % len(self.patterns)]
            coarse, fine, _ = self.generator.generate_pair(pattern)

        # 分离 DEM (索引6)
        dem = coarse[6:7].copy()  # (1, H, W)
        coarse_input = coarse.copy()

        if self.transform:
            coarse_input, fine, dem = self.transform(coarse_input, fine, dem)

        return (torch.from_numpy(coarse_input).float(),
                torch.from_numpy(fine).float(),
                torch.from_numpy(dem).float())

    @staticmethod
    def collate_fn(batch):
        """合并 batch"""
        coarse = torch.stack([b[0] for b in batch])
        fine = torch.stack([b[1] for b in batch])
        dem = torch.stack([b[2] for b in batch])
        return coarse, fine, dem


class WeatherDataModule:
    """
    PyTorch Lightning 风格 DataModule
    管理 train/val/test 数据加载
    """

    def __init__(self, batch_size: int = 16,
                 train_dir: Optional[Path] = None,
                 val_dir: Optional[Path] = None,
                 test_dir: Optional[Path] = None,
                 use_generator: bool = True,
                 num_workers: int = 4):
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.use_generator = use_generator

        from pathlib import Path
        base = Path("/mnt/d/Developer/workplace/py/iteam/trae/data")
        self.train_dir = train_dir or base / "training"
        self.val_dir = val_dir or base / "validation"
        self.test_dir = test_dir or base / "test"

    def train_dataloader(self) -> DataLoader:
        use_gen = self.use_generator or not self.train_dir.exists()
        ds = WeatherDataset(
            data_dir=self.train_dir,
            mode="generator" if use_gen else "file",
            n_samples=3000,
            transform=weather_augmentation(),
        )
        return DataLoader(ds, batch_size=self.batch_size,
                          shuffle=True, num_workers=self.num_workers,
                          collate_fn=WeatherDataset.collate_fn,
                          pin_memory=True)

    def val_dataloader(self) -> DataLoader:
        use_gen = self.use_generator or not self.val_dir.exists()
        ds = WeatherDataset(
            data_dir=self.val_dir,
            mode="generator" if use_gen else "file",
            n_samples=500,
        )
        return DataLoader(ds, batch_size=self.batch_size,
                          shuffle=False, num_workers=self.num_workers,
                          collate_fn=WeatherDataset.collate_fn,
                          pin_memory=True)

    def test_dataloader(self) -> DataLoader:
        use_gen = self.use_generator or not self.test_dir.exists()
        ds = WeatherDataset(
            data_dir=self.test_dir,
            mode="generator" if use_gen else "file",
            n_samples=500,
        )
        return DataLoader(ds, batch_size=self.batch_size,
                          shuffle=False, num_workers=self.num_workers,
                          collate_fn=WeatherDataset.collate_fn,
                          pin_memory=True)


# ── 气象数据增强 ─────────────────────────────────


class weather_augmentation:
    """
    专为气象场设计的数据增强

    成都平原特点:
    - 地形抬升不旋转 (保留 DEM 方向)
    - 温度/风场不能翻转 (物理约束)
    """

    def __init__(self, p: float = 0.5):
        self.p = p

    def __call__(self, coarse, fine, dem):
        if np.random.random() > self.p:
            return coarse, fine, dem

        aug_type = np.random.choice(["noise", "crop", "mixup"])

        if aug_type == "noise":
            # 物理约束的传感器噪声
            noise_std = np.random.uniform(0.01, 0.05)
            noise = np.random.normal(0, noise_std, coarse.shape)
            # 不污染 DEM (索引6)
            noise[6:7] = 0
            coarse = coarse + noise

            noise_f = np.random.normal(0, noise_std * 0.5, fine.shape)
            fine = fine + noise_f

        elif aug_type == "crop":
            # 随机中心裁剪 (保持成都平原主体)
            H, W = coarse.shape[1:]
            crop_h = int(H * np.random.uniform(0.85, 0.95))
            crop_w = int(W * np.random.uniform(0.85, 0.95))
            y0 = np.random.randint(0, H - crop_h)
            x0 = np.random.randint(0, W - crop_w)
            coarse = coarse[:, y0:y0+crop_h, x0:x0+crop_w]
            dem = dem[:, y0:y0+crop_h, x0:x0+crop_w]
            # 上采样回原始大小
            from scipy.ndimage import zoom
            for c in range(coarse.shape[0]):
                coarse[c] = zoom(coarse[c], (H / crop_h, W / crop_w), order=1)
            dem[0] = zoom(dem[0], (H / crop_h, W / crop_w), order=1)

            Hf, Wf = fine.shape[1:]
            crop_hf = int(Hf * crop_h / H)
            crop_wf = int(Wf * crop_w / W)
            y0f = int(y0 * Hf / H)
            x0f = int(x0 * Wf / W)
            fine = fine[:, y0f:y0f+crop_hf, x0f:x0f+crop_wf]
            for c in range(fine.shape[0]):
                fine[c] = zoom(fine[c], (Hf / crop_hf, Wf / crop_wf), order=1)

        elif aug_type == "mixup":
            # 两个样本插值 (训练时在 collate 里做，这里先占位)
            pass

        return coarse, fine, dem
