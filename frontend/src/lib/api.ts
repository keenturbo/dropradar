const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://dropradar-production.up.railway.app';

interface Domain {
  id: number;
  name: string;
  da_score: number;
  backlinks: number;
  spam_score: number;
  status: string;
  drop_date: string;
  tld: string;
  length: number;
}

interface DomainsResponse {
  domains: Domain[];
  total: number;
  skip: number;
  limit: number;
}

interface StatsResponse {
  total: number;
  avg_da: number;
  available: number;
  low_spam: number;
}

interface ScanResponse {
  status: string;
  domains_found: number;
  message: string;
}

export async function getDomains(): Promise<DomainsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/domains`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  return response.json();
}

export async function getStats(): Promise<StatsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/stats`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  return response.json();
}

export async function startScan(mode: string = 'domainsdb', barkKey?: string): Promise<ScanResponse> {
  console.log('🚀 API: Starting scan...', { mode, barkKey });
  
  const url = `${API_BASE_URL}/api/v1/scan?mode=${mode}`;
  console.log('📡 API URL:', url);
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ bark_key: barkKey }),
  });
  
  console.log('📥 API Response status:', response.status);
  
  if (!response.ok) {
    const errorText = await response.text();
    console.error('❌ API Error:', errorText);
    throw new Error(`扫描失败: ${response.status} ${errorText}`);
  }
  
  const data = await response.json();
  console.log('✅ API Response data:', data);
  
  return data;
}

export async function testNotification(barkKey: string): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/test-notification`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ bark_key: barkKey }),
  });
  
  if (!response.ok) {
    throw new Error('Notification test failed');
  }
  
  return response.json();
}