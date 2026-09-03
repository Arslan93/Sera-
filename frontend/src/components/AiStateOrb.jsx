import React from 'react';
import { useApp } from '../context/AppContext';

export default function AiStateOrb({ size = 'mini' }) {
  const { aiState, activeTool } = useApp();

  const isHero = size === 'hero';

  function formatToolName(name) {
    if (!name) return 'tool';
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  let labelText = 'SERA is idle and ready';
  let labelClass = 'text-xs font-mono text-slate-500 font-medium';

  if (aiState === 'listening') {
    labelText = 'Listening for speech...';
    labelClass = 'text-xs font-mono text-emerald-700 font-semibold';
  } else if (aiState === 'thinking') {
    labelText = activeTool ? `Coordinating tool: ${formatToolName(activeTool)}` : 'Thinking & analyzing...';
    labelClass = 'text-xs font-mono text-purple-700 font-semibold';
  } else if (aiState === 'speaking') {
    labelText = 'Speaking response...';
    labelClass = 'text-xs font-mono text-amber-700 font-semibold';
  }

  return (
    <div className="flex items-center gap-3">
      <div 
        className={`ai-orb ${isHero ? 'ai-orb-hero' : 'ai-orb-mini'} state-${aiState}`}
        title={`SERA State: ${aiState}`}
      />
      {isHero && (
        <div>
          <div className="font-bold text-xs text-slate-900">Agentic Orchestrator</div>
          <div className={labelClass}>{labelText}</div>
        </div>
      )}
    </div>
  );
}
