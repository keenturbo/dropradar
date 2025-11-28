'use client';

import { useState } from 'react';

// Mock data - 模拟高价值域名数据
const mockDomains = [
  { id: 1, name: 'gemini4.com', da: 45, backlinks: 1250, spamScore: 3, status: 'Available', dropDate: '2025-12-05' },
  { id: 2, name: 'claude-pro.ai', da: 38, backlinks: 890, spamScore: 5, status: 'Available', dropDate: '2025-12-06' },
  { id: 3, name: 'gpt5.io', da: 52, backlinks: 2100, spamScore: 2, status: 'Auction', dropDate: '2025-12-04' },
  { id: 4, name: 'ai-tools.net', da: 41, backlinks: 1560, spamScore: 4, status: 'Available', dropDate: '2025-12-07' },
  { id: 5, name: 'seo-master.com', da: 48, backlinks: 1890, spamScore: 6, status: 'Pending', dropDate: '2025-12-08' },
];

export default function Home() {
  const [domains] = useState(mockDomains);
  const [scanning, setScanning] = useState(false);

  const handleScan = () => {
    setScanning(true);
    setTimeout(() => setScanning(false), 2000);
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
              disabled={scanning}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-lg font-semibold transition-all"
            >
              {scanning ? 'Scanning...' : 'Start Scan'}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
            <div className="text-slate-400 text-sm font-medium">Total Domains</div>
            <div className="text-3xl font-bold text-white mt-2">{domains.length}</div>
          </div>
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
            <div className="text-slate-400 text-sm font-medium">Avg DA Score</div>
            <div className="text-3xl font-bold text-white mt-2">
              {Math.round(domains.reduce((sum, d) => sum + d.da, 0) / domains.length)}
            </div>
          </div>
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
            <div className="text-slate-400 text-sm font-medium">Available</div>
            <div className="text-3xl font-bold text-green-400 mt-2">
              {domains.filter(d => d.status === 'Available').length}
            </div>
          </div>
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
            <div className="text-slate-400 text-sm font-medium">Low Spam</div>
            <div className="text-3xl font-bold text-blue-400 mt-2">
              {domains.filter(d => d.spamScore < 5).length}
            </div>
          </div>
        </div>

        {/* Domain Table */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-700">
            <h2 className="text-xl font-semibold text-white">High-Value Domains</h2>
          </div>
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
                        domain.da >= 45 ? 'text-green-400' : 
                        domain.da >= 35 ? 'text-yellow-400' : 'text-slate-400'
                      }`}>
                        {domain.da}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                      {domain.backlinks.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-semibold ${
                        domain.spamScore < 5 ? 'text-green-400' : 
                        domain.spamScore < 10 ? 'text-yellow-400' : 'text-red-400'
                      }`}>
                        {domain.spamScore}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        domain.status === 'Available' ? 'bg-green-900/30 text-green-400' :
                        domain.status === 'Auction' ? 'bg-yellow-900/30 text-yellow-400' :
                        'bg-slate-700 text-slate-400'
                      }`}>
                        {domain.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                      {domain.dropDate}
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
        </div>

        {/* Footer Note */}
        <div className="mt-8 text-center text-slate-500 text-sm">
          <p>MVP Demo - Mock data shown. Backend integration in progress.</p>
        </div>
      </main>
    </div>
  );
}
