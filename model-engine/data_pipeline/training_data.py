"""
训练数据生成器
为 CNN 订正器和 U-Net 降尺度器生成配对训练数据


数据配对:
  coarse_input (50×50, 3km) → ground_truth (150×150, 1km)


数据来源:
  1. 模拟: WRF 物理约束合成 (开发和调参用)
  2. 真实: WRF 历史输出 → 3km ↔ 1km 配对
  3. 真实: ERA5 重分析 → 降尺度配对
"""
import logging
from pathlib import Path
from typing import Optional, Tuple, List

import numpy as np
import xarray as xr

from .config import CONFIG

logger = logging.getLogger(__name__)

DATA_DIR = Path("/mnt/d/Developer/workplace/py/iteam/trae/data")
TRAIN_DIR = DATA_DIR / "training"
VAL_DIR = DATA_DIR / "validation"
TEST_DIR = DATA_DIR / "test"

# ── 物理约束的合成数据生成 ──────────────────────


class PhysicsConstrainedGenerator:
    """
    基于物理知识的合成训练数据
    模拟成都平原真实气象特征:
    - 西侧龙门山抬升导致的地形风
    - 城市热岛效应
    - 盆地山谷风日变化
    - 短时强降水前兆
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.domain = CONFIG.domain

    def generate_pair(self, pattern: str = "random") -> Tuple[np.ndarray, np.ndarray]:
        """
        生成一组配对数据 (粗网格 → 细网格)

        Returns:
            coarse: (11, Hc, Wc) — 3km 粗网格
            fine: (6, Hf, Wf) — 1km 细网格真值
        """
        Hc, Wc = self.domain.coarse_grid
        Hf, Wf = self.domain.fine_grid

        # 选择一个天气模式
        patterns = {
            "plain_winter": self._plain_winter,
            "summer_heat": self._summer_heat,
            "rain_event": self._rain_event,
            "mountain_wave": self._mountain_wave,
            "city_heat_island": self._city_heat_island,
        }
        if pattern == "random":
            pattern = self.rng.choice(list(patterns.keys()))
        generator = patterns.get(pattern, self._plain_winter)

        # 生成粗网格和细网格
        coarse, fine, _ = generator(Hc, Wc, Hf, Wf)
        return coarse, fine

    def _add_dem(self, H: int, W: int) -> np.ndarray:
        """成都平原西高东低的简化 DEM"""
        y, x = np.mgrid[0:H, 0:W]
        dem = 500 + 400 * (1 - y / H) - 200 * (x / W)
        dem += self.rng.normal(0, 20, (H, W))  # 小尺度地形
        return dem

    def _plain_winter(self, Hc, Wc, Hf, Wf):
        """冬季静稳天气: 弱风 + 逆温层"""
        u10 = self.rng.normal(1.0, 0.5, (Hc, Wc))
        v10 = self.rng.normal(0.3, 0.3, (Hc, Wc))
        t2m = self.rng.normal(280, 3, (Hc, Wc))  # 7°C
        rh2m = self.rng.normal(65, 10, (Hc, Wc))
        ps = self.rng.normal(1015, 3, (Hc, Wc))
        blh = self.rng.normal(300, 100, (Hc, Wc))
        dem = self._add_dem(Hc, Wc)

        coarse = np.stack([u10, v10, t2m, rh2m, ps, blh, dem,
                           u10*0.1, v10*0.1, t2m*0.01, ps*0.001], axis=0)

        # 细网格: 添加小尺度湍流
        u10_f = self._upscale_add_noise(u10, Hf, Wf, 0.3)
        v10_f = self._upscale_add_noise(v10, Hf, Wf, 0.2)
        t2m_f = self._upscale_add_noise(t2m, Hf, Wf, 1.0)
        rh2m_f = self._upscale_add_noise(rh2m, Hf, Wf, 5)
        ps_f = self._upscale_add_noise(ps, Hf, Wf, 1)
        blh_f = self._upscale_add_noise(blh, Hf, Wf, 50)

        fine = np.stack([u10_f, v10_f, t2m_f, rh2m_f, ps_f, blh_f], axis=0)
        return coarse, fine, dem

    def _summer_heat(self, Hc, Wc, Hf, Wf):
        """夏季高温: 强辐射 + 热低压"""
        u10 = self.rng.normal(2.0, 1.0, (Hc, Wc))
        v10 = self.rng.normal(0.5, 0.8, (Hc, Wc))
        t2m = self.rng.normal(305, 2, (Hc, Wc))  # 32°C
        rh2m = self.rng.normal(50, 8, (Hc, Wc))
        ps = self.rng.normal(998, 2, (Hc, Wc))
        blh = self.rng.normal(800, 200, (Hc, Wc))

        coarse = np.stack([u10, v10, t2m, rh2m, ps, blh,
                           self._add_dem(Hc, Wc),
                           u10*0.1, v10*0.1, t2m*0.01, ps*0.001], axis=0)

        fine = np.stack([
            self._upscale_add_noise(u10, Hf, Wf, 0.5),
            self._upscale_add_noise(v10, Hf, Wf, 0.4),
            self._upscale_add_noise(t2m, Hf, Wf, 1.5),
            self._upscale_add_noise(rh2m, Hf, Wf, 4),
            self._upscale_add_noise(ps, Hf, Wf, 1),
            self._upscale_add_noise(blh, Hf, Wf, 100),
        ], axis=0)
        return coarse, fine, None

    def _rain_event(self, Hc, Wc, Hf, Wf):
        """降水事件: 强风 + 高湿 + 低压"""
        # 模拟锋面过境
        front_x = self.rng.integers(Wc // 3, 2 * Wc // 3)
        u10 = -self.rng.normal(5, 2, (Hc, Wc))
        v10 = self.rng.normal(3, 1, (Hc, Wc))
        # 锋面前后温度梯度
        t2m = 285 - 10 * (np.arange(Wc)[None, :] > front_x) + self.rng.normal(0, 1, (Hc, Wc))
        rh2m = self.rng.normal(85, 5, (Hc, Wc))
        ps = self.rng.normal(1005, 5, (Hc, Wc))
        # 锋面附近 PBL 抬升
        dem_c = self._add_dem(Hc, Wc)
        blh = self.rng.normal(400 + 300 * (np.abs(np.arange(Wc)[None, :] - front_x) < 5),
                              100, (Hc, Wc))

        coarse = np.stack([u10, v10, t2m, rh2m, ps, blh, dem_c,
                           u10*0.1, v10*0.1, t2m*0.01, ps*0.001], axis=0)
        fine = np.stack([
            self._upscale_add_noise(u10, Hf, Wf, 1.0),
            self._upscale_add_noise(v10, Hf, Wf, 0.8),
            self._upscale_add_noise(t2m, Hf, Wf, 2),
            self._upscale_add_noise(rh2m, Hf, Wf, 5),
            self._upscale_add_noise(ps, Hf, Wf, 2),
            self._upscale_add_noise(blh, Hf, Wf, 80),
        ], axis=0)
        return coarse, fine, None

    def _mountain_wave(self, Hc, Wc, Hf, Wf):
        """山地波动: 龙门山地形抬升"""
        dem_c = self._add_dem(Hc, Wc)
        dem_f = self._add_dem(Hf, Wf)
        # 地形抬升触发波动
        uplift = dem_c / 500.0
        u10 = 2 + 3 * uplift + self.rng.normal(0, 0.5, (Hc, Wc))
        v10 = 1 + uplift * 0.5 + self.rng.normal(0, 0.3, (Hc, Wc))
        t2m = 290 - 5 * (dem_c - 500) / 500 + self.rng.normal(0, 1, (Hc, Wc))
        rh2m = 60 + 15 * uplift + self.rng.normal(0, 5, (Hc, Wc))
        ps = 1013 - 30 * (dem_c - 500) / 500 + self.rng.normal(0, 2, (Hc, Wc))
        blh = 500 + 300 * uplift + self.rng.normal(0, 100, (Hc, Wc))

        coarse = np.stack([u10, v10, t2m, rh2m, ps, blh, dem_c,
                           u10*0.1, v10*0.1, t2m*0.01, ps*0.001], axis=0)
        fine = np.stack([
            self._upscale_add_noise(u10, Hf, Wf, 0.5),
            self._upscale_add_noise(v10, Hf, Wf, 0.3),
            self._upscale_add_noise(t2m, Hf, Wf, 1.5),
            self._upscale_add_noise(rh2m, Hf, Wf, 5),
            self._upscale_add_noise(ps, Hf, Wf, 1.5),
            self._upscale_add_noise(blh, Hf, Wf, 80),
        ], axis=0)

        # 在粗网格输入里额外注入 DEM 信息
        dem_downscaled = np.resize(dem_c, (1, Hc, Wc))
        coarse = np.concatenate([coarse[:6], dem_downscaled,
                                 coarse[6:]], axis=0)
        return coarse, fine, dem_f

    def _city_heat_island(self, Hc, Wc, Hf, Wf):
        """城市热岛: 成都中心高温"""
        cy, cx = Hc // 2, Wc // 2
        y, x = np.ogrid[:Hc, :Wc]
        # 城市热岛高斯核
        heat_kernel = np.exp(-((y - cy)**2 + (x - cx)**2) / (2 * 8**2))
        u10 = self.rng.normal(1.5, 0.8, (Hc, Wc))
        v10 = self.rng.normal(0.5, 0.6, (Hc, Wc))
        t2m = 288 + 6 * heat_kernel + self.rng.normal(0, 0.5, (Hc, Wc))  # 15°C +6°C 热岛
        rh2m = 55 - 10 * heat_kernel + self.rng.normal(0, 5, (Hc, Wc))  # 热岛干
        ps = self.rng.normal(1008, 2, (Hc, Wc))
        blh = 400 + 200 * heat_kernel + self.rng.normal(0, 50, (Hc, Wc))

        coarse = np.stack([u10, v10, t2m, rh2m, ps, blh,
                           self._add_dem(Hc, Wc),
                           u10*0.1, v10*0.1, t2m*0.01, ps*0.001], axis=0)
        fine = np.stack([
            self._upscale_add_noise(u10, Hf, Wf, 0.3),
            self._upscale_add_noise(v10, Hf, Wf, 0.2),
            self._upscale_add_noise(t2m, Hf, Wf, 1.0),
            self._upscale_add_noise(rh2m, Hf, Wf, 3),
            self._upscale_add_noise(ps, Hf, Wf, 1),
            self._upscale_add_noise(blh, Hf, Wf, 40),
        ], axis=0)
        return coarse, fine, None

    def _upscale_add_noise(self, coarse: np.ndarray, Hf: int, Wf: int,
                           noise_std: float) -> np.ndarray:
        """粗网格上采样 + 物理约束的随机扰动"""
        from scipy.ndimage import zoom
        scale_h = Hf / coarse.shape[0]
        scale_w = Wf / coarse.shape[1]
        up = zoom(coarse, (scale_h, scale_w), order=1)

        # 小尺度扰动 (平滑空间相关噪声)
        noise = self.rng.normal(0, noise_std, (Hf + 4, Wf + 4))
        from scipy.ndimage import gaussian_filter
        noise = gaussian_filter(noise, sigma=2)[2:-2, 2:-2]
        return up + noise

    def generate_dataset(self, n_pairs: int = 1000,
                         save_dir: Optional[Path] = None) -> List[Tuple[np.ndarray, np.ndarray]]:
        """批量生成训练数据集"""
        save_dir = save_dir or TRAIN_DIR
        save_dir.mkdir(parents=True, exist_ok=True)

        patterns = ["plain_winter", "summer_heat", "rain_event",
                    "mountain_wave", "city_heat_island"]

        pairs = []
        for i in range(n_pairs):
            pattern = self.rng.choice(patterns)
            coarse, fine = self.generate_pair(pattern)

            if save_dir:
                np.save(save_dir / f"coarse_{i:05d}.npy", coarse)
                np.save(save_dir / f"fine_{i:05d}.npy", fine)

            pairs.append((coarse, fine))
            if (i + 1) % 200 == 0:
                logger.info(f"  生成 {i+1}/{n_pairs} 组")

        return pairs


# ── 真实数据加载 (WRF 历史输出) ─────────────────


def load_wrf_output(file_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    从 WRF NetCDF 输出加载配对数据

    WRF 嵌套输出:
      - d01: 3km 父域 → coarse input
      - d02: 1km 子域 → fine target

    Args:
        file_path: WRF 输出文件路径 (*.nc)
    Returns:
        coarse_input: (11, 50, 50)
        fine_target:  (6, 150, 150)
    """
    ds = xr.open_dataset(file_path)
    Hc, Wc = CONFIG.domain.coarse_grid
    Hf, Wf = CONFIG.domain.fine_grid

    # 裁剪到成都平原区域
    lat_slice = slice(CONFIG.domain.lat_center - 0.75, CONFIG.domain.lat_center + 0.75)
    lon_slice = slice(CONFIG.domain.lon_center - 0.75, CONFIG.domain.lon_center + 0.75)

    def extract_var(ds, varname, target_shape):
        if varname in ds:
            data = ds[varname].sel(south_north=lat_slice, west_east=lon_slice).values
            from scipy.ndimage import zoom
            sy, sx = target_shape[0] / data.shape[0], target_shape[1] / data.shape[1]
            return zoom(data, (sy, sx), order=1)
        return np.zeros(target_shape)

    coarse_vars = ["U10", "V10", "T2", "Q2", "PSFC", "PBLH"]
    fine_vars = ["U10", "V10", "T2", "Q2", "PSFC", "PBLH"]

    coarse = np.stack([extract_var(ds, v, (Hc, Wc)) for v in coarse_vars], axis=0)
    fine = np.stack([extract_var(ds, v, (Hf, Wf)) for v in fine_vars], axis=0)

    # 添加 DEM 和标准化辅助通道
    dem = _load_dem(Hc, Wc)
    coarse_extra = np.stack([
        dem,
        coarse[0] / 10, coarse[1] / 10,
        coarse[2] / 300, coarse[4] / 1000
    ], axis=0)
    coarse = np.concatenate([coarse, coarse_extra], axis=0)

    return coarse, fine


def _load_dem(H: int, W: int) -> np.ndarray:
    """加载或生成 DEM"""
    from scipy.ndimage import zoom
    base_dem = np.fromfunction(lambda i, j: 500 + 400 * (1 - i / 50) - 200 * (j / 50), (50, 50))
    return zoom(base_dem, (H / 50, W / 50), order=1)


# ── 批量数据生成入口 ────────────────────────────


def generate_all_training_data(n_train: int = 3000,
                               n_val: int = 500,
                               n_test: int = 500):
    """生成全部训练/验证/测试数据"""
    gen = PhysicsConstrainedGenerator(seed=42)

    logger.info(f"生成训练数据 {n_train} 组 → {TRAIN_DIR}")
    gen.generate_dataset(n_train, TRAIN_DIR)

    logger.info(f"生成验证数据 {n_val} 组 → {VAL_DIR}")
    gen.generate_dataset(n_val, VAL_DIR)

    logger.info(f"生成测试数据 {n_test} 组 → {TEST_DIR}")
    gen.generate_dataset(n_test, TEST_DIR)

    logger.info(f"✅ 全部生成完成: 训练 {n_train} + 验证 {n_val} + 测试 {n_test}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    generate_all_training_data()
