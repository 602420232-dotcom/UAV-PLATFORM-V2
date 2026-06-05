"""
多区域部署 - 容灾备份、数据同步、多区域协同
"""
import json
import logging
import time
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RegionStatus(Enum):
    ACTIVE = "active"
    STANDBY = "standby"
    FAILED = "failed"
    SYNCING = "syncing"


@dataclass
class Region:
    name: str
    endpoint: str
    status: RegionStatus
    priority: int
    last_heartbeat: float = 0.0
    load: float = 0.0


class MultiRegionDeployer:
    """多区域部署管理器"""

    def __init__(self):
        self.regions: Dict[str, Region] = {}
        self.active_region: Optional[str] = None
        self.sync_interval = 5.0
        self._running = False
        self.missed_heartbeats: Dict[str, int] = {}
        self.max_missed_heartbeats = 3

    def add_region(self, name: str, endpoint: str, priority: int = 1):
        """注册区域"""
        self.regions[name] = Region(
            name=name,
            endpoint=endpoint,
            status=RegionStatus.STANDBY,
            priority=priority
        )
        self.missed_heartbeats[name] = 0
        if not self.active_region or priority == max(r.priority for r in self.regions.values()):
            self.active_region = name
            self.regions[name].status = RegionStatus.ACTIVE
        logger.info(f"注册区域: {name} @ {endpoint} (优先级={priority})")

    def start_health_check(self):
        """启动健康检查"""
        self._running = True
        threading.Thread(target=self._health_check_loop, daemon=True).start()

    def _health_check_loop(self):
        while self._running:
            now = time.time()
            for name, region in self.regions.items():
                if region.status == RegionStatus.FAILED:
                    continue
                if now - region.last_heartbeat > 30:
                    self.missed_heartbeats[name] = self.missed_heartbeats.get(name, 0) + 1
                    logger.warning(
                        f"区域 {name} 心跳超时 "
                        f"({self.missed_heartbeats[name]}/{self.max_missed_heartbeats})"
                    )
                    if self.missed_heartbeats[name] >= self.max_missed_heartbeats:
                        self.check_failover(name)
                else:
                    self.missed_heartbeats[name] = 0
            time.sleep(self.sync_interval)

    def check_failover(self, failed_region: str):
        """检查并执行故障转移"""
        region = self.regions.get(failed_region)
        if not region or region.status == RegionStatus.FAILED:
            return

        logger.warning(
            f"触发故障转移: {failed_region} 已连续 "
            f"{self.missed_heartbeats.get(failed_region, 0)} 次心跳丢失"
        )
        region.status = RegionStatus.FAILED
        logger.info(f"区域 {failed_region} 状态已标记为 FAILED")
        self._failover(failed_region)

    def _failover(self, failed_region: str):
        """故障转移 - 将最高优先级的 STANDBY 区域提升为 ACTIVE"""
        available = [
            (n, r) for n, r in self.regions.items()
            if n != failed_region and r.status == RegionStatus.STANDBY
        ]
        if available:
            available.sort(key=lambda x: x[1].priority, reverse=True)
            new_active = available[0][0]
            self.active_region = new_active
            self.regions[new_active].status = RegionStatus.ACTIVE
            logger.info(
                f"故障转移完成: {failed_region} → {new_active} "
                f"(优先级={self.regions[new_active].priority})"
            )
        else:
            logger.error("故障转移失败: 没有可用的 STANDBY 区域可提升为 ACTIVE")

    def sync_data(self, data: dict, sync_type: str = "incremental"):
        """跨区域数据同步"""
        for name, region in self.regions.items():
            if region.status != RegionStatus.FAILED:
                region.status = RegionStatus.SYNCING
                logger.info(f"同步 {sync_type} 数据到 {name}: {len(json.dumps(data))} bytes")
                region.last_heartbeat = time.time()
                self.missed_heartbeats[name] = 0
                region.status = RegionStatus.ACTIVE \
                    if name == self.active_region else RegionStatus.STANDBY

    def get_active_endpoint(self) -> Optional[str]:
        """获取当前活跃区域端点"""
        if self.active_region and self.regions[self.active_region].status != RegionStatus.FAILED:
            return self.regions[self.active_region].endpoint
        return None

    def get_region_status(self) -> List[dict]:
        return [{"name": n, "endpoint": r.endpoint, "status": r.status.value,
                 "active": n == self.active_region} for n, r in self.regions.items()]


class DisasterRecovery:
    """容灾备份管理器"""

    def __init__(self):
        self.backup_regions: List[str] = []
        self.recovery_scripts: Dict[str, str] = {}
        self.checkpoint_path = "backups/checkpoints"

    def create_checkpoint(self, service_name: str, data: dict):
        """创建备份检查点"""
        import os
        os.makedirs(f"{self.checkpoint_path}/{service_name}", exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = f"{self.checkpoint_path}/{service_name}/checkpoint_{timestamp}.json"
        with open(path, 'w') as f:
            json.dump(data, f)
        logger.info(f"检查点创建: {path}")
        return path

    def restore_from_checkpoint(
        self,
        service_name: str,
        checkpoint_path: str | None = None
    ) -> Optional[dict]:
        """从检查点恢复"""
        import glob
        if not checkpoint_path:
            files = sorted(glob.glob(f"{self.checkpoint_path}/{service_name}/checkpoint_*.json"))
            if not files:
                return None
            checkpoint_path = files[-1]
        with open(checkpoint_path, 'r') as f:
            return json.load(f)

    def register_recovery_script(self, service: str, script_path: str):
        """注册恢复脚本"""
        self.recovery_scripts[service] = script_path
        logger.info(f"恢复脚本注册: {service} → {script_path}")
