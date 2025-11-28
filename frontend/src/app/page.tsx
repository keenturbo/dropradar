'use client';

import { useState, useEffect } from 'react';
import { getDomains, getStats, startScan, deleteDomain, clearAllDomains } from '@/lib/api';

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

interface Stats {
  total: number;
  avg_da: number;
  available: number;
  low_spam: number;
}

export default function Home() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [stats, setStats] = useState<Stats>({ total: 0, avg_da: 0, available: 0, low_spam: 0 });
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [domainsResponse, statsData] = await Promise.all([
        getDomains(),
        getStats()
      ]);
      
      console.log('Domains response:', domainsResponse);
      console.log('Stats data:', statsData);
      
      if (domainsResponse && Array.isArray(domainsResponse.domains)) {
        setDomains(domainsResponse.domains);
      } else {
        console.error('Invalid domains data structure:', domainsResponse);
        setDomains([]);
      }
      
      if (statsData && typeof statsData === 'object') {
        setStats({
          total: statsData.total || 0,
          avg_da: statsData.avg_da || 0,
          available: statsData.available || 0,
          low_spam: statsData.low_spam || 0
        });
      } else {
        console.error('Invalid stats data structure:', statsData);
      }
      
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError('无法连接到后端 API');
      setDomains([]);
      setStats({ total: 0, avg_da: 0, available: 0, low_spam: 0 });
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    console.log('🔘 Scan button clicked');
    
    try {
      setScanning(true);
      setError(null);
      
      console.log('📞 Calling startScan API...');
      const result = await startScan('expireddomains');
      
      console.log('✅ Scan completed:', result);
      
      if (typeof window !== 'undefined' && window.alert) {
        window.alert(`✅ ${result.message}`);
      }
      
      console.log('🔄 Refreshing data...');
      await fetchData();
      
    } catch (err: any) {
      console.error('❌ Scan error:', err);
      const errorMsg = err.message || '扫描失败，请检查网络连接';
      setError(errorMsg);
      
      if (typeof window !== 'undefined' && window.alert) {
        window.alert(`❌ ${errorMsg}`);
      }
    } finally {
      setScanning(false);
      console.log('🏁 Scan process finished');
    }
  };

  // 🆕 删除单个域名
  const handleDelete = async (domainId: number, domainName: string) => {
    if (!confirm(`确认删除域名 ${domainName}？`)) {
      return;
    }
    
    try {
      await deleteDomain(domainId);
      alert('删除成功');
      await fetchData();
    } catch (err) {
      alert('删除失败');
    }
  };

  // 🆕 清空所有域名
  const handleClearAll = async () => {
    if (!confirm('确认清空所有域名？此操作不可恢复！')) {
      return;
    }
    
    try {
      const result = await clearAllDomains();
      alert(result.message);
      await fetchData();
    } catch (err) {
      alert('清空失败');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit' 
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <header className="border-b border-gray-700 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">DropRadar</h1>
              <p className="text-gray-400 text-sm mt-1">高价值过期域名监控雷达</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleClearAll}
                className="px-6 py-3 rounded-lg font-semibold bg-red-600 hover:bg-red-700 text-white transition-all"
              >
                🗑️ 清空所有
              </button>
              <button
                onClick={handleScan}
                disabled={scanning || loading}
                className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                  scanning || loading
                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-blue-500/50'
                }`}
              >
                {scanning ? '扫描中...' : '🔍 Start Scan'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200">
            ⚠️ {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-blue-500 transition-all">
            <div className="text-gray-400 text-sm mb-2">Total Domains</div>
            <div className="text-3xl font-bold text-white">{stats.total}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-green-500 transition-all">
            <div className="text-gray-400 text-sm mb-2">Average DA</div>
            <div className="text-3xl font-bold text-green-400">{stats.avg_da.toFixed(1)}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-purple-500 transition-all">
            <div className="text-gray-400 text-sm mb-2">Available</div>
            <div className="text-3xl font-bold text-purple-400">{stats.available}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-yellow-500 transition-all">
            <div className="text-gray-400 text-sm mb-2">Low Spam Score</div>
            <div className="text-3xl font-bold text-yellow-400">{stats.low_spam}</div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700 bg-gray-900/50">
            <h2 className="text-xl font-semibold text-white">高价值域名列表</h2>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
              <p className="text-gray-400 mt-4">加载中...</p>
            </div>
          ) : domains.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-400 text-lg">暂无数据</p>
              <p className="text-gray-500 text-sm mt-2">点击右上角 "Start Scan" 开始扫描</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-900/50">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Domain</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">DA Score</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Backlinks</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Spam Score</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Drop Date</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {domains.map((domain) => (
                    <tr key={domain.id} className="hover:bg-gray-700/50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-white font-medium">{domain.name}</div>
                        <div className="text-gray-400 text-sm">{domain.tld} • {domain.length} chars</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${
                          domain.da_score >= 40 ? 'bg-green-900 text-green-300' :
                          domain.da_score >= 30 ? 'bg-yellow-900 text-yellow-300' :
                          'bg-gray-700 text-gray-300'
                        }`}>
                          {domain.da_score}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-300">
                        {domain.backlinks.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${
                          domain.spam_score < 5 ? 'bg-green-900 text-green-300' :
                          domain.spam_score < 10 ? 'bg-yellow-900 text-yellow-300' :
                          'bg-red-900 text-red-300'
                        }`}>
                          {domain.spam_score}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-blue-900 text-blue-300">
                          {domain.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-300">
                        {formatDate(domain.drop_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex gap-2">
                          <a
                            href={`https://www.namecheap.com/domains/registration/results/?domain=${domain.name}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
                          >
                            Register →
                          </a>
                          <button
                            onClick={() => handleDelete(domain.id, domain.name)}
                            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors"
                          >
                            删除
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>Powered by Railway + Vercel • Built with Next.js + FastAPI</p>
        </div>
      </main>
    </div>
  );
}