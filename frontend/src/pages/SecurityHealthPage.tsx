import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { SecurityHealthOverview } from '@/components/security/SecurityHealthOverview';
import { ShieldCheck, ShieldAlert, FileText, ArrowRight } from 'lucide-react';

export default function SecurityHealthPage() {
  const navigate = useNavigate();

  useEffect(() => {
    document.title = 'Security Health — CodeGuard V2';
  }, []);

  return (
    <AppShell>
      <div className="flex-1 flex flex-col min-h-0 bg-slate-50/50 dark:bg-[#0a0d14]">
        {/* Top Header */}
        <div className="border-b border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0d111a] px-4 sm:px-8 py-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="p-1 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <span className="text-xs font-mono font-medium text-slate-500">
                  Continuous Posture &amp; Audit Telemetry
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                Security Health
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1">
                Repository security overview synthesized from static AST rules, taint tracking, and LLM evaluations.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Link
                to="/security/risk"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-slate-900 text-white hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white transition-colors"
              >
                <span>View Risk Matrix</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 p-4 sm:p-8 overflow-y-auto max-w-6xl mx-auto w-full">
          <SecurityHealthOverview />
        </div>
      </div>
    </AppShell>
  );
}
