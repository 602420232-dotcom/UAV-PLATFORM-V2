"""
实验快照管理器
实现实验完整状态的序列化与恢复，确保科研可复现性
"""
import os
import json
import hashlib
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from loguru import logger
import pickle


@dataclass
class ExperimentSnapshot:
    """实验快照"""
    snapshot_id: str           # 快照ID（哈希生成）
    experiment_id: str         # 实验ID
    algorithm_name: str        # 算法名称
    algorithm_version: str     # 算法版本
    timestamp: str             # 快照时间
    
    # 输入数据
    input_data: Dict[str, Any]  # 输入数据路径/摘要
    input_data_hash: str        # 输入数据哈希（用于校验）
    
    # 参数配置
    parameters: Dict[str, Any]  # 完整参数配置
    
    # 环境信息
    environment: Dict[str, str] # 环境信息（Python版本、库版本等）
    
    # 输出数据
    output_data: Dict[str, Any] # 输出数据路径/摘要
    output_data_hash: str       # 输出数据哈希
    
    # 指标
    metrics: Dict[str, float]   # 评估指标
    
    # 随机种子
    random_seed: Optional[int]  # 随机种子
    
    # 备注
    notes: Optional[str]        # 实验备注


class SnapshotManager:
    """实验快照管理器"""
    
    def __init__(self, base_path: str = "./experiments/snapshots"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def create_snapshot(self, 
                       experiment_id: str,
                       algorithm_name: str,
                       algorithm_version: str,
                       input_data: Dict[str, Any],
                       parameters: Dict[str, Any],
                       output_data: Dict[str, Any],
                       metrics: Dict[str, float],
                       random_seed: Optional[int] = None,
                       notes: Optional[str] = None) -> ExperimentSnapshot:
        """创建实验快照"""
        
        timestamp = datetime.now().isoformat()
        
        # 计算数据哈希
        input_hash = self._compute_hash(input_data)
        output_hash = self._compute_hash(output_data)
        
        # 生成快照ID
        snapshot_content = f"{experiment_id}:{algorithm_name}:{timestamp}:{input_hash}"
        snapshot_id = hashlib.sha256(snapshot_content.encode()).hexdigest()[:16]
        
        # 收集环境信息
        environment = self._collect_environment()
        
        snapshot = ExperimentSnapshot(
            snapshot_id=snapshot_id,
            experiment_id=experiment_id,
            algorithm_name=algorithm_name,
            algorithm_version=algorithm_version,
            timestamp=timestamp,
            input_data=input_data,
            input_data_hash=input_hash,
            parameters=parameters,
            environment=environment,
            output_data=output_data,
            output_data_hash=output_hash,
            metrics=metrics,
            random_seed=random_seed,
            notes=notes
        )
        
        # 保存快照
        self._save_snapshot(snapshot)
        
        logger.info(f"实验快照已创建: {snapshot_id} (实验: {experiment_id})")
        return snapshot
        
    def load_snapshot(self, snapshot_id: str) -> Optional[ExperimentSnapshot]:
        """加载实验快照"""
        snapshot_path = self.base_path / f"{snapshot_id}.json"
        
        if not snapshot_path.exists():
            logger.warning(f"快照不存在: {snapshot_id}")
            return None
            
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return ExperimentSnapshot(**data)
        
    def verify_snapshot(self, snapshot_id: str) -> bool:
        """验证快照完整性"""
        snapshot = self.load_snapshot(snapshot_id)
        if not snapshot:
            return False
            
        # 验证输入数据哈希
        input_data = self._load_data(snapshot.input_data)
        current_input_hash = self._compute_hash(input_data)
        
        if current_input_hash != snapshot.input_data_hash:
            logger.error(f"输入数据哈希不匹配: {snapshot_id}")
            return False
            
        # 验证输出数据哈希
        output_data = self._load_data(snapshot.output_data)
        current_output_hash = self._compute_hash(output_data)
        
        if current_output_hash != snapshot.output_data_hash:
            logger.error(f"输出数据哈希不匹配: {snapshot_id}")
            return False
            
        logger.info(f"快照验证通过: {snapshot_id}")
        return True
        
    def list_snapshots(self, experiment_id: Optional[str] = None) -> list:
        """列出快照"""
        snapshots = []
        
        for snapshot_file in self.base_path.glob("*.json"):
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if experiment_id is None or data.get('experiment_id') == experiment_id:
                snapshots.append(data)
                
        return sorted(snapshots, key=lambda x: x['timestamp'], reverse=True)
        
    def _compute_hash(self, data: Any) -> str:
        """计算数据哈希"""
        if isinstance(data, np.ndarray):
            return hashlib.sha256(data.tobytes()).hexdigest()[:16]
        elif isinstance(data, dict):
            content = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(content.encode()).hexdigest()[:16]
        else:
            content = str(data)
            return hashlib.sha256(content.encode()).hexdigest()[:16]
            
    def _collect_environment(self) -> Dict[str, str]:
        """收集环境信息"""
        import platform
        import sys
        
        return {
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'numpy_version': np.__version__,
            'timestamp': datetime.now().isoformat()
        }
        
    def _save_snapshot(self, snapshot: ExperimentSnapshot):
        """保存快照到文件"""
        snapshot_path = self.base_path / f"{snapshot.snapshot_id}.json"
        
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(snapshot), f, indent=2, ensure_ascii=False, default=str)
            
    def _load_data(self, data_info: Dict[str, Any]) -> Any:
        """加载数据"""
        if 'path' in data_info:
            path = data_info['path']
            if path.endswith('.npy'):
                return np.load(path)
            elif path.endswith('.pkl'):
                with open(path, 'rb') as f:
                    return pickle.load(f)
        return data_info
