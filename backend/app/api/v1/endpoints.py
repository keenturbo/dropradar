from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from typing import List

from app.database import get_db
from app.models.domain import Domain
from app.schemas.domain import DomainResponse, DomainCreate, DomainUpdate
from app.services.scanner import DomainScanner

router = APIRouter(
    prefix="/api/v1",
    tags=["domains"],
)


@router.get("/domains")
def get_all_domains(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取所有域名列表（分页）"""
    domains = db.query(Domain).offset(skip).limit(limit).all()
    return {
        "domains": domains,
        "total": db.query(Domain).count(),
        "skip": skip,
        "limit": limit
    }


@router.get("/domains/top5", response_model=List[DomainResponse])
def get_top5_domains(db: Session = Depends(get_db)):
    """获取质量最高的 Top 5 域名"""
    domains = db.query(Domain).order_by(
        Domain.quality_score.desc()
    ).limit(5).all()
    
    if not domains:
        raise HTTPException(status_code=404, detail="No domains found")
    
    return domains


@router.get("/domains/{domain_name}", response_model=DomainResponse)
def get_domain_by_name(domain_name: str, db: Session = Depends(get_db)):
    """获取特定域名详情"""
    domain = db.query(Domain).filter(Domain.name == domain_name).first()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    return domain


@router.post("/domains", response_model=DomainResponse)
def create_domain(domain: DomainCreate, db: Session = Depends(get_db)):
    """手动创建单个域名记录"""
    
    # 检查是否已存在
    existing = db.query(Domain).filter(Domain.name == domain.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Domain already exists")
    
    db_domain = Domain(**domain.dict())
    db.add(db_domain)
    db.commit()
    db.refresh(db_domain)
    
    return db_domain


@router.put("/domains/{domain_name}", response_model=DomainResponse)
def update_domain(
    domain_name: str,
    domain_update: DomainUpdate,
    db: Session = Depends(get_db)
):
    """更新域名信息"""
    
    db_domain = db.query(Domain).filter(Domain.name == domain_name).first()
    
    if not db_domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    update_data = domain_update.dict(exclude_unset=True)
    update_data['updated_at'] = datetime.now()
    
    for key, value in update_data.items():
        setattr(db_domain, key, value)
    
    db.commit()
    db.refresh(db_domain)
    
    return db_domain


@router.delete("/domains/{domain_id}")
def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    """删除域名记录"""
    
    db_domain = db.query(Domain).filter(Domain.id == domain_id).first()
    
    if not db_domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    db.delete(db_domain)
    db.commit()
    
    return {"message": f"Domain deleted successfully"}


@router.delete("/domains/all")
def clear_all_domains(db: Session = Depends(get_db)):
    """清空所有域名"""
    
    count = db.query(Domain).count()
    db.query(Domain).delete()
    db.commit()
    
    return {"status": "success", "message": f"Deleted {count} domains"}


@router.post("/scan")
def scan_domains(mode: str = Query("expireddomains"), db: Session = Depends(get_db)):
    """
    执行域名扫描任务
    
    参数：
    - mode: 扫描模式（目前支持 expireddomains）
    
    流程：
    1. 从 ExpiredDomains.net 抓取 4 页（100 个域名）
    2. 批量获取 DA 分数
    3. 计算综合质量分数
    4. 返回 Top 5，保存到数据库
    """
    
    print("\n" + "="*80)
    print(f"🚀 开始执行域名扫描任务（模式: {mode}）...")
    print("="*80 + "\n")
    
    scanner = DomainScanner(mode=mode)
    top_domains = scanner.scan()  # 返回 Top 5
    
    if not top_domains:
        raise HTTPException(status_code=500, detail="Scan failed, no domains found")
    
    # 保存到数据库
    for domain_data in top_domains:
        domain_name = domain_data['name']
        
        # 检查是否已存在
        existing = db.query(Domain).filter(Domain.name == domain_name).first()
        
        if existing:
            # 更新现有记录
            existing.da_score = domain_data['da_score']
            existing.backlinks = domain_data['backlinks']
            existing.referring_domains = domain_data['referring_domains']
            existing.quality_score = domain_data['quality_score']
            existing.price = domain_data['price']
            existing.bids = domain_data['bids']
            existing.wikipedia_links = domain_data['wikipedia_links']
            existing.domain_age = domain_data['domain_age']
            existing.spam_score = domain_data['spam_score']
            existing.last_seen = datetime.now()
            existing.updated_at = datetime.now()
            existing.is_new = False
            
            print(f"🔄 更新已存在的域名: {domain_name}")
            
        else:
            # 创建新记录
            db_domain = Domain(
                name=domain_name,
                da_score=domain_data['da_score'],
                backlinks=domain_data['backlinks'],
                referring_domains=domain_data['referring_domains'],
                spam_score=domain_data['spam_score'],
                status='available',
                drop_date=domain_data['drop_date'],
                tld=domain_data['tld'],
                length=domain_data['length'],
                domain_age=domain_data['domain_age'],
                price=domain_data['price'],
                bids=domain_data['bids'],
                wikipedia_links=domain_data['wikipedia_links'],
                quality_score=domain_data['quality_score'],
                is_new=True,
                notified=False
            )
            db.add(db_domain)
            
            print(f"✨ 保存新域名: {domain_name}")
    
    db.commit()
    
    # 刷新数据获取最新状态
    top5_from_db = db.query(Domain).order_by(
        Domain.quality_score.desc()
    ).limit(5).all()
    
    print("\n" + "="*80)
    print("✅ 扫描完成，已保存 Top 5 到数据库")
    print("="*80 + "\n")
    
    return {
        "status": "success",
        "message": "✅ Scan completed and Top 5 domains saved to database",
        "mode": mode,
        "total_scanned": 100,
        "top_domains_saved": len(top_domains),
        "top_5_domains": [
            {
                "name": d.name,
                "quality_score": d.quality_score,
                "da_score": d.da_score,
                "backlinks": d.backlinks,
                "referring_domains": d.referring_domains,
                "price": d.price,
                "bids": d.bids,
                "domain_age": d.domain_age,
                "wikipedia_links": d.wikipedia_links,
                "is_new": d.is_new,
                "created_at": d.created_at.isoformat()
            }
            for d in top5_from_db
        ]
    }


@router.post("/scan-top5")
def scan_and_save_top5(db: Session = Depends(get_db)):
    """
    执行扫描：抓取 4 页（100 个域名），计算质量分数，保存 Top 5 到数据库
    
    流程：
    1. 从 ExpiredDomains.net 抓取 4 页（100 个域名）
    2. 批量获取 DA 分数
    3. 计算综合质量分数
    4. 返回 Top 5，保存到数据库
    """
    
    print("\n" + "="*80)
    print("🚀 开始执行域名扫描任务...")
    print("="*80 + "\n")
    
    scanner = DomainScanner(mode='expireddomains')
    top_domains = scanner.scan()  # 返回 Top 5
    
    if not top_domains:
        raise HTTPException(status_code=500, detail="Scan failed, no domains found")
    
    # 保存到数据库
    for domain_data in top_domains:
        domain_name = domain_data['name']
        
        # 检查是否已存在
        existing = db.query(Domain).filter(Domain.name == domain_name).first()
        
        if existing:
            # 更新现有记录
            existing.da_score = domain_data['da_score']
            existing.backlinks = domain_data['backlinks']
            existing.referring_domains = domain_data['referring_domains']
            existing.quality_score = domain_data['quality_score']
            existing.price = domain_data['price']
            existing.bids = domain_data['bids']
            existing.wikipedia_links = domain_data['wikipedia_links']
            existing.domain_age = domain_data['domain_age']
            existing.spam_score = domain_data['spam_score']
            existing.last_seen = datetime.now()
            existing.updated_at = datetime.now()
            existing.is_new = False
            
            print(f"🔄 更新已存在的域名: {domain_name}")
            
        else:
            # 创建新记录
            db_domain = Domain(
                name=domain_name,
                da_score=domain_data['da_score'],
                backlinks=domain_data['backlinks'],
                referring_domains=domain_data['referring_domains'],
                spam_score=domain_data['spam_score'],
                status='available',
                drop_date=domain_data['drop_date'],
                tld=domain_data['tld'],
                length=domain_data['length'],
                domain_age=domain_data['domain_age'],
                price=domain_data['price'],
                bids=domain_data['bids'],
                wikipedia_links=domain_data['wikipedia_links'],
                quality_score=domain_data['quality_score'],
                is_new=True,
                notified=False
            )
            db.add(db_domain)
            
            print(f"✨ 保存新域名: {domain_name}")
    
    db.commit()
    
    # 刷新数据获取最新状态
    top5_from_db = db.query(Domain).order_by(
        Domain.quality_score.desc()
    ).limit(5).all()
    
    print("\n" + "="*80)
    print("✅ 扫描完成，已保存 Top 5 到数据库")
    print("="*80 + "\n")
    
    return {
        "status": "success",
        "message": "✅ Scan completed and Top 5 domains saved to database",
        "total_scanned": 100,
        "top_domains_saved": len(top_domains),
        "top_5_domains": [
            {
                "name": d.name,
                "quality_score": d.quality_score,
                "da_score": d.da_score,
                "backlinks": d.backlinks,
                "referring_domains": d.referring_domains,
                "price": d.price,
                "bids": d.bids,
                "domain_age": d.domain_age,
                "wikipedia_links": d.wikipedia_links,
                "is_new": d.is_new,
                "created_at": d.created_at.isoformat()
            }
            for d in top5_from_db
        ]
    }


@router.get("/stats")
def get_domain_stats(db: Session = Depends(get_db)):
    """获取域名统计数据"""
    
    total = db.query(Domain).count()
    new_domains = db.query(Domain).filter(Domain.is_new == True).count()
    notified = db.query(Domain).filter(Domain.notified == True).count()
    
    # 平均质量分数
    avg_quality = db.query(func.avg(Domain.quality_score)).scalar() or 0
    
    # 平均 DA 分数
    avg_da = db.query(func.avg(Domain.da_score)).scalar() or 0
    
    # 平均价格
    avg_price = db.query(func.avg(Domain.price)).scalar() or 0
    
    return {
        "total": total,
        "avg_da": round(avg_da, 1),
        "available": total,
        "low_spam": db.query(Domain).filter(Domain.spam_score < 10).count()
    }


@router.get("/domains/filter/by-quality")
def filter_domains_by_quality(
    min_score: float = 50.0,
    max_score: float = 100.0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """按质量分数范围筛选域名"""
    
    domains = db.query(Domain).filter(
        Domain.quality_score >= min_score,
        Domain.quality_score <= max_score
    ).order_by(Domain.quality_score.desc()).limit(limit).all()
    
    return domains


@router.get("/domains/filter/by-da")
def filter_domains_by_da(
    min_da: int = 10,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """按 DA 分数筛选域名"""
    
    domains = db.query(Domain).filter(
        Domain.da_score >= min_da
    ).order_by(Domain.da_score.desc()).limit(limit).all()
    
    return domains


@router.get("/domains/filter/by-price")
def filter_domains_by_price(
    min_price: int = 0,
    max_price: int = 5000,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """按价格范围筛选域名"""
    
    domains = db.query(Domain).filter(
        Domain.price >= min_price,
        Domain.price <= max_price
    ).order_by(Domain.quality_score.desc()).limit(limit).all()
    
    return domains
