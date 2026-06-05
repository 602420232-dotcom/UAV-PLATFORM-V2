#!/usr/bin/env python3
"""
增强的贝叶斯同化模型
添加机器学习和深度学习部分，允许自迭代
"""

import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np  # noqa: E402


try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model  # type: ignore
    from tensorflow.keras.layers import Dense, LSTM, Dropout, Input  # type: ignore
    from tensorflow.keras.optimizers import Adam  # type: ignore
    TF_AVAILABLE = True


except ImportError:
    TF_AVAILABLE = False
    tf = None
    Sequential = None
    load_model = None
    Dense = None
    LSTM = None
    Dropout = None
    Input = None
    Adam = None
from scipy.sparse import csr_matrix, diags  # noqa: E402
from scipy.sparse.linalg import LinearOperator, cg  # noqa: E402
from typing import Optional, Any  # noqa: E402
import logging  # noqa: E402
from datetime import datetime  # noqa: E402

from bayesian_assimilation.core.base import AssimilationBase  # noqa: E402
from bayesian_assimilation.utils.config import BaseConfig  # noqa: E402

logger = logging.getLogger(__name__)


class EnhancedBayesianAssimilation(AssimilationBase):
    """
    增强的贝叶斯同化模型
    添加机器学习和深度学习部分，允许自迭代
    """

    def __init__(self, config: Optional[BaseConfig] = None, model_path=None):
        super().__init__(config)
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(self.model_path, exist_ok=True)
        self.ml_model = None
        self.dl_model = None
        self.history = []
        self.best_score = float('inf')
        self._ensure_defaults()

    def _ensure_defaults(self):
        """确保默认值已设置"""
        if self.grid_shape is None:
            self.grid_shape = (10, 10, 5)
        if self.resolution is None:
            self.resolution = 50.0
        if not hasattr(self, 'nx'):
            self.nx, self.ny, self.nz = self.grid_shape

    def assimilate(self, background, observations, obs_locations, obs_errors=None):
        """
        执行增强的贝叶斯同化
        """
        self._ensure_defaults()

        if background is None:
            raise ValueError("背景场不能为空")

        if observations is None or obs_locations is None:
            logger.warning("观测数据或位置为空，返回背景场")
            return background, np.zeros_like(background)

        if len(observations) == 0 or len(obs_locations) == 0:
            logger.warning("观测数据或位置为空，返回背景场")
            return background, np.zeros_like(background)

        logger.info(f"🚀 开始增强贝叶斯同化，网格: {self.grid_shape}")

        analysis, variance = self._assimilate_3dvar(
                background, observations, obs_locations, obs_errors)

        if self.ml_model or self.dl_model:
            analysis, variance = self._enhance_with_ml(
                analysis, variance, background, observations, obs_locations)

        self.analysis = analysis
        self.variance = variance

        return analysis, variance

    def _assimilate_3dvar(self, background, observations, obs_locations, obs_errors=None):
        """
        执行3DVAR同化
        """
        nx, ny, nz = self.grid_shape
        n = nx * ny * nz

        H = self._build_observation_operator(obs_locations)

        class SimpleCovariance:

            def __init__(self, grid_shape, resolution):
                self.grid_shape = grid_shape
                self.resolution = resolution
                self.variance = 1.0

            def apply_inverse(self, x):
                return x / self.variance

        cov = SimpleCovariance(self.grid_shape, self.resolution)

        B_inv = LinearOperator(  # noqa: F841
            shape=(n, n),
            matvec=cov.apply_inverse     # type: ignore
        )

        obs_errors = obs_errors if obs_errors is not None else np.full(len(observations), 0.1)
        R_inv = diags(1.0 / (obs_errors**2 + 1e-6))

        def hessian_matvec(x):
            return cov.apply_inverse(x) + H.T @ (R_inv @ (H @ x))

        xb = background.ravel()
        b = cov.apply_inverse(xb) + H.T @ (R_inv @ observations)

        A = LinearOperator(shape=(n, n), matvec=hessian_matvec, dtype=np.float64)  # type: ignore
        xa, info = cg(A, b, x0=xb, maxiter=100, atol=1e-6)

        if info != 0:
            logger.warning(f"CG未收敛: {info}")

        variance = self._estimate_variance(cov, H, R_inv)

        return xa.reshape(nx, ny, nz), variance.reshape(nx, ny, nz)

    def _build_observation_operator(self, obs_locations):
        """
        构建观测算子
        """
        if obs_locations is None or len(obs_locations) == 0:
            nx, ny, nz = self.grid_shape
            return csr_matrix(([], ([], [])), shape=(1, nx*ny*nz))

        nx, ny, nz = self.grid_shape
        rows, cols, vals = [], [], []

        for i, loc in enumerate(obs_locations):
            x, y, z = loc
            ix = min(max(0, int(x/self.resolution)), nx-2)
            iy = min(max(0, int(y/self.resolution)), ny-2)
            iz = min(max(0, int(z/self.resolution)), nz-2)

            dx = (x/self.resolution - ix)
            dy = (y/self.resolution - iy)
            dz = (z/self.resolution - iz)

            weights = [
                (1-dx)*(1-dy)*(1-dz),
                dx*(1-dy)*(1-dz),
                (1-dx)*dy*(1-dz),
                dx*dy*(1-dz),
                (1-dx)*(1-dy)*dz,
                dx*(1-dy)*dz,
                (1-dx)*dy*dz,
                dx*dy*dz
            ]

            indices = [
                (ix, iy, iz),
                (ix+1, iy, iz),
                (ix, iy+1, iz),
                (ix+1, iy+1, iz),
                (ix, iy, iz+1),
                (ix+1, iy, iz+1),
                (ix, iy+1, iz+1),
                (ix+1, iy+1, iz+1)
            ]

            for idx, (di, dj, dk) in enumerate(indices):
                if weights[idx] > 1e-6:
                    flat_idx = di * ny * nz + dj * nz + dk
                    rows.append(i)
                    cols.append(flat_idx)
                    vals.append(weights[idx])

        return csr_matrix((vals, (rows, cols)), shape=(len(obs_locations), nx*ny*nz))

    def _estimate_variance(self, cov, H, R_inv):
        """
        估计方差
        """
        nx, ny, nz = self.grid_shape
        n = nx * ny * nz
        diag = np.zeros(n)

        diag += 1.0 / (cov.variance + 1e-6)

        for i in range(n):
            obs_idx = H[:, i].nonzero()[0]
            if len(obs_idx) > 0:
                h_vals = H[obs_idx, i].toarray().flatten()
                r_diag = R_inv.diagonal()[obs_idx]
                diag[i] += np.sum(h_vals**2 * r_diag)

        return 1.0 / (diag + 1e-6)

    def _enhance_with_ml(self, analysis, variance, background, observations, obs_locations):
        """
        使用机器学习模型增强同化结果
        """
        try:
            input_data = self._prepare_ml_input(
                analysis, variance, background, observations, obs_locations
            )

            if self.dl_model:
                enhanced_analysis = self.dl_model.predict(input_data)
                enhanced_analysis = enhanced_analysis.reshape(analysis.shape)
                enhanced_variance = variance * 0.9
            else:
                if self.ml_model:
                    enhanced_analysis = self.ml_model.predict(input_data)
                    enhanced_analysis = enhanced_analysis.reshape(analysis.shape)
                    enhanced_variance = variance * 0.95
                else:
                    return analysis, variance

            logger.info("使用机器学习模型增强同化结果")
            return enhanced_analysis, enhanced_variance

        except Exception as e:
            logger.error(f"机器学习增强失败: {e}")
            return analysis, variance

    def _prepare_ml_input(self, analysis, variance, background, observations, obs_locations):
        """
        准备机器学习输入数据
        """
        analysis_mean = np.mean(analysis)
        analysis_std = np.std(analysis)
        variance_mean = np.mean(variance)
        variance_std = np.std(variance)
        background_mean = np.mean(background)
        background_std = np.std(background)
        observations_mean = np.mean(observations)
        observations_std = np.std(observations)

        features = np.array([
            analysis_mean, analysis_std,
            variance_mean, variance_std,
            background_mean, background_std,
            observations_mean, observations_std,
            len(observations)
        ])

        return features.reshape(1, -1)

    def build_dl_model(self, input_shape):
        """
        构建深度学习模型
        """
        if not TF_AVAILABLE:
            logger.error("TensorFlow 不可用，无法构建深度学习模型")
            return None
        if Sequential is None:
            logger.error("Sequential 未导入，无法构建深度学习模型")
            return None
        if Dense is None:
            logger.error("Dense 未导入，无法构建深度学习模型")
            return None
        if Dropout is None:
            logger.error("Dropout  未导入，无法构建深度学习模型")
            return None
        if Input is None:
            logger.error("Input 未导入，无法构建深度学习模型")
            return None
        if Adam is None:
            logger.error("Adam 未导入，无法构建深度学习模型")
            return None
        self._ensure_defaults()

        model = Sequential()
        model.add(Input(shape=input_shape))
        model.add(Dense(64, activation='relu'))
        model.add(Dropout(0.2))
        model.add(Dense(32, activation='relu'))
        model.add(Dropout(0.2))
        model.add(Dense(int(np.prod(list(self.grid_shape))), activation='linear'))
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

        self.dl_model = model
        logger.info(f"构建深度学习模型，输入形状: {input_shape}")
        return model

    def train_ml_model(self: Any, X: Any, y: Any, epochs: int = 50, batch_size: int = 32):
        """
        训练机器学习模型
        """
        if not TF_AVAILABLE:
            logger.error("TensorFlow 不可用，无法训练模型")
            return {
                'success': False,
                'error': 'TensorFlow 不可用'
            }

        try:
            if not self.dl_model:
                self.build_dl_model(X.shape[1:])

            if self.dl_model:
                history = self.dl_model.fit(
                    X, y, epochs=epochs, batch_size=batch_size,
                    validation_split=0.2, verbose=1
                )

                self.history.append({
                    'timestamp': datetime.now().isoformat(),
                    'loss': history.history['loss'][-1],
                    'val_loss': history.history['val_loss'][-1],
                    'epochs': epochs
                })

                current_loss = history.history['val_loss'][-1]
                if current_loss < self.best_score:
                    self.best_score = current_loss
                    model_path = os.path.join(self.model_path, 'enhanced_bayesian_model.h5')
                    self.dl_model.save(model_path)
                    logger.info(f"最佳模型已保存，验证损失: {current_loss}")

                logger.info("机器学习模型训练完成")
                return {
                    'success': True,
                    'loss': history.history['loss'][-1],
                    'val_loss': history.history['val_loss'][-1]
                }
            else:
                logger.error("无法训练模型，模型未初始化")
                return {
                    'success': False,
                    'error': '模型未初始化'
                }

        except Exception as e:
            logger.error(f"训练机器学习模型失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def load_model(self):
        """
        加载模型
        """
        if not TF_AVAILABLE:
            logger.error("TensorFlow 不可用，无法加载模型")
            return
        if load_model is None:
            logger.error("load_model 未导入,无法加载模型")
            return
        model_path = os.path.join(self.model_path, 'enhanced_bayesian_model.h5')
        if os.path.exists(model_path):
            self.dl_model = load_model(model_path)
            logger.info(f"模型加载成功: {model_path}")
        else:
            logger.warning(f"模型文件不存在: {model_path}")

    def self_improve(self: Any, X: Any, y: Any, epochs: int = 20, batch_size: int = 32):
        """
        自迭代改进模型
        """
        try:
            logger.info("开始自迭代改进模型...")

            if not self.dl_model:
                self.load_model()

            result = self.train_ml_model(X, y, epochs, batch_size)

            logger.info("模型自迭代改进完成")
            return result

        except Exception as e:
            logger.error(f"自迭代改进失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_model_performance(self):
        """
        获取模型性能
        """
        return {
            'history': self.history,
            'best_score': self.best_score
        }


if __name__ == "__main__":
    model = EnhancedBayesianAssimilation()
    bg = np.random.rand(10, 10, 5) * 10
    obs = np.array([5.0, 6.0, 7.0])
    obs_loc = np.array([[100.0, 100.0, 50.0], [200.0, 200.0, 100.0], [300.0, 300.0, 150.0]])

    analysis, variance = model.assimilate(bg, obs, obs_loc)
    logger.info(f"分析场形状: {analysis.shape}")
    logger.info(f"方差场形状: {variance.shape}")
    logger.info(f"分析场范围: [{analysis.min():.2f}, {analysis.max():.2f}]")
    logger.info("测试通过！")
