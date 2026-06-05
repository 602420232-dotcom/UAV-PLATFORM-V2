import uuid
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class JobService:

    def __init__(self):
        self._jobs: Dict[str, dict] = {}

    def create_job(self, algorithm: str, config: dict | None = None) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "id": job_id,
            "algorithm": algorithm,
            "config": config or {},
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        logger.info(f"创建任务 {job_id}: algorithm={algorithm}")
        return job_id

    def update_status(self, job_id: str, status: str, result: Any = None):
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = status
            if result is not None:
                self._jobs[job_id]["result"] = result
            self._jobs[job_id]["updated_at"] = datetime.now().isoformat()

    def get_job(self, job_id: str) -> dict | None:
        return self._jobs.get(job_id)

    def list_jobs(self, limit: int = 10) -> list:
        sorted_jobs = sorted(
            self._jobs.values(),
            key=lambda x: x.get("created_at", ""),
            reverse=True,
        )
        return sorted_jobs[:limit]

    def get_stats(self) -> dict:
        total = len(self._jobs)
        completed = sum(1 for j in self._jobs.values() if j["status"] == "completed")
        failed = sum(1 for j in self._jobs.values() if j["status"] == "failed")
        return {"total": total, "completed": completed, "failed": failed}
