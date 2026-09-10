import React, { useState, useMemo } from 'react';
import { ReviewReport, ReviewIssue, Severity } from '@/types';
import { SeverityBadge, SourceBadge } from '@/components/common/Badges';
import { Search, Filter, SlidersHorizontal } from 'lucide-react';

interface FindingListProps {
  report: ReviewReport;
  selectedFilePath: string;
  selectedIssue: ReviewIssue | null;
  onSelectIssue: (filePath: string, issue: ReviewIssue) => void;
  mode: 'meaningful' | 'style' | 'suppressed';
  onModeChange: (mode: 'meaningful' | 'style' | 'suppressed') => void;
}

export const FindingList: React.FC<FindingListProps> = ({
  report,
  selectedFilePath,
  selectedIssue,
  onSelectIssue,
  mode,
  onModeChange,
}) => {
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Collect all issues across all files
  const items = useMemo(() => {
    const list: Array<{ filePath: string; issue: ReviewIssue }> = [];

    if (Array.isArray(report?.file_reports)) {
      report.file_reports.forEach((fr) => {
        if (Array.isArray(fr?.issues)) {
          fr.issues.forEach((iss) => {
        const isLowSignal =
          iss.issue_type === 'style' ||
          iss.severity === 'info' ||
          iss.issue.toLowerCase().includes('style') ||
          iss.issue.toLowerCase().includes('whitespace') ||
          iss.issue.toLowerCase().includes('docstring');

        const isSuppressed = (iss.confidence ?? 1) < 0.3;

        if (mode === 'style' && !isLowSignal) return;
        if (mode === 'suppressed' && !isSuppressed) return;
        if (mode === 'meaningful' && (isLowSignal || isSuppressed)) return;

        // Apply severity filter
        if (severityFilter !== 'all' && iss.severity !== severityFilter) {
          return;
        }

        // Apply search query
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const match =
            iss.issue.toLowerCase().includes(q) ||
            (iss.category && iss.category.toLowerCase().includes(q)) ||
            fr.file_path.toLowerCase().includes(q) ||
            String(iss.line).includes(q);
          if (!match) return;
        }

        list.push({ filePath: fr.file_path, issue: iss });
          });
        }
      });
    }

    return list;
  }, [report, mode, severityFilter, searchQuery]);

  const stats = report.summary_stats || {
    meaningful_issues: 0,
    style_findings: 0,
    suppressed_findings: 0,
  };

  const meaningfulCount = stats.meaningful_issues ?? stats.total_issues ?? 0;
  const styleCount = stats.style_findings ?? 0;
  const suppressedCount = stats.suppressed_findings ?? 0;

  return (
    <div className="h-full flex flex-col bg-white dark:bg-[#0c1017] border-r border-slate-200 dark:border-slate-800/80">
      {/* Category Mode Switcher */}
      <div className="p-2.5 border-b border-slate-200 dark:border-slate-800/80 bg-slate-50 dark:bg-[#0e131d]">
        <div className="flex items-center gap-1 p-0.5 rounded bg-slate-200/70 dark:bg-slate-800 text-[11px] font-medium">
          <button
            type="button"
            onClick={() => onModeChange('meaningful')}
            className={`flex-1 py-1 rounded transition-colors ${
              mode === 'meaningful'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Meaningful ({meaningfulCount})
          </button>
          <button
            type="button"
            onClick={() => onModeChange('style')}
            className={`flex-1 py-1 rounded transition-colors ${
              mode === 'style'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Style ({styleCount})
          </button>
          <button
            type="button"
            onClick={() => onModeChange('suppressed')}
            className={`flex-1 py-1 rounded transition-colors ${
              mode === 'suppressed'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Suppressed ({suppressedCount})
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-2.5 border-b border-slate-200 dark:border-slate-800/80 space-y-2">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 w-3.5 h-3.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search findings..."
            className="w-full pl-8 pr-3 py-1.5 text-xs rounded bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Severity Filter Pills */}
        <div className="flex flex-wrap gap-1 text-[11px] font-mono">
          {['all', 'critical', 'high', 'medium', 'low'].map((sev) => (
            <button
              key={sev}
              type="button"
              onClick={() => setSeverityFilter(sev)}
              className={`px-2 py-0.5 rounded capitalize transition-colors ${
                severityFilter === sev
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Findings List */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/60">
        {items.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500">
            No findings match current filter criteria.
          </div>
        ) : (
          items.map(({ filePath, issue }, idx) => {
            const isSelected =
              selectedIssue === issue ||
              (selectedFilePath === filePath &&
                selectedIssue?.line === issue.line &&
                selectedIssue?.issue === issue.issue);

            return (
              <div
                key={`${filePath}-${issue.line}-${idx}`}
                onClick={() => onSelectIssue(filePath, issue)}
                className={`p-3 cursor-pointer transition-colors ${
                  isSelected
                    ? 'bg-blue-50/80 dark:bg-blue-950/30 border-l-2 border-l-blue-600'
                    : 'hover:bg-slate-50 dark:hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-1.5">
                    <SeverityBadge severity={issue.severity} size="sm" />
                    <span className="text-[11px] font-medium text-slate-600 dark:text-slate-400 truncate max-w-[120px]">
                      {issue.category || issue.issue_type}
                    </span>
                  </div>
                  <SourceBadge source={issue.source} />
                </div>

                <div className="text-xs font-medium text-slate-900 dark:text-slate-100 leading-snug line-clamp-2">
                  {issue.issue}
                </div>

                <div className="mt-1.5 flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <span className="truncate max-w-[170px]" title={filePath}>
                    {filePath.split('/').pop()}
                  </span>
                  <span>L{issue.line}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
