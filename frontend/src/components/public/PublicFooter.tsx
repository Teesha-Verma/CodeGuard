import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { CodeGuardLogo } from '@/components/common/Logo';
import { apiClient } from '@/lib/api/client';
import { ShieldCheck, GitPullRequest, Code2, Terminal, ExternalLink, Activity } from 'lucide-react';

export const PublicFooter: React.FC = () => {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    apiClient
      .checkHealth()
      .then(() => {
        if (mounted) setBackendOnline(true);
      })
      .catch(() => {
        if (mounted) setBackendOnline(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <footer className="border-t border-slate-200 dark:border-slate-800/80 bg-slate-50/50 dark:bg-[#070a0f] text-slate-600 dark:text-slate-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 lg:gap-12">
          {/* Col 1: Brand & Purpose */}
          <div className="md:col-span-2 space-y-4">
            <Link to="/" className="inline-block hover:opacity-90 transition-opacity">
              <CodeGuardLogo size="md" />
            </Link>
            <p className="text-xs leading-relaxed max-w-md text-slate-600 dark:text-slate-400">
              Developer-focused code review and security analysis platform. Detects logic flaws,
              taint paths, and critical vulnerabilities across pull requests using structural AST
              parsing, graph traversal, and contextual reasoning.
            </p>
            <div className="flex items-center gap-3 pt-2">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md text-[11px] font-mono border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60">
                <span
                  className={`w-2 h-2 rounded-full ${
                    backendOnline === true
                      ? 'bg-emerald-500 animate-pulse'
                      : backendOnline === false
                      ? 'bg-amber-500'
                      : 'bg-slate-400'
                  }`}
                />
                <span>
                  Backend API:{' '}
                  {backendOnline === true
                    ? 'Connected (v2.0)'
                    : backendOnline === false
                    ? 'Local Standalone'
                    : 'Checking...'}
                </span>
              </div>
            </div>
          </div>

          {/* Col 2: Product Capabilities */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-slate-200 mb-3 font-mono">
              Product
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <Link
                  to="/review/pr"
                  className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors inline-flex items-center gap-1.5"
                >
                  <GitPullRequest className="w-3 h-3 text-slate-400" />
                  <span>Pull Request Review</span>
                </Link>
              </li>
              <li>
                <Link
                  to="/review/snippet"
                  className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors inline-flex items-center gap-1.5"
                >
                  <Code2 className="w-3 h-3 text-slate-400" />
                  <span>Snippet Analysis</span>
                </Link>
              </li>
              <li>
                <Link
                  to="/reviews"
                  className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors inline-flex items-center gap-1.5"
                >
                  <Terminal className="w-3 h-3 text-slate-400" />
                  <span>Review Records</span>
                </Link>
              </li>
              <li>
                <Link
                  to="/dashboard"
                  className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors inline-flex items-center gap-1.5"
                >
                  <Activity className="w-3 h-3 text-slate-400" />
                  <span>Developer Dashboard</span>
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 3: Architecture & Workspace */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-slate-200 mb-3 font-mono">
              Pipeline & Auth
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <Link to="/login" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  Sign In
                </Link>
              </li>
              <li>
                <Link to="/signup" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  Create Account
                </Link>
              </li>
              <li>
                <Link to="/settings" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  Workspace Rules & Config
                </Link>
              </li>
              <li>
                <span className="text-slate-400 dark:text-slate-500 font-mono text-[11px]">
                  Engine: AST + CFG + Taint + Groq
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-12 pt-6 border-t border-slate-200 dark:border-slate-800/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500 dark:text-slate-500">
          <div className="flex items-center gap-2">
            <span>© {new Date().getFullYear()} CodeGuard V2.</span>
            <span className="text-slate-300 dark:text-slate-700">|</span>
            <span>Deterministic Static Analysis & Reasoning</span>
          </div>
          <div className="flex items-center gap-4 text-[11px] font-mono">
            <span className="inline-flex items-center gap-1 text-slate-500">
              <ShieldCheck className="w-3 h-3 text-emerald-500" />
              <span>Zero Artificial Fluff</span>
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
