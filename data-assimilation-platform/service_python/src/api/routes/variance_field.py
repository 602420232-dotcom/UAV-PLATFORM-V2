from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/variance", tags=["variance"])


@router.post("/compute")
async def compute_variance(request: Dict[str, Any]):
    try:
        background = request.get("background")
        if not background:
            raise HTTPException(status_code=400, detail="缺少 background 参数")

        return {
            "status": "success",
            "variance": None,
            "message": "方差场计算功能需集成 algorithm_core",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
