import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { RepositoryRiskTable } from '@/components/security/RepositoryRiskTable';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export default function RiskViewPage() {
  useEffect(() => {
    document.title = 'Repository Risk View — CodeGuard V2';
  }, []);

  return (
    <AppShell>
      <div className="flex-1 flex flex-col min-h-0 bg-slate-50/50 dark:bg-[#0a0d14]">
        {/* Top Header */}
        <div className="border-b border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0d111a] px-4 sm:px-8 py-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Link
                  to="/security"
                  className="text-xs font-mono text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 flex items-center gap-1"
                >
                  <ArrowLeft className="w-3 h-3" />
                  <span>Security Health</span>
                </Link>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                Repository Risk View
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1">
                Architectural risk ranking by severity weight and interprocedural module fan-in.
              </p>
            </div>
          </div>
        </div>

        {/* Risk Table Content Body */}
        <div className="flex-1 p-4 sm:p-8 overflow-y-auto max-w-6xl mx-auto w-full">
          <RepositoryRiskTable />
        </div>
      </div>
    </AppShell>
  );
}
