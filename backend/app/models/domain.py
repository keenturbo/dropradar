from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from datetime import datetime
import enum
from app.core.database import Base


class DomainStatus(str, enum.Enum):
    AVAILABLE = "available"
    AUCTION = "auction"
    REGISTERED = "registered"
    PENDING = "pending"


class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    da_score = Column(Integer, default=0)  # Domain Authority
    backlinks = Column(Integer, default=0)
    spam_score = Column(Float, default=0.0)
    status = Column(Enum(DomainStatus), default=DomainStatus.AVAILABLE)
    drop_date = Column(DateTime, nullable=True)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional metadata
    tld = Column(String, default=".com")  # Top-level domain
    length = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Domain {self.name} DA:{self.da_score}>"
