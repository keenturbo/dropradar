from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func  # ✅ 导入 func
from typing import List, Optional
from datetime import datetime, timedelta
import random

from app.core.database import get_db
from app.models.domain import Domain, DomainStatus
from app.services.notification import notify_bark

router = APIRouter()

# 模拟高价值域名词汇库
TECH_KEYWORDS = ["ai", "gpt", "gemini", "claude", "llm", "quantum", "neural", "crypto", "defi", "metaverse"]
PREFIXES = ["super", "ultra", "mega", "hyper", "next", "future", "smart", "auto"]
SUFFIXES = ["hub", "lab", "forge", "flow", "verse", "sphere", "stack", "cloud"]

def generate_mock_domain():
    """生成模拟域名"""
    patterns = [
        f"{random.choice(TECH_KEYWORDS)}{random.randint(2, 9)}",
        f"{random.choice(PREFIXES)}-{random.choice(TECH_KEYWORDS)}",
        f"{random.choice(TECH_KEYWORDS)}-{random.choice(SUFFIXES)}",
        f"{random.choice(TECH_KEYWORDS)}{random.choice(SUFFIXES)}",
    ]
    name = random.choice(patterns)
    tld = random.choice([".com", ".ai", ".io", ".net"])
    return name + tld

@router.get("/domains")
def get_domains(
    skip: int = 0,
    limit: int = 100,
    min_da: Optional[int] = None,
    max_spam: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取域名列表，支持过滤"""
    try:
        query = db.query(Domain)
        
        if min_da:
            query = query.filter(Domain.da_score >= min_da)
        if max_spam:
            query = query.filter(Domain.spam_score <= max_spam)
        if status:
            query = query.filter(Domain.status == status)
        
        domains = query.order_by(Domain.da_score.desc()).offset(skip).limit(limit).all()
        total = query.count()
        
        return {
            "domains": domains,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        print(f"Error fetching domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan")
def start_scan(
    bark_key: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """触发域名扫描任务"""
    try:
        print("🔍 Starting domain scan...")
        
        num_domains = random.randint(5, 10)
        new_domains = []
        
        for _ in range(num_domains):
            domain_name = generate_mock_domain()
            
            existing = db.query(Domain).filter(Domain.name == domain_name).first()
            if existing:
                continue
            
            da_score = random.randint(25, 65)
            backlinks = random.randint(50, 500)
            spam_score = random.randint(0, 15)
            
            domain = Domain(
                name=domain_name,
                da_score=da_score,
                backlinks=backlinks,
                spam_score=spam_score,
                status=DomainStatus.AVAILABLE,
                drop_date=datetime.now().date() + timedelta(days=random.randint(1, 30)),
                tld=domain_name.split('.')[-1],
                length=len(domain_name.split('.')[0])
            )
            
            db.add(domain)
            new_domains.append(domain_name)
            
            if da_score > 40 and spam_score < 10 and bark_key:
                try:
                    notify_bark(
                        bark_key=bark_key,
                        title="🚨 高价值域名发现",
                        content=f"{domain_name} | DA:{da_score} | Spam:{spam_score}%",
                        url=f"https://www.namecheap.com/domains/registration/results/?domain={domain_name}"
                    )
                except Exception as notify_error:
                    print(f"Bark notification failed: {notify_error}")
        
        db.commit()
        
        print(f"✅ Scan completed. Found {len(new_domains)} new domains.")
        
        return {
            "status": "success",
            "domains_found": len(new_domains),
            "message": f"扫描完成，发现 {len(new_domains)} 个高价值域名"
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"扫描失败: {str(e)}")


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """获取统计数据"""
    try:
        total = db.query(Domain).count()
        
        # ✅ 修复：直接使用 func.avg()
        avg_da_result = db.query(func.avg(Domain.da_score)).scalar()
        avg_da = round(float(avg_da_result), 1) if avg_da_result else 0.0
        
        available = db.query(Domain).filter(Domain.status == DomainStatus.AVAILABLE).count()
        low_spam = db.query(Domain).filter(Domain.spam_score < 10).count()
        
        return {
            "total": total,
            "avg_da": avg_da,
            "available": available,
            "low_spam": low_spam
        }
    except Exception as e:
        print(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-notification")
def test_notification(request: dict):
    """测试 Bark 通知"""
    try:
        bark_key = request.get("bark_key")
        if not bark_key:
            raise HTTPException(status_code=400, detail="bark_key is required")
        
        notify_bark(
            bark_key=bark_key,
            title="🔔 DropRadar 测试通知",
            content="Bark 通知系统工作正常！",
            url="https://github.com/keenturbo/dropradar"
        )
        
        return {"status": "success", "message": "通知已发送"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))