import asyncio
import logging
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import whois
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.domain import Domain
from app.services.ai_generator import AIGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomainScanner:
    def __init__(self):
        self.db = SessionLocal()
        self.ai_generator = AIGenerator()

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
            # 如果到期时间小于当前时间，说明已过期（且未续费）
            
            is_expired = expiry_date < now
            
            return {
                'real_expiry': expiry_date,
                'is_expired': is_expired,
                'is_valid': True
            }
        except Exception as e:
            # logger.error(f"WHOIS lookup failed for {domain_name}: {str(e)}")
            return {'real_expiry': None, 'is_expired': False, 'is_valid': False}

    async def fetch_single_page(self, page: int, retries=3) -> List[Dict]:
        """抓取单页数据（带重试）"""
        url = "https://member.expireddomains.net/domains/expiredcom/"
        cookies = {
            "s_id": settings.EXPIRED_DOMAINS_COOKIE  # 从环境变量获取
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
            "fwhois": "1",    # 仅显示有 Whois 的
            "fmarket": "0",   # 排除市场域名
            "flast24": "1"    # 仅最近 24 小时
        }

        for attempt in range(retries):
            try:
                # 注意：curl_cffi 在某些环境下 close 时会报错，这里尝试忽略
                try:
                    async with AsyncSession() as session:
                        resp = await session.get(url, params=params, cookies=cookies, headers=headers, timeout=30)
                        
                        if resp.status_code != 200:
                            logger.warning(f"Page {page} failed with status {resp.status_code}")
                            continue
                            
                        content = resp.text
                except RuntimeError:
                    # 忽略 curl_cffi 在关闭 loop 时的已知错误
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
                    
                    # 提取其他指标 (示例)
                    bl = 0 # Backlinks
                    try:
                        bl_text = cols[2].get_text(strip=True)
                        if 'K' in bl_text:
                            bl = int(float(bl_text.replace('K', '')) * 1000)
                        else:
                            bl = int(bl_text)
                    except:
                        pass

                    domains.append({
                        "domain": domain_name,
                        "source": "expireddomains.net",
                        "backlinks": bl,
                        "da_score": 0, # 稍后计算
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
        return all_domains

    def calculate_da_mock(self, domain: str) -> int:
        """模拟计算 DA 分数 (这里用简单的伪随机算法，实际应调 API)"""
        # 基于域名长度和字符做简单的哈希映射，保持同一个域名分数固定
        seed = sum(ord(c) for c in domain)
        random.seed(seed)
        
        # 80% 概率低分，20% 概率高分
        if random.random() > 0.8:
            return random.randint(20, 50)
        return random.randint(0, 15)

    def generate_mock_domains(self, count=20) -> List[Dict]:
        """B层：生成模拟的高质量域名（降级方案）"""
        logger.info(f"⚠️ [B 层] 触发降级：生成 {count} 个模拟域名")
        
        prefixes = ["cloud", "ai", "meta", "cyber", "tech", "data", "smart", "net", "web", "sys"]
        suffixes = ["hub", "lab", "box", "base", "now", "ify", "ly", "io", "dev", "app"]
        tlds = [".com", ".io", ".ai", ".net", ".org"]
        
        mock_domains = []
        for _ in range(count):
            d_name = f"{random.choice(prefixes)}{random.choice(suffixes)}{random.choice(tlds)}"
            mock_domains.append({
                "domain": d_name,
                "da_score": random.randint(15, 45),
                "backlinks": random.randint(100, 5000),
                "source": "mock_generator",
                "status": "available",
                "registered_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(days=30)
            })
            
        return mock_domains

    async def generate_ai_domains(self, topic="technology", count=10) -> List[Dict]:
        """C层：调用 AI 生成域名（增值方案）"""
        logger.info(f"🧠 [C 层] 触发 AI 生成：主题 {topic}, 数量 {count}")
        try:
            # 调用 AIGenerator 服务
            ai_suggestions = await self.ai_generator.generate_domains(topic, count)
            
            formatted_domains = []
            for name in ai_suggestions:
                formatted_domains.append({
                    "domain": name,
                    "da_score": random.randint(25, 60), # AI 生成的通常质量较高
                    "backlinks": 0,
                    "source": "ai_claude",
                    "status": "suggestion",
                    "registered_at": datetime.now(),
                    "expires_at": datetime.now() + timedelta(days=365)
                })
            return formatted_domains
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return []

    async def scan(self):
        """主扫描逻辑：A -> B -> C 降级"""
        logger.info("🚀 开始三层降级扫描...")
        
        final_results = []
        
        # --- A 层：真实爬虫 ---
        logger.info("🕷️ [A 层] 抓取 ExpiredDomains.net")
        raw_domains = await self.fetch_expireddomains_multi_pages(pages=4)
        
        # 只有当抓取到数据时才进行验证
        if raw_domains:
            # 1. 计算/获取 DA 分数
            logger.info(f"🔍 开始计算质量分数（共 {len(raw_domains)} 个域名）...")
            for d in raw_domains:
                d['da_score'] = self.calculate_da_mock(d['domain'])
                
            # 2. 按 DA 排序取 Top 5
            top_domains = sorted(raw_domains, key=lambda x: x['da_score'], reverse=True)[:5]
            
            # 3. WHOIS 验证
            logger.info("🔍 对 Top 5 进行 WHOIS 验证...")
            valid_a_domains = []
            for d in top_domains:
                logger.info(f"Checking {d['domain']}...")
                verify_res = self.verify_expiry_date_via_whois(d['domain'])
                
                if verify_res['is_expired']:
                    logger.info(f"✅ 验证通过: {d['domain']} (过期日: {verify_res['real_expiry']})")
                    d['expires_at'] = verify_res['real_expiry']
                    d['status'] = 'expired_confirmed'
                    valid_a_domains.append(d)
                else:
                    logger.info(f"❌ 已续费: {d['domain']} (到期日: {verify_res.get('real_expiry')})")
            
            final_results.extend(valid_a_domains)
        
        # --- B 层：模拟数据（如果 A 层结果不足 2 个）---
        if len(final_results) < 2:
            logger.info("⚠️ A 层有效数据不足，启动 B 层补位...")
            mock_data = self.generate_mock_domains(count=5 - len(final_results))
            final_results.extend(mock_data)
            
        # --- C 层：AI 增值（可选，总是补充几个高质量建议）---
        # 这里假设配置开启 AI
        try:
            ai_data = await self.generate_ai_domains(topic="SaaS and AI", count=3)
            final_results.extend(ai_data)
        except Exception as e:
            logger.warning(f"C 层执行失败: {e}")

        # --- 结果入库 ---
        logger.info(f"💾 正在保存 {len(final_results)} 个域名到数据库...")
        saved_count = 0
        for item in final_results:
            # 查重
            exists = self.db.query(Domain).filter(Domain.domain == item['domain']).first()
            if not exists:
                new_domain = Domain(
                    domain=item['domain'],
                    da_score=item.get('da_score', 0),
                    backlinks=item.get('backlinks', 0),
                    source=item.get('source', 'unknown'),
                    status=item.get('status', 'pending'),
                    expires_at=item.get('expires_at')
                )
                self.db.add(new_domain)
                saved_count += 1
        
        try:
            self.db.commit()
            logger.info(f"✅ 成功入库 {saved_count} 个新域名")
        except Exception as e:
            self.db.rollback()
            logger.error(f"数据库提交失败: {e}")

        return final_results