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
    mode: str = 'domainsdb',
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
        
        scanner = DomainScanner(mode=mode)
        found_domains = scanner.scan()
        
        print(f"📦 Scanner returned {len(found_domains)} domains")
        
        new_count = 0
        high_value_domains = []
        
        for domain_data in found_domains:
            existing = db.query(Domain).filter(Domain.name == domain_data['name']).first()
            if existing:
                print(f"⏭️ Domain {domain_data['name']} already exists, skipping")
                continue
            
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
            
            if domain_data['da_score'] >= 40 and domain_data['spam_score'] < 10:
                high_value_domains.append(domain_data)
        
        db.commit()
        
        if bark_key and high_value_domains:
            try:
                for domain_data in high_value_domains[:3]:
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


# 🆕 删除功能 - 注意路由顺序！

@router.delete("/domains/all")
def clear_all_domains(db: Session = Depends(get_db)):
    """清空所有域名"""
    try:
        count = db.query(Domain).count()
        db.query(Domain).delete()
        db.commit()
        
        print(f"🗑️ Cleared all {count} domains from database")
        
        return {"status": "success", "message": f"已清空 {count} 个域名"}
        
    except Exception as e:
        db.rollback()
        print(f"❌ Clear all failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/domains/{domain_id}")
def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    """删除指定域名"""
    try:
        domain = db.query(Domain).filter(Domain.id == domain_id).first()
        
        if not domain:
            raise HTTPException(status_code=404, detail="域名不存在")
        
        domain_name = domain.name
        db.delete(domain)
        db.commit()
        
        print(f"🗑️ Deleted domain: {domain_name} (ID: {domain_id})")
        
        return {"status": "success", "message": f"已删除域名: {domain_name}"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))