import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { getStoredReviews } from '@/lib/storage/reviews';
import { apiClient, DashboardStatsResponse } from '@/lib/api/client';
import { StoredReviewRecord } from '@/types';
import { StatusBadge } from '@/components/common/Badges';
import {
  GitPullRequest,
  Code2,
  ShieldCheck,
  AlertTriangle,
  Clock,
  ArrowRight,
  Plus,
  RefreshCw,
} from 'lucide-react';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [reviews, setReviews] = useState<StoredReviewRecord[]>([]);
  const [stats, setStats] = useState<DashboardStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const loadReviews = async () => {
    setLoading(true);
    const local = getStoredReviews();
    setReviews(local);

    try {
      const [backendStats, remoteReviews] = await Promise.allSettled([
        apiClient.getDashboardStats(),
        apiClient.listReviews(),
      ]);

      if (backendStats.status === 'fulfilled' && backendStats.value) {
        setStats(backendStats.value);
      }

      if (remoteReviews.status === 'fulfilled' && remoteReviews.value?.reviews) {
        const map = new Map<string, StoredReviewRecord>();
        local.forEach((r) => map.set(r.review_id, r));
        remoteReviews.value.reviews.forEach((r) =>
          map.set(r.review_id, {
            review_id: r.review_id,
            type: r.type,
            repo_url: r.repo_url,
            pr_number: r.pr_number,
            filename: r.filename,
            language: r.language,
            status: (r.status === 'completed'
              ? 'completed'
              : r.status === 'failed' || r.status === 'cancelled'
              ? 'failed'
              : r.status === 'queued'
              ? 'queued'
              : 'running') as 'running' | 'completed' | 'failed' | 'queued',
            created_at: r.created_at,
            duration_seconds: r.duration_seconds,
            total_issues: r.total_issues,
            critical_issues: r.critical_issues,
            high_issues: r.high_issues,
          })
        );
        const merged = Array.from(map.values()).sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setReviews(merged);
      }
    } catch {
      // Keep local data
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReviews();
  }, []);

  // Compute metrics from actual stored review data with server authoritative fallback
  const totalReviews = stats?.total_reviews ?? reviews.length;
  const completedReviews = stats?.completed_reviews ?? reviews.filter((r) => r.status === 'completed').length;
  const totalIssuesFound = stats?.total_issues ?? reviews.reduce((sum, r) => sum + (r.total_issues || 0), 0);
  const criticalHighIssues = stats?.critical_high_issues ?? reviews.reduce(
    (sum, r) => sum + (r.critical_issues || 0) + (r.high_issues || 0),
    0
  );

  return (
    <AppShell>
      <div className="p-4 sm:p-8 max-w-6xl mx-auto w-full space-y-8">
        {/* Header and Value Proposition */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight font-mono">
                CodeGuard V2
              </h1>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                Hybrid Static + LLM
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1">
              Security-focused code review for GitHub repositories and Python code.
            </p>
          </div>

          {/* Primary Action Buttons */}
          <div className="flex items-center gap-2.5">
            <Link
              to="/review/pr"
              className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 text-xs font-semibold shadow-xs transition-colors"
            >
              <GitPullRequest className="w-3.5 h-3.5" />
              <span>Review Pull Request</span>
            </Link>
            <Link
              to="/review/snippet"
              className="flex items-center gap-2 px-3.5 py-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 text-xs font-semibold transition-colors"
            >
              <Code2 className="w-3.5 h-3.5 text-slate-400" />
              <span>Analyze Snippet</span>
            </Link>
          </div>
        </div>

        {/* Real Summary Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f]">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Total Reviews
            </div>
            <div className="mt-1 text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100 font-mono">
              {loading ? '--' : totalReviews}
            </div>
          </div>

          <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f]">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Issues Found
            </div>
            <div className="mt-1 text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100 font-mono">
              {loading ? '--' : totalIssuesFound}
            </div>
          </div>

          <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f]">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Critical / High
            </div>
            <div className="mt-1 text-2xl sm:text-3xl font-bold font-mono text-orange-600 dark:text-orange-400">
              {loading ? '--' : criticalHighIssues}
            </div>
          </div>

          <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f]">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Completed
            </div>
            <div className="mt-1 text-2xl sm:text-3xl font-bold font-mono text-emerald-600 dark:text-emerald-400">
              {loading ? '--' : completedReviews}
            </div>
          </div>
        </div>

        {/* Recent Reviews Table */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              Recent Reviews
            </h2>
            <button
              onClick={loadReviews}
              className="text-xs font-mono text-slate-500 hover:text-slate-900 dark:hover:text-slate-300 flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Refresh</span>
            </button>
          </div>

          <div className="border border-slate-200 dark:border-slate-800/80 rounded-lg overflow-hidden bg-white dark:bg-[#0f141f]">
            <div className="grid grid-cols-12 gap-2 px-4 py-2.5 bg-slate-50 dark:bg-slate-900/60 border-b border-slate-200 dark:border-slate-800/80 text-[11px] font-medium text-slate-500 uppercase tracking-wider">
              <div className="col-span-5 sm:col-span-4">Repository / PR</div>
              <div className="col-span-3 sm:col-span-2">Status</div>
              <div className="col-span-2 text-center">Issues</div>
              <div className="hidden sm:block sm:col-span-2 text-right">Duration</div>
              <div className="col-span-2 sm:col-span-2 text-right">Action</div>
            </div>

            <div className="divide-y divide-slate-100 dark:divide-slate-800/60">
              {reviews.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500 space-y-3">
                  <p>No code reviews have been run yet.</p>
                  <Link
                    to="/review/pr"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-blue-600 text-white text-xs font-medium"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Review Pull Request</span>
                  </Link>
                </div>
              ) : (
                reviews.map((rev) => {
                  const displayName =
                    rev.type === 'snippet'
                      ? (rev.filename || 'snippet.py')
                      : `${rev.repo_url?.replace(/^https?:\/\/github\.com\//, '') || 'repo'} #${rev.pr_number || '1'}`;

                  return (
                    <div
                      key={rev.review_id}
                      onClick={() => navigate(`/reviews/${rev.review_id}`)}
                      className="grid grid-cols-12 gap-2 px-4 py-3 items-center hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer transition-colors text-xs font-mono"
                    >
                      <div className="col-span-5 sm:col-span-4 truncate flex items-center gap-2">
                        {rev.type === 'snippet' ? (
                          <Code2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        ) : (
                          <GitPullRequest className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                        )}
                        <span className="font-semibold text-slate-900 dark:text-slate-100 truncate">
                          {displayName}
                        </span>
                      </div>

                      <div className="col-span-3 sm:col-span-2">
                        <StatusBadge status={rev.status} />
                      </div>

                      <div className="col-span-2 text-center font-bold text-slate-900 dark:text-slate-200">
                        {rev.status === 'completed' ? (rev.total_issues ?? 0) : '--'}
                      </div>

                      <div className="hidden sm:block sm:col-span-2 text-right text-slate-500">
                        {rev.duration_seconds ? `${rev.duration_seconds}s` : '--'}
                      </div>

                      <div className="col-span-2 sm:col-span-2 text-right">
                        <span className="inline-flex items-center gap-1 text-blue-600 dark:text-blue-400 font-medium hover:underline text-[11px]">
                          <span>Inspect</span>
                          <ArrowRight className="w-3 h-3" />
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
