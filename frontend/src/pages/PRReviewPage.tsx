import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { apiClient } from '@/lib/api/client';
import { saveStoredReview } from '@/lib/storage/reviews';
import {
  GitPullRequest,
  Loader2,
  AlertCircle,
  ArrowLeft,
  Info,
} from 'lucide-react';

export default function PRReviewPage() {
  const navigate = useNavigate();
  const [repoUrl, setRepoUrl] = useState('https://github.com/acme/payments-service');
  const [prNumber, setPrNumber] = useState('42');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;
    setError(null);

    if (!repoUrl.trim()) {
      setError('Please provide a valid GitHub repository URL.');
      return;
    }

    const prNum = parseInt(prNumber, 10);
    if (isNaN(prNum) || prNum <= 0) {
      setError('Please provide a valid numeric pull request number.');
      return;
    }

    setLoading(true);

    try {
      const res = await apiClient.submitPrReview(repoUrl.trim(), prNum);

      // Save initial review record locally
      saveStoredReview({
        review_id: res.review_id,
        type: 'pr',
        repo_url: repoUrl.trim(),
        pr_number: prNum,
        status: 'running',
        created_at: new Date().toISOString(),
        total_issues: 0,
        meaningful_issues: 0,
      });

      // Navigate to live review processing view
      navigate(`/reviews/${res.review_id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to submit review request.';
      setError(msg);
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="p-4 sm:p-8 max-w-2xl mx-auto w-full space-y-6">
        {/* Navigation back */}
        <div>
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Dashboard</span>
          </Link>
        </div>

        {/* Header */}
        <div className="border-b border-slate-200 dark:border-slate-800/80 pb-4">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              New review
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Analyze a code snippet or queue an async review for a GitHub pull request.
          </p>

          {/* Sub tabs */}
          <div className="flex items-center gap-4 mt-4 border-b border-slate-200 dark:border-slate-800">
            <Link
              to="/review/snippet"
              className="pb-2 text-xs font-medium text-slate-500 hover:text-slate-900 dark:hover:text-slate-300"
            >
              Snippet
            </Link>
            <span className="pb-2 text-xs font-semibold text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400">
              Pull request
            </span>
          </div>
        </div>

        {/* Submission Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3.5 rounded-lg border border-red-500/20 bg-red-500/10 text-red-700 dark:text-red-400 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold">Submission Error</div>
                <div className="font-mono mt-0.5">{error}</div>
                <div className="mt-2 text-[11px] text-slate-600 dark:text-slate-400">
                  Ensure the FastAPI backend is running on{' '}
                  <code className="px-1 py-0.5 rounded bg-slate-200 dark:bg-slate-800">
                    http://localhost:8000
                  </code>
                </div>
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-mono">
              Repository URL
            </label>
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/owner/repository"
              required
              className="w-full px-3 py-2 text-xs rounded-md bg-white dark:bg-[#0c1017] border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-mono">
              Pull Request Number
            </label>
            <input
              type="number"
              value={prNumber}
              onChange={(e) => setPrNumber(e.target.value)}
              placeholder="42"
              required
              min="1"
              className="w-full px-3 py-2 text-xs rounded-md bg-white dark:bg-[#0c1017] border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-[#0f141f] border border-slate-200 dark:border-slate-800/80 text-xs text-slate-600 dark:text-slate-400 space-y-1.5 leading-relaxed">
            <div className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-blue-500" />
              <span>Review Workflow Details</span>
            </div>
            <p>
              CodeGuard reviews the pull request changes while using repository-wide information as supporting context. Analysis runs asynchronously through our static analyzers, Gemini RAG, and Groq LLM reasoning pipeline.
            </p>
          </div>

          <div className="pt-2 flex items-center justify-between">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 text-xs font-semibold shadow-xs transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Submitting Review...</span>
                </>
              ) : (
                <>
                  <GitPullRequest className="w-3.5 h-3.5" />
                  <span>Review Pull Request</span>
                </>
              )}
            </button>

            <span className="text-[11px] font-mono text-slate-500">
              Timeout: 300s
            </span>
          </div>
        </form>
      </div>
    </AppShell>
  );
}
