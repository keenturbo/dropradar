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
    """获取域名列表"""
    domains = db.query(Domain).order_by(Domain.created_at.desc()).offset(skip).limit(limit).all()
    return domains


@router.get("/domains/{domain_id}")
def get_domain(domain_id: int, db: Session = Depends(get_db)):
    """获取单个域名详情"""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="域名不存在")
    return domain


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """获取统计信息"""
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
    """扫描域名"""
    scanner = DomainScanner(mode=mode)
    result = await scanner.scan()  # 返回 {all_domains: [...], top_5: [...]}
    
    all_domains = result.get("all_domains", [])
    top_5 = result.get("top_5", [])
    
    # 🔥 新增：准备返回给前端的域名列表
    return_domains = []
    
    # 数据库保存（确保不重复）
    new_count = 0
    updated_count = 0
    
    for domain_data in all_domains:
        try:
            # 检查是否已存在
            existing = db.query(Domain).filter(Domain.name == domain_data['name']).first()
            
            if existing:
                # 更新现有记录
                existing.da_score = domain_data.get('da_score', existing.da_score)
                existing.backlinks = domain_data.get('backlinks', existing.backlinks)
                existing.status = domain_data.get('status', existing.status)
                existing.drop_date = domain_data.get('drop_date', existing.drop_date)
                updated_count += 1
                
                # 🔥 添加到返回列表（转换为字典）
                return_domains.append({
                    "id": existing.id,
                    "name": existing.name,
                    "da_score": existing.da_score,
                    "backlinks": existing.backlinks,
                    "status": existing.status,
                    "drop_date": existing.drop_date.isoformat() if existing.drop_date else None,
                    "created_at": existing.created_at.isoformat() if existing.created_at else None
                })
            else:
                # 新增记录
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
                db.flush()  # 🔥 立即获取 ID
                new_count += 1
                
                # 🔥 添加到返回列表
                return_domains.append({
                    "id": new_domain.id,
                    "name": new_domain.name,
                    "da_score": new_domain.da_score,
                    "backlinks": new_domain.backlinks,
                    "status": new_domain.status,
                    "drop_date": new_domain.drop_date.isoformat() if new_domain.drop_date else None,
                    "created_at": new_domain.created_at.isoformat() if new_domain.created_at else None
                })
                
        except Exception as e:
            logger.error(f"保存域名 {domain_data.get('name')} 失败: {e}")
            continue
    
    try:
        db.commit()
        logger.info(f"✅ 数据库保存：新增 {new_count} 个域名，更新 {updated_count} 个")
    except Exception as e:
        db.rollback()
        logger.error(f"数据库提交失败: {e}")
        raise HTTPException(status_code=500, detail=f"数据库保存失败: {str(e)}")
    
    # 🔥 返回本次扫描到的域名列表（前端直接展示）
    return {
        "message": f"扫描完成：新增 {new_count} 个域名，更新 {updated_count} 个域名",
        "new_count": new_count,
        "updated_count": updated_count,
        "total": len(return_domains),
        "domains": return_domains,  # 本次扫描的所有域名
        "top_5": return_domains[:5]  # Top 5
    }