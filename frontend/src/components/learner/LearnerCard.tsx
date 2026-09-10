import React, { useState, useEffect } from 'react';
import { ReviewIssue } from '@/types';
import { SeverityBadge } from '@/components/common/Badges';
import { MiniQuiz } from '@/components/learner/MiniQuiz';
import { getTopicByCwe, SECURITY_TOPICS } from '@/lib/data/securityKnowledge';
import { apiClient, LearnerFindingResponse } from '@/lib/api/client';
import {
  BookOpen,
  AlertTriangle,
  Code2,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  GitCommit,
  Terminal,
  Cpu,
  BookmarkCheck,
  Sparkles,
} from 'lucide-react';

interface LearnerCardProps {
  issue: ReviewIssue;
  filePath: string;
  onFixInPlayground?: () => void;
  onShowDataflow?: () => void;
  onAskAssistant?: () => void;
}

export const LearnerCard: React.FC<LearnerCardProps> = ({
  issue,
  filePath,
  onFixInPlayground,
  onShowDataflow,
  onAskAssistant,
}) => {
  const [backendLesson, setBackendLesson] = useState<LearnerFindingResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .learnFinding({
        file_path: filePath,
        line: issue.line,
        issue_text: issue.issue,
        category: issue.category,
      })
      .then((data) => {
        if (!cancelled && data) {
          setBackendLesson(data);
        }
      })
      .catch(() => {
        // Fall back gracefully to local curriculum
      });

    return () => {
      cancelled = true;
    };
  }, [filePath, issue.line, issue.issue]);

  // Find associated topic by CWE or keyword
  const cwe = issue.standards?.[0] || issue.issue || 'sql-injection';
  const topic =
    getTopicByCwe(cwe) ||
    SECURITY_TOPICS.find((t) =>
      issue.issue.toLowerCase().includes(t.category.toLowerCase()) ||
      issue.issue.toLowerCase().includes('sql') ||
      issue.issue.toLowerCase().includes('command')
    ) ||
    SECURITY_TOPICS[0];

  const activeQuiz = backendLesson?.quiz
    ? {
        question: backendLesson.quiz.question,
        options: backendLesson.quiz.options,
        correctIndex: backendLesson.quiz.correct_index ?? backendLesson.quiz.correct_option ?? 0,
        explanation: backendLesson.quiz.explanation,
      }
    : topic.quiz;

  return (
    <div className="space-y-6">
      {/* Top Finding Header */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 sm:p-6 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <SeverityBadge severity={issue.severity} size="sm" />
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
              {topic.cwe} · {topic.owasp}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {onFixInPlayground && (
              <button
                type="button"
                onClick={onFixInPlayground}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400 border border-blue-200 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-500/20 transition-colors"
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>Fix in Playground</span>
              </button>
            )}
            {onShowDataflow && issue.dataflow_path && issue.dataflow_path.length > 0 && (
              <button
                type="button"
                onClick={onShowDataflow}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium bg-purple-50 text-purple-700 dark:bg-purple-500/10 dark:text-purple-400 border border-purple-200 dark:border-purple-800 hover:bg-purple-100 dark:hover:bg-purple-500/20 transition-colors"
              >
                <Terminal className="w-3.5 h-3.5" />
                <span>Show Dataflow</span>
              </button>
            )}
          </div>
        </div>

        <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100 leading-snug">
          {issue.issue}
        </h2>

        <div className="mt-2 text-xs font-mono text-slate-500 flex items-center gap-2">
          <span>Target: {filePath}:{issue.line}</span>
          <span>·</span>
          <span>Source: {issue.source}</span>
          <span>·</span>
          <span>Confidence: {((issue.confidence || 0.85) * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Educational Modules */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Module 1: The Core Security Concept */}
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 sm:p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2 text-blue-600 dark:text-blue-400">
              <BookOpen className="w-4 h-4" />
              <h3 className="text-xs font-mono uppercase tracking-wider font-bold">
                1. The Security Concept
              </h3>
            </div>
            <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-1.5">
              <span>{backendLesson?.concept_title || topic.title}</span>
              {backendLesson && (
                <span className="inline-flex items-center gap-0.5 text-[10px] font-mono px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
                  <Sparkles className="w-2.5 h-2.5" />
                  AI Grounded
                </span>
              )}
            </h4>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              {backendLesson?.concept_summary || topic.summary}
            </p>
            <div className="mt-4 p-3 rounded bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300">
              <span className="font-semibold block mb-1 text-[11px] font-mono text-slate-500">
                WHY IT MATTERS
              </span>
              <p className="text-[11.5px] leading-relaxed">{backendLesson?.why_it_matters || topic.whyItMatters}</p>
            </div>
          </div>
        </div>

        {/* Module 2: What Happened in YOUR Code */}
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 sm:p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2 text-amber-600 dark:text-amber-400">
              <AlertTriangle className="w-4 h-4" />
              <h3 className="text-xs font-mono uppercase tracking-wider font-bold">
                2. What Happened in Your Code
              </h3>
            </div>
            <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2">
              Specific Root Cause Breakdown
            </h4>
            <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 p-3 rounded-md">
              {backendLesson?.what_happened_in_code ||
                issue.root_cause ||
                'Unvalidated input flows directly into sensitive execution logic without safe parameterization.'}
            </p>

            {(backendLesson?.impact || issue.impact) && (
              <div className="mt-3 p-3 rounded bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300">
                <span className="font-semibold block mb-0.5 text-[11px] font-mono text-slate-500">
                  REAL-WORLD IMPACT
                </span>
                <p className="text-[11.5px] leading-relaxed">{backendLesson?.impact || issue.impact}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Module 3: Why CodeGuard Detected It & Dataflow Evidence */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 sm:p-6 shadow-xs">
        <div className="flex items-center gap-2 mb-3 text-slate-900 dark:text-slate-100">
          <Cpu className="w-4 h-4 text-blue-500" />
          <h3 className="text-xs font-mono uppercase tracking-wider font-bold">
            3. Why CodeGuard Detected It (Detection Chain)
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-3 rounded bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
            <span className="text-[10px] font-mono uppercase text-slate-500 font-bold block mb-1">
              Deterministic AST Check
            </span>
            <p className="text-slate-600 dark:text-slate-400 text-[11.5px] leading-relaxed">
              {topic.codeguardDetection.astRule}
            </p>
          </div>

          <div className="p-3 rounded bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
            <span className="text-[10px] font-mono uppercase text-slate-500 font-bold block mb-1">
              Taint Propagation Trace
            </span>
            <p className="text-slate-600 dark:text-slate-400 text-[11.5px] leading-relaxed">
              {topic.codeguardDetection.taintBehavior}
            </p>
          </div>

          <div className="p-3 rounded bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
            <span className="text-[10px] font-mono uppercase text-slate-500 font-bold block mb-1">
              Grounded Reasoning Verification
            </span>
            <p className="text-slate-600 dark:text-slate-400 text-[11.5px] leading-relaxed">
              {topic.codeguardDetection.reasoningPattern}
            </p>
          </div>
        </div>

        {/* Dataflow visualization trace snippet */}
        {issue.dataflow_path && issue.dataflow_path.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            <span className="text-[10px] font-mono uppercase text-slate-500 tracking-wider block mb-2 font-bold">
              Detected Taint Flow Path
            </span>
            <div className="flex flex-wrap items-center gap-1.5 p-3 rounded-md bg-slate-950 text-slate-100 font-mono text-[11px] overflow-x-auto">
              {issue.dataflow_path.map((step, idx) => (
                <React.Fragment key={idx}>
                  <span
                    className={`px-2 py-0.5 rounded border ${
                      idx === 0
                        ? 'bg-amber-950/60 border-amber-600 text-amber-300'
                        : idx === issue.dataflow_path!.length - 1
                        ? 'bg-rose-950/60 border-rose-600 text-rose-300 font-semibold'
                        : 'bg-slate-800 border-slate-700 text-slate-300'
                    }`}
                  >
                    {step}
                  </span>
                  {idx < issue.dataflow_path!.length - 1 && (
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Module 4: Safer Implementation */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 sm:p-6 shadow-xs">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
            <ShieldCheck className="w-4 h-4" />
            <h3 className="text-xs font-mono uppercase tracking-wider font-bold">
              4. Safer Implementation &amp; Fix
            </h3>
          </div>
          {onFixInPlayground && (
            <button
              type="button"
              onClick={onFixInPlayground}
              className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
            >
              <span>Test fix in playground</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          )}
        </div>

        <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed mb-3">
          {backendLesson?.safer_implementation || issue.fix || topic.preventiveGuidelines[0]}
        </p>

        {issue.patch ? (
          <div className="rounded-md bg-slate-950 text-slate-100 font-mono text-[11px] p-3 overflow-x-auto leading-relaxed border border-slate-800">
            <div className="text-slate-500 text-[10px] pb-1 border-b border-slate-800 mb-2">
              # Remediation Patch Diff
            </div>
            {issue.patch.split('\n').map((line, lidx) => (
              <div
                key={lidx}
                className={
                  line.startsWith('+')
                    ? 'text-emerald-400 bg-emerald-950/30 px-1 rounded'
                    : line.startsWith('-')
                    ? 'text-rose-400 bg-rose-950/30 px-1 rounded'
                    : line.startsWith('@@')
                    ? 'text-blue-400'
                    : 'text-slate-300'
                }
              >
                {line}
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-md bg-slate-950 text-slate-100 font-mono text-[11px] p-3 overflow-x-auto leading-relaxed border border-slate-800">
            <div className="text-slate-500 text-[10px] pb-1 border-b border-slate-800 mb-2">
              # Recommended Secure Pattern
            </div>
            <pre className="text-emerald-300">{topic.secureExample}</pre>
          </div>
        )}
      </div>

      {/* Module 5: Key Takeaways to Remember */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 sm:p-6 shadow-xs">
        <div className="flex items-center gap-2 mb-3 text-slate-900 dark:text-slate-100">
          <BookmarkCheck className="w-4 h-4 text-blue-500" />
          <h3 className="text-xs font-mono uppercase tracking-wider font-bold">
            5. Key Takeaways &amp; Preventative Rules
          </h3>
        </div>

        <ul className="space-y-2 text-xs text-slate-700 dark:text-slate-300">
          {(backendLesson?.key_takeaways && backendLesson.key_takeaways.length > 0
            ? backendLesson.key_takeaways
            : topic.preventiveGuidelines
          ).map((guide: string, gidx: number) => (
            <li key={gidx} className="flex items-start gap-2.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{guide}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Module 6: Interactive Knowledge Check Quiz */}
      <MiniQuiz quiz={activeQuiz} />
    </div>
  );
};
