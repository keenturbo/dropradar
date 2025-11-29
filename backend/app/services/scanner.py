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

OPENPAGERANK_API_KEY = os.getenv("OPENPAGERANK_API_KEY", "w00wkkkwo4c4sws4swggkswk8oksggsccck0go84")
EXPIREDDOMAINS_COOKIE = os.getenv("EXPIREDDOMAINS_COOKIE", "")

BROWSER_PROFILE = "chrome110"
TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"


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
        
        # 构建 URL 参数
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
    
    # 构建 URL（翻页）
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
                    if len(cols) < 23:  # 需要至少 23 列
                        continue
                    
                    domain_name = cols[0].text.strip()
                    
                    if not domain_name or domain_name.lower() in ['domain', 'name']:
                        continue
                    
                    if '.' not in domain_name:
                        continue
                    
                    # 列索引修正版本
                    backlinks = extract_number(cols[4].text.strip())  # 列4: BL
                    referring_domains = extract_number(cols[5].text.strip())  # 列5: DP
                    
                    wby_text = cols[6].text.strip()  # 列6: WBY（域名注册年份）
                    try:
                        domain_age_year = int(wby_text) if wby_text.isdigit() else 0
                    except:
                        domain_age_year = 0
                    
                    # 计算域名年龄
                    age_years = (datetime.now().year - domain_age_year) if domain_age_year > 1900 else 0
                    
                    # 列20: WPL (Wikipedia Links)
                    wikipedia_links = extract_number(cols[20].text.strip()) if len(cols) > 20 else 0
                    
                    # 列21: Price
                    price = extract_number(cols[21].text.strip()) if len(cols) > 21 else 0
                    
                    # 列22: Bids
                    bids = extract_number(cols[22].text.strip()) if len(cols) > 22 else 0
                    
                    domains.append({
                        'name': domain_name,
                        'da_score': 0,  # 后续批量获取
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
    
    await asyncio.sleep(2)  # 避免请求过快被封
    
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
    
    # 批量获取 DA 分数
    if all_domains:
        domain_names = [d['name'] for d in all_domains]
        da_scores = batch_get_pagerank(domain_names)
        
        # 更新 DA 分数
        for domain in all_domains:
            domain['da_score'] = da_scores.get(domain['name'], 0)
    
    return all_domains


def fetch_from_expireddomains() -> List[Dict]:
    """同步包装器（抓取 4 页 = 100 个域名）"""
    try:
        loop = asyncio.get_event_loop()
        
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(fetch_expireddomains_multi_pages(pages=4))
        else:
            return asyncio.run(fetch_expireddomains_multi_pages(pages=4))
            
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(fetch_expireddomains_multi_pages(pages=4))
            return result
        finally:
            loop.close()


class DomainScanner:
    """域名扫描器主类"""
    
    def __init__(self, mode='expireddomains'):
        self.mode = mode
    
    def scan(self) -> List[Dict]:
        """执行扫描（返回 Top 5）"""
        
        if self.mode == 'expireddomains':
            print("🕷️ 使用 ExpiredDomains.net 爬虫模式（4 页 = 100 个域名）")
            domains = fetch_from_expireddomains()
            
            if len(domains) == 0:
                print("⚠️ 未抓取到域名")
                return []
            
            print(f"\n🔍 开始计算质量分数（共 {len(domains)} 个域名）...")
            return self._filter_high_quality(domains)
        
        else:
            print(f"⚠️ 未知模式: {self.mode}")
            return []
    
    def _filter_high_quality(self, domains: List[Dict]) -> List[Dict]:
        """计算质量分数，返回 Top 5"""
        
        for domain in domains:
            score = 0
            
            # DA 分数权重 30%（0-100分 → 0-30）
            score += domain.get('da_score', 0) * 0.3
            
            # 外链数量权重 20%
            bl = domain.get('backlinks', 0)
            score += min(bl / 50, 20)  # 2500+ 外链 = 20 分
            
            # 引用域权重 20%
            rd = domain.get('referring_domains', 0)
            score += min(rd / 5, 20)  # 100+ 引用域 = 20 分
            
            # 域名年龄权重 10%
            age = domain.get('domain_age', 0)
            score += min(age / 2, 10)  # 20+ 年 = 10 分
            
            # 竞价价格权重 10%
            price = domain.get('price', 0)
            score += min(price / 200, 10)  # $2000+ = 10 分
            
            # 竞价次数权重 5%
            bids = domain.get('bids', 0)
            score += min(bids / 10, 5)  # 50+ 次竞价 = 5 分
            
            # 维基百科外链权重 5%
            wiki = domain.get('wikipedia_links', 0)
            score += min(wiki * 0.5, 5)  # 10+ 维基链接 = 5 分
            
            domain['quality_score'] = round(score, 2)
        
        # 按质量分数排序（降序）
        domains.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        # 打印 Top 5
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
        
        # 🔥 只返回 Top 5
        return domains[:5]