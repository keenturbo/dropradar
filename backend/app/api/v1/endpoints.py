from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database import get_db
from app.models.domain import Domain
from app.services.scanner import DomainScanner

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/domains")
def get_domains(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取域名列表（优先显示新域名）"""
    domains = db.query(Domain)\
        .order_by(Domain.is_new.desc(), Domain.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    return domains


@router.get("/domains/{domain_id}")
def get_domain(domain_id: int, db: Session = Depends(get_db)):
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="域名不存在")
    return domain


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_domains = db.query(Domain).count()
    new_domains = db.query(Domain).filter(Domain.is_new == True).count()
    avg_da = db.query(Domain).with_entities(Domain.da_score).all()
    avg_da_score = sum([d[0] for d in avg_da if d[0]]) / len(avg_da) if avg_da else 0
    
    return {
        "total_domains": total_domains,
        "new_domains": new_domains,
        "avg_da_score": round(avg_da_score, 2)
    }


@router.post("/scan")
async def scan_domains(mode: str = "expireddomains", db: Session = Depends(get_db)):
    """扫描域名 - 直接返回域名列表"""
    logger.info(f"🔍 开始扫描 (mode={mode})")
    scanner = DomainScanner(mode=mode)
    result = await scanner.scan()
    
    all_domains = result.get("all_domains", [])
    
    # 准备返回列表
    return_domains = []
    
    for domain_data in all_domains:
        try:
            # 查重
            existing = db.query(Domain).filter(Domain.name == domain_data['name']).first()
            
            if existing:
                # 更新
                existing.da_score = domain_data.get('da_score', existing.da_score)
                existing.backlinks = domain_data.get('backlinks', existing.backlinks)
                existing.status = domain_data.get('status', existing.status)
                existing.drop_date = domain_data.get('drop_date', existing.drop_date)
                existing.is_new = True # 重新标记为新
                
                return_domains.append(existing)
            else:
                # 新增
                new_domain = Domain(
                    name=domain_data['name'],
                    tld=domain_data.get('tld', ''),
                    length=domain_data.get('length', 0),
                    da_score=domain_data.get('da_score', 0),
                    backlinks=domain_data.get('backlinks', 0),
                    status=domain_data.get('status', 'pending'),
                    drop_date=domain_data.get('drop_date'),
                    is_new=True
                )
                db.add(new_domain)
                db.flush()
                return_domains.append(new_domain)
                
        except Exception as e:
            logger.error(f"保存失败: {e}")
            continue
    
    try:
        # 标记其他旧域名为 is_new=False
        db.query(Domain).filter(
            Domain.is_new == True,
            Domain.id.notin_([d.id for d in return_domains])
        ).update({'is_new': False})
        
        db.commit()
        logger.info(f"✅ 成功处理 {len(return_domains)} 个域名")
    except Exception as e:
        db.rollback()
        logger.error(f"数据库提交失败: {e}")
    
    # 🔥🔥🔥 关键修改：直接返回列表，而不是字典！
    return return_domains