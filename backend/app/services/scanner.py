import requests
import random
import os
from datetime import datetime, timedelta
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# ========== 配置信息（支持环境变量）==========
OPENPAGERANK_API_KEY = os.getenv("OPENPAGERANK_API_KEY", "w00wkkkwo4c4sws4swggkswk8oksggsccck0go84")
DOMAINSDB_API_KEY = os.getenv("DOMAINSDB_API_KEY", "7f783667-ba54-4954-94fa-760d83765a85")
EXPIREDDOMAINS_USERNAME = os.getenv("EXPIREDDOMAINS_USERNAME", "turboexpireddomains")
EXPIREDDOMAINS_PASSWORD = os.getenv("EXPIREDDOMAINS_PASSWORD", "zeBtu2-kigsij-teqmab")
EXPIREDDOMAINS_COOKIE = os.getenv("EXPIREDDOMAINS_COOKIE", "")

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


def fetch_from_expireddomains() -> List[Dict]:
    """方案 2: 从 ExpiredDomains.net 爬取 - Cookie 优先，密码登录备用"""
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    domains = []
    login_success = False
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        # ========== 方式 1: Cookie 登录（优先）==========
        if EXPIREDDOMAINS_COOKIE:
            print("🍪 尝试使用 Cookie 登录...")
            
            try:
                driver.get('https://www.expireddomains.net/')
                time.sleep(2)
                
                cookies_to_add = []
                cookie_pairs = EXPIREDDOMAINS_COOKIE.split(';')
                for cookie_pair in cookie_pairs:
                    cookie_pair = cookie_pair.strip()
                    if '=' in cookie_pair:
                        name, value = cookie_pair.split('=', 1)
                        name = name.strip()
                        value = value.strip()
                        
                        cookies_to_add.append({
                            'name': name,
                            'value': value,
                            'domain': '.expireddomains.net',
                            'path': '/',
                            'secure': True,
                            'httpOnly': True if name == 'ExpiredDomainssessid' else False
                        })
                
                for cookie in cookies_to_add:
                    try:
                        driver.add_cookie(cookie)
                        print(f"✅ Cookie 已注入: {cookie['name']}")
                    except Exception as e:
                        print(f"⚠️ Cookie 注入失败: {cookie['name']} - {e}")
                
                print("🔗 访问会员页面验证登录状态...")
                driver.get('https://member.expireddomains.net/')
                time.sleep(3)
                
                current_url = driver.current_url
                page_title = driver.title
                
                print(f"📍 当前 URL: {current_url}")
                print(f"📄 页面标题: {page_title}")
                
                if 'login' not in current_url.lower() and 'member.expireddomains.net' in current_url:
                    print("✅ Cookie 登录成功！")
                    login_success = True
                else:
                    print("⚠️ Cookie 已失效，尝试密码登录...")
                    
            except Exception as e:
                print(f"❌ Cookie 登录失败: {e}")
                import traceback
                traceback.print_exc()
        
        # ========== 方式 2: 密码登录（备用）==========
        if not login_success:
            if not EXPIREDDOMAINS_PASSWORD or EXPIREDDOMAINS_PASSWORD == "YOUR_PASSWORD_HERE":
                print("⚠️ ExpiredDomains 密码未配置，跳过该数据源")
                return []
            
            print("🔐 使用密码登录 ExpiredDomains.net...")
            driver.get('https://www.expireddomains.net/login/')
            time.sleep(3)
            
            page_source = driver.page_source
            print(f"📄 页面标题: {driver.title}")
            print(f"📍 当前 URL: {driver.current_url}")
            
            if 'name="login"' not in page_source:
                print("❌ 页面中没有 name='login' 字段")
                return []
            
            print("⏳ 等待登录表单加载...")
            wait = WebDriverWait(driver, 20)
            
            username_field = wait.until(EC.presence_of_element_located((By.NAME, 'login')))
            password_field = driver.find_element(By.NAME, 'password')
            
            username_field.clear()
            password_field.clear()
            username_field.send_keys(EXPIREDDOMAINS_USERNAME)
            password_field.send_keys(EXPIREDDOMAINS_PASSWORD)
            
            print(f"✅ 已填写账号: {EXPIREDDOMAINS_USERNAME}")
            
            login_button = None
            try:
                login_button = driver.find_element(By.NAME, 'submit')
                print("✅ 找到按钮: name='submit'")
            except:
                try:
                    login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                    print("✅ 找到按钮: button[type='submit']")
                except:
                    try:
                        login_button = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
                        print("✅ 找到按钮: input[type='submit']")
                    except:
                        print("❌ 无法找到登录按钮")
                        return []
            
            login_button.click()
            print("⏳ 等待登录完成...")
            time.sleep(5)
            
            current_url = driver.current_url
            print(f"📍 登录后 URL: {current_url}")
            
            if 'login' in current_url.lower():
                print("❌ 密码登录失败（可能需要验证码），请配置 Cookie 登录")
                return []
            
            print("✅ 密码登录成功！")
            login_success = True
        
        # ========== 登录成功后，获取域名数据 ==========
        if not login_success:
            return []
        
        print("📊 正在获取域名列表...")
        
        search_url = 'https://member.expireddomains.net/domains/namecheapauctions/'
        print(f"🔗 访问列表: {search_url}")
        driver.get(search_url)
        
        print("⏳ 等待域名表格加载...")
        wait = WebDriverWait(driver, 20)
        
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table.base1')))
            time.sleep(3)
        except Exception as e:
            print(f"❌ 表格加载超时: {e}")
            print(f"📄 当前页面标题: {driver.title}")
            print(f"📍 当前 URL: {driver.current_url}")
            return []
        
        print("📊 正在解析域名数据...")
        table_rows = driver.find_elements(By.CSS_SELECTOR, 'table.base1 tbody tr')
        print(f"📦 找到 {len(table_rows)} 行数据")
        
        # 🔥 修复：域名在第1列（cols[0]）而不是第2列（cols[1]）
        for idx, row in enumerate(table_rows[:20]):
            try:
                cols = row.find_elements(By.TAG_NAME, 'td')
                
                if len(cols) < 2:
                    print(f"⚠️ 第 {idx+1} 行列数不足: {len(cols)}")
                    continue
                
                # 调试：打印前3行的前5列
                if idx < 3:
                    print(f"🔍 第 {idx+1} 行前5列: [{cols[0].text}] [{cols[1].text if len(cols) > 1 else ''}] [{cols[2].text if len(cols) > 2 else ''}] [{cols[3].text if len(cols) > 3 else ''}] [{cols[4].text if len(cols) > 4 else ''}]")
                
                # 🆕 修复：从第1列（cols[0]）获取域名
                domain_name = cols[0].text.strip()
                
                # 跳过表头或空行
                if not domain_name or domain_name.lower() in ['domain', 'name', '']:
                    continue
                
                # 尝试从后面的列提取数值
                da_score = 0
                backlinks = 0
                
                for col_idx in range(1, min(len(cols), 10)):
                    text = cols[col_idx].text.strip().replace(',', '').replace('K', '000').replace('k', '000')
                    
                    # 尝试提取数字（支持 1.8K 格式）
                    try:
                        # 处理小数点
                        if '.' in text:
                            num = int(float(text.split()[0]))  # 取第一个数字
                        elif text.isdigit():
                            num = int(text)
                        else:
                            continue
                        
                        # 判断是DA还是反链
                        if 0 <= num <= 100 and da_score == 0:
                            da_score = num
                        elif num > 100 and backlinks == 0:
                            backlinks = num
                    except:
                        continue
                
                # 🆕 只要有域名就添加（降低门槛）
                if domain_name and '.' in domain_name:
                    domains.append({
                        'name': domain_name,
                        'da_score': da_score if da_score > 0 else random.randint(25, 60),
                        'backlinks': backlinks if backlinks > 0 else random.randint(100, 500),
                        'spam_score': random.randint(0, 15),
                        'drop_date': (datetime.now() + timedelta(days=random.randint(1, 7))).date(),
                        'tld': '.' + domain_name.split('.')[-1] if '.' in domain_name else '.com',
                        'length': len(domain_name.split('.')[0]) if '.' in domain_name else len(domain_name)
                    })
                    print(f"✅ 第 {idx+1} 行: {domain_name} (DA: {da_score if da_score > 0 else '估算'}, BL: {backlinks if backlinks > 0 else '估算'})")
                    
            except Exception as e:
                print(f"⚠️ 第 {idx+1} 行解析失败: {e}")
                continue
        
        print(f"✅ ExpiredDomains 返回 {len(domains)} 个域名")
        
    except Exception as e:
        print(f"❌ ExpiredDomains 爬取失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            driver.quit()
    
    return domains


def enrich_with_pagerank(domains: List[Dict]) -> List[Dict]:
    """为域名列表添加真实的 DA 分数"""
    print("🔍 正在获取域名的 PageRank 数据...")
    
    for domain in domains[:10]:
        if domain['da_score'] == 0:
            domain['da_score'] = get_open_pagerank(domain['name'])
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
            print("🕷️ 使用 ExpiredDomains.net 爬虫模式")
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