import React from 'react';
import { useApp } from '../context/AppContext';
import { LayoutDashboard, MessageSquare, Kanban, GraduationCap, Sliders } from 'lucide-react';

export default function NavRail() {
  const { currentView, setCurrentView, jobFollowups } = useApp();

  const hasUrgentFollowups = jobFollowups.some(f => f.is_overdue);

  return (
    <aside className="w-48 flex-shrink-0 bg-white border-r border-slate-200/80 flex flex-col justify-between p-2.5 shadow-sm">
      <nav className="space-y-1">
        <button 
          onClick={() => setCurrentView('console')}
          className={`nav-btn ${currentView === 'console' ? 'active' : ''}`}
        >
          <LayoutDashboard className="w-4 h-4" />
          <span>Console</span>
        </button>

        <button 
          onClick={() => setCurrentView('chat')}
          className={`nav-btn ${currentView === 'chat' ? 'active' : ''}`}
        >
          <MessageSquare className="w-4 h-4" />
          <span>Chat Hub</span>
        </button>

        <button 
          onClick={() => setCurrentView('pipeline')}
          className={`nav-btn relative ${currentView === 'pipeline' ? 'active' : ''}`}
        >
          <Kanban className="w-4 h-4" />
          <span>Pipeline</span>
          {hasUrgentFollowups && (
            <span className="w-2 h-2 rounded-full bg-amber-500 absolute right-3" title="Follow-up requires attention"></span>
          )}
        </button>

        <button 
          onClick={() => setCurrentView('study')}
          className={`nav-btn ${currentView === 'study' ? 'active' : ''}`}
        >
          <GraduationCap className="w-4 h-4" />
          <span>Study Lab</span>
        </button>

        <button 
          onClick={() => setCurrentView('dev')}
          className={`nav-btn ${currentView === 'dev' ? 'active' : ''}`}
        >
          <Sliders className="w-4 h-4" />
          <span>Dev & System</span>
        </button>
      </nav>

      {/* Bottom Profile / Hotkey Hint */}
      <div className="pt-2.5 border-t border-slate-100 px-2 text-[11px] text-slate-500 space-y-1 font-sans">
        <div className="flex items-center justify-between">
          <span className="font-medium text-slate-400">DEVELOPER</span>
          <span className="font-bold text-slate-800">Arslan</span>
        </div>
        <div className="text-[10.5px] text-slate-400 font-mono flex items-center justify-between">
          <span>Capture</span>
          <kbd className="px-1 rounded bg-slate-100 border border-slate-200">Ctrl+Shift+S</kbd>
        </div>
      </div>
    </aside>
  );
}
