from fastapi import APIRouter
from ..services.job_service import JobService

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
job_service = JobService()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "gpu_available": False,
    }


@router.get("/jobs")
async def list_jobs(limit: int = 10):
    return {"jobs": job_service.list_jobs(limit=limit)}


@router.get("/stats")
async def get_stats():
    return job_service.get_stats()
