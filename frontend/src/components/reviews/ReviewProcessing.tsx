import React, { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '@/lib/api/client';
import { updateStoredReview } from '@/lib/storage/reviews';
import { ReviewReport } from '@/types';
import {
  Loader2,
  Clock,
  GitPullRequest,
  AlertCircle,
  RotateCw,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Ban,
} from 'lucide-react';

interface ReviewProcessingProps {
  reviewId: string;
  repoUrl?: string;
  prNumber?: number;
  onCompleted?: (report: ReviewReport) => void;
}

type ReviewStatus = 'queued' | 'processing' | 'running' | 'completed' | 'failed' | 'cancelled' | 'timed_out';

const PIPELINE_STAGES = [
  { key: 'github_pr_resolution', label: 'GitHub PR metadata & branch resolution' },
  { key: 'git_clone_and_checkout', label: 'PR diff isolation & repository checkout' },
  { key: 'diff_parsing_and_scope_filter', label: 'Diff parsing & exact PR scope enforcement' },
  { key: 'repository_supporting_context', label: 'Supporting context & repository architecture' },
  { key: 'primary_file_static_analysis', label: 'Deterministic static analyzers & AI reasoning' },
  { key: 'metrics_synthesis', label: 'Invariant metrics calculation & synthesis' },
  { key: 'report_persistence', label: 'Report persistence & database indexing' },
];

export const ReviewProcessing: React.FC<ReviewProcessingProps> = ({
  reviewId,
  repoUrl = 'Repository Review',
  prNumber,
  onCompleted,
}) => {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [statusMessage, setStatusMessage] = useState('Connecting to review pipeline...');
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus>('processing');
  const [currentStageKey, setCurrentStageKey] = useState<string>('github_pr_resolution');
  const [error, setError] = useState<string | null>(null);
  const [retryTrigger, setRetryTrigger] = useState(0);

  const isTerminal = reviewStatus === 'completed' || reviewStatus === 'failed' || reviewStatus === 'cancelled' || reviewStatus === 'timed_out' || !!error;

  // 1. Elapsed timer - halts immediately once a terminal state is reached
  useEffect(() => {
    if (isTerminal) return;

    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [isTerminal]);

  // 2. Single Polling Loop with progressive backoff and AbortController
  const onCompletedRef = useRef(onCompleted);
  onCompletedRef.current = onCompleted;

  useEffect(() => {
    let isCancelled = false;
    let timeoutId: NodeJS.Timeout | null = null;
    const controller = new AbortController();

    async function poll() {
      if (isCancelled) return;

      try {
        // Use lightweight status endpoint (<10ms)
        const statusRes = await apiClient.getReviewStatus(reviewId, controller.signal);

        if (isCancelled) return;

        const rawStatus = (statusRes.status || 'processing').toLowerCase() as ReviewStatus;

        if (rawStatus === 'completed') {
          setReviewStatus('completed');
          setStatusMessage('Review complete. Loading report...');
          setCurrentStageKey('completed');

          // Fetch complete report once
          const reportRes = await apiClient.getReview(reviewId, controller.signal);
          if (reportRes.status === 'completed') {
            updateStoredReview(reviewId, {
              status: 'completed',
              duration_seconds: statusRes.duration_seconds || elapsedSeconds,
              report: reportRes.report,
            });
            onCompletedRef.current?.(reportRes.report);
            return;
          }
        } else if (rawStatus === 'failed') {
          const errMsg = statusRes.error_message || statusRes.message || 'Review pipeline failed during execution.';
          setReviewStatus('failed');
          setError(errMsg);
          updateStoredReview(reviewId, {
            status: 'failed',
            error_message: errMsg,
          });
          return;
        } else if (rawStatus === 'timed_out') {
          const errMsg = statusRes.error_message || 'Review execution timed out.';
          setReviewStatus('timed_out');
          setError(errMsg);
          updateStoredReview(reviewId, {
            status: 'failed',
            error_message: errMsg,
          });
          return;
        } else if (rawStatus === 'cancelled') {
          setReviewStatus('cancelled');
          setError('Review was cancelled.');
          updateStoredReview(reviewId, {
            status: 'failed',
            error_message: 'Review was cancelled.',
          });
          return;
        } else {
          // 'queued', 'processing', 'running'
          setReviewStatus(rawStatus);
          if (statusRes.message) setStatusMessage(statusRes.message);
          if (statusRes.stage) setCurrentStageKey(statusRes.stage);

          updateStoredReview(reviewId, {
            status: 'running',
            duration_seconds: statusRes.duration_seconds || elapsedSeconds,
          });
        }
      } catch (err: unknown) {
        if (isCancelled) return;
        if (err instanceof DOMException && err.name === 'AbortError') return;

        // Fallback: try standard getReview endpoint if status endpoint has unexpected issue
        try {
          const fallbackRes = await apiClient.getReview(reviewId, controller.signal);
          if (fallbackRes.status === 'completed') {
            setReviewStatus('completed');
            updateStoredReview(reviewId, {
              status: 'completed',
              report: fallbackRes.report,
            });
            onCompletedRef.current?.(fallbackRes.report);
            return;
          } else if (fallbackRes.status === 'failed') {
            setReviewStatus('failed');
            setError(fallbackRes.error || 'Review pipeline failed.');
            return;
          }
        } catch {
          // Keep polling softly
        }
      }

      // Progressive backoff interval:
      // 0 - 30s: 2.5s
      // 30 - 90s: 4.0s
      // 90s+: 6.0s
      const delay = elapsedSeconds < 30 ? 2500 : elapsedSeconds < 90 ? 4000 : 6000;

      if (!isCancelled) {
        timeoutId = setTimeout(poll, delay);
      }
    }

    poll();

    return () => {
      isCancelled = true;
      controller.abort();
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [reviewId, retryTrigger]);

  const activeStageIndex = Math.max(
    0,
    PIPELINE_STAGES.findIndex((s) => s.key === currentStageKey)
  );

  const handleRetry = () => {
    setError(null);
    setReviewStatus('processing');
    setStatusMessage('Re-checking review pipeline status...');
    setRetryTrigger((prev) => prev + 1);
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 bg-[#f8fafc] dark:bg-[#0a0d14]">
      <div className="w-full max-w-xl p-6 sm:p-8 rounded-xl border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f] shadow-xs space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
              <GitPullRequest className="w-4 h-4 text-blue-500" />
              <span>{prNumber ? `PR #${prNumber}` : 'Snippet analysis'}</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-1 font-mono">
              {repoUrl.replace(/^https?:\/\/github\.com\//, '')}
            </h2>
            <div className="text-xs font-mono text-slate-500 mt-0.5">
              review_id: {reviewId}
            </div>
          </div>

          {/* Honest Status Badge */}
          {error || reviewStatus === 'failed' || reviewStatus === 'timed_out' ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-xs font-mono text-red-600 dark:text-red-400">
              <XCircle className="w-3.5 h-3.5" />
              <span>Failed</span>
            </div>
          ) : reviewStatus === 'completed' ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-mono text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Completed</span>
            </div>
          ) : reviewStatus === 'cancelled' ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-500/10 border border-slate-500/20 text-xs font-mono text-slate-600 dark:text-slate-400">
              <Ban className="w-3.5 h-3.5" />
              <span>Cancelled</span>
            </div>
          ) : reviewStatus === 'queued' ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-xs font-mono text-amber-600 dark:text-amber-400">
              <Clock className="w-3.5 h-3.5" />
              <span>Queued</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs font-mono text-blue-600 dark:text-blue-400">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Running</span>
            </div>
          )}
        </div>

        {/* Error Notification if failed */}
        {error ? (
          <div className="p-4 rounded-lg border border-red-500/20 bg-red-500/10 text-red-700 dark:text-red-400 space-y-3">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
              <div>
                <div className="text-xs font-bold uppercase tracking-wider">
                  Analysis Pipeline Halted
                </div>
                <div className="text-xs font-mono mt-1 leading-relaxed">{error}</div>
              </div>
            </div>
            <div className="flex items-center gap-3 pt-1">
              <button
                type="button"
                onClick={handleRetry}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-red-600 text-white hover:bg-red-700 transition-colors"
              >
                <RotateCw className="w-3.5 h-3.5" />
                <span>Retry Connection</span>
              </button>
              <Link
                to="/"
                className="text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
              >
                Return to Dashboard
              </Link>
            </div>
          </div>
        ) : (
          <>
            {/* Live Progress Telemetry */}
            <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800/80 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-500">Pipeline Status:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {statusMessage}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-500">Elapsed Time:</span>
                <span className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  {elapsedSeconds}s
                </span>
              </div>
            </div>

            {/* Pipeline Stage Architecture Tracker */}
            <div className="space-y-2">
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                Execution Pipeline
              </div>
              <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                {PIPELINE_STAGES.map((stage, idx) => {
                  const isDone = idx < activeStageIndex || reviewStatus === 'completed';
                  const isCurrent = idx === activeStageIndex && reviewStatus !== 'completed';

                  return (
                    <div
                      key={stage.key}
                      className={`flex items-center gap-2.5 px-3 py-2 rounded text-xs font-mono transition-colors ${
                        isCurrent
                          ? 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/20 font-medium'
                          : isDone
                          ? 'text-slate-600 dark:text-slate-400 bg-slate-50/50 dark:bg-slate-900/20'
                          : 'text-slate-500 dark:text-slate-500'
                      }`}
                    >
                      {isDone ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                      ) : isCurrent ? (
                        <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin shrink-0" />
                      ) : (
                        <div className="w-3.5 h-3.5 rounded-full border border-slate-300 dark:border-slate-700 shrink-0" />
                      )}
                      <span className="truncate">{stage.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {/* Footer Navigation */}
        <div className="pt-2 border-t border-slate-200 dark:border-slate-800/80 flex items-center justify-between">
          <Link
            to="/"
            className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 font-medium"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
          <span className="text-[11px] font-mono text-slate-500">
            LLM: Groq primary (Gemini fallback)
          </span>
        </div>
      </div>
    </div>
  );
};
