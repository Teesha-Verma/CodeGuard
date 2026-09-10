import React from 'react';
import { Severity } from '@/types';
import { Cpu, Terminal, ShieldAlert, CheckCircle2, Loader2, AlertTriangle, XCircle, Clock } from 'lucide-react';

interface SeverityBadgeProps {
  severity: Severity | string;
  size?: 'sm' | 'md';
  className?: string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  severity,
  size = 'md',
  className = '',
}) => {
  const sev = (severity || 'info').toLowerCase();

  const styles: Record<string, string> = {
    critical:
      'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20',
    high:
      'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20',
    medium:
      'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
    low:
      'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
    info:
      'bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/20',
  };

  const style = styles[sev] || styles.info;
  const sizeClass = size === 'sm' ? 'text-[11px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5';

  return (
    <span
      className={`inline-flex items-center font-medium font-mono uppercase tracking-wider rounded border ${style} ${sizeClass} ${className}`}
    >
      {sev}
    </span>
  );
};

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const norm = (status || 'pending').toLowerCase();

  if (norm === 'completed' || norm === 'success') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 ${className}`}
      >
        <CheckCircle2 className="w-3.5 h-3.5" />
        Completed
      </span>
    );
  }

  if (norm === 'running' || norm === 'started' || norm === 'processing') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 ${className}`}
      >
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
        Running
      </span>
    );
  }

  if (norm === 'queued' || norm === 'pending') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-0.5 rounded-full bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20 ${className}`}
      >
        <Clock className="w-3.5 h-3.5" />
        Queued
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-0.5 rounded-full bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 ${className}`}
    >
      <XCircle className="w-3.5 h-3.5" />
      Failed
    </span>
  );
};

interface SourceBadgeProps {
  source: string;
  className?: string;
}

export const SourceBadge: React.FC<SourceBadgeProps> = ({ source, className = '' }) => {
  const norm = (source || '').toLowerCase();
  const isLlm = norm.includes('llm') || norm.includes('groq');

  return (
    <span
      className={`inline-flex items-center gap-1 text-[11px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700/60 ${className}`}
    >
      {isLlm ? (
        <>
          <Cpu className="w-3 h-3 text-blue-500" />
          <span>LLM</span>
        </>
      ) : (
        <>
          <Terminal className="w-3 h-3 text-slate-400" />
          <span>{source || 'Static'}</span>
        </>
      )}
    </span>
  );
};
