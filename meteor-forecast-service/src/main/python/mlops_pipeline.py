"""
MLOps 机器学习生命周期管理
模型训练、评估、版本管理与A/B测试
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    model_name: str
    version: str
    accuracy: float
    mse: float
    mae: float
    train_date: str
    dataset_size: int
    status: str = 'staging'


@dataclass
class ModelVersion:
    name: str
    version: str
    path: str
    metrics: ModelMetrics
    created_at: str
    is_active: bool = False


class MLOpsPipeline:
    """MLOps 生命周期管理流水线"""

    def __init__(self, model_registry_path: str = None):
        self.registry_path = model_registry_path or os.path.join(os.path.dirname(__file__), 'model_registry')
        os.makedirs(self.registry_path, exist_ok=True)
        self.registry_file = os.path.join(self.registry_path, 'model_registry.json')
        self.models = self._load_registry()

    def _load_registry(self) -> Dict:
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {'models': [], 'active_models': {}}

    def _save_registry(self):
        with open(self.registry_file, 'w') as f:
            json.dump(self.models, f, indent=2)

    def register_model(self, model, name: str, version: str, metrics: dict, dataset_size: int):
        """注册模型版本"""
        model_path = os.path.join(self.registry_path, f"{name}_{version}.pkl")
        import joblib
        joblib.dump(model, model_path)

        model_metrics = ModelMetrics(
            model_name=name,
            version=version,
            accuracy=metrics.get('accuracy', 0),
            mse=metrics.get('mse', 0),
            mae=metrics.get('mae', 0),
            train_date=datetime.now().isoformat(),
            dataset_size=dataset_size
        )

        model_version = ModelVersion(
            name=name,
            version=version,
            path=model_path,
            metrics=model_metrics,
            created_at=datetime.now().isoformat()
        )

        self.models['models'].append(asdict(model_version))
        self._save_registry()
        logger.info(f"模型注册: {name}:{version}")
        return model_version

    def promote_to_production(self, name: str, version: str):
        """将模型提升到生产环境"""
        self.models['active_models'][name] = version
        for m in self.models['models']:
            if m['name'] == name and m['version'] == version:
                m['metrics']['status'] = 'production'
        self._save_registry()
        logger.info(f"模型提升到生产: {name}:{version}")

    def get_active_model(self, name: str) -> Optional[str]:
        """获取当前生产环境的模型版本"""
        return self.models['active_models'].get(name)

    def ab_test(self, name: str, model_a: str, model_b: str, test_data) -> dict:
        """A/B 测试对比两个模型版本"""
        import joblib
        path_a = os.path.join(self.registry_path, f"{name}_{model_a}.pkl")
        path_b = os.path.join(self.registry_path, f"{name}_{model_b}.pkl")
        model_a_obj = joblib.load(path_a) if os.path.exists(path_a) else None
        model_b_obj = joblib.load(path_b) if os.path.exists(path_b) else None

        if model_a_obj is None or model_b_obj is None:
            return {'error': '模型版本不存在'}

        X_test, y_test = test_data
        pred_a = model_a_obj.predict(X_test)
        pred_b = model_b_obj.predict(X_test)
        from sklearn.metrics import mean_squared_error

        result = {
            'model_a': {'version': model_a, 'mse': float(mean_squared_error(y_test, pred_a))},
            'model_b': {'version': model_b, 'mse': float(mean_squared_error(y_test, pred_b))},
            'winner': model_a if mean_squared_error(y_test, pred_a) < mean_squared_error(y_test, pred_b) else model_b
        }
        logger.info(f"A/B 测试结果: {result['winner']} 胜出")
        return result

    def auto_rollback(self, name: str, current_version: str, previous_version: str, threshold: float = 0.05):
        """自动回滚机制"""
        current = next((m for m in self.models['models']
                       if m['name'] == name and m['version'] == current_version), None)
        previous = next((m for m in self.models['models']
                        if m['name'] == name and m['version'] == previous_version), None)
        if current and previous:
            curr_mse = current['metrics']['mse']
            prev_mse = previous['metrics']['mse']
            if curr_mse > prev_mse * (1 + threshold):
                logger.warning(f"性能下降 {((curr_mse - prev_mse) / prev_mse) * 100:.1f}%，自动回滚到 {previous_version}")
                self.promote_to_production(name, previous_version)
                return True
        return False
