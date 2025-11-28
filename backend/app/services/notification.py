import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def notify_bark(bark_key: str, title: str, content: str, url: Optional[str] = None) -> bool:
    """
    Send notification via Bark (iOS push notification service)
    
    Args:
        bark_key: User's Bark API key
        title: Notification title
        content: Notification body
        url: Optional URL to open when notification is tapped
        
    Returns:
        Success status
        
    Example:
        notify_bark(
            bark_key="your_key_here",
            title="🚨 High Value Domain",
            content="gemini4.com | DA:45 | Available",
            url="https://namecheap.com/domains/registration/results/?domain=gemini4.com"
        )
    """
    if not bark_key:
        logger.warning("Bark key not configured")
        return False
    
    try:
        # Bark API endpoint
        api_url = f"https://api.day.app/{bark_key}/{title}/{content}"
        
        params = {}
        if url:
            params['url'] = url
        
        # Add notification sound (optional)
        params['sound'] = 'alarm'
        
        response = requests.get(api_url, params=params, timeout=5)
        
        if response.status_code == 200:
            logger.info(f"Bark notification sent: {title}")
            return True
        else:
            logger.error(f"Bark API error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send Bark notification: {e}")
        return False


def notify_high_value_domain(bark_key: str, domain: dict) -> bool:
    """
    Send formatted notification for high-value domain
    
    Args:
        bark_key: User's Bark API key
        domain: Domain data dictionary
        
    Returns:
        Success status
    """
    title = "🚨 高价值域名过期"
    content = f"{domain['name']} | DA:{domain['da_score']} | 外链:{domain['backlinks']}"
    url = f"https://www.namecheap.com/domains/registration/results/?domain={domain['name']}"
    
    return notify_bark(bark_key, title, content, url)
