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
  const response = await fetch(`${API_BASE_URL}/api/v1/domains`);
  if (!response.ok) {
    throw new Error('Failed to fetch domains');
  }
  return response.json();
}

export async function getStats(): Promise<StatsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/stats`);
  if (!response.ok) {
    throw new Error('Failed to fetch stats');
  }
  return response.json();
}

export async function startScan(barkKey?: string): Promise<ScanResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/scan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ bark_key: barkKey }),
  });
  if (!response.ok) {
    throw new Error('Scan failed');
  }
  return response.json();
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