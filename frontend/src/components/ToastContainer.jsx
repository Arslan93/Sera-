import React from 'react';
import { useApp } from '../context/AppContext';
import { CheckCircle2, Info, AlertTriangle, AlertCircle, X } from 'lucide-react';

export default function ToastContainer() {
  const { toasts, removeToast } = useApp();

  if (!toasts.length) return null;

  return (
    <div id="toast-container" role="status" aria-live="polite">
      {toasts.map(toast => {
        let Icon = Info;
        let iconColor = 'text-blue-600';

        if (toast.type === 'success') {
          Icon = CheckCircle2;
          iconColor = 'text-emerald-600';
        } else if (toast.type === 'warning') {
          Icon = AlertTriangle;
          iconColor = 'text-amber-600';
        } else if (toast.type === 'error') {
          Icon = AlertCircle;
          iconColor = 'text-rose-600';
        }

        return (
          <div key={toast.id} className={`toast-item toast-${toast.type}`}>
            <div className="flex items-center gap-2 min-w-0">
              <Icon className={`w-4 h-4 ${iconColor} flex-shrink-0`} />
              <span className="truncate">{toast.message}</span>
            </div>
            <button 
              onClick={() => removeToast(toast.id)} 
              className="text-slate-400 hover:text-slate-600 p-0.5"
              title="Dismiss"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
