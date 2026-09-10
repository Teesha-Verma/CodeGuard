import React from 'react';
import { ReviewReport, ReviewIssue } from '@/types';
import { SeverityBadge, SourceBadge } from '@/components/common/Badges';
import { ArrowDown, CheckCircle2 } from 'lucide-react';

interface ExecutiveOverviewProps {
  report: ReviewReport;
  onSelectFinding?: (filePath: string, issue: ReviewIssue) => void;
}

export const ExecutiveOverview: React.FC<ExecutiveOverviewProps> = ({
  report,
  onSelectFinding,
}) => {
  const stats = report.summary_stats || {
    total_issues: 0,
    meaningful_issues: 0,
    style_findings: 0,
    suppressed_findings: 0,
    by_severity: { critical: 0, high: 0, medium: 0, low: 0, info: 0 },
    by_source: { llm: 0, static_analysis: 0 },
  };

  const totalIssues = stats.total_issues ?? 0;
  const meaningfulIssues = stats.meaningful_issues ?? stats.total_issues ?? 0;
  const styleFindings = stats.style_findings ?? 0;
  const suppressedFindings = stats.suppressed_findings ?? 0;

  const sev = stats.by_severity || { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
  const maxSev = Math.max(1, sev.critical, sev.high, sev.medium, sev.low, sev.info);

  const llmCount = stats.by_source?.llm ?? stats.reasoning_sources?.llm ?? 0;
  const staticCount = stats.by_source?.static_analysis ?? stats.reasoning_sources?.static_analysis ?? 0;
  const maxReasoning = Math.max(1, llmCount + staticCount);

  // Flatten all issues for table display
  const allIssues: Array<{ filePath: string; issue: ReviewIssue }> = [];
  if (Array.isArray(report?.file_reports)) {
    report.file_reports.forEach((fr) => {
      if (Array.isArray(fr?.issues)) {
        fr.issues.forEach((iss) => {
          allIssues.push({ filePath: fr.file_path, issue: iss });
        });
      }
    });
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto py-2">
      {/* 4 Primary Metric Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-5 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f]">
        <div>
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Total issues
          </div>
          <div className="mt-1 text-3xl font-bold text-slate-900 dark:text-slate-100 tracking-tight font-mono">
            {totalIssues}
          </div>
        </div>
        <div>
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Meaningful
          </div>
          <div className="mt-1 text-3xl font-bold text-slate-900 dark:text-slate-100 tracking-tight font-mono">
            {meaningfulIssues}
          </div>
        </div>
        <div>
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Style findings
          </div>
          <div className="mt-1 text-3xl font-bold text-slate-900 dark:text-slate-100 tracking-tight font-mono text-slate-500">
            {styleFindings}
          </div>
        </div>
        <div>
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Suppressed
          </div>
          <div className="mt-1 text-3xl font-bold text-slate-900 dark:text-slate-100 tracking-tight font-mono text-slate-500">
            {suppressedFindings}
          </div>
        </div>
      </div>

      {/* Breakdowns Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Severity Breakdown */}
        <div className="p-5 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f] space-y-3">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Severity breakdown
          </h3>
          <div className="space-y-2.5 pt-1">
            {[
              { label: 'Critical', count: sev.critical, color: 'bg-red-500' },
              { label: 'High', count: sev.high, color: 'bg-orange-500' },
              { label: 'Medium', count: sev.medium, color: 'bg-blue-500' },
              { label: 'Low', count: sev.low, color: 'bg-emerald-500' },
              { label: 'Info', count: sev.info, color: 'bg-slate-400' },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-3 text-xs">
                <span className="w-16 font-medium text-slate-600 dark:text-slate-400">
                  {item.label}
                </span>
                <div className="flex-1 h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${item.color}`}
                    style={{ width: `${(item.count / maxSev) * 100}%` }}
                  />
                </div>
                <span className="w-6 text-right font-mono font-medium text-slate-700 dark:text-slate-300">
                  {item.count}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Reasoning Source */}
        <div className="p-5 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f] space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Reasoning source
            </h3>
            <span className="text-[11px] font-mono text-slate-500">
              llama-3.3-70b-versatile
            </span>
          </div>
          <div className="space-y-3 pt-1">
            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  LLM reasoned
                </span>
                <span className="font-mono font-medium text-slate-900 dark:text-slate-100">
                  {llmCount}
                </span>
              </div>
              <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-blue-600"
                  style={{ width: `${(llmCount / maxReasoning) * 100}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Static analysis
                </span>
                <span className="font-mono font-medium text-slate-900 dark:text-slate-100">
                  {staticCount}
                </span>
              </div>
              <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-slate-400 dark:bg-slate-600"
                  style={{ width: `${(staticCount / maxReasoning) * 100}%` }}
                />
              </div>
            </div>

            <div className="pt-2 text-[11px] text-slate-500 font-mono">
              Model: llama-3.3-70b-versatile · 0 fallbacks invoked
            </div>
          </div>
        </div>
      </div>

      {/* Findings Table Preview */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Detected Findings ({allIssues.length})
          </h3>
        </div>

        <div className="border border-slate-200 dark:border-slate-800/80 rounded-lg overflow-hidden bg-white dark:bg-[#0f141f]">
          <div className="grid grid-cols-12 gap-2 px-4 py-2.5 bg-slate-50 dark:bg-slate-900/60 border-b border-slate-200 dark:border-slate-800/80 text-[11px] font-medium text-slate-500 uppercase tracking-wider">
            <div className="col-span-2">Severity</div>
            <div className="col-span-3">Category</div>
            <div className="col-span-5">Finding</div>
            <div className="col-span-2 text-right">Source</div>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {allIssues.map(({ filePath, issue }, idx) => (
              <div
                key={`${filePath}-${issue.line}-${idx}`}
                onClick={() => onSelectFinding?.(filePath, issue)}
                className="grid grid-cols-12 gap-2 px-4 py-3 items-center hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer transition-colors text-xs"
              >
                <div className="col-span-2">
                  <SeverityBadge severity={issue.severity} size="sm" />
                </div>
                <div className="col-span-3 font-medium text-slate-700 dark:text-slate-300 truncate">
                  {issue.category || issue.issue_type}
                </div>
                <div className="col-span-5 font-mono text-slate-900 dark:text-slate-200 truncate">
                  <span className="text-slate-500">{filePath}:{issue.line} · </span>
                  <span className="font-sans font-medium text-slate-800 dark:text-slate-100">
                    {issue.issue}
                  </span>
                </div>
                <div className="col-span-2 text-right">
                  <SourceBadge source={issue.source} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
