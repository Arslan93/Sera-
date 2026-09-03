import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';

const AppContext = createContext(null);

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within AppProvider');
  return context;
}

export function AppProvider({ children }) {
  // Navigation
  const [currentView, setCurrentView] = useState('console');
  const [isCmdOpen, setIsCmdOpen] = useState(false);

  // Connection & AI State Machine
  const [wsConnected, setWsConnected] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState(null);
  const [aiState, setAiState] = useState('idle'); // 'idle' | 'listening' | 'thinking' | 'speaking'
  const [activeTool, setActiveTool] = useState(null);

  // Chat & Session
  const [sessionId, setSessionId] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const wsRef = useRef(null);

  // Toggles
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [wakeEnabled, setWakeEnabled] = useState(false);
  const [clipboardEnabled, setClipboardEnabled] = useState(false);

  // Telemetry & Sparkline Buffer
  const [systemInfo, setSystemInfo] = useState({
    cpu: { usage_percent: '0%' },
    ram: { percent_used: 0, used_gb: 0, total_gb: 0 },
    disk: { percent_used: 0, free_gb: 0 },
    battery: { percent: null, power_plugged: true }
  });
  const [cpuHistory, setCpuHistory] = useState([14, 18, 15, 20, 18, 16, 22, 19, 17, 21, 19, 18, 20, 17, 18]);
  const [ramHistory, setRamHistory] = useState([41, 41, 42, 42, 42, 43, 42, 42, 43, 42, 42, 43, 42, 42, 42]);

  // Toasts
  const [toasts, setToasts] = useState([]);

  // Data Stores
  const [dailyBrief, setDailyBrief] = useState('');
  const [isBriefLoading, setIsBriefLoading] = useState(false);
  const [studySession, setStudySession] = useState(null);
  const [studyStats, setStudyStats] = useState(null);
  const [leads, setLeads] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [jobStats, setJobStats] = useState(null);
  const [jobFollowups, setJobFollowups] = useState([]);
  const [skills, setSkills] = useState([]);
  const [captures, setCaptures] = useState([]);
  const [readLater, setReadLater] = useState([]);

  // Toast Dispatcher
  const showToast = useCallback((message, type = 'info', duration = 3500) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  // ═══════════ WEBSOCKET ENGINE ═══════════
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/chat`;

    let reconnectTimer;
    function connect() {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
        setLastSyncTime(new Date().toLocaleTimeString());
        setAiState('idle');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'state') {
            setAiState(data.state);
          } else if (data.type === 'tool_call') {
            setAiState('thinking');
            setActiveTool(data.tool);
          } else if (data.type === 'chunk') {
            setStreamingContent(prev => prev + data.content);
          } else if (data.type === 'done') {
            setIsGenerating(false);
            setAiState('idle');
            setActiveTool(null);
            setStreamingContent(prev => {
              if (prev) {
                setChatMessages(msgs => [...msgs, { role: 'assistant', content: prev }]);
              }
              return '';
            });
            if (data.session_id) setSessionId(data.session_id);
          } else if (data.type === 'error') {
            setIsGenerating(false);
            setAiState('idle');
            setActiveTool(null);
            showToast(`Error: ${data.error}`, 'error');
          }
        } catch (e) {
          console.warn('WS parse error:', e);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        reconnectTimer = setTimeout(connect, 3500);
      };

      ws.onerror = () => {
        setWsConnected(false);
      };
    }

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      if (wsRef.current) wsRef.current.close();
    };
  }, [showToast]);

  // Send Chat Message
  const sendMessage = useCallback(async (content) => {
    if (!content.trim() || isGenerating) return;

    const userMsg = { role: 'user', content: content.trim() };
    setChatMessages(prev => [...prev, userMsg]);
    setIsGenerating(true);
    setStreamingContent('');
    setAiState('thinking');

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        message: content.trim(),
        voice: voiceEnabled
      }));
    } else {
      // HTTP Fallback
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: content.trim(), voice: voiceEnabled })
        });
        const data = await res.json();
        setIsGenerating(false);
        setAiState('idle');
        if (data.status === 'success') {
          setChatMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
        } else {
          showToast(data.detail || 'Failed to send message', 'error');
        }
      } catch (e) {
        setIsGenerating(false);
        setAiState('idle');
        showToast(e.message, 'error');
      }
    }
  }, [isGenerating, voiceEnabled, showToast]);

  // Reset Session
  const resetSession = useCallback(async () => {
    try {
      const res = await fetch('/api/session/new', { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        setSessionId(data.session_id);
        setChatMessages([]);
        showToast('New session started', 'success');
      }
    } catch (e) {
      showToast('Error resetting session', 'error');
    }
  }, [showToast]);

  // ═══════════ TELEMETRY POLLING ═══════════
  const pollTelemetry = useCallback(async () => {
    try {
      const res = await fetch('/api/system-info');
      if (!res.ok) return;
      const data = await res.json();
      if (data.status !== 'success') return;

      setSystemInfo(data);
      setLastSyncTime(new Date().toLocaleTimeString());

      const cpu = Math.round(parseFloat(data.cpu?.usage_percent || '0'));
      const ram = Math.round(parseFloat(data.ram?.percent_used || '0'));

      setCpuHistory(prev => {
        const next = [...prev, cpu];
        return next.length > 15 ? next.slice(1) : next;
      });

      setRamHistory(prev => {
        const next = [...prev, ram];
        return next.length > 15 ? next.slice(1) : next;
      });
    } catch (e) {
      console.warn('Telemetry poll error:', e);
    }
  }, []);

  useEffect(() => {
    pollTelemetry();
    const interval = setInterval(pollTelemetry, 3500);
    return () => clearInterval(interval);
  }, [pollTelemetry]);

  // ═══════════ DATA LOADERS ═══════════
  const fetchBrief = useCallback(async () => {
    setIsBriefLoading(true);
    try {
      const res = await fetch('/api/daily-brief');
      const data = await res.json();
      if (data.status === 'success') {
        setDailyBrief(data.brief_text || '');
      }
    } catch (e) {
      console.warn('Daily brief error:', e);
    } finally {
      setIsBriefLoading(false);
    }
  }, []);

  const fetchStudy = useCallback(async () => {
    try {
      const [statusRes, statsRes] = await Promise.all([
        fetch('/api/study/status'),
        fetch('/api/study/stats')
      ]);
      const statusData = await statusRes.json();
      const statsData = await statsRes.json();
      setStudySession(statusData.active_session || null);
      setStudyStats(statsData);
    } catch (e) {
      console.warn('Study fetch error:', e);
    }
  }, []);

  const fetchLeads = useCallback(async () => {
    try {
      const res = await fetch('/api/leads');
      const data = await res.json();
      if (data.status === 'success') {
        // Deduplicate leads
        const seen = new Set();
        const unique = [];
        (data.leads || []).forEach(l => {
          const key = `${l.name.toLowerCase()}-${(l.company || '').toLowerCase()}`;
          if (!seen.has(key)) {
            seen.add(key);
            unique.push(l);
          }
        });
        setLeads(unique);
      }
    } catch (e) {
      console.warn('Leads fetch error:', e);
    }
  }, []);

  const fetchJobs = useCallback(async () => {
    try {
      const [jobsRes, statsRes, followupsRes] = await Promise.all([
        fetch('/api/jobs'),
        fetch('/api/jobs/stats'),
        fetch('/api/jobs/followups')
      ]);
      const jobsData = await jobsRes.json();
      const statsData = await statsRes.json();
      const followupsData = await followupsRes.json();
      setJobs(jobsData.applications || []);
      setJobStats(statsData);
      setJobFollowups(followupsData.followups || []);
    } catch (e) {
      console.warn('Jobs fetch error:', e);
    }
  }, []);

  const fetchSkills = useCallback(async () => {
    try {
      const res = await fetch('/api/skills');
      const data = await res.json();
      setSkills(data.skills || []);
    } catch (e) {
      console.warn('Skills fetch error:', e);
    }
  }, []);

  const fetchCaptures = useCallback(async () => {
    try {
      const [capRes, rlRes] = await Promise.all([
        fetch('/api/captures'),
        fetch('/api/read-later')
      ]);
      const capData = await capRes.json();
      const rlData = await rlRes.json();
      setCaptures(capData.captures || []);
      setReadLater(rlData.links || []);
    } catch (e) {
      console.warn('Captures fetch error:', e);
    }
  }, []);

  // Initial Boot
  useEffect(() => {
    fetchBrief();
    fetchStudy();
    fetchLeads();
    fetchJobs();
    fetchSkills();
    fetchCaptures();

    // Fetch voice & clipboard toggle states
    fetch('/api/clipboard/status')
      .then(r => r.json())
      .then(d => setClipboardEnabled(d.listening || false))
      .catch(() => {});
  }, [fetchBrief, fetchStudy, fetchLeads, fetchJobs, fetchSkills, fetchCaptures]);

  // Toggle Handlers
  const toggleVoice = useCallback(async () => {
    try {
      const res = await fetch('/api/voice/toggle', { method: 'POST' });
      const data = await res.json();
      setVoiceEnabled(data.voice_enabled);
      showToast(`Voice output ${data.voice_enabled ? 'enabled' : 'disabled'}`, 'info');
    } catch (e) {
      showToast('Error toggling voice: ' + e.message, 'error');
    }
  }, [showToast]);

  const toggleWake = useCallback(async () => {
    try {
      const res = await fetch('/api/wake/toggle', { method: 'POST' });
      const data = await res.json();
      setWakeEnabled(data.wake_enabled);
      showToast(`Wake word 'Hey Sera' ${data.wake_enabled ? 'armed' : 'disabled'}`, data.wake_enabled ? 'success' : 'info');
    } catch (e) {
      showToast('Error toggling wake word: ' + e.message, 'error');
    }
  }, [showToast]);

  const toggleClipboard = useCallback(async () => {
    try {
      const res = await fetch('/api/clipboard/toggle', { method: 'POST' });
      const data = await res.json();
      setClipboardEnabled(data.listening);
      showToast(data.listening ? 'Clipboard capture armed (Ctrl+Shift+S)' : 'Clipboard capture paused', data.listening ? 'success' : 'info');
    } catch (e) {
      showToast('Error toggling clipboard: ' + e.message, 'error');
    }
  }, [showToast]);

  // Global Keyboard Shortcuts
  useEffect(() => {
    function handleKeyDown(e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCmdOpen(prev => !prev);
      }
      if (e.key === 'Escape') {
        setIsCmdOpen(false);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const value = {
    currentView,
    setCurrentView,
    isCmdOpen,
    setIsCmdOpen,
    wsConnected,
    lastSyncTime,
    aiState,
    setAiState,
    activeTool,
    sessionId,
    chatMessages,
    isGenerating,
    streamingContent,
    sendMessage,
    resetSession,
    voiceEnabled,
    wakeEnabled,
    clipboardEnabled,
    toggleVoice,
    toggleWake,
    toggleClipboard,
    systemInfo,
    cpuHistory,
    ramHistory,
    toasts,
    showToast,
    removeToast,
    dailyBrief,
    isBriefLoading,
    fetchBrief,
    studySession,
    studyStats,
    fetchStudy,
    leads,
    fetchLeads,
    jobs,
    jobStats,
    jobFollowups,
    fetchJobs,
    skills,
    fetchSkills,
    captures,
    readLater,
    fetchCaptures
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
