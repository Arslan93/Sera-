import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  Compass, 
  RefreshCw, 
  GraduationCap, 
  Activity, 
  Briefcase, 
  TrendingUp, 
  ArrowRight, 
  Play, 
  Square, 
  Plus, 
  AlertCircle,
  ChevronRight,
  Loader2
} from 'lucide-react';

const CIRCUMFERENCE_32 = 201.06;
const CRM_STAGES = ['New', 'Contacted', 'Proposal', 'Won', 'Lost'];

export default function ConsoleView() {
  const { 
    dailyBrief, 
    isBriefLoading, 
    fetchBrief, 
    studySession, 
    fetchStudy, 
    systemInfo, 
    pollTelemetry, 
    jobFollowups, 
    leads, 
    fetchLeads,
    setCurrentView,
    showToast
  } = useApp();

  // Study Session In-Place State
  const [selectedSubject, setSelectedSubject] = useState('Operating Systems');
  const [customGoal, setCustomGoal] = useState('');
  const [endNotes, setEndNotes] = useState('');
  const [elapsedTime, setElapsedTime] = useState('00:00:00');

  // Accordion CRM Card state
  const [expandedLeadId, setExpandedLeadId] = useState(null);

  // Stopwatch ticking
  useEffect(() => {
    let timer;
    if (studySession) {
      const startTime = new Date(studySession.started_at || studySession.start_time || Date.now()).getTime();
      const update = () => {
        const sec = Math.max(0, Math.floor((Date.now() - startTime) / 1000));
        const h = String(Math.floor(sec / 3600)).padStart(2, '0');
        const m = String(Math.floor((sec % 3600) / 60)).padStart(2, '0');
        const s = String(sec % 60).padStart(2, '0');
        setElapsedTime(`${h}:${m}:${s}`);
      };
      update();
      timer = setInterval(update, 1000);
    }
    return () => clearInterval(timer);
  }, [studySession]);

  // Start Study Handler
  async function handleStartStudy(e) {
    if (e) e.preventDefault();
    try {
      const res = await fetch('/api/study/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject: selectedSubject, goal: customGoal || 'Focused review' })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(`Study session started for ${selectedSubject}`, 'success');
        fetchStudy();
      } else {
        showToast(data.message || 'Error starting study', 'warning');
      }
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    }
  }

  // End Study Handler
  async function handleEndStudy() {
    try {
      const res = await fetch('/api/study/end', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: endNotes })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast('Study session completed and logged', 'success');
        setEndNotes('');
        fetchStudy();
      }
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    }
  }

  // Update CRM Lead Stage Inline
  async function handleLeadStageChange(leadId, newStage) {
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
      }
    } catch (err) {
      showToast('Failed to update stage: ' + err.message, 'error');
    }
  }

  // Hardware calculations
  const cpuPercent = parseFloat(systemInfo.cpu?.usage_percent || '0');
  const ramPercent = parseFloat(systemInfo.ram?.percent_used || '0');
  const diskPercent = parseFloat(systemInfo.disk?.percent_used || '0');
  const ramUsedGB = systemInfo.ram?.used_gb || 0;
  const ramTotalGB = systemInfo.ram?.total_gb || 0;
  const diskFreeGB = systemInfo.disk?.free_gb || 0;

  const cpuOffset = CIRCUMFERENCE_32 * (1 - Math.min(100, Math.max(0, cpuPercent)) / 100);
  const ramOffset = CIRCUMFERENCE_32 * (1 - Math.min(100, Math.max(0, ramPercent)) / 100);
  const diskOffset = CIRCUMFERENCE_32 * (1 - Math.min(100, Math.max(0, diskPercent)) / 100);

  // Structured brief parsing
  const briefSentences = (dailyBrief || '').split(/(?<=[.!?])\s+/);
  const actionItems = briefSentences.filter(s => /follow-up|deadline|overdue|client|lead|exam|quiz/i.test(s));
  const ambientItems = briefSentences.filter(s => !/follow-up|deadline|overdue|client|lead|exam|quiz/i.test(s));

  return (
    <div className="view-panel flex-1 overflow-y-auto p-5 space-y-4">
      {/* ☀️ HERO: DAILY ORIENTATION BRIEF */}
      <div className="studio-card-hero p-4 border-l-4 border-l-blue-500">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 min-w-0 flex-1">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 flex-shrink-0 mt-0.5 shadow-sm">
              <Compass className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 mb-1.5">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-900 font-mono">
                  DAILY ORIENTATION BRIEF
                </h2>
                <span className="px-1.5 py-0.2 rounded bg-slate-100 text-[10px] font-mono text-slate-600">
                  Arslan's Morning Compass
                </span>
              </div>

              {dailyBrief ? (
                <div className="space-y-2">
                  {actionItems.length > 0 && (
                    <div className="flex items-start gap-2 p-2 rounded-md bg-amber-50/80 border border-amber-200/80 text-amber-950 text-[12.5px]">
                      <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <b className="font-bold">Action Needed:</b> {actionItems.join(' ')}
                      </div>
                    </div>
                  )}
                  <div className="text-slate-800 text-[13px] leading-relaxed">
                    {ambientItems.join(' ') || dailyBrief}
                  </div>
                </div>
              ) : (
                <div className="text-slate-400 font-mono text-xs">
                  {isBriefLoading ? 'Compiling morning orientation...' : 'Ready to compile daily orientation.'}
                </div>
              )}
            </div>
          </div>

          <button 
            onClick={fetchBrief} 
            disabled={isBriefLoading}
            className="btn-secondary py-1 px-2.5 text-xs flex items-center gap-1 font-medium flex-shrink-0"
            title="Refresh orientation brief"
          >
            {isBriefLoading ? (
              <Loader2 className="w-3.5 h-3.5 text-slate-600 animate-spin" />
            ) : (
              <RefreshCw className="w-3.5 h-3.5 text-slate-600" />
            )}
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {/* ROW 1: STUDY SESSION VITALS + 3D HARDWARE TELEMETRY CLUSTER */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        
        {/* Card A: Study Session Vitals (In-Place Transition) */}
        <div className="studio-card p-4">
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 mb-3">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
                <GraduationCap className="w-3.5 h-3.5" />
              </div>
              <h3 className="font-bold text-xs text-slate-900">Study Session Vitals</h3>
            </div>
            <button 
              onClick={() => setCurrentView('study')} 
              className="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1"
            >
              <span>Open Full Lab</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          {studySession ? (
            /* ACTIVE IN-PLACE STATE */
            <div className="p-4 rounded-lg border border-emerald-200 bg-emerald-50/50 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 agentic-live"></span>
                  <span className="text-xs font-mono text-emerald-800 font-bold tracking-wider uppercase">
                    ACTIVE STUDY BLOCK
                  </span>
                </div>
                <span className="font-mono text-xl font-bold text-slate-900 tracking-tight">
                  {elapsedTime}
                </span>
              </div>
              <div className="text-sm font-bold text-slate-900 mb-0.5">{studySession.subject}</div>
              <div className="text-xs text-slate-600 mb-3 font-medium">{studySession.goal || 'Focused study block'}</div>
              <div className="flex items-center gap-2">
                <input 
                  type="text" 
                  value={endNotes}
                  onChange={(e) => setEndNotes(e.target.value)}
                  placeholder="Notes / topics covered..." 
                  className="studio-well text-xs px-3 py-1.5 flex-1 text-slate-800 bg-white"
                />
                <button 
                  onClick={handleEndStudy}
                  className="btn-primary bg-rose-600 hover:bg-rose-700 text-xs px-3 py-1.5 flex items-center gap-1.5 font-semibold"
                >
                  <Square className="w-3.5 h-3.5" />
                  <span>End Session</span>
                </button>
              </div>
            </div>
          ) : (
            /* PICKER IN-PLACE STATE */
            <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50">
              <div className="text-xs text-slate-600 mb-2 font-medium">Select Subject:</div>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {['Operating Systems', 'Computer Networks', 'DBMS & SQL', 'Theory of Computation', 'Deep Learning'].map(sub => (
                  <button 
                    key={sub}
                    type="button" 
                    onClick={() => setSelectedSubject(sub)}
                    className={`text-[11px] py-1 px-2.5 font-medium rounded-md transition-colors ${
                      selectedSubject === sub 
                        ? 'btn-primary' 
                        : 'btn-secondary'
                    }`}
                  >
                    {sub}
                  </button>
                ))}
              </div>

              <form onSubmit={handleStartStudy} className="flex gap-2">
                <input 
                  type="text" 
                  value={selectedSubject} 
                  onChange={(e) => setSelectedSubject(e.target.value)}
                  placeholder="Custom Topic..." 
                  required 
                  className="studio-well text-xs px-3 py-1.5 flex-1 bg-white text-slate-800 font-medium"
                />
                <input 
                  type="text" 
                  value={customGoal}
                  onChange={(e) => setCustomGoal(e.target.value)}
                  placeholder="Goal (e.g. 5 problems)" 
                  className="studio-well text-xs px-3 py-1.5 flex-1 bg-white text-slate-800"
                />
                <button type="submit" className="btn-primary text-xs px-3.5 py-1.5 flex items-center gap-1 font-semibold">
                  <Play className="w-3 h-3" />
                  <span>Start</span>
                </button>
              </form>
            </div>
          )}
        </div>

        {/* Card B: 3D HARDWARE TELEMETRY CLUSTER */}
        <div className="studio-card p-4">
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 mb-3">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
                <Activity className="w-3.5 h-3.5" />
              </div>
              <h3 className="font-bold text-xs text-slate-900">Hardware Telemetry Cluster</h3>
            </div>
            <button onClick={pollTelemetry} className="text-xs font-semibold text-slate-500 hover:text-slate-800">
              Refresh
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2 py-1">
            {/* Dial 1: CPU */}
            <div className="flex flex-col items-center">
              <div className={`dial-housing mb-1.5 ${cpuPercent >= 85 ? 'dial-critical' : (cpuPercent >= 70 ? 'dial-warning' : '')}`}>
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
              <span className="text-[11px] font-bold text-slate-700 tracking-tight">CPU LOAD</span>
              <span className="text-[10px] font-mono text-slate-400">Processor</span>
            </div>

            {/* Dial 2: RAM */}
            <div className="flex flex-col items-center">
              <div className={`dial-housing mb-1.5 ${ramPercent >= 85 ? 'dial-critical' : (ramPercent >= 75 ? 'dial-warning' : '')}`}>
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
              <span className="text-[11px] font-bold text-slate-700 tracking-tight">MEMORY</span>
              <span className="text-[10px] font-mono text-slate-400">{ramUsedGB}/{ramTotalGB} GB</span>
            </div>

            {/* Dial 3: Disk */}
            <div className="flex flex-col items-center">
              <div className="dial-housing mb-1.5">
                <div className="dial-track-recess">
                  <svg className="dial-svg" viewBox="0 0 76 76">
                    <circle className="dial-svg-track" cx="38" cy="38" r="32"></circle>
                    <circle 
                      className="dial-svg-value stroke-amber-500" 
                      cx="38" cy="38" r="32" 
                      strokeDasharray="201.06" 
                      strokeDashoffset={diskOffset}
                    ></circle>
                  </svg>
                  <div className="dial-hub">
                    <span className="font-mono font-bold text-[13px] text-slate-900 leading-none">
                      {Math.round(diskPercent)}%
                    </span>
                  </div>
                </div>
              </div>
              <span className="text-[11px] font-bold text-slate-700 tracking-tight">STORAGE</span>
              <span className="text-[10px] font-mono text-slate-400">{diskFreeGB} GB Free</span>
            </div>
          </div>
        </div>

      </div>

      {/* ROW 2: PENDING JOB FOLLOW-UPS + ACTIVE BUSINESS LEADS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        
        {/* Card C: Pending Job Follow-ups */}
        <div className="studio-card p-4">
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 mb-3">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
                <Briefcase className="w-3.5 h-3.5" />
              </div>
              <h3 className="font-bold text-xs text-slate-900">Job Application Follow-ups</h3>
            </div>
            <button 
              onClick={() => setCurrentView('pipeline')} 
              className="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1"
            >
              <span>View Funnel</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2">
            {jobFollowups.length > 0 ? (
              jobFollowups.slice(0, 3).map((f, i) => (
                <div key={i} className="flex items-center justify-between p-2.5 rounded-md bg-slate-50 border border-slate-200 text-xs">
                  <div>
                    <span className="font-semibold text-slate-900">{f.company}</span>
                    <span className="text-slate-500 ml-1.5">{f.role}</span>
                  </div>
                  <span className={`font-mono text-[11px] font-semibold ${
                    f.is_overdue ? 'text-amber-700 bg-amber-100/60 px-1.5 py-0.5 rounded' : 'text-slate-600'
                  }`}>
                    {f.is_overdue ? 'OVERDUE' : (f.days_until_followup ? `in ${f.days_until_followup}d` : '14d+ idle')}
                  </span>
                </div>
              ))
            ) : (
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 text-center">
                <p className="text-xs text-slate-600 mb-2">No pending job follow-ups due.</p>
                <button 
                  onClick={() => setCurrentView('pipeline')} 
                  className="btn-secondary text-[11px] py-1 px-2.5 inline-flex items-center gap-1 font-medium"
                >
                  <Plus className="w-3 h-3 text-blue-600" />
                  <span>Log a new application</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Card D: CRM Leads (Accordion Details + Inline Stage Dropdown) */}
        <div className="studio-card p-4">
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 mb-3">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-700">
                <TrendingUp className="w-3.5 h-3.5" />
              </div>
              <h3 className="font-bold text-xs text-slate-900">Client CRM Pipeline</h3>
            </div>
            <button 
              onClick={() => setCurrentView('pipeline')} 
              className="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1"
            >
              <span>Full Kanban</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2">
            {leads.length > 0 ? (
              leads.slice(0, 3).map((l, idx) => {
                const isExpanded = expandedLeadId === (l.id || idx);
                return (
                  <div key={l.id || idx} className="studio-card p-2.5 text-xs">
                    <div 
                      className="flex items-center justify-between cursor-pointer"
                      onClick={() => setExpandedLeadId(isExpanded ? null : (l.id || idx))}
                    >
                      <div className="flex items-center gap-1.5">
                        <ChevronRight className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                        <span className="font-semibold text-slate-900">{l.name}</span>
                        <span className="text-slate-500 font-normal">({l.company || 'Direct'})</span>
                      </div>
                      <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                        <span className="font-mono font-semibold text-emerald-700">{l.deal_value || ''}</span>
                        <select 
                          value={l.status || 'New'}
                          onChange={(e) => handleLeadStageChange(l.id || l.name, e.target.value)}
                          className="bg-white text-slate-700 border border-slate-200 rounded px-1.5 py-0.5 text-[10.5px] font-mono"
                        >
                          {CRM_STAGES.map(s => (
                            <option key={s} value={s}>{s}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="pt-2 mt-2 border-t border-slate-100 text-slate-600 text-[11px] space-y-1">
                        {l.notes && <div><b>Notes:</b> {l.notes}</div>}
                        {l.email && <div><b>Email:</b> {l.email}</div>}
                        {l.phone && <div><b>Phone:</b> {l.phone}</div>}
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="text-xs text-slate-500 font-mono p-3 bg-slate-50 rounded border border-slate-200 text-center">
                No active business leads recorded.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
