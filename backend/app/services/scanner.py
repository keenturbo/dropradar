import asyncio
import logging
import random
import re
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import whois
import requests
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup
from app.core.config import settings
from app.database import SessionLocal
from app.models.domain import Domain

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENPAGERANK_API_KEY = settings.OPENPAGERANK_API_KEY if hasattr(settings, 'OPENPAGERANK_API_KEY') else "w00wkkkwo4c4sws4swggkswk8oksggsccck0go84"

class DomainScanner:
    def __init__(self, mode: str = "expireddomains"):
        """
        初始化扫描器
        :param mode: 扫描模式，默认 "expireddomains"
        """
        self.db = SessionLocal()
        self.mode = mode

    def verify_expiry_date_via_whois(self, domain_name: str) -> Dict:
        """
        验证域名的真实到期时间
        返回: {'real_expiry': datetime, 'is_expired': bool, 'is_valid': bool}
        """
        try:
            w = whois.whois(domain_name)
            
            # 处理 whois 返回的日期可能是列表的情况
            expiry_date = w.expiration_date
            if isinstance(expiry_date, list):
                expiry_date = expiry_date[0]
                
            if not expiry_date:
                return {'real_expiry': None, 'is_expired': False, 'is_valid': False}
                
            now = datetime.now()
            is_expired = expiry_date < now
            
            return {
                'real_expiry': expiry_date,
                'is_expired': is_expired,
                'is_valid': True
            }
        except Exception as e:
            return {'real_expiry': None, 'is_expired': False, 'is_valid': False}

    def extract_number(self, text: str) -> int:
        """正则提取数字，处理 1.8K、1,992 等格式"""
        if not text:
            return 0
        
        match = re.search(r'(\d+(?:\.\d+)?)\s*K', text.upper())
        if match:
            return int(float(match.group(1)) * 1000)
        
        match = re.search(r'(\d[\d,]*)', text)
        if match:
            return int(match.group(1).replace(',', ''))
        
        return 0

    def batch_get_pagerank(self, domain_names: List[str]) -> Dict[str, int]:
        """批量获取 DA 分数（通过 OpenPageRank API）"""
        if not domain_names:
            return {}
        
        results = {}
        batch_size = 100
        
        logger.info(f"🔍 开始批量获取 {len(domain_names)} 个域名的 DA 分数...")
        
        for i in range(0, len(domain_names), batch_size):
            batch = domain_names[i:i+batch_size]
            
            params = {f"domains[{j}]": domain for j, domain in enumerate(batch)}
            
            try:
                response = requests.get(
                    "https://openpagerank.com/api/v1.0/getPageRank",
                    params=params,
                    headers={'API-OPR': OPENPAGERANK_API_KEY},
                    timeout=10
                )
                
                data = response.json()
                
                if data.get('status_code') == 200 and data.get('response'):
                    for item in data['response']:
                        domain = item['domain']
                        page_rank = item.get('page_rank_decimal', 0)
                        da_score = int(page_rank * 10)
                        results[domain] = da_score
                        logger.info(f"  ✅ {domain} → DA: {da_score}")
                    
                    logger.info(f"✅ 批次完成: 成功获取 {len(batch)} 个域名的 DA")
                else:
                    logger.warning(f"⚠️ OpenPageRank API 错误: {data}")
                    for domain in batch:
                        results[domain] = 0
                
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ 批量获取 DA 失败: {e}")
                for domain in batch:
                    results[domain] = 0
        
        return results

    async def fetch_single_page(self, page: int, retries=3) -> List[Dict]:
        """抓取单页数据（带重试）"""
        url = "https://member.expireddomains.net/domains/expiredcom/"
        cookies = {
            "s_id": settings.EXPIRED_DOMAINS_COOKIE
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": "https://member.expireddomains.net/domains/expiredcom/"
        }

        # 计算分页参数
        start = (page - 1) * 25
        params = {
            "start": start,
            "flimit": 25,
            "fwhois": "1",
            "fmarket": "0",
            "flast24": "1"
        }

        for attempt in range(retries):
            try:
                try:
                    async with AsyncSession() as session:
                        resp = await session.get(url, params=params, cookies=cookies, headers=headers, timeout=30)
                        
                        if resp.status_code != 200:
                            logger.warning(f"Page {page} failed with status {resp.status_code}")
                            continue
                            
                        content = resp.text
                except RuntimeError:
                    pass
                except Exception as e:
                    logger.error(f"Request error on page {page}: {e}")
                    continue

                domains = []
                soup = BeautifulSoup(content, 'html.parser')
                rows = soup.select('table.base1 tbody tr')
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) < 2:
                        continue
                        
                    domain_name = cols[0].get_text(strip=True)
                    
                    bl = 0
                    try:
                        bl_text = cols[2].get_text(strip=True)
                        bl = self.extract_number(bl_text)
                    except:
                        pass

                    domains.append({
                        "name": domain_name,
                        "backlinks": bl,
                        "da_score": 0,
                        "status": "pending"
                    })
                
                logger.info(f"✅ 第 {page} 页：成功解析 {len(domains)} 个域名")
                return domains

            except Exception as e:
                logger.error(f"Attempt {attempt+1} failed for page {page}: {str(e)}")
                await asyncio.sleep(2)
        
        return []

    async def fetch_expireddomains_multi_pages(self, pages=4) -> List[Dict]:
        """并发抓取多页"""
        logger.info(f"🚀 开始抓取前 {pages} 页（共约 {pages*25} 个域名）...")
        tasks = [self.fetch_single_page(page) for page in range(1, pages + 1)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_domains = []
        for res in results:
            if isinstance(res, list):
                all_domains.extend(res)
        
        logger.info(f"✅ 共抓取 {len(all_domains)} 个域名")
        
        # 🔥 新增：抓取到的域名立即全部存入数据库
        if all_domains:
            logger.info(f"💾 开始将 {len(all_domains)} 个抓取域名存入数据库...")
            saved_count = 0
            for d in all_domains:
                try:
                    exists = self.db.query(Domain).filter(Domain.name == d['name']).first()
                    if not exists:
                        new_domain = Domain(
                            name=d['name'],
                            da_score=d.get('da_score', 0),
                            backlinks=d.get('backlinks', 0),
                            status='scraped',  # 标记为爬取的
                            drop_date=None
                        )
                        self.db.add(new_domain)
                        saved_count += 1
                except Exception as e:
                    logger.error(f"保存域名 {d['name']} 失败: {e}")
                    continue
            
            try:
                self.db.commit()
                logger.info(f"✅ 成功将 {saved_count} 个抓取域名存入数据库")
            except Exception as e:
                self.db.rollback()
                logger.error(f"批量保存失败: {e}")
        
        return all_domains

    def generate_mock_domains(self, count=20) -> List[Dict]:
        """B层：生成模拟的高质量域名（确保唯一）"""
        logger.info(f"⚠️ [B 层] 触发降级：生成 {count} 个模拟域名")
        
        TECH_KEYWORDS = ["ai", "gpt", "gemini", "claude", "quantum", "neural", "crypto", "defi", "metaverse"]
        PREFIXES = ["super", "ultra", "mega", "next", "smart", "auto", "hyper"]
        SUFFIXES = ["hub", "lab", "flow", "cloud", "stack", "forge", "sphere"]
        
        mock_domains = []
        
        for i in range(count):
            # 使用 UUID 确保唯一性
            unique_suffix = str(uuid.uuid4())[:8]
            
            pattern = random.choice([
                f"{random.choice(TECH_KEYWORDS)}-{unique_suffix}",
                f"{random.choice(PREFIXES)}{random.choice(TECH_KEYWORDS)}-{unique_suffix}",
                f"{random.choice(TECH_KEYWORDS)}{random.choice(SUFFIXES)}-{unique_suffix}"
            ])
            
            tld = random.choice([".com", ".ai", ".io", ".net"])
            d_name = pattern + tld
            
            mock_domains.append({
                "name": d_name,
                "da_score": random.randint(25, 65),
                "backlinks": random.randint(50, 500),
                "status": "mock",  # 标记为模拟的
                "drop_date": datetime.now() + timedelta(days=random.randint(1, 30))
            })
            
            logger.info(f"  🎭 生成: {d_name} (DA: {mock_domains[-1]['da_score']})")
            
        return mock_domains

    async def scan(self):
        """主扫描逻辑：A -> B 降级"""
        logger.info("🚀 开始二层降级扫描...")
        
        final_results = []
        
        # --- A 层：真实爬虫（100个域名全存库）---
        logger.info("🕷️ [A 层] 抓取 ExpiredDomains.net")
        raw_domains = await self.fetch_expireddomains_multi_pages(pages=4)
        
        if raw_domains:
            # 1. 批量获取真实 DA 分数（仅对 Top 20）
            logger.info(f"🔍 开始获取 Top 20 的 DA 分数...")
            top_20 = sorted(raw_domains, key=lambda x: x.get('backlinks', 0), reverse=True)[:20]
            domain_names = [d['name'] for d in top_20]
            da_scores = self.batch_get_pagerank(domain_names)
            
            for d in top_20:
                d['da_score'] = da_scores.get(d['name'], 0)
                
            # 2. 按 DA 排序取 Top 5
            top_domains = sorted(top_20, key=lambda x: x['da_score'], reverse=True)[:5]
            
            # 3. WHOIS 验证
            logger.info("🔍 对 Top 5 进行 WHOIS 验证...")
            valid_a_domains = []
            for d in top_domains:
                logger.info(f"Checking {d['name']}...")
                verify_res = self.verify_expiry_date_via_whois(d['name'])
                
                if verify_res['is_expired']:
                    logger.info(f"✅ 验证通过: {d['name']} (过期日: {verify_res['real_expiry']})")
                    d['drop_date'] = verify_res['real_expiry']
                    d['status'] = 'expired_confirmed'
                    valid_a_domains.append(d)
                else:
                    logger.info(f"❌ 已续费: {d['name']} (到期日: {verify_res.get('real_expiry')})")
            
            final_results.extend(valid_a_domains)
        
        # --- B 层：模拟数据（如果 A 层结果不足）---
        if len(final_results) < 2:
            logger.info("⚠️ A 层有效数据不足，启动 B 层补位...")
            mock_count = 8 if len(final_results) == 0 else (5 - len(final_results))
            mock_data = self.generate_mock_domains(count=mock_count)
            final_results.extend(mock_data)

        # 返回字典格式，由 endpoints.py 统一入库
        logger.info(f"✅ 扫描完成，返回 {len(final_results)} 个域名（待展示）")
        return {
            "all_domains": final_results,
            "top_5": final_results[:5]
        }