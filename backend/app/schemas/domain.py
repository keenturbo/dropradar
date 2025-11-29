from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


class DomainBase(BaseModel):
    name: str
    tld: Optional[str] = None
    length: Optional[int] = None
    da_score: int = 0
    backlinks: int = 0
    referring_domains: int = 0
    spam_score: int = 0
    price: int = 0
    bids: int = 0
    domain_age: int = 0
    drop_date: Optional[date] = None
    wikipedia_links: int = 0
    quality_score: float = 0.0
    status: str = "available"
    is_new: bool = True
    notified: bool = False
    notes: Optional[str] = None


class DomainCreate(DomainBase):
    pass


class DomainUpdate(BaseModel):
    name: Optional[str] = None
    da_score: Optional[int] = None
    backlinks: Optional[int] = None
    referring_domains: Optional[int] = None
    spam_score: Optional[int] = None
    price: Optional[int] = None
    bids: Optional[int] = None
    domain_age: Optional[int] = None
    drop_date: Optional[date] = None
    wikipedia_links: Optional[int] = None
    quality_score: Optional[float] = None
    status: Optional[str] = None
    is_new: Optional[bool] = None
    notified: Optional[bool] = None
    notes: Optional[str] = None


class DomainResponse(DomainBase):
    id: int
    created_at: datetime
    updated_at: datetime
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True