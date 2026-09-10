import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { apiClient } from '@/lib/api/client';
import { getStoredReview, saveStoredReview, recordFromReport } from '@/lib/storage/reviews';
import { SAMPLE_REPORT_PR42 } from '@/lib/data/sampleReviews';
import { ReviewReport } from '@/types';
import { ReviewWorkspace } from '@/components/workspace/ReviewWorkspace';
import { ReviewProcessing } from '@/components/reviews/ReviewProcessing';
import {
  Loader2,
  AlertCircle,
  RotateCw,
} from 'lucide-react';

export default function ReviewDetailsPage() {
  const navigate = useNavigate();
  const { reviewId } = useParams<{ reviewId: string }>();

  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState<ReviewReport | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [repoUrl, setRepoUrl] = useState<string>('Repository Review');
  const [prNumber, setPrNumber] = useState<number | undefined>(undefined);

  const fetchReview = async () => {
    if (!reviewId) return;

    setLoading(true);
    setErrorMessage(null);

    // 1. Check local storage first
    const stored = getStoredReview(reviewId);
    if (stored) {
      if (stored.repo_url) setRepoUrl(stored.repo_url);
      if (stored.pr_number) setPrNumber(stored.pr_number);

      if (stored.report) {
        setReport(stored.report);
        setLoading(false);
        return;
      }

      if (stored.status === 'running' || stored.status === 'queued') {
        setIsProcessing(true);
        setLoading(false);
        return;
      }
    }

    // Special case for seed sample PR #42
    if (reviewId === 'rv_8f21ac') {
      setReport(SAMPLE_REPORT_PR42);
      saveStoredReview(recordFromReport(SAMPLE_REPORT_PR42));
      setLoading(false);
      return;
    }

    // 2. Fetch from backend API
    try {
      const res = await apiClient.getReview(reviewId);

      if (res.status === 'completed') {
        setReport(res.report);
        saveStoredReview(recordFromReport(res.report));
      } else if (res.status === 'running') {
        setIsProcessing(true);
      } else if (res.status === 'not_found') {
        // If not found in backend but in localStorage, check fallback
        if (stored?.report) {
          setReport(stored.report);
        } else {
          setErrorMessage('Review report not found on backend server.');
        }
      } else if (res.status === 'failed') {
        setErrorMessage(res.error || 'Review pipeline failed during execution.');
      }
    } catch (err: unknown) {
      if (stored?.report) {
        setReport(stored.report);
      } else {
        setErrorMessage(
          err instanceof Error ? err.message : 'Failed to connect to CodeGuard backend.'
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReview();
  }, [reviewId]);

  if (loading) {
    return (
      <AppShell>
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-[#f8fafc] dark:bg-[#0a0d14]">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-3" />
          <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            Loading review data...
          </h2>
          <p className="text-xs font-mono text-slate-500 mt-1">
            review_id: {reviewId}
          </p>
        </div>
      </AppShell>
    );
  }

  // Active Asynchronous Processing Screen
  if (isProcessing && reviewId) {
    return (
      <AppShell>
        <ReviewProcessing
          reviewId={reviewId}
          repoUrl={repoUrl}
          prNumber={prNumber}
          onCompleted={(completedReport) => {
            setReport(completedReport);
            setIsProcessing(false);
          }}
        />
      </AppShell>
    );
  }

  // Error State
  if (errorMessage && !report) {
    return (
      <AppShell>
        <div className="flex-1 flex flex-col items-center justify-center p-6 bg-[#f8fafc] dark:bg-[#0a0d14]">
          <div className="w-full max-w-md p-6 rounded-xl border border-red-500/20 bg-white dark:bg-[#0f141f] shadow-xs space-y-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Review Not Available
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">
                  {errorMessage}
                </p>
                <div className="text-[11px] font-mono text-slate-500 mt-1">
                  review_id: {reviewId}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2 border-t border-slate-200 dark:border-slate-800/80">
              <button
                type="button"
                onClick={fetchReview}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-blue-600 text-white hover:bg-blue-700 text-xs font-semibold"
              >
                <RotateCw className="w-3.5 h-3.5" />
                <span>Retry</span>
              </button>
              <Link
                to="/reviews"
                className="text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
              >
                Return to Reviews
              </Link>
            </div>
          </div>
        </div>
      </AppShell>
    );
  }

  // Completed State: 3-pane review workspace
  if (report) {
    return (
      <AppShell>
        <ReviewWorkspace report={report} onRefresh={fetchReview} />
      </AppShell>
    );
  }

  return null;
}
