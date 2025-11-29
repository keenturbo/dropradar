from sqlalchemy import Column, Integer, String, Date, Float, Boolean, DateTime, Numeric, Text
from sqlalchemy.sql import func
from database import Base

class Domain(Base):
    __tablename__ = "domains"
    
    # 基础信息
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    tld = Column(String(10))  # .com、.io 等
    length = Column(Integer)  # 域名长度
    
    # SEO 权重指标
    da_score = Column(Integer, default=0)  # Domain Authority (0-100)
    backlinks = Column(Integer, default=0)  # 外链数
    referring_domains = Column(Integer, default=0)  # 引用域数
    spam_score = Column(Integer, default=0)  # 垃圾分数 (0-100)
    
    # 竞价信息
    price = Column(Integer, default=0)  # 价格（美元）
    bids = Column(Integer, default=0)  # 竞价次数
    
    # 域名历史
    domain_age = Column(Integer, default=0)  # 域名年龄（年）
    drop_date = Column(Date)  # 到期日期
    wikipedia_links = Column(Integer, default=0)  # 维基百科外链数
    
    # 质量评分
    quality_score = Column(Float, default=0.0)  # 综合质量分数（0-100）
    status = Column(String(50), default="available")  # 状态：available、monitoring、expired
    
    # 时间戳
    first_seen = Column(DateTime, server_default=func.now(), nullable=False)
    last_seen = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 监控状态
    is_new = Column(Boolean, default=True)  # 是否新发现
    notified = Column(Boolean, default=False)  # 是否已推送通知
    
    # 备注
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Domain {self.name} - DA:{self.da_score} - Quality:{self.quality_score}>"