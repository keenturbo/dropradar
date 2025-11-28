import axios from 'axios';

// Railway API 地址
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://dropradar-production.up.railway.app';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Domain {
  id: number;
  name: string;
  da_score: number;
  backlinks_count: number;
  spam_score: number;
  status: string;
  drop_date: string;
  created_at: string;
}

export interface Stats {
  total_domains: number;
  avg_da: number;
  available_count: number;
  low_spam_count: number;
}

// 获取域名列表
export const getDomains = async (): Promise<Domain[]> => {
  try {
    const response = await api.get('/api/v1/domains');
    return response.data;
  } catch (error) {
    console.error('Error fetching domains:', error);
    return [];
  }
};

// 获取统计数据
export const getStats = async (): Promise<Stats | null> => {
  try {
    const response = await api.get('/api/v1/stats');
    return response.data;
  } catch (error) {
    console.error('Error fetching stats:', error);
    return null;
  }
};

// 触发扫描
export const startScan = async (): Promise<{ message: string; domains_found: number }> => {
  try {
    const response = await api.post('/api/v1/scan');
    return response.data;
  } catch (error) {
    console.error('Error starting scan:', error);
    throw error;
  }
};

// 测试 Bark 通知
export const testNotification = async (barkKey: string): Promise<{ message: string }> => {
  try {
    const response = await api.post('/api/v1/test-notification', { bark_key: barkKey });
    return response.data;
  } catch (error) {
    console.error('Error testing notification:', error);
    throw error;
  }
};

export default api;
