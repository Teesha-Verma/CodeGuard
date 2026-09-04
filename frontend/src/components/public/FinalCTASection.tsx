import React from 'react';
import { Link } from 'react-router-dom';
import { GitPullRequest, Code2, ArrowRight } from 'lucide-react';

export const FinalCTASection: React.FC = () => {
  return (
    <section className="py-20 md:py-28 border-t border-slate-200 dark:border-slate-800/80 bg-slate-50/50 dark:bg-[#080c13]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-8 sm:p-12 text-center shadow-xs">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-medium border border-blue-500/20 bg-blue-500/10 text-blue-700 dark:text-blue-400 mb-6">
            <span>Ready for Production Inspection</span>
          </div>

          <h2 className="text-2xl sm:text-4xl font-semibold tracking-tight text-slate-900 dark:text-slate-100 max-w-2xl mx-auto leading-tight">
            Review your next pull request with CodeGuard.
          </h2>

          <p className="mt-4 text-sm sm:text-base text-slate-600 dark:text-slate-400 max-w-xl mx-auto leading-relaxed">
            Run automated structural checks, track untrusted taint flows, and catch security vulnerabilities before they reach production environments.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3.5">
            <Link
              to="/review/pr"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-md text-xs sm:text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white shadow-xs transition-colors"
            >
              <GitPullRequest className="w-4 h-4" />
              <span>Review a Pull Request</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/review/snippet"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-md text-xs sm:text-sm font-medium border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900/60 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
            >
              <Code2 className="w-4 h-4 text-slate-500" />
              <span>Analyze Snippet</span>
            </Link>
          </div>

          <div className="mt-6 text-xs text-slate-500 font-mono">
            <span>Instant review execution · No complex configuration required</span>
          </div>
        </div>
      </div>
    </section>
  );
};
