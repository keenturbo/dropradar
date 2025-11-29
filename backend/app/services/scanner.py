import requests
import random
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict
from curl_cffi.requests import AsyncSession
import asyncio
from bs4 import BeautifulSoup
import time
import whois
from anthropic import Anthropic
import google.generativeai as genai

from app.core.config import settings

OPENPAGERANK_API_KEY = os.getenv("OPENPAGERANK_API_KEY", "w00wkkkwo4c4sws4swggkswk8oksggsccck0go84")
EXPIREDDOMAINS_COOKIE = os.getenv("EXPIREDDOMAINS_COOKIE", "")

BROWSER_PROFILE = "chrome110"
TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"


# ============= 新增：WHOIS 验证函数 =============
def verify_expiry_date_via_whois(domain_name: str) -> Dict[str, any]:
    """
    通过 WHOIS 查询验证真实到期日期
    
    返回：
    {
        'domain': 'example.com',
        'real_expiry': datetime(2026, 11, 5),
        'is_expired': False,
        'is_available': False,
        'error': None
    }
    """
    try:
        w = whois.whois(domain_name)
        
        expiry_date = w.expiration_date
        
        if isinstance(expiry_date, list):
            expiry_date = expiry_date[0]
        
        if not expiry_date:
            return {
                'domain': domain_name,
                'real_expiry': None,
                'is_expired': False,
                'is_available': False,
                'error': 'No expiry date found'
            }
        
        today = datetime.now()
        is_expired = expiry_date < today
        
        grace_period = timedelta(days=30)
        is_available = (today - expiry_date) > grace_period
        
        return {
            'domain': domain_name,
            'real_expiry': expiry_date,
            'is_expired': is_expired,
            'is_available': is_available,
            'error': None
        }
        
    except Exception as e:
        return {
            'domain': domain_name,
            'real_expiry': None,
            'is_expired': False,
            'is_available': False,
            'error': str(e)
        }


# ============= 新增：Mock 单词库（扩展版）=============
WORD_POOL = [
    # AI/科技类
    'ai', 'cloud', 'neural', 'deep', 'bot', 'auto', 'smart', 'quantum',
    'cyber', 'data', 'algo', 'crypto', 'meta', 'chain', 'edge', 'sync',
    'neural', 'tensor', 'vector', 'matrix',
    
    # 动作类
    'build', 'forge', 'craft', 'make', 'grow', 'scale', 'flow', 'link',
    'hub', 'lab', 'base', 'core', 'hive', 'mesh', 'grid', 'nexus',
    'create', 'launch', 'spark', 'boost',
    
    # 业务类
    'saas', 'api', 'app', 'dev', 'ops', 'tool', 'kit', 'suite', 'stack',
    'platform', 'studio', 'space', 'zone', 'spot', 'dash', 'pulse',
    'work', 'task', 'team', 'crew',
    
    # 行业类
    'health', 'finance', 'edu', 'legal', 'retail', 'media', 'travel',
    'music', 'sport', 'game', 'book', 'food', 'fashion', 'home',
    'tech', 'code', 'design', 'market',
    
    # 形容词
    'fast', 'easy', 'simple', 'quick', 'instant', 'magic', 'super',
    'pro', 'max', 'ultra', 'prime', 'elite', 'plus', 'next', 'neo',
    'swift', 'rapid', 'agile', 'smart',
    
    # 名词
    'sky', 'ocean', 'mountain', 'river', 'forest', 'star', 'moon',
    'sun', 'earth', 'wind', 'fire', 'light', 'stone', 'gold', 'silver',
    'wave', 'beam', 'spark', 'flux'
]

TLD_POOL = ['.ai', '.io', '.dev', '.app', '.tech', '.cloud', '.co', '.me']


def generate_mock_domains(count: int = 20) -> List[Dict]:
    """生成随机组合域名（扩展版）"""
    domains = []
    
    for _ in range(count):
        word_count = random.choice([2, 3])
        words = random.sample(WORD_POOL, word_count)
        name = ''.join(words)
        
        tld = random.choice(TLD_POOL)
        domain_name = f"{name}{tld}"
        
        domains.append({
            'name': domain_name,
            'da_score': random.randint(5, 25),
            'backlinks': random.randint(100, 1000),
            'referring_domains': random.randint(10, 100),
            'spam_score': random.randint(0, 20),
            'drop_date': (datetime.now() + timedelta(days=random.randint(1, 30))).date(),
            'tld': tld,
            'length': len(name),
            'domain_age': random.randint(1, 5),
            'price': random.randint(10, 200),
            'bids': random.randint(0, 5),
            'wikipedia_links': random.randint(0, 3),
            'quality_score': 0.0
        })
    
    return domains


# ============= 新增：AI 生成域名 =============
def generate_ai_domains(topic: str = "AI tools", count: int = 20) -> List[Dict]:
    """通过 AI 生成高质量域名建议（支持 Claude 和 Gemini）"""
    
    provider = settings.ai_provider.lower()
    
    # ===== Claude 生成 =====
    if provider == "claude":
        if not settings.anthropic_api_key:
            print("⚠️ 未配置 ANTHROPIC_API_KEY，跳过 AI 生成")
            return []
        
        try:
            client = Anthropic(api_key=settings.anthropic_api_key)
            
            prompt = f"""Generate {count} premium domain name suggestions for: "{topic}".

Requirements:
1. Short (5-15 chars before TLD)
2. Memorable, pronounceable
3. Related to {topic}
4. Use .ai, .io, .dev, .app, .tech, .cloud

Output format (one per line):
domainname.tld

Examples:
- cloudforge.ai
- buildhub.io

Generate {count} domains (only names, no explanations):"""

            message = client.messages.create(
                model=settings.ai_model_claude,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = message.content[0].text.strip()
            domain_lines = [line.strip() for line in content.split('\n') if '.' in line]
            
            print(f"✅ Claude 生成 {len(domain_lines[:count])} 个域名")
            return _parse_ai_domains(domain_lines[:count])
            
        except Exception as e:
            print(f"❌ Claude 生成失败: {e}")
            return []
    
    # ===== Gemini 生成 =====
    elif provider == "gemini":
        if not settings.google_api_key:
            print("⚠️ 未配置 GOOGLE_API_KEY，跳过 AI 生成")
            return []
        
        try:
            genai.configure(api_key=settings.google_api_key)
            model = genai.GenerativeModel(settings.ai_model_gemini)
            
            prompt = f"""Generate {count} premium domain name suggestions for: "{topic}".

Requirements:
1. Short (5-15 chars before TLD)
2. Memorable, pronounceable
3. Related to {topic}
4. Use .ai, .io, .dev, .app, .tech, .cloud

Output format (one per line):
domainname.tld

Examples:
- cloudforge.ai
- buildhub.io

Generate {count} domains (only names, no explanations):"""

            response = model.generate_content(prompt)
            content = response.text.strip()
            domain_lines = [line.strip() for line in content.split('\n') if '.' in line]
            
            print(f"✅ Gemini 生成 {len(domain_lines[:count])} 个域名")
            return _parse_ai_domains(domain_lines[:count])
            
        except Exception as e:
            print(f"❌ Gemini 生成失败: {e}")
            return []
    
    else:
        print(f"⚠️ 未知 AI 提供商: {provider}")
        return []


def _parse_ai_domains(domain_lines: List[str]) -> List[Dict]:
    """解析 AI 返回的域名列表"""
    domains = []
    
    for domain_name in domain_lines:
        domain_name = domain_name.split('. ', 1)[-1].strip()
        domain_name = domain_name.lstrip('- ')
        
        if not domain_name or '.' not in domain_name:
            continue
        
        tld = '.' + domain_name.split('.')[-1]
        name_part = domain_name.split('.')[0]
        
        domains.append({
            'name': domain_name,
            'da_score': 0,
            'backlinks': 0,
            'referring_domains': 0,
            'spam_score': 0,
            'drop_date': (datetime.now() + timedelta(days=7)).date(),
            'tld': tld,
            'length': len(name_part),
            'domain_age': 0,
            'price': 0,
            'bids': 0,
            'wikipedia_links': 0,
            'quality_score': 0.0
        })
    
    return domains


# ============= 原有函数保持不变 =============
def extract_number(text: str) -> int:
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


def batch_get_pagerank(domain_names: List[str]) -> Dict[str, int]:
    """批量获取 DA 分数（一次最多 100 个域名，避免 API 超限）"""
    
    if not domain_names:
        return {}
    
    results = {}
    batch_size = 100
    
    print(f"🔍 开始批量获取 {len(domain_names)} 个域名的 DA 分数...")
    
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
                    print(f"  ✅ {domain} → DA: {da_score}")
                
                print(f"✅ 批次完成: 成功获取 {len(batch)} 个域名的 DA")
            else:
                print(f"⚠️ OpenPageRank API 错误: {data}")
                for domain in batch:
                    results[domain] = 0
            
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ 批量获取 DA 失败: {e}")
            for domain in batch:
                results[domain] = 0
    
    return results


def get_dynamic_headers(referer: str = None) -> Dict[str, str]:
    """动态生成请求头"""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    
    if referer:
        headers["Referer"] = referer
        headers["Origin"] = "https://www.expireddomains.net"
    
    return headers


async def fetch_single_page(start: int = 0) -> List[Dict]:
    """抓取单页数据（25 个域名）"""
    
    cookie = os.getenv("EXPIREDDOMAINS_COOKIE", "")
    if not cookie:
        print("❌ 未配置 EXPIREDDOMAINS_COOKIE 环境变量")
        return []
    
    proxy = os.getenv("PROXY_URL", "")
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    if start == 0:
        url = "https://member.expireddomains.net/domains/namecheapauctions/?start=0#listing"
    else:
        url = f"https://member.expireddomains.net/domains/namecheapauctions/?start={start}#listing"
    
    headers = get_dynamic_headers(referer="https://www.expireddomains.net/")
    headers["Cookie"] = cookie
    
    domains = []
    page_num = start // 25 + 1
    
    try:
        print(f"🔗 正在抓取第 {page_num} 页 (start={start})...")
        
        async with AsyncSession() as session:
            response = await session.get(
                url,
                headers=headers,
                impersonate=BROWSER_PROFILE,
                timeout=TIMEOUT,
                proxies=proxies,
                allow_redirects=True
            )
            
            if response.status_code != 200:
                print(f"❌ HTTP 错误：{response.status_code}")
                return []
            
            if "login" in response.url.lower():
                print("❌ Cookie 已失效，被重定向到登录页")
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            table = soup.find('table', class_='base1')
            
            if not table:
                print(f"❌ 第 {page_num} 页未找到域名表格")
                return []
            
            tbody = table.find('tbody')
            if not tbody:
                print(f"❌ 第 {page_num} 页表格无 tbody")
                return []
            
            rows = tbody.find_all('tr')
            
            for idx, row in enumerate(rows):
                try:
                    cols = row.find_all('td')
                    if len(cols) < 23:
                        continue
                    
                    domain_name = cols[0].text.strip()
                    
                    if not domain_name or domain_name.lower() in ['domain', 'name']:
                        continue
                    
                    if '.' not in domain_name:
                        continue
                    
                    backlinks = extract_number(cols[4].text.strip())
                    referring_domains = extract_number(cols[5].text.strip())
                    
                    wby_text = cols[6].text.strip()
                    try:
                        domain_age_year = int(wby_text) if wby_text.isdigit() else 0
                    except:
                        domain_age_year = 0
                    
                    age_years = (datetime.now().year - domain_age_year) if domain_age_year > 1900 else 0
                    
                    wikipedia_links = extract_number(cols[20].text.strip()) if len(cols) > 20 else 0
                    price = extract_number(cols[21].text.strip()) if len(cols) > 21 else 0
                    bids = extract_number(cols[22].text.strip()) if len(cols) > 22 else 0
                    
                    domains.append({
                        'name': domain_name,
                        'da_score': 0,
                        'backlinks': backlinks,
                        'referring_domains': referring_domains,
                        'spam_score': random.randint(0, 15),
                        'drop_date': (datetime.now() + timedelta(days=random.randint(1, 7))).date(),
                        'tld': '.' + domain_name.split('.')[-1],
                        'length': len(domain_name.split('.')[0]),
                        'domain_age': age_years,
                        'price': price,
                        'bids': bids,
                        'wikipedia_links': wikipedia_links
                    })
                    
                except Exception as e:
                    print(f"⚠️ 第 {page_num} 页第 {idx+1} 行解析失败: {e}")
                    continue
            
            print(f"✅ 第 {page_num} 页：成功解析 {len(domains)} 个域名")
            
    except Exception as e:
        print(f"❌ 第 {page_num} 页抓取失败: {e}")
        import traceback
        traceback.print_exc()
    
    await asyncio.sleep(2)
    
    return domains


async def fetch_expireddomains_multi_pages(pages: int = 4) -> List[Dict]:
    """抓取前 N 页（默认 4 页 = 100 个域名，避免 API 超限）"""
    
    all_domains = []
    
    print(f"🚀 开始抓取前 {pages} 页（共约 {pages * 25} 个域名）...")
    
    for page_num in range(pages):
        start = page_num * 25
        domains = await fetch_single_page(start)
        all_domains.extend(domains)
        
        if len(domains) == 0:
            print(f"⚠️ 第 {page_num + 1} 页无数据，停止抓取")
            break
    
    print(f"\n✅ 共抓取 {len(all_domains)} 个域名")
    
    if all_domains:
        domain_names = [d['name'] for d in all_domains]
        da_scores = batch_get_pagerank(domain_names)
        
        for domain in all_domains:
            domain['da_score'] = da_scores.get(domain['name'], 0)
    
    return all_domains


def fetch_from_expireddomains() -> List[Dict]:
    """同步包装器（抓取 4 页 = 100 个域名）"""
    return asyncio.run(fetch_expireddomains_multi_pages(pages=4))


# ============= 修改：主扫描器类（三层降级） =============
class DomainScanner:
    """域名扫描器主类"""
    
    def __init__(self, mode='expireddomains'):
        self.mode = mode
    
    def scan(self) -> List[Dict]:
        """三层降级扫描"""
        
        print("\n" + "="*80)
        print("🚀 开始三层降级扫描...")
        print("="*80 + "\n")
        
        domains = []
        
        # ===== A 层：真实爬虫 + WHOIS 验证 =====
        if self.mode == 'expireddomains':
            print("🕷️ [A 层] 抓取 ExpiredDomains.net（4 页 = 100 个域名）")
            raw_domains = fetch_from_expireddomains()
            
            if raw_domains:
                print(f"\n🔍 开始 WHOIS 验证（共 {len(raw_domains)} 个域名）...\n")
                
                verified_domains = []
                
                for idx, domain_data in enumerate(raw_domains, 1):
                    domain_name = domain_data['name']
                    
                    print(f"  [{idx}/{len(raw_domains)}] 验证 {domain_name}...")
                    
                    whois_result = verify_expiry_date_via_whois(domain_name)
                    
                    if whois_result['error']:
                        print(f"    ⚠️ WHOIS 查询失败: {whois_result['error']}")
                        continue
                    
                    if not whois_result['is_expired']:
                        real_expiry = whois_result['real_expiry']
                        print(f"    ❌ 已续费：真实到期日期 {real_expiry.strftime('%Y-%m-%d')}")
                        continue
                    
                    if whois_result['is_available']:
                        print(f"    ✅ 真正过期可注册")
                        domain_data['drop_date'] = whois_result['real_expiry'].date()
                        verified_domains.append(domain_data)
                    else:
                        print(f"    ⏳ 在宽限期内")
                
                domains.extend(verified_domains)
                print(f"\n✅ [A 层] 验证后剩余 {len(verified_domains)} 个真正过期的域名\n")
            
            else:
                print("❌ [A 层] 爬虫失败，进入降级模式\n")
        
        # ===== B 层：Mock 组合域名（降级） =====
        if len(domains) < 5:
            print("🔄 [B 层] 生成组合域名（降级兜底）")
            mock_domains = generate_mock_domains(count=20)
            domains.extend(mock_domains)
            print(f"✅ [B 层] 生成 {len(mock_domains)} 个组合域名\n")
        
        # ===== C 层：AI 生成（可选） =====
        if len(domains) < 5 and (settings.anthropic_api_key or settings.google_api_key):
            print("🤖 [C 层] AI 生成高质量域名（最终兜底）")
            ai_domains = generate_ai_domains(topic="SaaS and AI tools", count=20)
            domains.extend(ai_domains)
            print(f"✅ [C 层] AI 生成 {len(ai_domains)} 个域名\n")
        
        # ===== 计算质量分数 + 返回 Top 5 =====
        if not domains:
            print("❌ 三层扫描全部失败")
            return []
        
        print(f"🔍 开始计算质量分数（共 {len(domains)} 个域名）...\n")
        return self._filter_high_quality(domains)
    
    def _filter_high_quality(self, domains: List[Dict]) -> List[Dict]:
        """计算质量分数，返回 Top 5"""
        
        for domain in domains:
            score = 0
            
            score += domain.get('da_score', 0) * 0.3
            
            bl = domain.get('backlinks', 0)
            score += min(bl / 50, 20)
            
            rd = domain.get('referring_domains', 0)
            score += min(rd / 5, 20)
            
            age = domain.get('domain_age', 0)
            score += min(age / 2, 10)
            
            price = domain.get('price', 0)
            score += min(price / 200, 10)
            
            bids = domain.get('bids', 0)
            score += min(bids / 10, 5)
            
            wiki = domain.get('wikipedia_links', 0)
            score += min(wiki * 0.5, 5)
            
            domain['quality_score'] = round(score, 2)
        
        domains.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        print(f"\n{'='*80}")
        print(f"🏆 TOP 5 高质量过期域名（共评估 {len(domains)} 个）")
        print(f"{'='*80}\n")
        
        for idx, d in enumerate(domains[:5], 1):
            print(f"{idx}. 【{d['name']}】")
            print(f"   📊 质量分: {d.get('quality_score', 0):.1f}/100")
            print(f"   🔗 DA: {d.get('da_score', 0)} | 外链: {d.get('backlinks', 0):,} | 引用域: {d.get('referring_domains', 0)}")
            print(f"   📅 年龄: {d.get('domain_age', 0)}年 | 价格: ${d.get('price', 0)} | 竞价: {d.get('bids', 0)}次 | Wiki: {d.get('wikipedia_links', 0)}")
            print()
        
        print(f"{'='*80}\n")
        
        return domains[:5]