import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { GraduationCap, Play, Square, RefreshCw } from 'lucide-react';

export default function StudyLabView() {
  const { studySession, studyStats, fetchStudy, showToast } = useApp();

  const [selectedSubject, setSelectedSubject] = useState('Operating Systems');
  const [customGoal, setCustomGoal] = useState('');
  const [endNotes, setEndNotes] = useState('');
  const [elapsedTime, setElapsedTime] = useState('00:00:00');

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
        showToast(`Study block started for ${selectedSubject}`, 'success');
        fetchStudy();
      } else {
        showToast(data.message || 'Error starting study', 'warning');
      }
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    }
  }

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

  const subjectTotals = studyStats?.subject_totals_minutes || {};
  const totalMin = studyStats?.total_study_minutes || 0;
  const sessionsCount = studyStats?.total_sessions || 0;
  const statEntries = Object.entries(subjectTotals);

  return (
    <div className="view-panel flex-1 overflow-y-auto p-5 space-y-4">
      {/* Active Session / Start Block Card */}
      <div className="studio-card p-4">
        <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 mb-3">
          <h2 className="text-xs font-bold text-slate-900 flex items-center gap-2">
            <GraduationCap className="w-4 h-4 text-emerald-600" />
            <span>RGPV Exam Study Sessions</span>
          </h2>
          <button onClick={fetchStudy} className="btn-secondary py-1 px-2.5 text-xs flex items-center gap-1">
            <RefreshCw className="w-3 h-3" />
            <span>Refresh</span>
          </button>
        </div>

        {studySession ? (
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
            <div className="text-xs text-slate-600 mb-3 font-medium">{studySession.goal || 'Focus study block'}</div>
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
          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50">
            <div className="text-xs text-slate-600 mb-2 font-medium">Quick Launch RGPV Subjects:</div>
            <div className="flex flex-wrap gap-1.5 mb-3">
              {['Operating Systems', 'Computer Networks', 'DBMS & SQL', 'Theory of Computation', 'Deep Learning'].map(sub => (
                <button 
                  key={sub}
                  type="button" 
                  onClick={() => setSelectedSubject(sub)}
                  className={`text-[11px] py-1 px-2.5 font-medium rounded-md transition-colors ${
                    selectedSubject === sub ? 'btn-primary' : 'btn-secondary'
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
                placeholder="Topic..." 
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

      {/* 7-Day Study Lookback Breakdown Card */}
      <div className="studio-card p-4">
        <div className="pb-2.5 border-b border-slate-100 mb-3">
          <h3 className="text-xs font-bold text-slate-900">Subject Breakdown (Last 7 Days)</h3>
        </div>

        {statEntries.length === 0 ? (
          <div className="text-xs text-slate-500 font-mono py-2">No study sessions recorded in the last 7 days.</div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs font-mono text-slate-600 mb-2">
              <span>Total Revision: <b className="text-emerald-700 font-bold">{(totalMin / 60).toFixed(1)} hrs</b> ({totalMin} min)</span>
              <span>{sessionsCount} Sessions</span>
            </div>
            <div className="space-y-2.5">
              {statEntries.map(([subj, mins]) => {
                const pct = totalMin > 0 ? Math.round((mins / totalMin) * 100) : 0;
                return (
                  <div key={subj}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-800 font-semibold">{subj}</span>
                      <span className="font-mono text-slate-500 text-[11px]">{mins} min ({pct}%)</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div className="bg-emerald-500 h-2 rounded-full transition-all duration-500" style={{ width: `${pct}%` }}></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
