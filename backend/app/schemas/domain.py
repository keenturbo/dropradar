from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DomainResponse(BaseModel):
    id: int
    name: str
    da_score: int
    backlinks: int
    spam_score: float
    status: str
    drop_date: Optional[datetime]
    discovered_at: datetime

    class Config:
        from_attributes = True


class ScanRequest(BaseModel):
    """Request model for manual scan trigger"""
    min_da: int = 20  # Minimum Domain Authority
    max_spam: float = 10.0  # Maximum Spam Score
    min_backlinks: int = 50  # Minimum backlinks
