from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models.domain import Domain, DomainStatus
from app.services.scanner import DomainScanner
from app.services.notification import notify_bark

router = APIRouter()


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
    mode: str = 'domainsdb',  # 默认使用 DomainDB + OpenPageRank
    bark_key: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    触发域名扫描任务
    
    mode 参数:
    - 'mock': 模拟数据（快速测试）
    - 'domainsdb': DomainDB + OpenPageRank（推荐，免费）
    - 'expireddomains': ExpiredDomains.net（需配置密码）
    - 'mixed': 混合两种数据源（最全面）
    """
    try:
        print(f"🔍 Starting scan with mode: {mode}")
        
        # 初始化扫描器
        scanner = DomainScanner(mode=mode)
        found_domains = scanner.scan()
        
        print(f"📦 Scanner returned {len(found_domains)} domains")
        
        new_count = 0
        high_value_domains = []
        
        for domain_data in found_domains:
            # 检查是否已存在
            existing = db.query(Domain).filter(Domain.name == domain_data['name']).first()
            if existing:
                print(f"⏭️ Domain {domain_data['name']} already exists, skipping")
                continue
            
            # 创建新域名记录
            domain = Domain(
                name=domain_data['name'],
                da_score=domain_data['da_score'],
                backlinks=domain_data['backlinks'],
                spam_score=domain_data['spam_score'],
                status=DomainStatus.AVAILABLE,
                drop_date=domain_data['drop_date'],
                tld=domain_data['tld'],
                length=domain_data['length']
            )
            
            db.add(domain)
            new_count += 1
            
            # 收集高价值域名用于通知
            if domain_data['da_score'] >= 40 and domain_data['spam_score'] < 10:
                high_value_domains.append(domain_data)
        
        db.commit()
        
        # 发送 Bark 通知（如果提供了 Key）
        if bark_key and high_value_domains:
            try:
                for domain_data in high_value_domains[:3]:  # 最多通知 3 个
                    notify_bark(
                        bark_key=bark_key,
                        title="🚨 高价值域名发现",
                        content=f"{domain_data['name']} | DA:{domain_data['da_score']} | Spam:{domain_data['spam_score']}%",
                        url=f"https://www.namecheap.com/domains/registration/results/?domain={domain_data['name']}"
                    )
            except Exception as notify_error:
                print(f"⚠️ Bark notification failed: {notify_error}")
        
        print(f"✅ Scan completed. Added {new_count} new domains to database.")
        
        return {
            "status": "success",
            "domains_found": new_count,
            "message": f"扫描完成，发现 {new_count} 个新域名（模式：{mode}）"
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