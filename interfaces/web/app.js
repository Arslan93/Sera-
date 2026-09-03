/**
 * SERA Studio Command Center — Frontend Application Logic (UX & Interaction Edition)
 * Zero frameworks. Pure, accessible, event-driven vanilla JavaScript.
 */

// Global State
const state = {
  currentView: 'console',
  session_id: null,
  ws: null,
  wsConnected: false,
  isGenerating: false,
  voiceEnabled: false,
  wakeEnabled: false,
  clipboardEnabled: false,
  activeStudySession: null,
  studyTimerInterval: null,
  studyStartTime: null,
  selectedSubjectChip: null,
  lastWsSyncTime: null,
  aiState: 'idle', // 'idle' | 'listening' | 'thinking' | 'speaking'
  activeTool: null,
  // Telemetry rolling buffer for sparklines
  cpuHistory: [12, 18, 15, 22, 19, 14, 25, 20, 18, 16, 21, 19, 24, 18, 17],
  ramHistory: [40, 41, 41, 42, 42, 43, 42, 41, 42, 43, 42, 42, 43, 42, 42]
};

const CIRCUMFERENCE_32 = 201.06; // 2 * PI * 32 for SVG dial arcs

// ═══════════ INITIALIZATION ═══════════
document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  initWebSocket();
  initNavigation();
  initKeyboardShortcuts();
  initCommandPalette();
  fetchInitialData();

  // Telemetry loop: poll hardware every 3.5 seconds
  pollSystemInfo();
  setInterval(pollSystemInfo, 3500);
});

// ═══════════ AI STATE ORB CONTROLLER ═══════════
function setAiState(aiState, toolLabel = null) {
  state.aiState = aiState;
  state.activeTool = toolLabel;

  // Update Mini Orb in Header
  const miniOrb = document.getElementById('ai-state-orb-mini');
  if (miniOrb) {
    miniOrb.className = `ai-orb ai-orb-mini state-${aiState}`;
  }

  // Update Hero Orb in Chat Hub
  const heroOrb = document.getElementById('ai-state-orb-hero');
  if (heroOrb) {
    heroOrb.className = `ai-orb ai-orb-hero state-${aiState}`;
  }

  // Update Status Label in Chat Hub
  const statusLabel = document.getElementById('ai-orb-label');
  if (statusLabel) {
    if (aiState === 'listening') {
      statusLabel.textContent = 'Listening for speech...';
      statusLabel.className = 'text-xs font-mono text-emerald-700 font-semibold';
    } else if (aiState === 'thinking') {
      statusLabel.textContent = toolLabel ? `Coordinating tool: ${formatToolName(toolLabel)}` : 'Thinking & analyzing...';
      statusLabel.className = 'text-xs font-mono text-purple-700 font-semibold';
    } else if (aiState === 'speaking') {
      statusLabel.textContent = 'Speaking response...';
      statusLabel.className = 'text-xs font-mono text-amber-700 font-semibold';
    } else {
      statusLabel.textContent = 'SERA is idle and ready';
      statusLabel.className = 'text-xs font-mono text-slate-500 font-medium';
    }
  }

  // Accessibility: Screen-reader announcement
  const ariaRegion = document.getElementById('ai-state-aria');
  if (ariaRegion) {
    ariaRegion.textContent = `SERA state: ${aiState} ${toolLabel ? '- calling ' + toolLabel : ''}`;
  }
}

function formatToolName(name) {
  if (!name) return 'tool';
  return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// ═══════════ TOAST NOTIFICATION SYSTEM ═══════════
function showToast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast-item toast-${type}`;
  toast.setAttribute('role', 'alert');

  let iconName = 'info';
  let iconColor = 'text-blue-600';
  if (type === 'success') { iconName = 'check-circle'; iconColor = 'text-emerald-600'; }
  else if (type === 'warning') { iconName = 'alert-triangle'; iconColor = 'text-amber-600'; }
  else if (type === 'error') { iconName = 'alert-circle'; iconColor = 'text-rose-600'; }

  toast.innerHTML = `
    <div class="flex items-center gap-2 min-w-0">
      <i data-lucide="${iconName}" class="w-4 h-4 ${iconColor} flex-shrink-0"></i>
      <span class="truncate">${escapeHtml(message)}</span>
    </div>
    <button onclick="this.parentElement.remove()" class="text-slate-400 hover:text-slate-600 p-0.5" title="Dismiss">
      <i data-lucide="x" class="w-3.5 h-3.5"></i>
    </button>
  `;

  container.appendChild(toast);
  lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    setTimeout(() => toast.remove(), 200);
  }, duration);
}

// ═══════════ NAVIGATION ═══════════
function initNavigation() {
  const navBtns = document.querySelectorAll('[data-view]');
  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const viewName = btn.getAttribute('data-view');
      switchView(viewName);
    });
  });
}

function switchView(viewName) {
  state.currentView = viewName;

  document.querySelectorAll('[data-view]').forEach(btn => {
    if (btn.getAttribute('data-view') === viewName) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  document.querySelectorAll('.view-panel').forEach(panel => {
    panel.classList.add('hidden');
  });

  const activePanel = document.getElementById(`view-${viewName}`);
  if (activePanel) {
    activePanel.classList.remove('hidden');
  }

  if (viewName === 'pipeline') {
    fetchLeads();
    fetchJobs();
  } else if (viewName === 'study') {
    fetchStudyData();
  } else if (viewName === 'dev') {
    fetchSkills();
    fetchCaptures();
  } else if (viewName === 'chat') {
    scrollChatToBottom();
    const input = document.getElementById('chat-input');
    if (input) setTimeout(() => input.focus(), 50);
  } else if (viewName === 'console') {
    fetchOverviewData();
  }

  lucide.createIcons();
}

// ═══════════ INITIAL DATA ═══════════
async function fetchInitialData() {
  await fetchDailyBrief();
  await fetchHistory();
  await fetchStudyData();
  await fetchOverviewData();
  await fetchVoiceAndClipboardStatus();
}

// ═══════════ HARDWARE TELEMETRY & 3D DIALS ═══════════
async function pollSystemInfo() {
  try {
    const res = await fetch('/api/system-info');
    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== 'success') return;

    state.lastWsSyncTime = new Date().toLocaleTimeString();

    const cpuPercent = parseFloat(data.cpu?.usage_percent || '0');
    const ramPercent = parseFloat(data.ram?.percent_used || '0');
    const diskPercent = parseFloat(data.disk?.percent_used || '0');

    const ramUsedGB = data.ram?.used_gb || 0;
    const ramTotalGB = data.ram?.total_gb || 0;
    const diskFreeGB = data.disk?.free_gb || 0;
    const batVal = data.battery?.percent || null;
    const isPlugged = data.battery?.power_plugged ?? true;

    // Push into rolling sparkline history (keep last 15 items)
    state.cpuHistory.push(Math.round(cpuPercent));
    if (state.cpuHistory.length > 15) state.cpuHistory.shift();

    state.ramHistory.push(Math.round(ramPercent));
    if (state.ramHistory.length > 15) state.ramHistory.shift();

    // 1. Top bar chips
    const elCpu = document.getElementById('hdr-cpu');
    const elRam = document.getElementById('hdr-ram');
    const elBat = document.getElementById('hdr-bat');

    if (elCpu) elCpu.textContent = `${cpuPercent}% CPU`;
    if (elRam) elRam.textContent = `${ramPercent}% RAM`;
    if (elBat) {
      elBat.textContent = batVal !== null ? `${batVal}% BAT` : (isPlugged ? 'AC Power' : 'Battery');
    }

    // 2. 3D Dial: CPU (with threshold states)
    const dialCpuVal = document.getElementById('dial-cpu-val');
    const dialCpuSvg = document.getElementById('dial-cpu-svg');
    const dialCpuHousing = document.getElementById('dial-cpu-housing');

    if (dialCpuVal) dialCpuVal.textContent = `${Math.round(cpuPercent)}%`;
    if (dialCpuSvg) {
      const offset = CIRCUMFERENCE_32 * (1 - Math.min(100, Math.max(0, cpuPercent)) / 100);
      dialCpuSvg.style.strokeDashoffset = offset;
    }
    if (dialCpuHousing) {
      if (cpuPercent >= 85) {
        dialCpuHousing.className = 'dial-housing dial-critical mb-1.5';
      } else if (cpuPercent >= 70) {
        dialCpuHousing.className = 'dial-housing dial-warning mb-1.5';
      } else {
        dialCpuHousing.className = 'dial-housing mb-1.5';
      }
    }

    // 3. 3D Dial: RAM (with threshold states)
    const dialRamVal = document.getElementById('dial-ram-val');
    const dialRamSub = document.getElementById('dial-ram-sub');
    const dialRamSvg = document.getElementById('dial-ram-svg');
    const dialRamHousing = document.getElementById('dial-ram-housing');

    if (dialRamVal) dialRamVal.textContent = `${Math.round(ramPercent)}%`;
    if (dialRamSub) dialRamSub.textContent = `${ramUsedGB}/${ramTotalGB} GB`;
    if (dialRamSvg) {
      const offset = CIRCUMFERENCE_32 * (1 - Math.min(100, Math.max(0, ramPercent)) / 100);
      dialRamSvg.style.strokeDashoffset = offset;
    }
    if (dialRamHousing) {
      if (ramPercent >= 85) {
        dialRamHousing.className = 'dial-housing dial-critical mb-1.5';
      } else if (ramPercent >= 75) {
        dialRamHousing.className = 'dial-housing dial-warning mb-1.5';
      } else {
        dialRamHousing.className = 'dial-housing mb-1.5';
      }
    }

    // 4. 3D Dial: Disk
    const dialDiskVal = document.getElementById('dial-disk-val');
    const dialDiskSub = document.getElementById('dial-disk-sub');
    const dialDiskSvg = document.getElementById('dial-disk-svg');

    if (dialDiskVal) dialDiskVal.textContent = `${Math.round(diskPercent)}%`;
    if (dialDiskSub) dialDiskSub.textContent = `${diskFreeGB} GB Free`;
    if (dialDiskSvg) {
      const offset = CIRCUMFERENCE_32 * (1 - Math.min(100, Math.max(0, diskPercent)) / 100);
      dialDiskSvg.style.strokeDashoffset = offset;
    }

  } catch (err) {
    console.warn('Telemetry poll error:', err);
  }
}

// Sparkline popover tooltip on hover
function showSparklinePopover(type, element) {
  let popover = document.getElementById('sparkline-popover');
  if (!popover) {
    popover = document.createElement('div');
    popover.id = 'sparkline-popover';
    popover.className = 'absolute z-50 p-2 rounded-lg bg-slate-900 text-white shadow-xl text-xs font-mono pointer-events-none';
    document.body.appendChild(popover);
  }

  const rect = element.getBoundingClientRect();
  popover.style.left = `${rect.left}px`;
  popover.style.top = `${rect.bottom + 6}px`;

  const history = type === 'cpu' ? state.cpuHistory : state.ramHistory;
  const label = type === 'cpu' ? 'CPU 60s Trend' : 'RAM 60s Trend';

  popover.innerHTML = `
    <div class="text-[10.5px] text-slate-400 mb-1 font-semibold">${label}</div>
    <div class="sparkline-container bg-slate-800">
      ${history.map(v => `<div class="sparkline-bar bg-blue-400" style="height: ${Math.max(4, Math.round(v * 0.28))}px;" title="${v}%"></div>`).join('')}
    </div>
    <div class="flex justify-between text-[9px] text-slate-400 mt-1">
      <span>60s ago</span>
      <span>Now: ${history[history.length - 1]}%</span>
    </div>
  `;
  popover.classList.remove('hidden');
}

function hideSparklinePopover() {
  const popover = document.getElementById('sparkline-popover');
  if (popover) popover.classList.add('hidden');
}

// ═══════════ WEBSOCKET CHAT ═══════════
function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

  state.ws = new WebSocket(wsUrl);

  state.ws.onopen = () => {
    state.wsConnected = true;
    state.lastWsSyncTime = new Date().toLocaleTimeString();
    updateWsStatusIndicator(true);
    setAiState('idle');
  };

  state.ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleWsMessage(data);
    } catch (e) {
      console.warn('WS parse error:', e);
    }
  };

  state.ws.onclose = () => {
    state.wsConnected = false;
    updateWsStatusIndicator(false);
    setTimeout(initWebSocket, 3500);
  };

  state.ws.onerror = (err) => {
    console.error('WS Error:', err);
  };
}

function updateWsStatusIndicator(connected) {
  const badge = document.getElementById('ws-status-badge');
  if (!badge) return;

  if (connected) {
    badge.className = 'flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 font-mono text-[11px] font-semibold cursor-pointer hover:bg-emerald-100 transition-colors';
    badge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500"></span><span>LIVE</span>`;
  } else {
    badge.className = 'flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-amber-700 font-mono text-[11px] font-semibold cursor-pointer hover:bg-amber-100 transition-colors';
    badge.innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-500"></span><span>OFFLINE</span>`;
  }
}

function toggleConnectionPopover() {
  const popover = document.getElementById('ws-popover');
  if (!popover) return;
  popover.classList.toggle('hidden');

  const statusText = document.getElementById('ws-popover-status');
  const syncText = document.getElementById('ws-popover-sync');
  if (statusText) {
    statusText.textContent = state.wsConnected ? 'Connected & streaming' : 'Disconnected (retrying...)';
    statusText.className = state.wsConnected ? 'text-emerald-700 font-bold' : 'text-amber-700 font-bold';
  }
  if (syncText) {
    syncText.textContent = state.lastWsSyncTime || 'Pending first sync';
  }
}

let currentStreamingAiBubble = null;
let currentStreamingText = '';

function handleWsMessage(data) {
  if (data.type === 'state') {
    setAiState(data.state);
  } else if (data.type === 'tool_call') {
    setAiState('thinking', data.tool);
    showToolIndicator(`Running tool: ${formatToolName(data.tool)}`);
  } else if (data.type === 'chunk') {
    if (!currentStreamingAiBubble) {
      createStreamingAiBubble();
    }
    currentStreamingText += data.content;
    renderAiContent(currentStreamingAiBubble, currentStreamingText);
    scrollChatToBottom();
  } else if (data.type === 'done') {
    state.isGenerating = false;
    setAiState('idle');
    hideToolIndicator();
    setSendButtonLoading(false);
    currentStreamingAiBubble = null;
    currentStreamingText = '';
    if (data.session_id) state.session_id = data.session_id;
    scrollChatToBottom();
  } else if (data.type === 'error') {
    state.isGenerating = false;
    setAiState('idle');
    hideToolIndicator();
    setSendButtonLoading(false);
    showToast(`Error: ${data.error}`, 'error');
    if (currentStreamingAiBubble) {
      currentStreamingAiBubble.innerHTML += `<div class="text-rose-600 text-xs mt-2 font-mono">Error: ${escapeHtml(data.error)}</div>`;
    }
  }
}

function createStreamingAiBubble() {
  const chatList = document.getElementById('chat-messages');
  if (!chatList) return;

  hideToolIndicator();

  const msgWrapper = document.createElement('div');
  msgWrapper.className = 'flex items-start gap-3';
  msgWrapper.innerHTML = `
    <div class="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-white text-xs font-mono font-bold flex-shrink-0 mt-0.5 shadow-sm">S</div>
    <div class="chat-bubble-ai prose-sera flex-1 overflow-x-auto text-[13.5px]">
      <span class="text-slate-400 font-mono text-xs">...</span>
    </div>
  `;
  chatList.appendChild(msgWrapper);
  currentStreamingAiBubble = msgWrapper.querySelector('.chat-bubble-ai');
  scrollChatToBottom();
}

function renderAiContent(container, markdownText) {
  if (!container) return;
  try {
    container.innerHTML = marked.parse(markdownText);
  } catch (e) {
    container.textContent = markdownText;
  }
}

function showToolIndicator(text = 'Running agentic tool...') {
  const ind = document.getElementById('agentic-tool-indicator');
  const txt = document.getElementById('agentic-tool-text');
  if (ind && txt) {
    txt.textContent = text;
    ind.classList.remove('hidden');
  }
}

function hideToolIndicator() {
  const ind = document.getElementById('agentic-tool-indicator');
  if (ind) ind.classList.add('hidden');
}

// Send Chat Message
async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  if (!input) return;
  const message = input.value.trim();
  if (!message || state.isGenerating) return;

  input.value = '';
  state.isGenerating = true;
  setSendButtonLoading(true);

  appendUserBubble(message);
  setAiState('thinking');
  showToolIndicator('SERA is coordinating tools...');
  scrollChatToBottom();

  if (state.wsConnected && state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify({
      message: message,
      voice: state.voiceEnabled
    }));
  } else {
    // HTTP Fallback
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message, voice: state.voiceEnabled })
      });
      const data = await res.json();
      hideToolIndicator();
      state.isGenerating = false;
      setSendButtonLoading(false);
      setAiState('idle');

      if (data.status === 'success') {
        createStreamingAiBubble();
        renderAiContent(currentStreamingAiBubble, data.response);
        currentStreamingAiBubble = null;
      } else {
        appendErrorBubble(data.detail || 'Failed to get response');
        showToast(data.detail || 'Error processing request', 'error');
      }
    } catch (e) {
      hideToolIndicator();
      state.isGenerating = false;
      setSendButtonLoading(false);
      setAiState('idle');
      appendErrorBubble(e.message);
      showToast(e.message, 'error');
    }
  }
}

function appendUserBubble(text) {
  const chatList = document.getElementById('chat-messages');
  if (!chatList) return;

  const msgWrapper = document.createElement('div');
  msgWrapper.className = 'flex justify-end';
  msgWrapper.innerHTML = `
    <div class="chat-bubble-user">
      ${escapeHtml(text)}
    </div>
  `;
  chatList.appendChild(msgWrapper);
}

function appendErrorBubble(text) {
  const chatList = document.getElementById('chat-messages');
  if (!chatList) return;

  const msgWrapper = document.createElement('div');
  msgWrapper.className = 'flex items-start gap-3';
  msgWrapper.innerHTML = `
    <div class="w-8 h-8 rounded-lg bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600 text-xs font-mono font-bold flex-shrink-0 mt-0.5">!</div>
    <div class="chat-bubble-ai border-rose-200 text-rose-700 text-xs font-mono">
      ${escapeHtml(text)}
    </div>
  `;
  chatList.appendChild(msgWrapper);
  scrollChatToBottom();
}

function setSendButtonLoading(loading) {
  const btn = document.getElementById('btn-send');
  if (btn) {
    btn.disabled = loading;
    btn.innerHTML = loading 
      ? `<span class="agentic-live text-xs font-mono">Processing...</span>`
      : `<i data-lucide="send" class="w-3.5 h-3.5"></i><span>Send</span>`;
    lucide.createIcons();
  }
}

function scrollChatToBottom() {
  const container = document.getElementById('chat-container');
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

async function fetchHistory() {
  try {
    const res = await fetch('/api/history');
    if (!res.ok) return;
    const data = await res.json();
    if (data.session_id) state.session_id = data.session_id;

    const chatList = document.getElementById('chat-messages');
    if (!chatList) return;
    chatList.innerHTML = '';

    if (data.messages && data.messages.length > 0) {
      data.messages.forEach(msg => {
        if (msg.role === 'user') {
          appendUserBubble(msg.content);
        } else if (msg.role === 'assistant') {
          createStreamingAiBubble();
          renderAiContent(currentStreamingAiBubble, msg.content);
          currentStreamingAiBubble = null;
        }
      });
      scrollChatToBottom();
    } else {
      appendAiWelcomeMessage();
    }
  } catch (e) {
    console.warn('Error fetching history:', e);
  }
}

async function startNewSession() {
  try {
    const res = await fetch('/api/session/new', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      state.session_id = data.session_id;
      const chatList = document.getElementById('chat-messages');
      if (chatList) chatList.innerHTML = '';
      appendAiWelcomeMessage();
      showToast('New session started', 'success');
    }
  } catch (e) {
    showToast('Failed to reset session', 'error');
  }
}

function appendAiWelcomeMessage() {
  const chatList = document.getElementById('chat-messages');
  if (!chatList) return;
  const msgWrapper = document.createElement('div');
  msgWrapper.className = 'flex items-start gap-3';
  msgWrapper.innerHTML = `
    <div class="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-white text-xs font-mono font-bold flex-shrink-0 mt-0.5 shadow-sm">S</div>
    <div class="chat-bubble-ai text-[13.5px] text-slate-700">
      <p class="font-semibold text-slate-900 mb-1">Session initialized.</p>
      Ready for coding assistance, study recall quizzes, CRM updates, or desktop tasks.
    </div>
  `;
  chatList.appendChild(msgWrapper);
}

// ═══════════ DAILY BRIEF (STRUCTURED SCANNING) ═══════════
async function fetchDailyBrief() {
  const card = document.getElementById('daily-brief-content');
  const btn = document.getElementById('btn-refresh-brief');
  if (!card) return;

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i><span>Updating...</span>`;
    lucide.createIcons();
  }

  try {
    const res = await fetch('/api/daily-brief');
    if (!res.ok) throw new Error('Network error');
    const data = await res.json();
    if (data.status === 'success') {
      // Structure the prose into scannable lines
      const text = data.brief_text || '';
      card.innerHTML = formatStructuredBrief(text);
      showToast('Daily brief refreshed', 'info');
    } else {
      card.innerHTML = `<span class="text-xs text-slate-500 font-mono">Daily brief not yet generated.</span>`;
    }
  } catch (e) {
    card.innerHTML = `<span class="text-xs text-slate-500 font-mono">Ready to compile daily orientation.</span>`;
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<i data-lucide="refresh-cw" class="w-3.5 h-3.5 text-slate-600"></i><span class="hidden sm:inline">Refresh</span>`;
      lucide.createIcons();
    }
  }
}

function formatStructuredBrief(text) {
  // Split into sentences and categorize
  const sentences = text.split(/(?<=[.!?])\s+/);
  const actionItems = [];
  const ambientItems = [];

  sentences.forEach(s => {
    if (/follow-up|deadline|overdue|client|lead|exam|quiz/i.test(s)) {
      actionItems.push(s);
    } else {
      ambientItems.push(s);
    }
  });

  return `
    <div class="space-y-2">
      ${actionItems.length > 0 ? `
        <div class="flex items-start gap-2 p-2 rounded-md bg-amber-50/80 border border-amber-200/80 text-amber-950 text-[12.5px]">
          <i data-lucide="alert-circle" class="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5"></i>
          <div><b class="font-bold">Action Needed:</b> ${escapeHtml(actionItems.join(' '))}</div>
        </div>
      ` : ''}
      <div class="text-slate-800 text-[13px] leading-relaxed">
        ${escapeHtml(ambientItems.join(' ') || text)}
      </div>
    </div>
  `;
}

// ═══════════ OVERVIEW / CONSOLE DASHBOARD ═══════════
async function fetchOverviewData() {
  // 1. Pending follow-ups
  try {
    const res = await fetch('/api/jobs/followups');
    const data = await res.json();
    const listEl = document.getElementById('ov-job-followups');
    if (listEl) {
      if (data.status === 'success' && data.followups && data.followups.length > 0) {
        listEl.innerHTML = data.followups.slice(0, 3).map(f => `
          <div class="flex items-center justify-between p-2.5 rounded-md bg-slate-50 border border-slate-200 text-xs">
            <div>
              <span class="font-semibold text-slate-900">${escapeHtml(f.company)}</span>
              <span class="text-slate-500 ml-1.5">${escapeHtml(f.role || '')}</span>
            </div>
            <span class="font-mono text-[11px] font-semibold ${f.is_overdue ? 'text-amber-700 bg-amber-100/60 px-1.5 py-0.5 rounded' : 'text-slate-600'}">${f.is_overdue ? 'OVERDUE' : (f.days_until_followup ? `in ${f.days_until_followup}d` : '14d+ idle')}</span>
          </div>
        `).join('');
      } else {
        // Empty state with secondary action
        listEl.innerHTML = `
          <div class="p-4 bg-slate-50 rounded-lg border border-slate-200 text-center">
            <p class="text-xs text-slate-600 mb-2">No pending job follow-ups due.</p>
            <button onclick="switchView('pipeline'); document.getElementById('job-form-modal').classList.remove('hidden');" class="btn-secondary text-[11px] py-1 px-2.5 inline-flex items-center gap-1 font-medium">
              <i data-lucide="plus" class="w-3 h-3 text-blue-600"></i>
              <span>Log a new application</span>
            </button>
          </div>
        `;
        lucide.createIcons();
      }
    }
  } catch (e) {
    console.warn('Overview jobs error:', e);
  }

  // 2. CRM Leads snapshot (Accordion + Inline Stage Change)
  try {
    const res = await fetch('/api/leads');
    const data = await res.json();
    const listEl = document.getElementById('ov-crm-deals');
    if (listEl) {
      if (data.status === 'success' && data.leads && data.leads.length > 0) {
        const seen = new Set();
        const uniqueLeads = [];
        data.leads.forEach(l => {
          const key = `${l.name.toLowerCase()}-${(l.company || '').toLowerCase()}`;
          if (!seen.has(key)) {
            seen.add(key);
            uniqueLeads.push(l);
          }
        });

        listEl.innerHTML = uniqueLeads.slice(0, 3).map((l, idx) => `
          <div class="studio-card p-2.5 text-xs">
            <div class="flex items-center justify-between cursor-pointer" onclick="toggleCrmAccordion('ov-crm-acc-${idx}')">
              <div class="flex items-center gap-1.5">
                <i data-lucide="chevron-right" id="ov-crm-acc-${idx}-icon" class="w-3.5 h-3.5 text-slate-400 transition-transform"></i>
                <span class="font-semibold text-slate-900">${escapeHtml(l.name)}</span>
                <span class="text-slate-500 font-normal">(${escapeHtml(l.company || 'Direct')})</span>
              </div>
              <div class="flex items-center gap-2" onclick="event.stopPropagation()">
                <span class="font-mono font-semibold text-emerald-700">${escapeHtml(l.deal_value || '')}</span>
                <select onchange="updateLeadStage('${escapeHtml(l.id || l.name)}', this.value)" class="bg-white text-slate-700 border border-slate-200 rounded px-1 py-0.5 text-[10px] font-mono">
                  ${CRM_STAGES.map(s => `<option value="${s}" ${s.toLowerCase() === (l.status || 'New').toLowerCase() ? 'selected' : ''}>${s}</option>`).join('')}
                </select>
              </div>
            </div>
            <div id="ov-crm-acc-${idx}" class="crm-accordion-body text-slate-600 text-[11px] border-t border-slate-100 mt-2">
              <div class="pt-1 space-y-1">
                ${l.notes ? `<div><b>Notes:</b> ${escapeHtml(l.notes)}</div>` : ''}
                ${l.email ? `<div><b>Email:</b> ${escapeHtml(l.email)}</div>` : ''}
                ${l.phone ? `<div><b>Phone:</b> ${escapeHtml(l.phone)}</div>` : ''}
              </div>
            </div>
          </div>
        `).join('');
        lucide.createIcons();
      } else {
        listEl.innerHTML = `<div class="text-xs text-slate-500 font-mono p-3 bg-slate-50 rounded border border-slate-200 text-center">No active business leads recorded.</div>`;
      }
    }
  } catch (e) {
    console.warn('Overview CRM error:', e);
  }
}

function toggleCrmAccordion(id) {
  const el = document.getElementById(id);
  const icon = document.getElementById(`${id}-icon`);
  if (!el) return;
  const isOpen = el.classList.toggle('open');
  if (icon) {
    icon.style.transform = isOpen ? 'rotate(90deg)' : 'rotate(0deg)';
  }
}

// ═══════════ CRM PIPELINE (KANBAN) ═══════════
const CRM_STAGES = ['New', 'Contacted', 'Proposal', 'Won', 'Lost'];

async function fetchLeads() {
  try {
    const res = await fetch('/api/leads');
    const data = await res.json();
    if (data.status !== 'success') return;

    const seen = new Set();
    const uniqueLeads = [];
    (data.leads || []).forEach(l => {
      const key = `${l.name.toLowerCase()}-${(l.company || '').toLowerCase()}`;
      if (!seen.has(key)) {
        seen.add(key);
        uniqueLeads.push(l);
      }
    });

    CRM_STAGES.forEach(stage => {
      const colEl = document.getElementById(`crm-col-${stage.toLowerCase()}`);
      const countEl = document.getElementById(`crm-count-${stage.toLowerCase()}`);
      if (!colEl) return;

      const stageLeads = uniqueLeads.filter(l => (l.status || 'New').toLowerCase() === stage.toLowerCase());
      if (countEl) countEl.textContent = stageLeads.length;

      if (stageLeads.length === 0) {
        colEl.innerHTML = `<div class="text-[11px] text-slate-400 font-mono text-center py-5 border border-dashed border-slate-200 rounded-md bg-slate-50/50">No leads</div>`;
      } else {
        colEl.innerHTML = stageLeads.map((lead, idx) => `
          <div class="studio-card p-3 mb-2.5 text-xs">
            <div class="flex items-start justify-between mb-1">
              <span class="font-semibold text-slate-900">${escapeHtml(lead.name)}</span>
              <span class="font-mono text-emerald-700 font-semibold text-[11px]">${escapeHtml(lead.deal_value || '$0')}</span>
            </div>
            <div class="text-slate-500 text-[11px] mb-1.5">${escapeHtml(lead.company || 'Direct')}</div>
            ${lead.notes ? `<div class="text-slate-600 text-[11px] bg-slate-50 border border-slate-200 p-2 rounded mb-2 font-mono truncate">${escapeHtml(lead.notes)}</div>` : ''}
            <div class="flex items-center justify-between border-t border-slate-100 pt-2 mt-1">
              <select onchange="updateLeadStage('${escapeHtml(lead.id || lead.name)}', this.value)" class="bg-white text-slate-700 border border-slate-200 rounded px-1.5 py-0.5 text-[11px] font-mono">
                ${CRM_STAGES.map(s => `<option value="${s}" ${s.toLowerCase() === stage.toLowerCase() ? 'selected' : ''}>Move: ${s}</option>`).join('')}
              </select>
              <span class="text-[10px] text-slate-400 font-mono">${(lead.phone || lead.email || '').slice(0, 14)}</span>
            </div>
          </div>
        `).join('');
      }
    });
  } catch (e) {
    console.error('Failed to load leads:', e);
  }
}

async function updateLeadStage(leadId, newStage) {
  try {
    const res = await fetch('/api/leads/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lead_identifier: leadId, status: newStage })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`Lead stage updated to ${newStage}`, 'success');
      fetchLeads();
      fetchOverviewData();
    }
  } catch (e) {
    showToast('Failed to update stage: ' + e.message, 'error');
  }
}

async function handleCreateLeadSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    name: form.name.value.trim(),
    company: form.company.value.trim(),
    deal_value: form.deal_value.value.trim(),
    phone: form.phone.value.trim(),
    email: form.email.value.trim(),
    notes: form.notes.value.trim()
  };

  try {
    const res = await fetch('/api/leads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`Lead created for ${payload.name}`, 'success');
      form.reset();
      document.getElementById('lead-form-modal').classList.add('hidden');
      fetchLeads();
      fetchOverviewData();
    }
  } catch (e) {
    showToast('Error creating lead: ' + e.message, 'error');
  }
}

// ═══════════ JOB APPLICATION TRACKER ═══════════
const JOB_STAGES = ['applied', 'oa_test', 'interview', 'offer', 'rejected'];

async function fetchJobs() {
  try {
    const [jobsRes, statsRes, followupsRes] = await Promise.all([
      fetch('/api/jobs'),
      fetch('/api/jobs/stats'),
      fetch('/api/jobs/followups')
    ]);

    const jobsData = await jobsRes.json();
    const statsData = await statsRes.json();
    const followupsData = await followupsRes.json();

    // Funnel count banner
    const statsBanner = document.getElementById('job-stats-banner');
    if (statsBanner && statsData.status === 'success') {
      const counts = statsData.stage_counts || {};
      statsBanner.innerHTML = `
        <div class="flex items-center gap-4 text-xs font-mono text-slate-600">
          <span>Total: <b class="text-slate-900">${statsData.total_applications || 0}</b></span>
          <span>Applied: <b class="text-blue-600">${counts.applied || 0}</b></span>
          <span>OA: <b class="text-cyan-600">${counts.oa_test || 0}</b></span>
          <span>Interview: <b class="text-amber-600">${counts.interview || 0}</b></span>
          <span>Offers: <b class="text-emerald-600">${counts.offer || 0}</b></span>
          <span>Rejected: <b class="text-rose-600">${counts.rejected || 0}</b></span>
        </div>
      `;
    }

    // Follow-ups banner
    const followupsEl = document.getElementById('job-urgent-followups');
    if (followupsEl && followupsData.status === 'success') {
      const items = followupsData.followups || [];
      if (items.length > 0) {
        followupsEl.classList.remove('hidden');
        followupsEl.innerHTML = `
          <div class="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs shadow-sm">
            <div class="font-semibold text-amber-900 flex items-center gap-1.5 mb-1.5">
              <i data-lucide="clock" class="w-3.5 h-3.5 text-amber-600"></i>
              <span>${items.length} Follow-ups Require Action:</span>
            </div>
            <div class="space-y-1.5">
              ${items.map(it => `
                <div class="flex items-center justify-between text-[11.5px]">
                  <span class="text-slate-800 font-medium"><b>${escapeHtml(it.company)}</b> — ${escapeHtml(it.role || '')}</span>
                  <span class="font-mono text-[11px] font-semibold ${it.is_overdue ? 'text-amber-800 bg-amber-200/60 px-1.5 py-0.5 rounded' : 'text-slate-600'}">${it.is_overdue ? 'OVERDUE' : `${it.days_until_followup}d left`}</span>
                </div>
              `).join('')}
            </div>
          </div>
        `;
        lucide.createIcons();
      } else {
        followupsEl.classList.add('hidden');
      }
    }

    // Populate Job stage columns
    const apps = jobsData.applications || [];
    JOB_STAGES.forEach(stage => {
      const colEl = document.getElementById(`job-col-${stage}`);
      const countEl = document.getElementById(`job-count-${stage}`);
      if (!colEl) return;

      const stageApps = apps.filter(a => (a.stage || 'applied').toLowerCase() === stage.toLowerCase());
      if (countEl) countEl.textContent = stageApps.length;

      if (stageApps.length === 0) {
        colEl.innerHTML = `<div class="text-[11px] text-slate-400 font-mono text-center py-5 border border-dashed border-slate-200 rounded-md bg-slate-50/50">Empty</div>`;
      } else {
        colEl.innerHTML = stageApps.map(app => `
          <div class="studio-card p-3 mb-2.5 text-xs">
            <div class="flex items-start justify-between mb-1">
              <span class="font-semibold text-slate-900">${escapeHtml(app.company)}</span>
              <span class="text-[10px] text-slate-500 font-mono px-1 rounded bg-slate-100">${escapeHtml(app.platform || 'Direct')}</span>
            </div>
            <div class="text-slate-600 text-[11px] mb-2 font-medium">${escapeHtml(app.role || '')}</div>
            ${app.notes ? `<div class="text-slate-500 text-[10.5px] bg-slate-50 border border-slate-200 p-2 rounded mb-2 font-mono truncate" title="${escapeHtml(app.notes)}">${escapeHtml(app.notes)}</div>` : ''}
            <div class="flex items-center justify-between border-t border-slate-100 pt-2 mt-1">
              <select onchange="updateJobStage('${escapeHtml(app.company)}', this.value)" class="bg-white text-slate-700 border border-slate-200 rounded px-1.5 py-0.5 text-[11px] font-mono">
                ${JOB_STAGES.map(s => `<option value="${s}" ${s === stage ? 'selected' : ''}>${s}</option>`).join('')}
              </select>
              <span class="text-[10px] text-slate-400 font-mono">${(app.applied_date || '').slice(5)}</span>
            </div>
          </div>
        `).join('');
      }
    });

  } catch (e) {
    console.error('Failed to load jobs:', e);
  }
}

async function updateJobStage(company, newStage) {
  try {
    const res = await fetch('/api/jobs/stage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company: company, stage: newStage })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`${company} moved to ${newStage}`, 'success');
      fetchJobs();
      fetchOverviewData();
    }
  } catch (e) {
    showToast('Failed to update stage: ' + e.message, 'error');
  }
}

async function handleLogJobSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    company: form.company.value.trim(),
    role: form.role.value.trim(),
    platform: form.platform.value.trim(),
    notes: form.notes.value.trim()
  };

  try {
    const res = await fetch('/api/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`Application saved for ${payload.company}`, 'success');
      form.reset();
      document.getElementById('job-form-modal').classList.add('hidden');
      fetchJobs();
      fetchOverviewData();
    }
  } catch (e) {
    showToast('Error saving job: ' + e.message, 'error');
  }
}

// ═══════════ STUDY SESSION (IN-PLACE TRANSITION) ═══════════
async function fetchStudyData() {
  try {
    const [statusRes, statsRes] = await Promise.all([
      fetch('/api/study/status'),
      fetch('/api/study/stats')
    ]);

    const statusData = await statusRes.json();
    const statsData = await statsRes.json();

    state.activeStudySession = statusData.active_session;

    renderActiveStudySession();
    renderStudyStats(statsData);
  } catch (e) {
    console.warn('Study data fetch error:', e);
  }
}

function selectStudyChip(subject, btnElement) {
  state.selectedSubjectChip = subject;
  document.querySelectorAll('.study-subject-chip').forEach(b => {
    b.className = 'study-subject-chip btn-secondary text-[11px] py-1 px-2.5 font-medium';
  });
  btnElement.className = 'study-subject-chip btn-primary text-[11px] py-1 px-2.5 font-medium';

  const subInput = document.getElementById('study-custom-subject');
  if (subInput) {
    subInput.value = subject;
  }
}

function renderActiveStudySession() {
  // Update both the Console preview card and the Study Lab view
  const containers = [
    document.getElementById('study-session-card'),
    document.getElementById('study-session-card-lab')
  ];

  containers.forEach(container => {
    if (!container) return;

    if (state.activeStudySession) {
      const sess = state.activeStudySession;
      state.studyStartTime = new Date(sess.started_at || sess.start_time || Date.now()).getTime();

      container.innerHTML = `
        <div class="p-4 rounded-lg border border-emerald-200 bg-emerald-50/50 shadow-sm animate-pulse-subtle">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 agentic-live"></span>
              <span class="text-xs font-mono text-emerald-800 font-bold tracking-wider uppercase">ACTIVE STUDY BLOCK</span>
            </div>
            <span class="study-live-clock font-mono text-xl font-bold text-slate-900 tracking-tight">00:00:00</span>
          </div>
          <div class="text-sm font-bold text-slate-900 mb-0.5">${escapeHtml(sess.subject)}</div>
          <div class="text-xs text-slate-600 mb-3 font-medium">${escapeHtml(sess.goal || 'Focus study block')}</div>
          <div class="flex items-center gap-2">
            <input type="text" class="study-end-notes-input studio-well text-xs px-3 py-1.5 flex-1 text-slate-800 bg-white" placeholder="Notes / topics covered...">
            <button onclick="endStudySession()" class="btn-primary bg-rose-600 hover:bg-rose-700 text-xs px-3 py-1.5 flex items-center gap-1.5 font-semibold">
              <i data-lucide="square" class="w-3.5 h-3.5"></i>
              <span>End Session</span>
            </button>
          </div>
        </div>
      `;

      if (state.studyTimerInterval) clearInterval(state.studyTimerInterval);
      updateStudyClock();
      state.studyTimerInterval = setInterval(updateStudyClock, 1000);

    } else {
      if (state.studyTimerInterval) clearInterval(state.studyTimerInterval);
      container.innerHTML = `
        <div class="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50">
          <div class="text-xs text-slate-600 mb-2 font-medium">Select Subject:</div>
          <div class="flex flex-wrap gap-1.5 mb-3">
            <button type="button" onclick="selectStudyChip('Operating Systems', this)" class="study-subject-chip btn-secondary text-[11px] py-1 px-2.5 font-medium">Operating Systems</button>
            <button type="button" onclick="selectStudyChip('Computer Networks', this)" class="study-subject-chip btn-secondary text-[11px] py-1 px-2.5 font-medium">Computer Networks</button>
            <button type="button" onclick="selectStudyChip('DBMS & SQL', this)" class="study-subject-chip btn-secondary text-[11px] py-1 px-2.5 font-medium">DBMS & SQL</button>
            <button type="button" onclick="selectStudyChip('Theory of Computation', this)" class="study-subject-chip btn-secondary text-[11px] py-1 px-2.5 font-medium">TOC</button>
            <button type="button" onclick="selectStudyChip('Deep Learning', this)" class="study-subject-chip btn-secondary text-[11px] py-1 px-2.5 font-medium">Deep Learning</button>
          </div>
          <form onsubmit="handleStartStudyForm(event)" class="flex gap-2">
            <input type="text" id="study-custom-subject" name="subject" placeholder="Topic..." required class="studio-well text-xs px-3 py-1.5 flex-1 bg-white text-slate-800 font-medium">
            <input type="text" name="goal" placeholder="Goal (e.g. 5 problems)" class="studio-well text-xs px-3 py-1.5 flex-1 bg-white text-slate-800">
            <button type="submit" class="btn-primary text-xs px-3.5 py-1.5 flex items-center gap-1 font-semibold">
              <i data-lucide="play" class="w-3 h-3"></i>
              <span>Start</span>
            </button>
          </form>
        </div>
      `;
    }
  });

  lucide.createIcons();
}

function updateStudyClock() {
  const clocks = document.querySelectorAll('.study-live-clock');
  if (!clocks.length || !state.studyStartTime) return;
  const elapsedSec = Math.max(0, Math.floor((Date.now() - state.studyStartTime) / 1000));
  const h = String(Math.floor(elapsedSec / 3600)).padStart(2, '0');
  const m = String(Math.floor((elapsedSec % 3600) / 60)).padStart(2, '0');
  const s = String(elapsedSec % 60).padStart(2, '0');
  clocks.forEach(c => c.textContent = `${h}:${m}:${s}`);
}

async function handleStartStudyForm(event) {
  event.preventDefault();
  const form = event.target;
  const subject = form.subject.value.trim();
  const goal = form.goal.value.trim();

  try {
    const res = await fetch('/api/study/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject: subject, goal: goal })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`Study block started for ${subject}`, 'success');
      fetchStudyData();
    } else {
      showToast(data.message || 'Failed to start session', 'warning');
    }
  } catch (e) {
    showToast('Failed to start study: ' + e.message, 'error');
  }
}

async function endStudySession() {
  const notesInputs = document.querySelectorAll('.study-end-notes-input');
  let notes = '';
  notesInputs.forEach(inp => { if (inp.value) notes = inp.value.trim(); });

  try {
    const res = await fetch('/api/study/end', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes: notes })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast('Study session completed and logged', 'success');
      fetchStudyData();
    }
  } catch (e) {
    showToast('Failed to end study: ' + e.message, 'error');
  }
}

function renderStudyStats(statsData) {
  const el = document.getElementById('study-stats-breakdown');
  if (!el || statsData.status !== 'success') return;

  const subjectTotals = statsData.subject_totals_minutes || {};
  const totalMin = statsData.total_study_minutes || 0;
  const sessionsCount = statsData.total_sessions || 0;

  const entries = Object.entries(subjectTotals);
  if (entries.length === 0) {
    el.innerHTML = `<div class="text-xs text-slate-500 font-mono py-2">No study sessions recorded in the last 7 days.</div>`;
    return;
  }

  el.innerHTML = `
    <div class="mb-3 flex items-center justify-between text-xs font-mono text-slate-600">
      <span>Total Revision: <b class="text-emerald-700 font-bold">${(totalMin / 60).toFixed(1)} hrs</b> (${totalMin} min)</span>
      <span>${sessionsCount} Sessions</span>
    </div>
    <div class="space-y-2.5">
      ${entries.map(([subj, mins]) => {
        const pct = totalMin > 0 ? Math.round((mins / totalMin) * 100) : 0;
        return `
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-slate-800 font-semibold">${escapeHtml(subj)}</span>
              <span class="font-mono text-slate-500 text-[11px]">${mins} min (${pct}%)</span>
            </div>
            <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
              <div class="bg-emerald-500 h-2 rounded-full transition-all duration-500" style="width: ${pct}%;"></div>
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

// ═══════════ CODE SCAFFOLDER ═══════════
async function handleScaffoldSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const logEl = document.getElementById('scaffold-log');

  const payload = {
    project_type: form.project_type.value,
    destination_folder: form.destination_folder.value.trim(),
    name: form.name.value.trim()
  };

  if (logEl) {
    logEl.innerHTML = `<span class="text-blue-600 font-mono text-xs">Scaffolding ${payload.project_type} into ${payload.destination_folder}...</span>`;
  }

  try {
    const res = await fetch('/api/scaffold', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (logEl) {
      if (data.status === 'success') {
        logEl.innerHTML = `<span class="text-emerald-600 font-mono text-xs font-medium">✓ Successfully scaffolded '${payload.name}' at ${escapeHtml(data.path || payload.destination_folder)}</span>`;
        showToast(`Generated template ${payload.name}`, 'success');
      } else {
        logEl.innerHTML = `<span class="text-rose-600 font-mono text-xs font-medium">✗ Error: ${escapeHtml(data.message || 'Failed')}</span>`;
        showToast('Scaffolding failed', 'error');
      }
    }
  } catch (e) {
    if (logEl) logEl.innerHTML = `<span class="text-rose-600 font-mono text-xs font-medium">✗ ${e.message}</span>`;
    showToast(e.message, 'error');
  }
}

// ═══════════ SKILLS MANAGER ═══════════
async function fetchSkills() {
  const listEl = document.getElementById('skills-list');
  if (!listEl) return;

  try {
    const res = await fetch('/api/skills');
    const data = await res.json();
    const skills = data.skills || [];

    listEl.innerHTML = skills.map(s => `
      <div class="studio-card p-3 flex items-center justify-between">
        <div>
          <div class="flex items-center gap-2 mb-0.5">
            <span class="font-semibold text-slate-900 text-xs">${escapeHtml(s.name)}</span>
            <span class="px-1.5 py-0.2 rounded bg-slate-100 text-[10px] font-mono text-slate-600 font-medium">${(s.tools || []).length} tools</span>
          </div>
          <p class="text-[11.5px] text-slate-500">${escapeHtml(s.description || '')}</p>
        </div>
        <button onclick="toggleSkill('${escapeHtml(s.name)}', ${!s.enabled})" class="${s.enabled ? 'btn-primary' : 'btn-secondary'} text-[11px] px-3 py-1 font-medium">
          ${s.enabled ? 'Enabled' : 'Disabled'}
        </button>
      </div>
    `).join('');
  } catch (e) {
    console.warn('Skills load error:', e);
  }
}

async function toggleSkill(skillName, enable) {
  try {
    const res = await fetch('/api/skills/toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skill_name: skillName, enable: enable })
    });
    if (res.ok) {
      showToast(`${skillName} ${enable ? 'enabled' : 'disabled'}`, 'info');
      fetchSkills();
    }
  } catch (e) {
    showToast('Error toggling skill: ' + e.message, 'error');
  }
}

// ═══════════ CLIPBOARD & READ-LATER AUDIT ═══════════
async function fetchCaptures() {
  try {
    const [capturesRes, readLaterRes] = await Promise.all([
      fetch('/api/captures'),
      fetch('/api/read-later')
    ]);

    const capturesData = await capturesRes.json();
    const readLaterData = await readLaterRes.json();

    const capEl = document.getElementById('captures-log');
    if (capEl) {
      const items = (capturesData.captures || []).slice(-8).reverse();
      if (items.length === 0) {
        capEl.innerHTML = `<div class="text-xs text-slate-500 font-mono py-3 text-center">No clipboard captures logged yet (Press Ctrl+Shift+S).</div>`;
      } else {
        capEl.innerHTML = items.map(c => `
          <div class="p-2.5 rounded-md bg-white border border-slate-200 text-xs shadow-sm">
            <div class="flex items-center justify-between mb-1">
              <span class="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase font-bold ${getBadgeClass(c.classification)}">${c.classification}</span>
              <span class="text-[10px] text-slate-400 font-mono">${(c.captured_at || '').slice(11, 19)}</span>
            </div>
            <div class="font-mono text-[11.5px] text-slate-800 truncate mb-1">${escapeHtml(c.raw_content)}</div>
            <div class="text-[10px] text-slate-500 font-mono">Filed to: ${escapeHtml(c.filed_to)}</div>
          </div>
        `).join('');
      }
    }

    const rlEl = document.getElementById('read-later-list');
    if (rlEl) {
      const links = (readLaterData.links || []).slice(-8).reverse();
      if (links.length === 0) {
        rlEl.innerHTML = `<div class="text-xs text-slate-500 font-mono py-3 text-center">Read later list is currently empty.</div>`;
      } else {
        rlEl.innerHTML = links.map(l => `
          <div class="flex items-center justify-between p-2.5 rounded-md bg-white border border-slate-200 text-xs shadow-sm">
            <a href="${escapeHtml(l.url)}" target="_blank" class="text-blue-600 hover:underline font-mono text-[11.5px] font-medium truncate flex-1 mr-2">${escapeHtml(l.title || l.url)}</a>
            <span class="text-[10px] text-slate-400 font-mono">${(l.added_at || '').slice(0, 10)}</span>
          </div>
        `).join('');
      }
    }
  } catch (e) {
    console.warn('Captures fetch error:', e);
  }
}

function getBadgeClass(cls) {
  switch (cls) {
    case 'code': return 'bg-blue-50 text-blue-700 border border-blue-200';
    case 'link': return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
    case 'task': return 'bg-amber-50 text-amber-700 border border-amber-200';
    default: return 'bg-slate-100 text-slate-700 border border-slate-200';
  }
}

// ═══════════ VOICE & CLIPBOARD TOGGLES ═══════════
async function fetchVoiceAndClipboardStatus() {
  try {
    const clipRes = await fetch('/api/clipboard/status');
    const clipData = await clipRes.json();
    state.clipboardEnabled = clipData.listening;
    updateClipboardToggleUI();
  } catch (e) {
    console.warn('Clipboard status error:', e);
  }
}

async function toggleVoiceTTS() {
  try {
    const res = await fetch('/api/voice/toggle', { method: 'POST' });
    const data = await res.json();
    state.voiceEnabled = data.voice_enabled;
    const btn = document.getElementById('btn-voice-toggle');
    if (btn) {
      btn.className = state.voiceEnabled 
        ? 'btn-primary text-xs py-1 px-2.5 flex items-center gap-1.5' 
        : 'btn-secondary text-xs py-1 px-2.5 flex items-center gap-1.5';
      btn.innerHTML = `<i data-lucide="volume-2" class="w-3.5 h-3.5"></i><span>Voice ${state.voiceEnabled ? 'ON' : 'OFF'}</span>`;
      lucide.createIcons();
    }
    showToast(`Voice output ${state.voiceEnabled ? 'enabled' : 'disabled'}`, 'info');
  } catch (e) {
    showToast('Voice toggle error: ' + e.message, 'error');
  }
}

async function toggleWakeWord() {
  try {
    const res = await fetch('/api/wake/toggle', { method: 'POST' });
    const data = await res.json();
    state.wakeEnabled = data.wake_enabled;
    const btn = document.getElementById('btn-wake-toggle');
    if (btn) {
      btn.className = state.wakeEnabled 
        ? 'btn-primary text-xs py-1 px-2.5 flex items-center gap-1.5 shadow-sm' 
        : 'btn-secondary text-xs py-1 px-2.5 flex items-center gap-1.5';
      btn.innerHTML = `<i data-lucide="radio" class="w-3.5 h-3.5 ${state.wakeEnabled ? 'agentic-live' : ''}"></i><span>Hey Sera ${state.wakeEnabled ? 'ARMED' : 'OFF'}</span>`;
      lucide.createIcons();
    }
    showToast(`Wake word 'Hey Sera' ${state.wakeEnabled ? 'armed & listening' : 'disabled'}`, state.wakeEnabled ? 'success' : 'info');
  } catch (e) {
    showToast('Wake toggle error: ' + e.message, 'error');
  }
}

async function toggleClipboardHotkey() {
  try {
    const res = await fetch('/api/clipboard/toggle', { method: 'POST' });
    const data = await res.json();
    state.clipboardEnabled = data.listening;
    updateClipboardToggleUI();
    if (state.clipboardEnabled) {
      showToast('Clipboard capture enabled — Ctrl+Shift+S to save', 'success');
    } else {
      showToast('Clipboard capture disabled', 'info');
    }
  } catch (e) {
    showToast('Clipboard toggle error: ' + e.message, 'error');
  }
}

function updateClipboardToggleUI() {
  const btn = document.getElementById('btn-clipboard-toggle');
  if (btn) {
    btn.className = state.clipboardEnabled 
      ? 'btn-primary text-xs py-1 px-2.5 flex items-center gap-1.5' 
      : 'btn-secondary text-xs py-1 px-2.5 flex items-center gap-1.5';
    btn.innerHTML = `<i data-lucide="clipboard" class="w-3.5 h-3.5"></i><span>Capture ${state.clipboardEnabled ? 'ON' : 'OFF'}</span>`;
    lucide.createIcons();
  }
}

async function recordMicInput() {
  const micBtn = document.getElementById('btn-mic-input');
  setAiState('listening');

  if (micBtn) {
    micBtn.disabled = true;
    micBtn.innerHTML = `<span class="agentic-live text-xs font-mono text-rose-600 font-bold">● LISTENING</span>`;
  }

  try {
    const res = await fetch('/api/voice/listen', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success' && data.transcription) {
      const input = document.getElementById('chat-input');
      if (input) {
        input.value = data.transcription;
        sendChatMessage();
      }
    } else {
      setAiState('idle');
    }
  } catch (e) {
    setAiState('idle');
    showToast('Microphone capture error: ' + e.message, 'error');
  } finally {
    if (micBtn) {
      micBtn.disabled = false;
      micBtn.innerHTML = `<i data-lucide="mic" class="w-3.5 h-3.5"></i>`;
      lucide.createIcons();
    }
  }
}

// ═══════════ COMMAND PALETTE (CTRL+K) ═══════════
const COMMANDS = [
  { id: 'view-console', title: 'Go to Console (Home)', category: 'Navigation', shortcut: '1', action: () => switchView('console') },
  { id: 'view-chat', title: 'Go to Chat Hub', category: 'Navigation', shortcut: '2', action: () => switchView('chat') },
  { id: 'view-pipeline', title: 'Go to Pipeline (CRM & Jobs)', category: 'Navigation', shortcut: '3', action: () => switchView('pipeline') },
  { id: 'view-study', title: 'Go to Study Lab', category: 'Navigation', shortcut: '4', action: () => switchView('study') },
  { id: 'view-dev', title: 'Go to Dev & System Tools', category: 'Navigation', shortcut: '5', action: () => switchView('dev') },
  { id: 'act-brief', title: 'Refresh Daily Orientation Brief', category: 'Actions', shortcut: 'R', action: () => fetchDailyBrief() },
  { id: 'act-new-session', title: 'Start New Chat Session', category: 'Actions', shortcut: 'N', action: () => startNewSession() },
  { id: 'act-study-os', title: 'Start Study: Operating Systems', category: 'Study Lab', shortcut: '', action: () => startStudyQuick('Operating Systems') },
  { id: 'act-study-cn', title: 'Start Study: Computer Networks', category: 'Study Lab', shortcut: '', action: () => startStudyQuick('Computer Networks') },
  { id: 'act-study-dbms', title: 'Start Study: DBMS & SQL', category: 'Study Lab', shortcut: '', action: () => startStudyQuick('DBMS & SQL') },
  { id: 'act-toggle-voice', title: 'Toggle Voice Response (TTS)', category: 'Toggles', shortcut: 'V', action: () => toggleVoiceTTS() },
  { id: 'act-toggle-wake', title: 'Toggle Wake Word (Hey Sera)', category: 'Toggles', shortcut: 'W', action: () => toggleWakeWord() },
  { id: 'act-toggle-clip', title: 'Toggle Clipboard Capture (Ctrl+Shift+S)', category: 'Toggles', shortcut: 'C', action: () => toggleClipboardHotkey() }
];

let selectedCmdIndex = 0;

function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Cmd/Ctrl + K: Command palette
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      toggleCommandPalette();
    }
    // Cmd/Ctrl + Enter in chat input: send
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      const activeEl = document.activeElement;
      if (activeEl && activeEl.id === 'chat-input') {
        e.preventDefault();
        sendChatMessage();
      }
    }
    // Escape: close modal / popover
    if (e.key === 'Escape') {
      closeCommandPalette();
      const popover = document.getElementById('ws-popover');
      if (popover && !popover.classList.contains('hidden')) popover.classList.add('hidden');
    }
  });
}

function initCommandPalette() {
  const input = document.getElementById('cmd-palette-input');
  if (!input) return;

  input.addEventListener('input', () => {
    renderCommandList(input.value);
  });

  input.addEventListener('keydown', (e) => {
    const items = document.querySelectorAll('.cmd-item');
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedCmdIndex = (selectedCmdIndex + 1) % items.length;
      highlightCommandItem();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedCmdIndex = (selectedCmdIndex - 1 + items.length) % items.length;
      highlightCommandItem();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (items[selectedCmdIndex]) {
        items[selectedCmdIndex].click();
      }
    }
  });
}

function toggleCommandPalette() {
  const modal = document.getElementById('cmd-palette-modal');
  if (!modal) return;
  const isHidden = modal.classList.toggle('hidden');
  if (!isHidden) {
    selectedCmdIndex = 0;
    const input = document.getElementById('cmd-palette-input');
    if (input) {
      input.value = '';
      setTimeout(() => input.focus(), 40);
    }
    renderCommandList('');
  }
}

function closeCommandPalette() {
  const modal = document.getElementById('cmd-palette-modal');
  if (modal) modal.classList.add('hidden');
}

function renderCommandList(query) {
  const listEl = document.getElementById('cmd-palette-list');
  if (!listEl) return;

  const filtered = COMMANDS.filter(c => 
    c.title.toLowerCase().includes(query.toLowerCase()) || 
    c.category.toLowerCase().includes(query.toLowerCase())
  );

  selectedCmdIndex = 0;

  if (filtered.length === 0) {
    listEl.innerHTML = `<div class="text-xs text-slate-400 font-mono py-6 text-center">No commands matching "${escapeHtml(query)}"</div>`;
    return;
  }

  listEl.innerHTML = filtered.map((cmd, idx) => `
    <div class="cmd-item ${idx === 0 ? 'selected' : ''}" onclick="executeCommand(${COMMANDS.indexOf(cmd)})">
      <div class="flex items-center gap-2.5">
        <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">${cmd.category}</span>
        <span class="font-medium">${escapeHtml(cmd.title)}</span>
      </div>
      ${cmd.shortcut ? `<kbd class="font-mono text-[10.5px] px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-500">${cmd.shortcut}</kbd>` : ''}
    </div>
  `).join('');
}

function highlightCommandItem() {
  const items = document.querySelectorAll('.cmd-item');
  items.forEach((it, idx) => {
    if (idx === selectedCmdIndex) {
      it.classList.add('selected');
      it.scrollIntoView({ block: 'nearest' });
    } else {
      it.classList.remove('selected');
    }
  });
}

function executeCommand(index) {
  closeCommandPalette();
  const cmd = COMMANDS[index];
  if (cmd && cmd.action) {
    cmd.action();
  }
}

async function startStudyQuick(subject) {
  switchView('study');
  try {
    const res = await fetch('/api/study/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject: subject, goal: 'Quick review' })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`Study block started for ${subject}`, 'success');
      fetchStudyData();
    }
  } catch (e) {
    showToast('Failed to start study: ' + e.message, 'error');
  }
}

// Helper: safe HTML escaping
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
