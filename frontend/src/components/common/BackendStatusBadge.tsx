import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api/client';
import { Activity } from 'lucide-react';

export const BackendStatusBadge: React.FC = () => {
  const [status, setStatus] = useState<'checking' | 'connected' | 'offline'>('checking');
  const [version, setVersion] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function check() {
      try {
        const res = await apiClient.checkHealth();
        if (isMounted) {
          setStatus('connected');
          setVersion(res.version);
        }
      } catch {
        if (isMounted) {
          setStatus('offline');
        }
      }
    }

    check();
    const interval = setInterval(check, 30000); // polite 30s interval
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div
      className="flex items-center gap-2 px-2.5 py-1.5 rounded text-xs font-mono border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 text-slate-600 dark:text-slate-400"
      title={
        status === 'connected'
          ? `Backend online (v${version || '2.0.0'})`
          : status === 'checking'
          ? 'Connecting to backend...'
          : 'Backend unreachable at http://localhost:8000 (Local demo active)'
      }
    >
      <div className="relative flex h-2 w-2">
        {status === 'connected' && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
        )}
        <span
          className={`relative inline-flex rounded-full h-2 w-2 ${
            status === 'connected'
              ? 'bg-emerald-500'
              : status === 'checking'
              ? 'bg-amber-400'
              : 'bg-rose-500'
          }`}
        />
      </div>
      <span className="truncate">
        {status === 'connected'
          ? 'API Connected'
          : status === 'checking'
          ? 'Connecting...'
          : 'API Offline'}
      </span>
    </div>
  );
};
