"""
实验日志记录器
结构化记录算法实验过程，支持实时监控和事后分析
"""
import os
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from loguru import logger
import threading


@dataclass
class ExperimentLogEntry:
    """实验日志条目"""
    timestamp: str
    level: str           # INFO, WARNING, ERROR, PROGRESS
    stage: str           # 实验阶段（初始化/预处理/计算/后处理）
    message: str
    metrics: Optional[Dict[str, float]] = None
    elapsed_ms: Optional[int] = None


class ExperimentLogger:
    """实验日志记录器"""
    
    def __init__(self, experiment_id: str, algorithm_name: str, 
                 base_path: str = "./experiments/logs"):
        self.experiment_id = experiment_id
        self.algorithm_name = algorithm_name
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.base_path / f"{experiment_id}.jsonl"
        self.start_time = time.time()
        self.entries: List[ExperimentLogEntry] = []
        self._lock = threading.Lock()
        self._stage_start_times: Dict[str, float] = {}
        
        # 初始化日志
        self.info("experiment_start", "实验开始", {
            'experiment_id': experiment_id,
            'algorithm': algorithm_name,
            'start_time': datetime.now().isoformat()
        })
        
    def info(self, stage: str, message: str, metrics: Optional[Dict] = None):
        """记录信息日志"""
        self._log("INFO", stage, message, metrics)
        
    def warning(self, stage: str, message: str, metrics: Optional[Dict] = None):
        """记录警告日志"""
        self._log("WARNING", stage, message, metrics)
        
    def error(self, stage: str, message: str, metrics: Optional[Dict] = None):
        """记录错误日志"""
        self._log("ERROR", stage, message, metrics)
        
    def progress(self, stage: str, current: int, total: int, message: str = ""):
        """记录进度"""
        percentage = (current / total * 100) if total > 0 else 0
        self._log("PROGRESS", stage, 
                  f"{message} [{current}/{total}] {percentage:.1f}%",
                  {'progress_current': current, 'progress_total': total, 'progress_pct': percentage})
        
    def metric(self, stage: str, metrics: Dict[str, float]):
        """记录指标"""
        self._log("METRIC", stage, "指标更新", metrics)
        
    def stage_start(self, stage: str):
        """阶段开始"""
        self._stage_start_times[stage] = time.time()
        self._log("INFO", stage, f"阶段开始: {stage}")
        
    def stage_end(self, stage: str):
        """阶段结束"""
        elapsed = 0
        if stage in self._stage_start_times:
            elapsed = int((time.time() - self._stage_start_times[stage]) * 1000)
        self._log("INFO", stage, f"阶段完成: {stage}", elapsed_ms=elapsed)
        
    def experiment_end(self, final_metrics: Optional[Dict] = None):
        """实验结束"""
        total_elapsed = int((time.time() - self.start_time) * 1000)
        self._log("INFO", "experiment_end", "实验完成", 
                  metrics=final_metrics, elapsed_ms=total_elapsed)
        
    def get_summary(self) -> Dict:
        """获取实验摘要"""
        total_time = int((time.time() - self.start_time) * 1000)
        
        # 统计各阶段耗时
        stage_times = {}
        for entry in self.entries:
            if entry.elapsed_ms and entry.stage not in stage_times:
                stage_times[entry.stage] = entry.elapsed_ms
                
        return {
            'experiment_id': self.experiment_id,
            'algorithm': self.algorithm_name,
            'total_entries': len(self.entries),
            'total_time_ms': total_time,
            'stage_times': stage_times,
            'error_count': sum(1 for e in self.entries if e.level == 'ERROR'),
            'warning_count': sum(1 for e in self.entries if e.level == 'WARNING')
        }
        
    def export_to_json(self) -> str:
        """导出为JSON文件"""
        output_path = self.base_path / f"{self.experiment_id}_full.json"
        
        data = {
            'experiment_id': self.experiment_id,
            'algorithm': self.algorithm_name,
            'entries': [asdict(e) for e in self.entries],
            'summary': self.get_summary()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
        return str(output_path)
        
    def _log(self, level: str, stage: str, message: str, 
             metrics: Optional[Dict] = None, elapsed_ms: Optional[int] = None):
        """内部日志记录"""
        entry = ExperimentLogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            stage=stage,
            message=message,
            metrics=metrics,
            elapsed_ms=elapsed_ms
        )
        
        with self._lock:
            self.entries.append(entry)
            
            # 写入JSONL文件
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(entry), ensure_ascii=False, default=str) + '\n')
                
        # 同时输出到标准日志
        logger.log(level, f"[{self.experiment_id}] [{stage}] {message}")
