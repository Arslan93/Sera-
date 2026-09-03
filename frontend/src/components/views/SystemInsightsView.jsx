import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  Monitor, 
  Cpu, 
  HardDrive, 
  Gamepad2, 
  Zap, 
  Activity, 
  Wifi, 
  Battery, 
  User, 
  Search, 
  RefreshCw, 
  ShieldCheck, 
  ShieldAlert, 
  Loader2,
  AlertCircle
} from 'lucide-react';

const CIRCUMFERENCE_32 = 201.06;

export default function SystemInsightsView() {
  const { showToast } = useApp();
  const [activeTab, setActiveTab] = useState('overview');

  // Tab Data States
  const [overview, setOverview] = useState(null);
  const [appsData, setAppsData] = useState({ apps: [], cache_age_seconds: 0 });
  const [appsSearch, setAppsSearch] = useState('');
  const [gamesData, setGamesData] = useState({ games: [] });
  const [startupData, setStartupData] = useState({ programs: [] });
  const [processesData, setProcessesData] = useState({ processes: [], sort_by: 'memory' });
  const [procSort, setProcSort] = useState('memory');
  const [networkData, setNetworkData] = useState(null);
  const [batteryData, setBatteryData] = useState(null);
  const [accountData, setAccountData] = useState(null);

  // Loading States
  const [loadingOverview, setLoadingOverview] = useState(false);
  const [loadingApps, setLoadingApps] = useState(false);
  const [loadingGames, setLoadingGames] = useState(false);
  const [loadingStartup, setLoadingStartup] = useState(false);
  const [loadingNetwork, setLoadingNetwork] = useState(false);

  // Fetch Overview
  const fetchOverview = useCallback(async () => {
    setLoadingOverview(true);
    try {
      const res = await fetch('/api/system/overview');
      const data = await res.json();
      if (data.status === 'success') setOverview(data);
    } catch (e) {
      console.warn('Overview fetch error:', e);
    } finally {
      setLoadingOverview(false);
    }
  }, []);

  // Fetch Apps
  const fetchApps = useCallback(async (force = false) => {
    setLoadingApps(true);
    try {
      const url = `/api/system/apps?force_refresh=${force ? 'true' : 'false'}`;
      const res = await fetch(url);
      const data = await res.json();
      if (data.status === 'success') setAppsData(data);
    } catch (e) {
      console.warn('Apps fetch error:', e);
    } finally {
      setLoadingApps(false);
    }
  }, []);

  // Fetch Games
  const fetchGames = useCallback(async (force = false) => {
    setLoadingGames(true);
    try {
      const url = `/api/system/games?force_refresh=${force ? 'true' : 'false'}`;
      const res = await fetch(url);
      const data = await res.json();
      if (data.status === 'success') setGamesData(data);
    } catch (e) {
      console.warn('Games fetch error:', e);
    } finally {
      setLoadingGames(false);
    }
  }, []);

  // Fetch Startup
  const fetchStartup = useCallback(async () => {
    setLoadingStartup(true);
    try {
      const res = await fetch('/api/system/startup');
      const data = await res.json();
      if (data.status === 'success') setStartupData(data);
    } catch (e) {
      console.warn('Startup fetch error:', e);
    } finally {
      setLoadingStartup(false);
    }
  }, []);

  // Fetch Processes
  const fetchProcesses = useCallback(async (sort = procSort) => {
    try {
      const res = await fetch(`/api/system/processes?sort_by=${sort}&limit=25`);
      const data = await res.json();
      if (data.status === 'success') setProcessesData(data);
    } catch (e) {
      console.warn('Processes fetch error:', e);
    }
  }, [procSort]);

  // Fetch Network
  const fetchNetwork = useCallback(async () => {
    setLoadingNetwork(true);
    try {
      const res = await fetch('/api/system/network');
      const data = await res.json();
      if (data.status === 'success') setNetworkData(data);
    } catch (e) {
      console.warn('Network fetch error:', e);
    } finally {
      setLoadingNetwork(false);
    }
  }, []);

  // Fetch Battery
  const fetchBattery = useCallback(async () => {
    try {
      const res = await fetch('/api/system/battery');
      const data = await res.json();
      if (data.status === 'success') setBatteryData(data);
    } catch (e) {
      console.warn('Battery fetch error:', e);
    }
  }, []);

  // Fetch Account
  const fetchAccount = useCallback(async () => {
    try {
      const res = await fetch('/api/system/account');
      const data = await res.json();
      if (data.status === 'success') setAccountData(data);
    } catch (e) {
      console.warn('Account fetch error:', e);
    }
  }, []);

  // Initial Load
  useEffect(() => {
    fetchOverview();
    fetchBattery();
    fetchAccount();
  }, [fetchOverview, fetchBattery, fetchAccount]);

  // Tab change triggers
  useEffect(() => {
    if (activeTab === 'apps' && appsData.apps.length === 0) fetchApps();
    if (activeTab === 'games' && gamesData.games.length === 0) fetchGames();
    if (activeTab === 'startup' && startupData.programs.length === 0) fetchStartup();
    if (activeTab === 'processes') fetchProcesses(procSort);
    if (activeTab === 'network' && !networkData) fetchNetwork();
  }, [activeTab, appsData.apps.length, gamesData.games.length, startupData.programs.length, networkData, fetchApps, fetchGames, fetchStartup, fetchProcesses, fetchNetwork, procSort]);

  // Process polling when on Processes tab
  useEffect(() => {
    if (activeTab !== 'processes') return;
    const interval = setInterval(() => fetchProcesses(procSort), 3500);
    return () => clearInterval(interval);
  }, [activeTab, fetchProcesses, procSort]);

  // Calculations for dials
  const cpuPercent = overview?.cpu?.usage_percent || 0;
  const ramPercent = overview?.ram?.percent_used || 0;
  const cpuOffset = CIRCUMFERENCE_32 * (1 - Math.min(100, Math.max(0, cpuPercent)) / 100);
  const ramOffset = CIRCUMFERENCE_32 * (1 - Math.min(100, Math.max(0, ramPercent)) / 100);

  // Filtered Apps
  const filteredApps = (appsData.apps || []).filter(a => 
    a.name.toLowerCase().includes(appsSearch.toLowerCase()) || 
    (a.publisher || '').toLowerCase().includes(appsSearch.toLowerCase())
  );

  const hasBattery = batteryData?.has_battery;

  return (
    <div className="view-panel flex-1 flex flex-col min-h-0 bg-[#F8FAFC]">
      {/* Top Header & Sub-Tab Bar */}
      <div className="flex-shrink-0 bg-white border-b border-slate-200 px-5 pt-3.5 pb-0 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 gap-2">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shadow-sm">
              <Monitor className="w-4 h-4" />
            </div>
            <div>
              <h1 className="font-bold text-sm text-slate-900 leading-none">System Insights</h1>
              <span className="text-[11px] font-mono text-slate-500">Hardware, Inventory & Process Diagnostics</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 font-mono text-[10.5px] text-slate-600 font-semibold">
              Host: {overview?.hostname || 'Scanning...'}
            </span>
          </div>
        </div>

        {/* In-Page Sub-Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto border-t border-slate-100 pt-1 text-xs font-medium">
          <button 
            onClick={() => setActiveTab('overview')} 
            className={`px-3 py-2 border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'overview' 
                ? 'border-blue-600 text-blue-600 font-bold' 
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Overview</span>
          </button>

          <button 
            onClick={() => setActiveTab('apps')} 
            className={`px-3 py-2 border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'apps' 
                ? 'border-blue-600 text-blue-600 font-bold' 
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <HardDrive className="w-3.5 h-3.5" />
            <span>Applications ({appsData.total_apps || 0})</span>
          </button>

          <button 
            onClick={() => setActiveTab('games')} 
            className={`px-3 py-2 border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'games' 
                ? 'border-blue-600 text-blue-600 font-bold' 
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <Gamepad2 className="w-3.5 h-3.5" />
            <span>Games ({gamesData.total_games || 0})</span>
          </button>

          <button 
            onClick={() => setActiveTab('startup')} 
            className={`px-3 py-2 border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'startup' 
                ? 'border-blue-600 text-blue-600 font-bold' 
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Startup</span>
          </button>

          <button 
            onClick={() => setActiveTab('processes')} 
            className={`px-3 py-2 border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'processes' 
                ? 'border-blue-600 text-blue-600 font-bold' 
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Processes</span>
          </button>

          <button 
            onClick={() => setActiveTab('network')} 
            className={`px-3 py-2 border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'network' 
                ? 'border-blue-600 text-blue-600 font-bold' 
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <Wifi className="w-3.5 h-3.5" />
            <span>Network</span>
          </button>

          {hasBattery && (
            <button 
              onClick={() => setActiveTab('battery')} 
              className={`px-3 py-2 border-b-2 flex items-center gap-1.5 transition-colors ${
                activeTab === 'battery' 
                  ? 'border-blue-600 text-blue-600 font-bold' 
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <Battery className="w-3.5 h-3.5" />
              <span>Battery</span>
            </button>
          )}

          <button 
            onClick={() => setActiveTab('account')} 
            className={`px-3 py-2 border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'account' 
                ? 'border-blue-600 text-blue-600 font-bold' 
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <User className="w-3.5 h-3.5" />
            <span>Account</span>
          </button>
        </div>
      </div>

      {/* Main Tab Content Area */}
      <div className="flex-1 overflow-y-auto p-5">
        
        {/* ═══════════ SUB-TAB 1: OVERVIEW ═══════════ */}
        {activeTab === 'overview' && (
          <div className="space-y-4 max-w-6xl mx-auto animate-in fade-in duration-100">
            {/* Row 1: Hardware Dials + Per-Drive Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              
              {/* CPU & RAM 3D Radial Dials */}
              <div className="studio-card p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100 mb-2">
                  <span className="font-bold text-xs text-slate-800">Processor & Memory Vitals</span>
                  <button onClick={fetchOverview} className="text-xs text-slate-400 hover:text-slate-700">
                    <RefreshCw className={`w-3 h-3 ${loadingOverview ? 'animate-spin' : ''}`} />
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2 py-2">
                  {/* CPU Dial */}
                  <div className="flex flex-col items-center">
                    <div className="dial-housing mb-1">
                      <div className="dial-track-recess">
                        <svg className="dial-svg" viewBox="0 0 76 76">
                          <circle className="dial-svg-track" cx="38" cy="38" r="32"></circle>
                          <circle 
                            className="dial-svg-value stroke-blue-500" 
                            cx="38" cy="38" r="32" 
                            strokeDasharray="201.06" 
                            strokeDashoffset={cpuOffset}
                          ></circle>
                        </svg>
                        <div className="dial-hub">
                          <span className="font-mono font-bold text-[13px] text-slate-900 leading-none">
                            {Math.round(cpuPercent)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    <span className="text-[11px] font-bold text-slate-700">CPU</span>
                    <span className="text-[10px] font-mono text-slate-400">
                      {overview?.cpu?.logical_cores} Cores
                    </span>
                  </div>

                  {/* RAM Dial */}
                  <div className="flex flex-col items-center">
                    <div className="dial-housing mb-1">
                      <div className="dial-track-recess">
                        <svg className="dial-svg" viewBox="0 0 76 76">
                          <circle className="dial-svg-track" cx="38" cy="38" r="32"></circle>
                          <circle 
                            className="dial-svg-value stroke-emerald-500" 
                            cx="38" cy="38" r="32" 
                            strokeDasharray="201.06" 
                            strokeDashoffset={ramOffset}
                          ></circle>
                        </svg>
                        <div className="dial-hub">
                          <span className="font-mono font-bold text-[13px] text-slate-900 leading-none">
                            {Math.round(ramPercent)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    <span className="text-[11px] font-bold text-slate-700">RAM</span>
                    <span className="text-[10px] font-mono text-slate-400">
                      {overview?.ram?.used_gb} / {overview?.ram?.total_gb} GB
                    </span>
                  </div>
                </div>

                <div className="text-[10.5px] text-slate-500 font-mono text-center pt-2 border-t border-slate-100">
                  Uptime: <b className="text-slate-800">{overview?.uptime_human || 'Calculating...'}</b>
                </div>
              </div>

              {/* Multi-Drive Storage Breakdown */}
              <div className="studio-card p-4 lg:col-span-2">
                <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 mb-3">
                  <div className="flex items-center gap-2">
                    <HardDrive className="w-4 h-4 text-blue-600" />
                    <span className="font-bold text-xs text-slate-800">Storage Drives Breakdown</span>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400">
                    {(overview?.disks || []).length} partitions mounted
                  </span>
                </div>

                <div className="space-y-3">
                  {(overview?.disks || []).map((d, i) => (
                    <div key={i} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                      <div className="flex items-center justify-between text-xs mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900">{d.device || d.mountpoint}</span>
                          <span className="text-[10px] font-mono px-1 rounded bg-slate-200 text-slate-700">
                            {d.fstype}
                          </span>
                        </div>
                        <span className="font-mono text-[11px] text-slate-600">
                          <b>{d.free_gb} GB free</b> of {d.total_gb} GB ({d.percent_used}% used)
                        </span>
                      </div>
                      <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                        <div 
                          className={`h-2 rounded-full transition-all duration-500 ${
                            d.percent_used > 85 ? 'bg-rose-500' : (d.percent_used > 70 ? 'bg-amber-500' : 'bg-blue-600')
                          }`}
                          style={{ width: `${d.percent_used}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Row 2: Detailed Specs Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="studio-card p-3.5 text-xs">
                <span className="text-[10.5px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-1">OPERATING SYSTEM</span>
                <div className="font-bold text-slate-900 text-[13px] mb-0.5">{overview?.os?.system} {overview?.os?.release}</div>
                <div className="text-slate-500 text-[11px] font-mono">{overview?.os?.version}</div>
                <div className="text-slate-400 text-[10.5px] font-mono mt-1">Arch: {overview?.os?.architecture}</div>
              </div>

              <div className="studio-card p-3.5 text-xs">
                <span className="text-[10.5px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-1">PROCESSOR</span>
                <div className="font-bold text-slate-900 text-[13px] mb-0.5 truncate" title={overview?.cpu?.processor}>
                  {overview?.cpu?.processor}
                </div>
                <div className="text-slate-500 text-[11px] font-mono">
                  {overview?.cpu?.physical_cores} Physical / {overview?.cpu?.logical_cores} Logical Cores
                </div>
                <div className="text-slate-400 text-[10.5px] font-mono mt-1">
                  Speed: {overview?.cpu?.current_freq_mhz || '--'} MHz
                </div>
              </div>

              <div className="studio-card p-3.5 text-xs">
                <span className="text-[10.5px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-1">GRAPHICS</span>
                <div className="font-bold text-slate-900 text-[13px] mb-0.5 truncate" title={overview?.gpu}>
                  {overview?.gpu || 'GPU info unavailable'}
                </div>
                <div className="text-slate-500 text-[11px] font-mono">Integrated / Dedicated</div>
              </div>

              <div className="studio-card p-3.5 text-xs">
                <span className="text-[10.5px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-1">NETWORK IDENTITY</span>
                <div className="font-bold text-slate-900 text-[13px] mb-0.5">{overview?.hostname}</div>
                <div className="text-slate-500 text-[11px] font-mono">User: {overview?.username}</div>
              </div>
            </div>
          </div>
        )}

        {/* ═══════════ SUB-TAB 2: APPLICATIONS ═══════════ */}
        {activeTab === 'apps' && (
          <div className="space-y-3 max-w-6xl mx-auto animate-in fade-in duration-100">
            <div className="studio-card p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="relative flex-1">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input 
                  type="text" 
                  value={appsSearch}
                  onChange={(e) => setAppsSearch(e.target.value)}
                  placeholder="Search installed applications or publishers..." 
                  className="studio-well w-full pl-9 pr-3 py-1.5 text-xs bg-white text-slate-800"
                />
              </div>

              <div className="flex items-center gap-2 flex-shrink-0 text-xs font-mono text-slate-500">
                <span>
                  {appsData.cached ? `Last scanned ${Math.round(appsData.cache_age_seconds / 60)}m ago` : 'Fresh scan'}
                </span>
                <button 
                  onClick={() => fetchApps(true)} 
                  disabled={loadingApps}
                  className="btn-secondary py-1 px-2.5 flex items-center gap-1.5 text-[11px]"
                >
                  <RefreshCw className={`w-3 h-3 ${loadingApps ? 'animate-spin' : ''}`} />
                  <span>Rescan Registry</span>
                </button>
              </div>
            </div>

            <div className="studio-card overflow-hidden">
              <div className="overflow-x-auto max-h-[560px]">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3">Application Name</th>
                      <th className="py-2.5 px-3">Version</th>
                      <th className="py-2.5 px-3">Publisher</th>
                      <th className="py-2.5 px-3 text-right">Install Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredApps.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="py-8 text-center text-slate-400 font-mono">
                          {loadingApps ? 'Scanning registry for installed applications...' : 'No applications matching search.'}
                        </td>
                      </tr>
                    ) : (
                      filteredApps.map((app, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                          <td className="py-2 px-3 font-semibold text-slate-900">{app.name}</td>
                          <td className="py-2 px-3 font-mono text-slate-600 text-[11.5px]">{app.version || '--'}</td>
                          <td className="py-2 px-3 text-slate-500 text-[11.5px]">{app.publisher || 'Unknown'}</td>
                          <td className="py-2 px-3 font-mono text-slate-400 text-[11px] text-right">{app.install_date || '--'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ═══════════ SUB-TAB 3: GAMES ═══════════ */}
        {activeTab === 'games' && (
          <div className="space-y-4 max-w-6xl mx-auto animate-in fade-in duration-100">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <div>
                <h3 className="font-bold text-xs text-slate-900">Installed Games Library</h3>
                <span className="text-[11px] text-slate-500">Detected from Steam and Epic Games launchers</span>
              </div>
              <button 
                onClick={() => fetchGames(true)} 
                disabled={loadingGames}
                className="btn-secondary py-1 px-2.5 flex items-center gap-1.5 text-xs"
              >
                <RefreshCw className={`w-3 h-3 ${loadingGames ? 'animate-spin' : ''}`} />
                <span>Rescan Launchers</span>
              </button>
            </div>

            {(gamesData.games || []).length === 0 ? (
              <div className="studio-card p-10 text-center">
                <Gamepad2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="font-semibold text-xs text-slate-700 mb-1">No game launchers detected</p>
                <p className="text-[11px] text-slate-400 font-mono">
                  No Steam or Epic Games libraries were found in standard Windows directories.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {gamesData.games.map((g, i) => (
                  <div key={i} className="studio-card p-3.5 flex flex-col justify-between hover:border-blue-300 transition-colors">
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                          g.platform === 'Steam' ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'bg-purple-50 text-purple-700 border border-purple-200'
                        }`}>
                          {g.platform}
                        </span>
                        {g.size_gb > 0 && (
                          <span className="font-mono text-[11px] text-slate-600 font-semibold">{g.size_gb} GB</span>
                        )}
                      </div>
                      <h4 className="font-bold text-xs text-slate-900 mb-1">{g.name}</h4>
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono truncate pt-2 mt-2 border-t border-slate-100" title={g.install_path}>
                      {g.install_path}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ═══════════ SUB-TAB 4: STARTUP ═══════════ */}
        {activeTab === 'startup' && (
          <div className="space-y-3 max-w-6xl mx-auto animate-in fade-in duration-100">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <div>
                <h3 className="font-bold text-xs text-slate-900">Windows Startup Programs</h3>
                <span className="text-[11px] text-slate-500">Read-only diagnostic audit from Registry Run keys and Startup folder</span>
              </div>
              <button onClick={fetchStartup} className="btn-secondary py-1 px-2.5 flex items-center gap-1.5 text-xs">
                <RefreshCw className={`w-3 h-3 ${loadingStartup ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>

            <div className="studio-card overflow-hidden">
              <div className="divide-y divide-slate-100 max-h-[540px] overflow-y-auto">
                {(startupData.programs || []).map((p, i) => (
                  <div key={i} className="p-3 flex items-start justify-between text-xs hover:bg-slate-50/80 transition-colors">
                    <div className="min-w-0 flex-1 pr-4">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-slate-900">{p.name}</span>
                        <span className="text-[10px] font-mono px-1.5 rounded bg-slate-100 text-slate-500">
                          {p.location}
                        </span>
                      </div>
                      <div className="font-mono text-[11px] text-slate-500 truncate" title={p.command}>
                        {p.command}
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-50 border border-emerald-200 text-emerald-700 flex-shrink-0">
                      Enabled
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ═══════════ SUB-TAB 5: PROCESSES ═══════════ */}
        {activeTab === 'processes' && (
          <div className="space-y-3 max-w-6xl mx-auto animate-in fade-in duration-100">
            <div className="studio-card p-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-700">Sort Processes By:</span>
                <button 
                  onClick={() => { setProcSort('memory'); fetchProcesses('memory'); }}
                  className={`px-2.5 py-1 text-xs font-medium rounded ${
                    procSort === 'memory' ? 'btn-primary' : 'btn-secondary'
                  }`}
                >
                  Memory (RAM)
                </button>
                <button 
                  onClick={() => { setProcSort('cpu'); fetchProcesses('cpu'); }}
                  className={`px-2.5 py-1 text-xs font-medium rounded ${
                    procSort === 'cpu' ? 'btn-primary' : 'btn-secondary'
                  }`}
                >
                  CPU Load
                </button>
              </div>

              <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
                <span className="w-2 h-2 rounded-full bg-emerald-500 agentic-live"></span>
                <span>Live polling (3.5s)</span>
              </div>
            </div>

            <div className="studio-card overflow-hidden">
              <div className="overflow-x-auto max-h-[520px]">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3">PID</th>
                      <th className="py-2.5 px-3">Process Name</th>
                      <th className="py-2.5 px-3 text-right">CPU %</th>
                      <th className="py-2.5 px-3 text-right">Memory (RAM)</th>
                      <th className="py-2.5 px-3 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(processesData.processes || []).map((proc) => (
                      <tr key={proc.pid} className={`hover:bg-slate-50/80 transition-colors ${proc.is_high_resource ? 'bg-amber-50/40' : ''}`}>
                        <td className="py-2 px-3 font-mono text-slate-500">{proc.pid}</td>
                        <td className="py-2 px-3 font-semibold text-slate-900">{proc.name}</td>
                        <td className={`py-2 px-3 font-mono text-right font-semibold ${
                          proc.cpu_percent > 30 ? 'text-amber-700' : 'text-slate-700'
                        }`}>
                          {proc.cpu_percent}%
                        </td>
                        <td className={`py-2 px-3 font-mono text-right font-semibold ${
                          proc.memory_mb > 1200 ? 'text-rose-700' : 'text-slate-700'
                        }`}>
                          {proc.memory_mb} MB
                        </td>
                        <td className="py-2 px-3 text-right">
                          {proc.is_high_resource ? (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-100 text-amber-800">
                              High Load
                            </span>
                          ) : (
                            <span className="text-[11px] font-mono text-slate-400">Normal</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ═══════════ SUB-TAB 6: NETWORK ═══════════ */}
        {activeTab === 'network' && (
          <div className="space-y-4 max-w-6xl mx-auto animate-in fade-in duration-100">
            {/* Active Connection Hero */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="studio-card p-4">
                <span className="text-[10.5px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  ACTIVE ADAPTER
                </span>
                <div className="font-bold text-slate-900 text-sm mb-1">
                  {networkData?.active_adapter?.name || 'No active connection'}
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-1.5 py-0.5 rounded text-[10.5px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
                    {networkData?.active_adapter?.type}
                  </span>
                  <span className="font-mono text-xs text-slate-600">
                    IPv4: {networkData?.active_adapter?.ipv4}
                  </span>
                </div>
              </div>

              <div className="studio-card p-4">
                <span className="text-[10.5px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  PUBLIC IP ADDRESS
                </span>
                <div className="font-bold text-slate-900 text-sm mb-1 font-mono">
                  {networkData?.public_ip || 'Checking...'}
                </div>
                <div className="text-slate-400 text-[11px] font-mono">
                  Echo service cached for 1 hour
                </div>
              </div>

              <div className="studio-card p-4">
                <span className="text-[10.5px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  TRAFFIC SINCE BOOT
                </span>
                <div className="font-mono text-xs space-y-1 mt-1">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Sent:</span>
                    <b className="text-slate-800">{networkData?.bandwidth?.bytes_sent_mb || 0} MB</b>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Received:</span>
                    <b className="text-slate-800">{networkData?.bandwidth?.bytes_recv_mb || 0} MB</b>
                  </div>
                </div>
              </div>
            </div>

            {/* All Adapters List */}
            <div className="studio-card p-4">
              <h3 className="font-bold text-xs text-slate-900 mb-3">All Detected Interfaces</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(networkData?.adapters || []).map((ad, i) => (
                  <div key={i} className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-slate-900">{ad.name}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                        ad.is_up ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-200 text-slate-500'
                      }`}>
                        {ad.is_up ? 'CONNECTED' : 'DISCONNECTED'}
                      </span>
                    </div>
                    <div className="text-slate-500 font-mono text-[11px] space-y-0.5">
                      <div>IP: {ad.ipv4}</div>
                      <div>MAC: {ad.mac}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ═══════════ SUB-TAB 7: BATTERY ═══════════ */}
        {activeTab === 'battery' && hasBattery && (
          <div className="max-w-md mx-auto studio-card p-5 text-center space-y-4 animate-in fade-in duration-100">
            <h3 className="font-bold text-xs text-slate-900">Battery & Power Health</h3>
            
            <div className="flex justify-center">
              <div className="dial-housing">
                <div className="dial-track-recess">
                  <svg className="dial-svg" viewBox="0 0 76 76">
                    <circle className="dial-svg-track" cx="38" cy="38" r="32"></circle>
                    <circle 
                      className="dial-svg-value stroke-emerald-500" 
                      cx="38" cy="38" r="32" 
                      strokeDasharray="201.06" 
                      strokeDashoffset={CIRCUMFERENCE_32 * (1 - (batteryData?.percent || 0) / 100)}
                    ></circle>
                  </svg>
                  <div className="dial-hub">
                    <span className="font-mono font-bold text-[15px] text-slate-900 leading-none">
                      {batteryData?.percent}%
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-1 text-xs">
              <div className="font-semibold text-slate-800">
                {batteryData?.power_plugged ? '⚡ AC Power Connected (Charging/Charged)' : 'Running on Battery Power'}
              </div>
              <div className="text-slate-500 font-mono text-[11px]">
                Estimated: {batteryData?.time_remaining_human}
              </div>
            </div>
          </div>
        )}

        {/* ═══════════ SUB-TAB 8: ACCOUNT ═══════════ */}
        {activeTab === 'account' && (
          <div className="max-w-lg mx-auto studio-card p-5 space-y-4 animate-in fade-in duration-100">
            <div className="flex items-center gap-3 pb-3 border-b border-slate-100">
              <div className="w-10 h-10 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-sm">
                {(accountData?.username || 'U')[0].toUpperCase()}
              </div>
              <div>
                <h3 className="font-bold text-sm text-slate-900">{accountData?.username}</h3>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    accountData?.is_administrator ? 'bg-purple-50 text-purple-700 border border-purple-200' : 'bg-slate-100 text-slate-600'
                  }`}>
                    {accountData?.account_type}
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">Node: {accountData?.os_node}</span>
                </div>
              </div>
            </div>

            <div className="text-xs space-y-2 font-mono">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Home Directory:</span>
                <span className="text-slate-800 font-medium">{accountData?.home_directory}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Privilege Scope:</span>
                <span className="text-slate-800 font-medium">Local Read-Only Diagnostic</span>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
