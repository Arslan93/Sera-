import React from 'react';
import { useApp } from '../context/AppContext';

export default function SparklinePopover({ type, position, onClose }) {
  const { cpuHistory, ramHistory } = useApp();

  if (!position) return null;

  const history = type === 'cpu' ? cpuHistory : ramHistory;
  const label = type === 'cpu' ? 'CPU 60s Trend' : 'RAM 60s Trend';
  const currentVal = history[history.length - 1] || 0;

  return (
    <div 
      className="fixed z-50 p-2.5 rounded-lg bg-slate-900 text-white shadow-xl text-xs font-mono pointer-events-none"
      style={{ left: `${position.left}px`, top: `${position.top}px` }}
    >
      <div className="text-[10.5px] text-slate-400 mb-1 font-semibold">{label}</div>
      <div className="flex items-end gap-1 h-7 p-1 bg-slate-800 rounded">
        {history.map((val, i) => (
          <div 
            key={i} 
            className="flex-1 bg-blue-400 rounded-sm"
            style={{ height: `${Math.max(3, Math.round(val * 0.25))}px` }}
          />
        ))}
      </div>
      <div className="flex justify-between text-[9px] text-slate-400 mt-1">
        <span>60s ago</span>
        <span>Now: {currentVal}%</span>
      </div>
    </div>
  );
}
