import React, { useState, useRef } from 'react';
import { useApp } from '../context/AppContext';
import AiStateOrb from './AiStateOrb';
import SparklinePopover from './SparklinePopover';
import { Zap, Radio, Volume2, Clipboard, Plus, Search, X } from 'lucide-react';

export default function TopBar() {
  const { 
    wsConnected, 
    lastSyncTime, 
    systemInfo, 
    voiceEnabled, 
    wakeEnabled, 
    clipboardEnabled, 
    toggleVoice, 
    toggleWake, 
    toggleClipboard, 
    resetSession, 
    setIsCmdOpen,
    showToast
  } = useApp();

  const [popoverType, setPopoverType] = useState(null);
  const [popoverPos, setPopoverPos] = useState(null);
  const [showWsPopover, setShowWsPopover] = useState(false);

  const cpuPercent = parseFloat(systemInfo.cpu?.usage_percent || '0');
  const ramPercent = parseFloat(systemInfo.ram?.percent_used || '0');
  const batVal = systemInfo.battery?.percent;
  const isPlugged = systemInfo.battery?.power_plugged ?? true;

  function handleSparklineEnter(type, e) {
    const rect = e.currentTarget.getBoundingClientRect();
    setPopoverType(type);
    setPopoverPos({ left: rect.left, top: rect.bottom + 6 });
  }

  function handleSparklineLeave() {
    setPopoverType(null);
    setPopoverPos(null);
  }

  return (
    <header className="flex-shrink-0 bg-white border-b border-slate-200/80 px-4 py-2 flex items-center justify-between z-30 shadow-sm relative">
      <div className="flex items-center gap-3">
        {/* AI State Orb (Mini) Docked near Logo */}
        <div className="flex items-center gap-2">
          <AiStateOrb size="mini" />
          <span className="font-bold tracking-tight text-sm text-slate-900">SERA</span>
          <span className="px-1.5 py-0.2 rounded bg-slate-100 border border-slate-200 font-mono text-[10.5px] text-slate-600 font-medium">
            gpt-oss-120b
          </span>
        </div>

        <div className="h-3 w-px bg-slate-200 mx-1"></div>

        {/* Real-time Hardware Telemetry Chips with Sparklines */}
        <div className="hidden sm:flex items-center gap-2 font-mono text-[11px] text-slate-600">
          <div 
            onMouseEnter={(e) => handleSparklineEnter('cpu', e)}
            onMouseLeave={handleSparklineLeave}
            className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-50 border border-slate-200 cursor-help transition-colors hover:bg-slate-100"
            title="CPU load (hover for 60s sparkline)"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
            <span>{Math.round(cpuPercent)}% CPU</span>
          </div>

          <div 
            onMouseEnter={(e) => handleSparklineEnter('ram', e)}
            onMouseLeave={handleSparklineLeave}
            className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-50 border border-slate-200 cursor-help transition-colors hover:bg-slate-100"
            title="RAM load (hover for 60s sparkline)"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span>{Math.round(ramPercent)}% RAM</span>
          </div>

          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-50 border border-slate-200">
            <Zap className="w-3 h-3 text-amber-500" />
            <span>{batVal !== null && batVal !== undefined ? `${batVal}% BAT` : (isPlugged ? 'AC Power' : 'Battery')}</span>
          </div>
        </div>
      </div>

      {/* Sparkline Tooltip Popover */}
      <SparklinePopover 
        type={popoverType} 
        position={popoverPos} 
        onClose={() => setPopoverType(null)} 
      />

      {/* Right Controls & Quick Toggles */}
      <div className="flex items-center gap-2">
        {/* Command Palette Trigger */}
        <button 
          onClick={() => setIsCmdOpen(true)}
          className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-50 border border-slate-200 text-slate-500 text-xs hover:bg-slate-100 hover:text-slate-800 transition-colors"
          title="Open Command Palette (Ctrl+K)"
        >
          <Search className="w-3 h-3 text-slate-400" />
          <span>Command Menu</span>
          <kbd className="font-mono text-[10px] px-1 py-0.2 rounded bg-white border border-slate-200 text-slate-500">Ctrl+K</kbd>
        </button>

        {/* High-Contrast Connection Status Badge */}
        <div 
          onClick={() => setShowWsPopover(prev => !prev)}
          className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full border font-mono text-[11px] font-semibold cursor-pointer transition-colors ${
            wsConnected 
              ? 'bg-emerald-50 border-emerald-200 text-emerald-700 hover:bg-emerald-100' 
              : 'bg-amber-50 border-amber-200 text-amber-700 hover:bg-amber-100'
          }`}
          title="Click for connection diagnostics"
        >
          <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
          <span>{wsConnected ? 'LIVE' : 'OFFLINE'}</span>
        </div>

        {/* Connection Diagnostics Popover */}
        {showWsPopover && (
          <div className="absolute right-4 top-11 w-64 p-3 rounded-lg bg-white border border-slate-200 shadow-xl z-50 text-xs font-sans animate-in fade-in zoom-in-95 duration-100">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 mb-2">
              <span className="font-bold text-slate-900">SERA Daemon Link</span>
              <button onClick={() => setShowWsPopover(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="space-y-1.5 font-mono text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-500">Status:</span>
                <span className={wsConnected ? 'text-emerald-700 font-bold' : 'text-amber-700 font-bold'}>
                  {wsConnected ? 'Connected & Streaming' : 'Disconnected (Retrying...)'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Protocol:</span>
                <span className="text-slate-700">ws://127.0.0.1:8000</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Last Sync:</span>
                <span className="text-slate-700">{lastSyncTime || 'Pending first sync'}</span>
              </div>
            </div>
            <button 
              onClick={() => {
                showToast('Reconnecting WebSocket...', 'info');
                setShowWsPopover(false);
              }}
              className="btn-secondary w-full mt-2.5 py-1 text-[11px] text-center font-medium"
            >
              Force Reconnect
            </button>
          </div>
        )}

        {/* Mode Toggles */}
        <button 
          onClick={toggleWake}
          className={`text-xs py-1 px-2.5 flex items-center gap-1.5 ${wakeEnabled ? 'btn-primary shadow-sm' : 'btn-secondary'}`}
          title="Toggle hands-free 'Hey Sera' wake word listener"
        >
          <Radio className={`w-3.5 h-3.5 ${wakeEnabled ? 'agentic-live text-white' : 'text-blue-600'}`} />
          <span className="hidden lg:inline">Hey Sera {wakeEnabled ? 'ARMED' : 'OFF'}</span>
        </button>

        <button 
          onClick={toggleVoice}
          className={`text-xs py-1 px-2.5 flex items-center gap-1.5 ${voiceEnabled ? 'btn-primary' : 'btn-secondary'}`}
          title="Toggle spoken speech responses"
        >
          <Volume2 className="w-3.5 h-3.5" />
          <span className="hidden lg:inline">Voice {voiceEnabled ? 'ON' : 'OFF'}</span>
        </button>

        <button 
          onClick={toggleClipboard}
          className={`text-xs py-1 px-2.5 flex items-center gap-1.5 ${clipboardEnabled ? 'btn-primary' : 'btn-secondary'}`}
          title="Toggle Global Hotkey (Ctrl+Shift+S) Clipboard Capture"
        >
          <Clipboard className="w-3.5 h-3.5" />
          <span className="hidden lg:inline">Capture {clipboardEnabled ? 'ON' : 'OFF'}</span>
        </button>

        <button 
          onClick={resetSession}
          className="btn-primary text-xs py-1 px-2.5 flex items-center gap-1 font-semibold"
          title="Start a fresh chat conversation"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New</span>
        </button>
      </div>
    </header>
  );
}
