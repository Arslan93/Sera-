import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { Code, Puzzle, Clipboard, Bookmark, Box, RefreshCw } from 'lucide-react';

export default function DevSystemView() {
  const { skills, fetchSkills, captures, readLater, fetchCaptures, showToast } = useApp();

  // Scaffolder Form State
  const [projectType, setProjectType] = useState('react_component');
  const [destFolder, setDestFolder] = useState('src');
  const [componentName, setComponentName] = useState('DashboardCard');
  const [scaffoldLog, setScaffoldLog] = useState(null);
  const [isScaffolding, setIsScaffolding] = useState(false);

  async function handleScaffold(e) {
    e.preventDefault();
    setIsScaffolding(true);
    setScaffoldLog({ type: 'info', message: `Scaffolding ${projectType} into ${destFolder}...` });

    try {
      const res = await fetch('/api/scaffold', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_type: projectType,
          destination_folder: destFolder.trim(),
          name: componentName.trim()
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setScaffoldLog({ type: 'success', message: `✓ Successfully scaffolded '${componentName}' at ${data.path || destFolder}` });
        showToast(`Scaffolded ${componentName}`, 'success');
      } else {
        setScaffoldLog({ type: 'error', message: `✗ Error: ${data.message || 'Failed'}` });
        showToast('Scaffolding failed', 'error');
      }
    } catch (err) {
      setScaffoldLog({ type: 'error', message: `✗ ${err.message}` });
      showToast(err.message, 'error');
    } finally {
      setIsScaffolding(false);
    }
  }

  async function handleToggleSkill(skillName, currentState) {
    try {
      const res = await fetch('/api/skills/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill_name: skillName, enable: !currentState })
      });
      if (res.ok) {
        showToast(`${skillName} ${!currentState ? 'enabled' : 'disabled'}`, 'info');
        fetchSkills();
      }
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
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

  return (
    <div className="view-panel flex-1 overflow-y-auto p-5 space-y-4">
      {/* ROW 1: CODE SCAFFOLDER + SKILLS MANAGER */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Code Scaffolder Card */}
        <div className="studio-card p-4">
          <div className="pb-2.5 border-b border-slate-100 mb-3">
            <h2 className="text-xs font-bold text-slate-900 flex items-center gap-2">
              <Code className="w-4 h-4 text-blue-600" />
              <span>Instant Code Scaffolder</span>
            </h2>
          </div>
          <form onSubmit={handleScaffold} className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-600 text-[11px] mb-1 font-semibold">TEMPLATE</label>
              <select 
                value={projectType}
                onChange={(e) => setProjectType(e.target.value)}
                className="studio-well w-full px-3 py-2 bg-white text-slate-800 font-medium"
              >
                <option value="react_component">React Component (.jsx)</option>
                <option value="express_api">Express API Route (.js)</option>
                <option value="fastapi_api">FastAPI Endpoint (.py)</option>
                <option value="html_tailwind">HTML + Tailwind Page</option>
                <option value="python_cli">Python CLI Script</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-600 text-[11px] mb-1 font-semibold">DESTINATION FOLDER</label>
              <input 
                type="text" 
                value={destFolder}
                onChange={(e) => setDestFolder(e.target.value)}
                required 
                className="studio-well w-full px-3 py-2 bg-white text-slate-800 font-mono text-xs" 
              />
            </div>
            <div>
              <label className="block text-slate-600 text-[11px] mb-1 font-semibold">COMPONENT / FILE NAME</label>
              <input 
                type="text" 
                value={componentName}
                onChange={(e) => setComponentName(e.target.value)}
                required 
                className="studio-well w-full px-3 py-2 bg-white text-slate-800 font-medium text-xs" 
              />
            </div>
            <button 
              type="submit" 
              disabled={isScaffolding}
              className="btn-primary w-full py-2.5 text-xs font-semibold flex items-center justify-center gap-1.5 shadow-sm disabled:opacity-50"
            >
              <Box className="w-3.5 h-3.5" />
              <span>{isScaffolding ? 'Generating...' : 'Generate Template'}</span>
            </button>
          </form>

          {scaffoldLog && (
            <div className={`mt-3 p-2 rounded text-xs font-mono ${
              scaffoldLog.type === 'success' 
                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' 
                : (scaffoldLog.type === 'error' ? 'bg-rose-50 text-rose-800 border border-rose-200' : 'bg-blue-50 text-blue-800 border border-blue-200')
            }`}>
              {scaffoldLog.message}
            </div>
          )}
        </div>

        {/* Skills Manager Card */}
        <div className="studio-card p-4">
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 mb-3">
            <h2 className="text-xs font-bold text-slate-900 flex items-center gap-2">
              <Puzzle className="w-4 h-4 text-purple-600" />
              <span>Dynamic Skill Plugins</span>
            </h2>
            <button onClick={fetchSkills} className="text-xs text-blue-600 hover:underline font-medium flex items-center gap-1">
              <RefreshCw className="w-3 h-3" />
              <span>Reload</span>
            </button>
          </div>
          <div className="space-y-2.5 max-h-[320px] overflow-y-auto">
            {skills.map(s => (
              <div key={s.name} className="studio-card p-3 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="font-semibold text-slate-900 text-xs">{s.name}</span>
                    <span className="px-1.5 py-0.2 rounded bg-slate-100 text-[10px] font-mono text-slate-600 font-medium">
                      {(s.tools || []).length} tools
                    </span>
                  </div>
                  <p className="text-[11.5px] text-slate-500">{s.description || ''}</p>
                </div>
                <button 
                  onClick={() => handleToggleSkill(s.name, s.enabled)}
                  className={`text-[11px] px-3 py-1 font-medium rounded transition-colors ${
                    s.enabled ? 'btn-primary' : 'btn-secondary'
                  }`}
                >
                  {s.enabled ? 'Enabled' : 'Disabled'}
                </button>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* ROW 2: CLIPBOARD CAPTURES + READ LATER */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Clipboard Captures Card */}
        <div className="studio-card p-4">
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 mb-3">
            <h3 className="text-xs font-bold text-slate-900 flex items-center gap-2">
              <Clipboard className="w-4 h-4 text-blue-600" />
              <span>Clipboard Captures (Ctrl+Shift+S)</span>
            </h3>
            <button onClick={fetchCaptures} className="text-xs text-slate-500 hover:text-slate-800">
              Refresh
            </button>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {captures.length === 0 ? (
              <div className="text-xs text-slate-400 font-mono py-4 text-center">
                No clipboard captures logged yet (Press Ctrl+Shift+S).
              </div>
            ) : (
              captures.slice(-8).reverse().map((c, i) => (
                <div key={i} className="p-2.5 rounded-md bg-white border border-slate-200 text-xs shadow-sm">
                  <div className="flex items-center justify-between mb-1">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono uppercase font-bold ${getBadgeClass(c.classification)}`}>
                      {c.classification}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {(c.captured_at || '').slice(11, 19)}
                    </span>
                  </div>
                  <div className="font-mono text-[11.5px] text-slate-800 truncate mb-1">
                    {c.raw_content}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    Filed to: {c.filed_to}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Read-Later Links Card */}
        <div className="studio-card p-4">
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 mb-3">
            <h3 className="text-xs font-bold text-slate-900 flex items-center gap-2">
              <Bookmark className="w-4 h-4 text-emerald-600" />
              <span>Saved Read-Later Links</span>
            </h3>
            <button onClick={fetchCaptures} className="text-xs text-slate-500 hover:text-slate-800">
              Refresh
            </button>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {readLater.length === 0 ? (
              <div className="text-xs text-slate-400 font-mono py-4 text-center">
                Read later list is currently empty.
              </div>
            ) : (
              readLater.slice(-8).reverse().map((l, i) => (
                <div key={i} className="flex items-center justify-between p-2.5 rounded-md bg-white border border-slate-200 text-xs shadow-sm">
                  <a 
                    href={l.url} 
                    target="_blank" 
                    rel="noreferrer"
                    className="text-blue-600 hover:underline font-mono text-[11.5px] font-medium truncate flex-1 mr-2"
                  >
                    {l.title || l.url}
                  </a>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {(l.added_at || '').slice(0, 10)}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
