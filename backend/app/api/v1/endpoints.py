from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.models.domain import Domain, DomainStatus
from app.schemas.domain import DomainResponse, ScanRequest
from app.services.scanner import DomainScanner
from app.services.notification import notify_high_value_domain
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/domains", response_model=List[DomainResponse])
def get_domains(
    skip: int = 0,
    limit: int = 100,
    min_da: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get list of discovered domains
    
    Query Parameters:
    - skip: Pagination offset
    - limit: Max results (default 100)
    - min_da: Filter by minimum DA score
    """
    query = db.query(Domain)
    
    if min_da > 0:
        query = query.filter(Domain.da_score >= min_da)
    
    domains = query.order_by(Domain.da_score.desc()).offset(skip).limit(limit).all()
    return domains


@router.post("/scan")
async def trigger_scan(
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger manual domain scan
    
    This endpoint:
    1. Fetches expired domains from data sources
    2. Filters based on SEO criteria
    3. Saves to database
    4. Sends Bark notifications for high-value finds
    """
    try:
        scanner = DomainScanner()
        
        # Fetch domains based on criteria
        domains_data = scanner.fetch_expired_domains(
            min_da=scan_request.min_da,
            max_spam=scan_request.max_spam,
            min_backlinks=scan_request.min_backlinks
        )
        
        saved_count = 0
        notified_count = 0
        
        for domain_data in domains_data:
            # Check if domain already exists
            existing = db.query(Domain).filter(Domain.name == domain_data['name']).first()
            
            if not existing:
                # Create new domain record
                domain = Domain(
                    name=domain_data['name'],
                    da_score=domain_data['da_score'],
                    backlinks=domain_data['backlinks'],
                    spam_score=domain_data['spam_score'],
                    status=DomainStatus(domain_data['status']),
                    drop_date=domain_data.get('drop_date'),
                    length=len(domain_data['name'].split('.')[0]),
                    tld='.' + domain_data['name'].split('.')[-1]
                )
                
                db.add(domain)
                saved_count += 1
                
                # Send notification for high-value domains
                if domain.da_score >= 30 and domain.spam_score < 8:
                    if settings.BARK_KEY:
                        background_tasks.add_task(
                            notify_high_value_domain,
                            settings.BARK_KEY,
                            domain_data
                        )
                        notified_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Scan completed",
            "results": {
                "total_found": len(domains_data),
                "new_saved": saved_count,
                "notifications_sent": notified_count
            }
        }
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Get dashboard statistics
    """
    total = db.query(Domain).count()
    available = db.query(Domain).filter(Domain.status == DomainStatus.AVAILABLE).count()
    
    avg_da = db.query(Domain).with_entities(
        db.func.avg(Domain.da_score)
    ).scalar() or 0
    
    low_spam = db.query(Domain).filter(Domain.spam_score < 10).count()
    
    return {
        "total_domains": total,
        "available": available,
        "average_da": round(avg_da, 1),
        "low_spam": low_spam
    }


@router.post("/test-notification")
def test_bark_notification():
    """
    Test Bark notification
    """
    if not settings.BARK_KEY:
        raise HTTPException(status_code=400, detail="Bark key not configured")
    
    from app.services.notification import notify_bark
    
    success = notify_bark(
        bark_key=settings.BARK_KEY,
        title="DropRadar 测试通知",
        content="系统运行正常 ✅",
        url="https://github.com/keenturbo/dropradar"
    )
    
    if success:
        return {"success": True, "message": "Notification sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send notification")
