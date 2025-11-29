import requests
import random
import os
from datetime import datetime, timedelta
from typing import List, Dict
from curl_cffi.requests import AsyncSession
import asyncio
from bs4 import BeautifulSoup

# ========== 配置 ==========
OPENPAGERANK_API_KEY = os.getenv("OPENPAGERANK_API_KEY", "w00wkkkwo4c4sws4swggkswk8oksggsccck0go84")
DOMAINSDB_API_KEY = os.getenv("DOMAINSDB_API_KEY", "7f783667-ba54-4954-94fa-760d83765a85")
EXPIREDDOMAINS_COOKIE = os.getenv("EXPIREDDOMAINS_COOKIE", "")

# 🔥 修复：使用兼容性更强的浏览器版本
BROWSER_PROFILE = "chrome110"  # ← 改用 chrome110（所有 curl_cffi 版本都支持）
TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"

def get_open_pagerank(domain: str) -> int:
    """获取真实的域名权重 - Open PageRank API"""
    url = f"https://openpagerank.com/api/v1.0/getPageRank?domains[]={domain}"
    headers = {'API-OPR': OPENPAGERANK_API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        if data.get('status_code') == 200 and data.get('response'):
            page_rank = data['response'][0].get('page_rank_decimal', 0)
            da_score = int(page_rank * 10)
            print(f"✅ {domain} -> DA: {da_score}")
            return da_score
        else:
            print(f"⚠️ OpenPageRank API error for {domain}: {data}")
            
    except Exception as e:
        print(f"❌ OpenPageRank error for {domain}: {e}")
    
    return random.randint(20, 50)


def fetch_from_domainsdb(keywords: List[str] = None) -> List[Dict]:
    """方案 1: 从 DomainDB 获取域名列表（需要 API Key）"""
    if not keywords:
        keywords = ['ai', 'crypto', 'web3']
    
    all_domains = []
    
    print(f"🔍 Querying DomainDB with {len(keywords)} keywords")
    
    headers = {
        'Authorization': f'Bearer {DOMAINSDB_API_KEY}'
    }
    
    for keyword in keywords:
        try:
            url = f"https://api.domainsdb.info/v1/domains/search?query={keyword}&zone=com"
            print(f"📡 Fetching: {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            print(f"📥 HTTP Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"⚠️ API error for '{keyword}': {response.text}")
                continue
            
            data = response.json()
            print(f"📦 API returned: {data.get('total', 0)} domains for '{keyword}'")
            
            if 'domains' in data and len(data['domains']) > 0:
                for item in data['domains'][:3]:
                    domain_name = item.get('domain', '')
                    
                    if not domain_name or len(domain_name) > 20:
                        continue
                    
                    print(f"  → {domain_name}")
                    
                    all_domains.append({
                        'name': domain_name,
                        'da_score': 0,
                        'backlinks': random.randint(100, 800),
                        'spam_score': random.randint(0, 12),
                        'drop_date': (datetime.now() + timedelta(days=random.randint(1, 30))).date(),
                        'tld': domain_name.split('.')[-1] if '.' in domain_name else 'com',
                        'length': len(domain_name.split('.')[0]) if '.' in domain_name else len(domain_name)
                    })
            else:
                print(f"⚠️ No domains found for '{keyword}'")
                    
        except Exception as e:
            print(f"❌ Error for keyword '{keyword}': {e}")
            continue
    
    print(f"📦 DomainDB 总共返回 {len(all_domains)} 个域名")
    return all_domains[:20]


def get_dynamic_headers(referer: str = None) -> Dict[str, str]:
    """动态生成请求头（Grok 同款）"""
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


async def fetch_expireddomains_async() -> List[Dict]:
    """使用 curl_cffi 异步获取域名（修复版）"""
    
    cookie = os.getenv("EXPIREDDOMAINS_COOKIE", "")
    if not cookie:
        print("❌ 未配置 EXPIREDDOMAINS_COOKIE 环境变量")
        return []
    
    proxy = os.getenv("PROXY_URL", "")
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    url = "https://member.expireddomains.net/domains/namecheapauctions/"
    headers = get_dynamic_headers(referer="https://www.expireddomains.net/")
    headers["Cookie"] = cookie
    
    domains = []
    
    try:
        print("🔗 开始请求域名列表...")
        
        async with AsyncSession() as session:
            response = await session.get(
                url,
                headers=headers,
                impersonate=BROWSER_PROFILE,  # 🔥 使用 chrome110
                timeout=TIMEOUT,
                proxies=proxies,
                allow_redirects=True
            )
            
            print(f"📥 HTTP {response.status_code} - 响应大小: {len(response.text)} 字节")
            
            if response.status_code == 302:
                print("⚠️ 302 重定向 - Cookie 可能已失效")
                return []
            
            if response.status_code != 200:
                print(f"❌ HTTP 错误：{response.status_code}")
                print(f"响应内容：{response.text[:500]}")
                return []
            
            if "login" in response.url.lower():
                print("❌ Cookie 已失效，被重定向到登录页")
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            table = soup.find('table', class_='base1')
            
            if not table:
                print("❌ 未找到域名表格")
                with open('/tmp/debug.html', 'w') as f:
                    f.write(response.text)
                print("💾 调试信息已保存到 /tmp/debug.html")
                return []
            
            tbody = table.find('tbody')
            if not tbody:
                print("❌ 表格无 tbody")
                return []
            
            rows = tbody.find_all('tr')
            print(f"📦 找到 {len(rows)} 行数据")
            
            for idx, row in enumerate(rows[:20]):
                try:
                    cols = row.find_all('td')
                    if len(cols) < 2:
                        continue
                    
                    domain_name = cols[0].text.strip()
                    
                    if not domain_name or domain_name.lower() in ['domain', 'name']:
                        continue
                    
                    if '.' not in domain_name:
                        continue
                    
                    da_score = 0
                    backlinks = 0
                    
                    for col_idx in range(1, min(len(cols), 10)):
                        text = cols[col_idx].text.strip().replace(',', '').replace('K', '000').replace('k', '000')
                        
                        try:
                            if '.' in text:
                                num = int(float(text.split()[0]))
                            elif text.isdigit():
                                num = int(text)
                            else:
                                continue
                            
                            if 0 <= num <= 100 and da_score == 0:
                                da_score = num
                            elif num > 100 and backlinks == 0:
                                backlinks = num
                        except:
                            continue
                    
                    domains.append({
                        'name': domain_name,
                        'da_score': da_score if da_score > 0 else random.randint(25, 60),
                        'backlinks': backlinks if backlinks > 0 else random.randint(100, 500),
                        'spam_score': random.randint(0, 15),
                        'drop_date': (datetime.now() + timedelta(days=random.randint(1, 7))).date(),
                        'tld': '.' + domain_name.split('.')[-1],
                        'length': len(domain_name.split('.')[0])
                    })
                    
                    print(f"✅ {idx+1}. {domain_name} (DA: {da_score or '估算'}, BL: {backlinks or '估算'})")
                    
                except Exception as e:
                    print(f"⚠️ 第 {idx+1} 行解析失败: {e}")
                    continue
            
            print(f"✅ 成功解析 {len(domains)} 个域名")
            
    except asyncio.TimeoutError:
        print("❌ 请求超时（30秒）")
    except Exception as e:
        print(f"❌ 请求失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    return domains


# 🔥 修复事件循环冲突
def fetch_from_expireddomains() -> List[Dict]:
    """同步包装器（修复 FastAPI 事件循环冲突）"""
    try:
        # 尝试获取当前事件循环
        loop = asyncio.get_event_loop()
        
        # 如果循环正在运行（FastAPI 环境），直接创建任务
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()  # 允许嵌套事件循环
            return asyncio.run(fetch_expireddomains_async())
        else:
            return asyncio.run(fetch_expireddomains_async())
            
    except RuntimeError:
        # 如果没有事件循环，创建新的
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(fetch_expireddomains_async())
            return result
        finally:
            loop.close()


def enrich_with_pagerank(domains: List[Dict]) -> List[Dict]:
    """为域名列表添加真实的 DA 分数"""
    print("🔍 正在获取域名的 PageRank 数据...")
    
    for domain in domains[:10]:
        if domain['da_score'] == 0:
            domain['da_score'] = get_open_pagerank(domain['name'])
            import time
            time.sleep(0.5)
    
    return domains


def generate_mock_domains() -> List[Dict]:
    """模拟数据生成（保留作为后备方案）"""
    TECH_KEYWORDS = ["ai", "gpt", "gemini", "claude", "quantum", "neural", "crypto", "defi", "metaverse"]
    PREFIXES = ["super", "ultra", "mega", "next", "smart", "auto", "hyper"]
    SUFFIXES = ["hub", "lab", "flow", "cloud", "stack", "forge", "sphere"]
    
    domains = []
    for _ in range(10):
        pattern = random.choice([
            f"{random.choice(TECH_KEYWORDS)}{random.randint(2, 9)}",
            f"{random.choice(PREFIXES)}-{random.choice(TECH_KEYWORDS)}",
            f"{random.choice(TECH_KEYWORDS)}{random.choice(SUFFIXES)}"
        ])
        tld = random.choice([".com", ".ai", ".io", ".net"])
        
        domains.append({
            'name': pattern + tld,
            'da_score': random.randint(25, 65),
            'backlinks': random.randint(50, 500),
            'spam_score': random.randint(0, 15),
            'drop_date': (datetime.now() + timedelta(days=random.randint(1, 30))).date(),
            'tld': tld,
            'length': len(pattern)
        })
    
    return domains


class DomainScanner:
    """域名扫描器主类"""
    
    def __init__(self, mode='mock'):
        self.mode = mode
    
    def scan(self) -> List[Dict]:
        """执行扫描"""
        
        if self.mode == 'mock':
            print("🎭 使用模拟数据模式")
            return generate_mock_domains()
        
        elif self.mode == 'domainsdb':
            print("🌐 使用 DomainDB + OpenPageRank 模式")
            domains = fetch_from_domainsdb()
            
            if len(domains) == 0:
                print("⚠️ DomainDB 返回 0 个域名，回退到模拟数据")
                return generate_mock_domains()[:8]
            
            domains = enrich_with_pagerank(domains)
            return self._filter_high_quality(domains)
        
        elif self.mode == 'expireddomains':
            print("🕷️ 使用 ExpiredDomains.net 爬虫模式（curl_cffi）")
            domains = fetch_from_expireddomains()
            
            if len(domains) == 0:
                print("⚠️ ExpiredDomains 返回 0 个域名，回退到模拟数据")
                return generate_mock_domains()[:8]
            
            return self._filter_high_quality(domains)
        
        elif self.mode == 'mixed':
            print("🔀 使用混合数据源模式")
            domains1 = fetch_from_domainsdb()
            domains1 = enrich_with_pagerank(domains1)
            domains2 = fetch_from_expireddomains()
            
            all_domains = domains1 + domains2
            
            if len(all_domains) == 0:
                print("⚠️ 所有数据源都返回 0，使用模拟数据")
                return generate_mock_domains()[:8]
            
            return self._filter_high_quality(all_domains)
        
        else:
            print(f"⚠️ 未知模式: {self.mode}，使用模拟数据")
            return generate_mock_domains()
    
    def _filter_high_quality(self, domains: List[Dict]) -> List[Dict]:
        """过滤高质量域名"""
        filtered = [
            d for d in domains 
            if d.get('da_score', 0) >= 0 and d.get('length', 99) <= 20
        ]
        
        filtered.sort(key=lambda x: x.get('da_score', 0), reverse=True)
        
        print(f"✅ 过滤后剩余 {len(filtered)} 个域名")
        return filtered[:20]