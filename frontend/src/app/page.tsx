'use client';

import { useState, useEffect } from 'react';
import { getDomains, getStats, startScan, Domain, Stats } from '@/lib/api';

export default function Home() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [scanning, setScanning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 初始加载数据
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [domainsData, statsData] = await Promise.all([
        getDomains(),
        getStats(),
      ]);
      setDomains(domainsData);
      setStats(statsData);
    } catch (err) {
      setError('Failed to load data from backend');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    setScanning(true);
    setError(null);
    try {
      const result = await startScan();
      console.log('Scan result:', result);
      // 扫描完成后重新加载数据
      await loadData();
    } catch (err) {
      setError('Scan failed. Please try again.');
      console.error(err);
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-2">
                <span className="text-4xl">📡</span>
                DropRadar
              </h1>
              <p className="text-slate-400 mt-1">High-Value Expired Domain Monitor</p>
            </div>
            <button
              onClick={handleScan}
              disabled={scanning || loading}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-lg font-semibold transition-all"
            >
              {scanning ? 'Scanning...' : 'Start Scan'}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-900/20 border border-red-800 text-red-400 px-6 py-4 rounded-lg">
            {error}
          </div>
        )}

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
              <div className="text-slate-400 text-sm font-medium">Total Domains</div>
              <div className="text-3xl font-bold text-white mt-2">{stats.total_domains}</div>
            </div>
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
              <div className="text-slate-400 text-sm font-medium">Avg DA Score</div>
              <div className="text-3xl font-bold text-white mt-2">{stats.avg_da}</div>
            </div>
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
              <div className="text-slate-400 text-sm font-medium">Available</div>
              <div className="text-3xl font-bold text-green-400 mt-2">{stats.available_count}</div>
            </div>
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
              <div className="text-slate-400 text-sm font-medium">Low Spam</div>
              <div className="text-3xl font-bold text-blue-400 mt-2">{stats.low_spam_count}</div>
            </div>
          </div>
        )}

        {/* Domain Table */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-700">
            <h2 className="text-xl font-semibold text-white">High-Value Domains</h2>
          </div>
          
          {loading ? (
            <div className="px-6 py-12 text-center text-slate-400">
              Loading domains...
            </div>
          ) : domains.length === 0 ? (
            <div className="px-6 py-12 text-center text-slate-400">
              No domains found. Click "Start Scan" to search for high-value expired domains.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-900/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Domain
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      DA Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Backlinks
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Spam %
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Drop Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {domains.map((domain) => (
                    <tr key={domain.id} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-white">{domain.name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`text-sm font-semibold ${
                          domain.da_score >= 45 ? 'text-green-400' : 
                          domain.da_score >= 35 ? 'text-yellow-400' : 'text-slate-400'
                        }`}>
                          {domain.da_score}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                        {domain.backlinks_count.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`text-sm font-semibold ${
                          domain.spam_score < 5 ? 'text-green-400' : 
                          domain.spam_score < 10 ? 'text-yellow-400' : 'text-red-400'
                        }`}>
                          {domain.spam_score}%
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          domain.status === 'available' ? 'bg-green-900/30 text-green-400' :
                          domain.status === 'auction' ? 'bg-yellow-900/30 text-yellow-400' :
                          'bg-slate-700 text-slate-400'
                        }`}>
                          {domain.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                        {domain.drop_date}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <a
                          href={`https://www.namecheap.com/domains/registration/results/?domain=${domain.name}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 font-medium"
                        >
                          Register →
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer Note */}
        <div className="mt-8 text-center text-slate-500 text-sm">
          <p>Connected to Railway Backend: https://dropradar-production.up.railway.app</p>
        </div>
      </main>
    </div>
  );
}
