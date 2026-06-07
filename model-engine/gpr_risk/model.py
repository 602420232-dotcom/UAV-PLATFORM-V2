"""
GPR 贝叶斯风险方差场
基于高斯过程回归的不确定性量化

输入: U-Net 残差场 (预测 - 真值)
输出: 风险方差场 + 置信区间

实现: GPyTorch (基于 PyTorch 的高斯过程库)
"""
import logging
import torch
from dataclasses import dataclass
from typing import Optional, Tuple
import gpytorch  # pyright: ignore[reportMissingImports]
from gpytorch.means import ConstantMean  # pyright: ignore[reportMissingImports]
from gpytorch.kernels import RBFKernel, ScaleKernel  # pyright: ignore[reportMissingImports]
from gpytorch.distributions import MultivariateNormal  # pyright: ignore[reportMissingImports]
from scipy.stats import norm

logger = logging.getLogger(__name__)


@dataclass
class GPRConfig:
    """高斯过程配置"""
    kernel_type: str = "rbf"      # rbf | spectral | product
    lr: float = 0.01
    n_iter: int = 200
    n_inducing: int = 500         # 诱导点数量
    batch_size: int = 256
    device: str = "cuda"


class GPRegressionModel(gpytorch.models.ExactGP):
    """精确高斯过程回归"""

    def __init__(self, train_x, train_y, likelihood):
        super().__init__(train_x, train_y, likelihood)
        self.mean_module = ConstantMean()
        self.covar_module = ScaleKernel(RBFKernel())

    def forward(self, x):
        mean = self.mean_module(x)
        covar = self.covar_module(x)
        return MultivariateNormal(mean, covar)


class SparseGPModel(gpytorch.models.ApproximateGP):
    """变分稀疏高斯过程（大规模数据用）"""

    def __init__(self, inducing_points):
        variational_dist = gpytorch.variational.CholeskyVariationalDistribution(
            inducing_points.size(0))
        variational_strategy = gpytorch.variational.VariationalStrategy(
            self, inducing_points, variational_dist, learn_inducing_locations=True)
        super().__init__(variational_strategy)
        self.mean_module = ConstantMean()
        self.covar_module = ScaleKernel(RBFKernel())

    def forward(self, x):
        mean = self.mean_module(x)
        covar = self.covar_module(x)
        return MultivariateNormal(mean, covar)


class GPRiskEstimator:
    """
    高斯过程风险场估计器
    — 学习 U-Net 预测误差的空间分布
    — 预测未采样位置的误差方差
    — 输出: 标准风险场 (μ, σ²)
    """

    def __init__(self, config: Optional[GPRConfig] = None):
        self.config = config or GPRConfig()
        self.likelihood = None
        self.model = None
        self.trained = False

    def _prepare_data(self, residual: torch.Tensor,
                      coords: Optional[torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor]:
        """将残差场转为训练数据 (N, 2) -> (N,)"""
        B, C, H, W = residual.shape
        if coords is None:
            # 自动生成格点坐标
            y_grid, x_grid = torch.meshgrid(
                torch.linspace(0, 1, H, device=residual.device),
                torch.linspace(0, 1, W, device=residual.device),
                indexing="ij")
            coords = torch.stack([x_grid.flatten(), y_grid.flatten()], dim=-1)

        # 展平残差 (只取第一通道用于 GPR)
        values = residual[:, 0].reshape(B, -1).T  # (N, B)
        return coords, values

    def fit(self, residual: torch.Tensor, coords: Optional[torch.Tensor] = None):
        """
        拟合高斯过程

        Args:
            residual: U-Net 预测残差 (B, C, H, W)
            coords: 格点坐标 (N, 2) 或 None (自动生成)
        """
        coords, values = self._prepare_data(residual, coords)
        N = coords.shape[0]

        if N > self.config.n_inducing:
            # 使用稀疏GP
            inducing = coords[torch.randperm(N)[:self.config.n_inducing]]
            self.likelihood = gpytorch.likelihoods.GaussianLikelihood()
            self.model = SparseGPModel(inducing)
        else:
            self.likelihood = gpytorch.likelihoods.GaussianLikelihood()
            self.model = GPRegressionModel(coords, values[:, 0], self.likelihood)

        self.model.train()
        self.likelihood.train()

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.config.lr)
        mll = gpytorch.mlls.ExactMarginalLogLikelihood(self.likelihood, self.model)

        for i in range(self.config.n_iter):
            optimizer.zero_grad()
            output = self.model(coords)
            loss = -mll(output, values[:, 0])
            loss.backward()
            optimizer.step()

            if i % 50 == 0:
                logger.info(f"  [GPR] iter {i:4d}/{self.config.n_iter}  loss={loss.item():.4f}")

        self.trained = True

    def predict(self, coords: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        预测风险场

        Args:
            coords: 查询点坐标 (M, 2)

        Returns:
            mean: 预测均值 (M, )
            variance: 预测方差 (M, ) — 高方差 = 高风险
        """
        if not self.trained:
            raise RuntimeError("GPR not fitted yet")

        assert self.model is not None
        assert self.likelihood is not None

        self.model.eval()
        self.likelihood.eval()

        with torch.no_grad(), gpytorch.settings.fast_pred_var():
            pred = self.likelihood(self.model(coords))
            return pred.mean, pred.variance

    def risk_field(self, fine_grid: Tuple[int, int],
                   device: str = "cuda") -> torch.Tensor:
        """
        生成完整风险方差场

        Args:
            fine_grid: (H, W) 目标网格大小
            device: 计算设备

        Returns:
            risk_map: 风险场 (1, H, W) — 值越大越危险
        """
        H, W = fine_grid
        y, x = torch.meshgrid(
            torch.linspace(0, 1, H, device=device),
            torch.linspace(0, 1, W, device=device),
            indexing="ij")
        coords = torch.stack([x.flatten(), y.flatten()], dim=-1)

        _, variance = self.predict(coords)
        return variance.reshape(1, H, W)


def compute_risk_score(mean: torch.Tensor, variance: torch.Tensor,
                       wind_threshold: float = 10.0) -> torch.Tensor:
    """
    综合风险评分

    Risk = α · 风切变 + β · 方差 + γ · 超阈值概率

    Args:
        mean: GPR 预测均值 (风场订正)
        variance: GPR 预测方差
        wind_threshold: 风速阈值 (m/s)

    Returns:
        risk: 综合风险 (越高越危险)
    """
    # 风速均值
    wind_speed = torch.sqrt(mean[..., 0]**2 + mean[..., 1]**2)
    # 超阈值概率 (假设高斯分布)
    exceed_prob = torch.tensor(
        norm.sf(
            wind_speed.cpu().numpy(),
            loc=mean.cpu(),
            scale=torch.sqrt(variance).cpu()))
    exceed_prob = exceed_prob.to(mean.device)

    risk = 0.3 * wind_speed + 0.4 * torch.sqrt(variance) + 0.3 * exceed_prob
    return risk
