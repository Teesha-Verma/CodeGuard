import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ReviewIssue, ReviewReport } from '@/types';
import { SeverityBadge, SourceBadge } from '@/components/common/Badges';
import { useActiveFinding } from '@/lib/context/ActiveFindingContext';
import {
  ExternalLink,
  ShieldCheck,
  EyeOff,
  GitCommit,
  CheckCircle2,
  ChevronRight,
  ArrowRight,
  Sparkles,
  Info,
  BookOpen,
  Bot,
  Code2,
  Terminal,
} from 'lucide-react';

interface FindingDetailsProps {
  filePath: string;
  issue: ReviewIssue | null;
  fileContent?: string;
  report?: ReviewReport | null;
  onResolve?: () => void;
  onSuppress?: () => void;
}

export const FindingDetails: React.FC<FindingDetailsProps> = ({
  filePath,
  issue,
  fileContent,
  report,
  onResolve,
  onSuppress,
}) => {
  const navigate = useNavigate();
  const { setActiveFinding } = useActiveFinding();
  const [resolved, setResolved] = useState(false);
  const [suppressed, setSuppressed] = useState(false);

  if (!issue) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-white dark:bg-[#0d111a]">
        <Info className="w-8 h-8 text-slate-300 dark:text-slate-700 mb-3" />
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
          No Finding Selected
        </h3>
        <p className="text-xs text-slate-500 max-w-xs mt-1">
          Select an issue from the list or click a highlighted line in the code viewer to inspect details.
        </p>
      </div>
    );
  }

  const confidencePct = issue.confidence
    ? (issue.confidence > 1 ? issue.confidence : issue.confidence * 100).toFixed(0)
    : '85';

  const isLlm =
    issue.reasoning_source === 'llm' ||
    (typeof issue.source === 'string' && issue.source.toLowerCase().includes('llm'));

  return (
    <div className="h-full flex flex-col bg-white dark:bg-[#0d111a] border-l border-slate-200 dark:border-slate-800/80 overflow-y-auto">
      {/* Top Badges Bar */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800/80 space-y-2.5">
        <div className="flex flex-wrap items-center gap-2">
          <SeverityBadge severity={issue.severity} size="sm" />
          <span className="text-xs font-medium px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700/60">
            {issue.category || issue.issue_type}
          </span>
          <span className="text-xs font-mono text-slate-500 flex items-center gap-1">
            {isLlm ? '✦ LLM reasoned' : '⚙ Static analysis'} · confidence {confidencePct}%
          </span>
        </div>

        {/* Title */}
        <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 leading-snug">
          {issue.issue}
        </h2>

        {/* File and Line Location */}
        <div className="text-xs font-mono text-slate-500">
          {filePath}:{issue.line}
        </div>

        {/* Contextual Capability Actions */}
        <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-100 dark:border-slate-800/60">
          <button
            type="button"
            onClick={() => {
              setActiveFinding(issue, filePath, fileContent || '', report);
              navigate('/learn');
            }}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400 border border-blue-200 dark:border-blue-800/80 hover:bg-blue-100 dark:hover:bg-blue-500/20 transition-colors cursor-pointer"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Learn Why</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setActiveFinding(issue, filePath, fileContent || '', report, 'Explain this finding in detail');
              navigate('/assistant');
            }}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium bg-purple-50 text-purple-700 dark:bg-purple-500/10 dark:text-purple-400 border border-purple-200 dark:border-purple-800/80 hover:bg-purple-100 dark:hover:bg-purple-500/20 transition-colors cursor-pointer"
          >
            <Bot className="w-3.5 h-3.5" />
            <span>Ask CodeGuard</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setActiveFinding(issue, filePath, fileContent || '', report);
              navigate('/playground');
            }}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/80 hover:bg-emerald-100 dark:hover:bg-emerald-500/20 transition-colors cursor-pointer"
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Fix This</span>
          </button>

          {(report?.review_id || (issue.dataflow_path && issue.dataflow_path.length > 0)) && (
            <button
              type="button"
              onClick={() => {
                setActiveFinding(issue, filePath, fileContent || '', report);
                navigate('/dataflow');
              }}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400 border border-amber-200 dark:border-amber-800/80 hover:bg-amber-100 dark:hover:bg-amber-500/20 transition-colors cursor-pointer"
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Show Data Flow</span>
            </button>
          )}
        </div>
      </div>

      {/* Details Sections */}
      <div className="flex-1 p-4 space-y-5 text-xs">
        {/* Reasoning / Root Cause */}
        <div>
          <h4 className="text-[11px] font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-1.5">
            Reasoning
          </h4>
          <p className="text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-900/40 p-3 rounded-md border border-slate-200 dark:border-slate-800/80 font-sans">
            {issue.root_cause || 'No detailed root cause explanation provided by analyzer.'}
          </p>
        </div>

        {/* Trigger Condition if present */}
        {issue.trigger_condition && (
          <div>
            <h4 className="text-[11px] font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-1">
              Trigger Condition
            </h4>
            <p className="text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
              {issue.trigger_condition}
            </p>
          </div>
        )}

        {/* Impact if present */}
        {issue.impact && (
          <div>
            <h4 className="text-[11px] font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-1">
              Impact
            </h4>
            <p className="text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
              {issue.impact}
            </p>
          </div>
        )}

        {/* Dataflow Path */}
        {issue.dataflow_path && issue.dataflow_path.length > 0 && (
          <div>
            <h4 className="text-[11px] font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">
              Dataflow path
            </h4>
            <div className="flex flex-wrap items-center gap-1.5 p-2.5 rounded-md bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 font-mono text-[11px] text-slate-800 dark:text-slate-200">
              {issue.dataflow_path.map((step, idx) => (
                <React.Fragment key={idx}>
                  <span className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    {step}
                  </span>
                  {idx < issue.dataflow_path!.length - 1 && (
                    <ArrowRight className="w-3 h-3 text-slate-400" />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        )}

        {/* Related Standards (CWE / OWASP) */}
        {issue.standards && issue.standards.length > 0 && (
          <div>
            <h4 className="text-[11px] font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-1.5">
              Related standards
            </h4>
            <div className="flex flex-wrap gap-1.5 font-mono text-[11px]">
              {issue.standards.map((std) => {
                const topicId = std.toLowerCase().includes('89')
                  ? 'sql-injection'
                  : std.toLowerCase().includes('78')
                  ? 'command-injection'
                  : std.toLowerCase().includes('502')
                  ? 'insecure-deserialization'
                  : std.toLowerCase().includes('918')
                  ? 'ssrf'
                  : std.toLowerCase().includes('22')
                  ? 'path-traversal'
                  : 'sql-injection';

                return (
                  <button
                    key={std}
                    type="button"
                    onClick={() => navigate(`/learn/academy?topic=${topicId}`)}
                    className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700/60 hover:border-blue-400 dark:hover:border-blue-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer"
                  >
                    {std} ↗
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Recommended Fix */}
        <div>
          <h4 className="text-[11px] font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-1.5">
            Recommended Fix
          </h4>
          <p className="text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
            {issue.fix || 'No automated fix specified.'}
          </p>
        </div>

        {/* Patch Diff */}
        {issue.patch && (
          <div>
            <h4 className="text-[11px] font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <GitCommit className="w-3.5 h-3.5 text-blue-500" />
              <span>Suggested Patch</span>
            </h4>
            <div className="rounded-md border border-slate-200 dark:border-slate-800/80 bg-slate-950 text-slate-100 font-mono text-[11px] p-2.5 overflow-x-auto leading-relaxed">
              {issue.patch.split('\n').map((patchLine, pidx) => {
                const isAdd = patchLine.startsWith('+');
                const isDel = patchLine.startsWith('-');
                const isHeader = patchLine.startsWith('@@');

                return (
                  <div
                    key={pidx}
                    className={`whitespace-pre ${
                      isAdd
                        ? 'text-emerald-400 bg-emerald-950/30'
                        : isDel
                        ? 'text-rose-400 bg-rose-950/30'
                        : isHeader
                        ? 'text-blue-400'
                        : 'text-slate-300'
                    }`}
                  >
                    {patchLine}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Detection Sources */}
        {issue.detection_sources && issue.detection_sources.length > 0 && (
          <div>
            <h4 className="text-[11px] font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-1.5">
              Detection Sources
            </h4>
            <div className="flex flex-wrap gap-1">
              {issue.detection_sources.map((src) => (
                <span
                  key={src}
                  className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700"
                >
                  {src}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Action Footer matching Screenshot 4 */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800/80 flex items-center justify-between bg-slate-50/50 dark:bg-[#0b0e16]/50 shrink-0">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              setResolved(!resolved);
              onResolve?.();
            }}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              resolved
                ? 'bg-emerald-600 text-white'
                : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            {resolved ? 'Resolved' : 'Mark resolved'}
          </button>

          <button
            type="button"
            onClick={() => {
              setSuppressed(!suppressed);
              onSuppress?.();
            }}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              suppressed
                ? 'bg-slate-600 text-white'
                : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            {suppressed ? 'Suppressed' : 'Suppress'}
          </button>
        </div>

        <button
          type="button"
          onClick={() => {
            alert(`Opening target file ${filePath} at line ${issue.line}`);
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          <span>Open in GitHub</span>
        </button>
      </div>
    </div>
  );
};
