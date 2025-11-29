from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.database import get_db, Domain
from app.services.scanner import DomainScanner
from app.schemas.domain import DomainCreate, DomainResponse

router = APIRouter()


@router.get("/domains", response_model=List[DomainResponse])
def get_domains(
    skip: int = 0,
    limit: int = 100,
    min_da: int = Query(default=0, ge=0, le=100),
    db: Session = Depends(get_db)
):
    """获取域名列表（支持分页和 DA 过滤）"""
    query = db.query(Domain)
    
    if min_da > 0:
        query = query.filter(Domain.da_score >= min_da)
    
    domains = query.order_by(Domain.quality_score.desc()).offset(skip).limit(limit).all()
    return domains


@router.delete("/domains/all")
def delete_all_domains(db: Session = Depends(get_db)):
    """删除所有域名（危险操作）"""
    count = db.query(Domain).delete()
    db.commit()
    return {"status": "success", "deleted_count": count}


@router.post("/scan-top5")
async def scan_top5(db: Session = Depends(get_db)):
    """扫描并返回 Top 5 高质量域名"""
    return await scan_domains(mode="expireddomains", db=db)


@router.post("/scan")
async def scan_domains(
    mode: str = Query(default="expireddomains"),
    db: Session = Depends(get_db)
):
    """扫描域名（支持 mode 参数）"""
    scanner = DomainScanner(mode=mode)
    result = scanner.scan()  # 返回 {all_domains: [...], top_5: [...]}
    
    all_domains = result.get("all_domains", [])
    top_5 = result.get("top_5", [])
    
    # ===== 批量存入数据库（去重）=====
    saved_count = 0
    updated_count = 0
    
    for domain_data in all_domains:
        # 检查是否已存在
        existing = db.query(Domain).filter(Domain.name == domain_data['name']).first()
        
        if existing:
            # 更新现有记录（更新 DA、外链等数据）
            existing.da_score = domain_data.get('da_score', 0)
            existing.backlinks = domain_data.get('backlinks', 0)
            existing.referring_domains = domain_data.get('referring_domains', 0)
            existing.spam_score = domain_data.get('spam_score', 0)
            existing.quality_score = domain_data.get('quality_score', 0)
            existing.price = domain_data.get('price', 0)
            existing.bids = domain_data.get('bids', 0)
            existing.wikipedia_links = domain_data.get('wikipedia_links', 0)
            existing.domain_age = domain_data.get('domain_age', 0)
            updated_count += 1
        else:
            # 新增记录
            new_domain = Domain(
                name=domain_data['name'],
                da_score=domain_data.get('da_score', 0),
                backlinks=domain_data.get('backlinks', 0),
                referring_domains=domain_data.get('referring_domains', 0),
                spam_score=domain_data.get('spam_score', 0),
                drop_date=domain_data.get('drop_date'),
                tld=domain_data.get('tld', ''),
                length=domain_data.get('length', 0),
                domain_age=domain_data.get('domain_age', 0),
                price=domain_data.get('price', 0),
                bids=domain_data.get('bids', 0),
                wikipedia_links=domain_data.get('wikipedia_links', 0),
                quality_score=domain_data.get('quality_score', 0)
            )
            db.add(new_domain)
            saved_count += 1
    
    db.commit()
    
    print(f"✅ 数据库保存：新增 {saved_count} 个域名，更新 {updated_count} 个")
    
    return {
        "status": "success",
        "total_scanned": len(all_domains),
        "saved_to_db": saved_count,
        "updated_in_db": updated_count,
        "top_5": top_5
    }


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """获取统计信息"""
    total = db.query(Domain).count()
    high_quality = db.query(Domain).filter(Domain.da_score >= 30).count()
    
    recent_7days = db.query(Domain).filter(
        Domain.created_at >= datetime.now() - timedelta(days=7)
    ).count()
    
    return {
        "total_domains": total,
        "high_quality_domains": high_quality,
        "recent_7days": recent_7days
    }


@router.delete("/domains/{domain_id}")
def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    """删除指定域名"""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    db.delete(domain)
    db.commit()
    
    return {"status": "success", "message": f"Deleted domain: {domain.name}"}