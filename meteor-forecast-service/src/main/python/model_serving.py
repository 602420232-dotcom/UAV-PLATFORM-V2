"""
模型服务化 - RL推理服务 API + A/B测试 + 模型版本管理
"""
import json
import os
import logging
import numpy as np
from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    STAGING = "staging"
    PRODUCTION = "production"
    ROLLED_BACK = "rolled_back"
    DEPRECATED = "deprecated"


@dataclass
class ModelRecord:
    name: str
    version: str
    algorithm: str
    path: str
    status: ModelStatus
    metrics: Dict[str, float]
    created_at: str
    description: str = ""


class ModelServingAPI:
    """模型服务化推理API"""

    def __init__(self, registry_path: str = "model_registry"):
        self.registry_path = registry_path
        os.makedirs(registry_path, exist_ok=True)
        self.registry_file = os.path.join(registry_path, "model_registry.json")
        self.registry = self._load_registry()
        self.active_models: Dict[str, Any] = {}
        self.traffic_splits: Dict[str, Dict[str, int]] = {}

    def _load_registry(self) -> Dict:
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {"models": [], "traffic_splits": {}}

    def _save_registry(self):
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def register_model(self, name: str, version: str, algorithm: str, model_obj,
                       metrics: Dict[str, float], description: str = "") -> ModelRecord:
        """注册新模型版本"""
        model_path = os.path.join(self.registry_path, f"{name}_{version}.pkl")
        import joblib
        joblib.dump(model_obj, model_path)
        record = ModelRecord(
            name=name, version=version, algorithm=algorithm,
            path=model_path, status=ModelStatus.STAGING,
            metrics=metrics, created_at=datetime.now().isoformat(),
            description=description
        )
        self.registry["models"].append(asdict(record))
        self._save_registry()
        logger.info(f"模型注册: {name}:{version} ({algorithm})")
        return record

    def promote(self, name: str, version: str):
        """提升模型到生产环境"""
        for m in self.registry["models"]:
            if m["name"] == name:
                if m["version"] == version:
                    m["status"] = ModelStatus.PRODUCTION.value
                elif m["status"] == ModelStatus.PRODUCTION.value:
                    m["status"] = ModelStatus.STAGING.value
        self._save_registry()
        self.active_models.pop(name, None)
        logger.info(f"模型提升: {name}:{version} → PRODUCTION")

    def rollback(self, name: str, target_version: str):
        """回滚到指定版本"""
        for m in self.registry["models"]:
            if m["name"] == name and m["status"] == ModelStatus.PRODUCTION.value:
                m["status"] = ModelStatus.ROLLED_BACK.value
            if m["name"] == name and m["version"] == target_version:
                m["status"] = ModelStatus.PRODUCTION.value
        self._save_registry()
        logger.info(f"模型回滚: {name} → {target_version}")

    def set_traffic_split(self, name: str, version_a: str, version_b: str,
                          weight_a: int = 90, weight_b: int = 10):
        """设置A/B测试流量分配"""
        self.registry["traffic_splits"][name] = {
            "version_a": version_a, "version_b": version_b,
            "weight_a": weight_a, "weight_b": weight_b
        }
        self._save_registry()
        logger.info(f"流量分配 {name}: {version_a}={weight_a}%, {version_b}={weight_b}%")

    def predict(self, name: str, input_data: Any) -> Dict:
        """统一推理接口(带A/B测试分流)"""
        import joblib
        split = self.registry["traffic_splits"].get(name, {})
        if split and np.random.randint(100) < split.get("weight_b", 0):
            version = split["version_b"]
        else:
            version = self._get_active_version(name) or split.get("version_a", "latest")
        model_path = os.path.join(self.registry_path, f"{name}_{version}.pkl")
        if not os.path.exists(model_path):
            return {"error": f"模型 {name}:{version} 不存在"}
        model = joblib.load(model_path)
        result = model.predict(input_data)
        return {"model": name, "version": version, "result": result.tolist() if hasattr(result, 'tolist') else result}

    def _get_active_version(self, name: str) -> Optional[str]:
        for m in self.registry["models"]:
            if m["name"] == name and m["status"] == ModelStatus.PRODUCTION.value:
                return m["version"]
        return None


class RLModelServing:
    """强化学习模型服务化"""

    def __init__(self):
        self.models: Dict[str, RLPolicy] = {}

    def load_policy(self, name: str, policy: 'RLPolicy'):
        self.models[name] = policy

    def select_action(self, model_name: str, state: np.ndarray) -> np.ndarray:
        """强化学习动作选择"""
        if model_name not in self.models:
            raise ValueError(f"模型 {model_name} 未加载")
        return self.models[model_name].select_action(state)


class RLPolicy:
    """强化学习策略基类"""

    def __init__(self, model=None):
        self.model = model

    def select_action(self, state: np.ndarray) -> np.ndarray:
        return np.array([0, 0])
