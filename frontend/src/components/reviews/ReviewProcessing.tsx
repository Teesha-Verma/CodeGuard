import React, { useEffect, useState } from 'react';
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
  Cpu,
} from 'lucide-react';

interface ReviewProcessingProps {
  reviewId: string;
  repoUrl?: string;
  prNumber?: number;
  onCompleted?: (report: ReviewReport) => void;
}

export const ReviewProcessing: React.FC<ReviewProcessingProps> = ({
  reviewId,
  repoUrl = 'Repository Review',
  prNumber,
  onCompleted,
}) => {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [statusMessage, setStatusMessage] = useState('Initializing review pipeline...');
  const [error, setError] = useState<string | null>(null);
  const [pollCount, setPollCount] = useState(0);

  // General pipeline stages for visual orientation (without fake percentages)
  const pipelineStages = [
    'Repository checkout and diff isolation',
    'AST parsing and heuristic rules',
    'Flake8, PyLint, and Bandit linters',
    'Control Flow Graph & cyclomatic analysis',
    'Dataflow graph & taint tracking',
    'Repository architecture & risk hotspots',
    'Gemini RAG vector retrieval (768-dim)',
    'Groq LLM reasoning (llama-3.3-70b-versatile)',
    'Invariant metrics calculation & synthesis',
  ];

  // Active stage estimate based on elapsed time without fake percentage numbers
  const currentStageIndex = Math.min(
    pipelineStages.length - 1,
    Math.floor(elapsedSeconds / 4)
  );

  // Elapsed timer
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Polling loop
  useEffect(() => {
    let isCancelled = false;

    async function poll() {
      if (isCancelled) return;

      try {
        const res = await apiClient.getReview(reviewId);

        if (res.status === 'completed') {
          updateStoredReview(reviewId, {
            status: 'completed',
            duration_seconds: elapsedSeconds,
            report: res.report,
          });
          onCompleted?.(res.report);
          return;
        }

        if (res.status === 'running') {
          if (res.message) setStatusMessage(res.message);
          updateStoredReview(reviewId, {
            status: 'running',
            duration_seconds: elapsedSeconds,
          });
        } else if (res.status === 'failed') {
          setError(res.error || 'Review pipeline failed during execution.');
          updateStoredReview(reviewId, {
            status: 'failed',
            error_message: res.error,
          });
          return;
        } else if (res.status === 'not_found') {
          // Keep polling for a brief grace period if just initiated
          if (pollCount > 8) {
            setError('Review was not found on backend.');
            return;
          }
        }
      } catch (err: unknown) {
        // Network warning without halting polling immediately
        console.warn('Polling notice:', err);
      }

      // Schedule next poll in 2.5s
      if (!isCancelled && !error) {
        setTimeout(() => {
          setPollCount((c) => c + 1);
        }, 2500);
      }
    }

    poll();

    return () => {
      isCancelled = true;
    };
  }, [reviewId, pollCount, error, elapsedSeconds, onCompleted]);

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

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs font-mono text-blue-600 dark:text-blue-400">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Running</span>
          </div>
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
                <div className="text-xs font-mono mt-1">{error}</div>
              </div>
            </div>
            <div className="flex items-center gap-3 pt-1">
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  setPollCount(0);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-red-600 text-white hover:bg-red-700"
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
                {pipelineStages.map((stage, idx) => {
                  const isDone = idx < currentStageIndex;
                  const isCurrent = idx === currentStageIndex;

                  return (
                    <div
                      key={stage}
                      className={`flex items-center gap-2.5 px-3 py-2 rounded text-xs font-mono transition-colors ${
                        isCurrent
                          ? 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/20 font-medium'
                          : isDone
                          ? 'text-slate-600 dark:text-slate-400 bg-slate-50/50 dark:bg-slate-900/20'
                          : 'text-slate-600 dark:text-slate-400'
                      }`}
                    >
                      {isDone ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                      ) : isCurrent ? (
                        <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin shrink-0" />
                      ) : (
                        <div className="w-3.5 h-3.5 rounded-full border border-slate-300 dark:border-slate-700 shrink-0" />
                      )}
                      <span className="truncate">{stage}</span>
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
          <span className="text-[11px] font-mono text-slate-600 dark:text-slate-400">
            LLM: llama-3.3-70b-versatile
          </span>
        </div>
      </div>
    </div>
  );
};
