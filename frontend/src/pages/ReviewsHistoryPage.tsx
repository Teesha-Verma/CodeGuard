import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { getStoredReviews, deleteStoredReview } from '@/lib/storage/reviews';
import { apiClient } from '@/lib/api/client';
import { StoredReviewRecord } from '@/types';
import { StatusBadge } from '@/components/common/Badges';
import {
  Plus,
  Search,
  Code2,
  GitPullRequest,
  Trash2,
} from 'lucide-react';

export default function ReviewsHistoryPage() {
  const navigate = useNavigate();
  const [reviews, setReviews] = useState<StoredReviewRecord[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const loadData = async () => {
    const local = getStoredReviews();
    setReviews(local);

    try {
      const remote = await apiClient.listReviews();
      if (remote && Array.isArray(remote.reviews)) {
        // Merge remote and local by review_id
        const map = new Map<string, StoredReviewRecord>();
        local.forEach((r) => map.set(r.review_id, r));
        remote.reviews.forEach((r) =>
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
      // Offline fallback: keep local data
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filtered = reviews.filter((r) => {
    if (statusFilter !== 'all' && r.status !== statusFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      const name =
        r.type === 'snippet'
          ? r.filename?.toLowerCase()
          : `${r.repo_url} #${r.pr_number}`.toLowerCase();
      if (!name?.includes(q)) return false;
    }
    return true;
  });

  const handleDelete = async (e: React.MouseEvent, reviewId: string) => {
    e.stopPropagation();
    if (confirm('Remove this review from your history?')) {
      deleteStoredReview(reviewId);
      try {
        await apiClient.deleteReview(reviewId);
      } catch {
        // Ignore remote delete error
      }
      loadData();
    }
  };

  // Find any failed reviews to highlight error messages at the bottom matching Screenshot 3
  const failedReview = reviews.find((r) => r.status === 'failed' && r.error_message);

  return (
    <AppShell>
      <div className="p-4 sm:p-8 max-w-5xl mx-auto w-full space-y-6">
        {/* Header matching Screenshot 3 */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800/80 pb-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              PR reviews
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Async review queue and historical analysis results.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Link
              to="/review/pr"
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-md bg-white dark:bg-slate-100 text-slate-900 dark:text-slate-950 hover:bg-slate-50 text-xs font-semibold shadow-xs border border-slate-300 dark:border-transparent transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Queue review</span>
            </Link>
          </div>
        </div>

        {/* Filter controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by repository or PR..."
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-md bg-white dark:bg-[#0c1017] border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Status:</span>
            <div className="flex items-center gap-1 text-xs font-mono">
              {['all', 'completed', 'running', 'queued', 'failed'].map((st) => (
                <button
                  key={st}
                  type="button"
                  onClick={() => setStatusFilter(st)}
                  className={`px-2 py-1 rounded capitalize transition-colors ${
                    statusFilter === st
                      ? 'bg-blue-600 text-white font-medium'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Queue Table matching Screenshot 3 */}
        <div className="border border-slate-200 dark:border-slate-800/80 rounded-lg overflow-hidden bg-white dark:bg-[#0f141f]">
          <div className="grid grid-cols-12 gap-2 px-4 py-3 bg-slate-50 dark:bg-slate-900/60 border-b border-slate-200 dark:border-slate-800/80 text-[11px] font-medium text-slate-500 uppercase tracking-wider">
            <div className="col-span-5 sm:col-span-5 font-mono">Repository / PR</div>
            <div className="col-span-3 sm:col-span-3">Status</div>
            <div className="col-span-2 sm:col-span-2 text-center font-mono">Issues</div>
            <div className="col-span-2 sm:col-span-2 text-right font-mono">Duration</div>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-xs">
            {filtered.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                No reviews found matching current filter.
              </div>
            ) : (
              filtered.map((rev) => {
                const displayName =
                  rev.type === 'snippet'
                    ? (rev.filename || 'snippet.py')
                    : `${rev.repo_url?.replace(/^https?:\/\/github\.com\//, '') || 'repo'} #${rev.pr_number || '1'}`;

                return (
                  <div
                    key={rev.review_id}
                    onClick={() => navigate(`/reviews/${rev.review_id}`)}
                    className="grid grid-cols-12 gap-2 px-4 py-3.5 items-center hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <div className="col-span-5 sm:col-span-5 flex items-center gap-2 truncate">
                      {rev.type === 'snippet' ? (
                        <Code2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      ) : (
                        <GitPullRequest className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                      )}
                      <span className="font-bold text-slate-900 dark:text-slate-100 truncate">
                        {displayName}
                      </span>
                    </div>

                    <div className="col-span-3 sm:col-span-3">
                      <StatusBadge status={rev.status} />
                    </div>

                    <div className="col-span-2 sm:col-span-2 text-center font-bold text-slate-900 dark:text-slate-100">
                      {rev.status === 'completed' ? (rev.total_issues ?? 0) : '--'}
                    </div>

                    <div className="col-span-2 sm:col-span-2 text-right text-slate-500 flex items-center justify-end gap-3">
                      <span>
                        {rev.duration_seconds ? `${rev.duration_seconds}s` : '--'}
                      </span>
                      <button
                        type="button"
                        onClick={(e) => handleDelete(e, rev.review_id)}
                        className="p-1 rounded text-slate-400 hover:text-red-500 transition-colors"
                        title="Delete from local history"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Failed Review Footnote matching Screenshot 3 */}
        {failedReview && (
          <div className="text-xs font-mono text-slate-500 pt-2">
            {failedReview.repo_url?.replace(/^https?:\/\/github\.com\//, '')} #{failedReview.pr_number} failed — {failedReview.error_message}
          </div>
        )}
      </div>
    </AppShell>
  );
}
