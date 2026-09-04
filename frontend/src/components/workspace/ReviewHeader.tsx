import React from 'react';
import { ReviewReport } from '@/types';
import { StatusBadge } from '@/components/common/Badges';
import {
  Columns,
  BarChart3,
  Network,
  Copy,
  Check,
  RotateCw,
  GitPullRequest,
  Code2,
} from 'lucide-react';

interface ReviewHeaderProps {
  report: ReviewReport;
  activeView: 'workspace' | 'overview' | 'intelligence';
  onViewChange: (view: 'workspace' | 'overview' | 'intelligence') => void;
  onRefresh?: () => void;
}

export const ReviewHeader: React.FC<ReviewHeaderProps> = ({
  report,
  activeView,
  onViewChange,
  onRefresh,
}) => {
  const [copiedTrace, setCopiedTrace] = React.useState(false);

  const isSnippet = !report.repo_url || report.repo_url === 'snippet';
  const title = isSnippet
    ? (report.snippet_filename || 'snippet.py')
    : `${report.repo_url?.replace(/^https?:\/\/github\.com\//, '') || 'repo'} · PR #${report.pr_number || '1'}`;

  const filesCount = report.file_reports?.length || 1;
  const durationText = report.duration_seconds ? `completed in ${report.duration_seconds}s` : 'completed';

  const copyTrace = () => {
    if (!report.trace_id) return;
    navigator.clipboard.writeText(report.trace_id);
    setCopiedTrace(true);
    setTimeout(() => setCopiedTrace(false), 2000);
  };

  return (
    <div className="border-b border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0a0d14] px-4 sm:px-6 py-3 shrink-0">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Left Title & Status */}
        <div>
          <div className="flex items-center gap-3">
            {isSnippet ? (
              <Code2 className="w-5 h-5 text-blue-500 shrink-0" />
            ) : (
              <GitPullRequest className="w-5 h-5 text-blue-500 shrink-0" />
            )}
            <h1 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight font-mono">
              {title}
            </h1>
            <StatusBadge status="completed" />
          </div>

          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs font-mono text-slate-500">
            <span
              onClick={copyTrace}
              className="hover:text-slate-700 dark:hover:text-slate-300 cursor-pointer flex items-center gap-1"
              title="Click to copy trace ID"
            >
              trace_id: {report.trace_id}
              {copiedTrace ? (
                <Check className="w-3 h-3 text-emerald-500" />
              ) : (
                <Copy className="w-3 h-3 opacity-60" />
              )}
            </span>
            <span>·</span>
            <span>{filesCount} {filesCount === 1 ? 'file' : 'files'}</span>
            <span>·</span>
            <span>{durationText}</span>
          </div>
        </div>

        {/* Right View Switcher */}
        <div className="flex items-center gap-2">
          <div className="flex items-center p-0.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-900 text-xs font-medium">
            <button
              type="button"
              onClick={() => onViewChange('workspace')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-colors ${
                activeView === 'workspace'
                  ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-xs font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              <span>Workspace</span>
            </button>

            <button
              type="button"
              onClick={() => onViewChange('overview')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-colors ${
                activeView === 'overview'
                  ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-xs font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Overview</span>
            </button>

            {!isSnippet && (
              <button
                type="button"
                onClick={() => onViewChange('intelligence')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-colors ${
                  activeView === 'intelligence'
                    ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-xs font-semibold'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                <Network className="w-3.5 h-3.5" />
                <span>Repo Intel</span>
              </button>
            )}
          </div>

          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              className="p-1.5 rounded-md border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              title="Re-run review"
            >
              <RotateCw className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
