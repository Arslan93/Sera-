import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { Search } from 'lucide-react';

export default function CommandPalette() {
  const { 
    isCmdOpen, 
    setIsCmdOpen, 
    setCurrentView, 
    fetchBrief, 
    resetSession, 
    toggleVoice, 
    toggleWake, 
    toggleClipboard,
    showToast,
    fetchStudy
  } = useApp();

  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);

  const COMMANDS = [
    { id: '1', title: 'Go to Console (Home)', category: 'Navigation', shortcut: '1', action: () => setCurrentView('console') },
    { id: '2', title: 'Go to Chat Hub', category: 'Navigation', shortcut: '2', action: () => setCurrentView('chat') },
    { id: '3', title: 'Go to Pipeline (CRM & Jobs)', category: 'Navigation', shortcut: '3', action: () => setCurrentView('pipeline') },
    { id: '4', title: 'Go to Study Lab', category: 'Navigation', shortcut: '4', action: () => setCurrentView('study') },
    { id: '5', title: 'Go to Dev & System Tools', category: 'Navigation', shortcut: '5', action: () => setCurrentView('dev') },
    { id: '6', title: 'Refresh Daily Orientation Brief', category: 'Actions', shortcut: 'R', action: () => fetchBrief() },
    { id: '7', title: 'Start New Chat Session', category: 'Actions', shortcut: 'N', action: () => resetSession() },
    { 
      id: '8', 
      title: 'Start Study: Operating Systems', 
      category: 'Study Lab', 
      action: async () => {
        setCurrentView('study');
        await fetch('/api/study/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ subject: 'Operating Systems', goal: 'Core revision' })
        });
        fetchStudy();
        showToast('Study session started for Operating Systems', 'success');
      } 
    },
    { 
      id: '9', 
      title: 'Start Study: Computer Networks', 
      category: 'Study Lab', 
      action: async () => {
        setCurrentView('study');
        await fetch('/api/study/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ subject: 'Computer Networks', goal: 'Protocols & OSI' })
        });
        fetchStudy();
        showToast('Study session started for Computer Networks', 'success');
      } 
    },
    { id: '10', title: 'Toggle Voice Response (TTS)', category: 'Toggles', shortcut: 'V', action: toggleVoice },
    { id: '11', title: 'Toggle Wake Word (Hey Sera)', category: 'Toggles', shortcut: 'W', action: toggleWake },
    { id: '12', title: 'Toggle Clipboard Capture (Ctrl+Shift+S)', category: 'Toggles', shortcut: 'C', action: toggleClipboard }
  ];

  const filtered = COMMANDS.filter(c => 
    c.title.toLowerCase().includes(query.toLowerCase()) || 
    c.category.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    if (isCmdOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isCmdOpen]);

  if (!isCmdOpen) return null;

  function handleKeyDown(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % (filtered.length || 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + filtered.length) % (filtered.length || 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        filtered[selectedIndex].action();
        setIsCmdOpen(false);
      }
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-slate-900/40 backdrop-blur-[2px] z-50 flex items-start justify-center pt-[14vh] px-4"
      onClick={(e) => { if (e.target === e.currentTarget) setIsCmdOpen(false); }}
    >
      <div className="w-full max-w-[540px] bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="p-3 border-b border-slate-200 flex items-center gap-2.5">
          <Search className="w-4 h-4 text-slate-400 flex-shrink-0" />
          <input 
            ref={inputRef}
            type="text" 
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
            onKeyDown={handleKeyDown}
            placeholder="Type a command, jump to a panel, or start a study block..." 
            className="w-full text-xs text-slate-900 placeholder-slate-400 focus:outline-none bg-transparent font-medium"
          />
          <kbd className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-400">ESC</kbd>
        </div>

        <div className="p-2 max-h-72 overflow-y-auto space-y-1">
          {filtered.length === 0 ? (
            <div className="text-xs text-slate-400 font-mono py-6 text-center">No commands matching "{query}"</div>
          ) : (
            filtered.map((cmd, idx) => (
              <div 
                key={cmd.id}
                onClick={() => { cmd.action(); setIsCmdOpen(false); }}
                className={`cmd-item ${idx === selectedIndex ? 'selected' : ''}`}
              >
                <div className="flex items-center gap-2.5">
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
                    {cmd.category}
                  </span>
                  <span className="font-medium text-xs text-slate-800">{cmd.title}</span>
                </div>
                {cmd.shortcut && (
                  <kbd className="font-mono text-[10.5px] px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-500">
                    {cmd.shortcut}
                  </kbd>
                )}
              </div>
            ))
          )}
        </div>

        <div className="p-2 border-t border-slate-100 bg-slate-50 text-[11px] text-slate-400 font-mono flex justify-between px-3">
          <span>Navigate with ↑ / ↓</span>
          <span>Press Enter to run</span>
        </div>
      </div>
    </div>
  );
}
