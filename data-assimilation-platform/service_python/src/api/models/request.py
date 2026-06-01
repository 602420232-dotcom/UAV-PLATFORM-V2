from pydantic import BaseModel, Field
from typing import List, Optional


class SelfImproveRequest(BaseModel):
    job_id: str = Field(..., description="任务ID")
    X: List[List[float]] = Field(..., description="输入特征数据")
    y: List[float] = Field(..., description="目标标签数据")
    epochs: int = Field(default=20, ge=1, le=500, description="训练轮次")
    batch_size: int = Field(default=32, ge=1, le=1024, description="批次大小")
