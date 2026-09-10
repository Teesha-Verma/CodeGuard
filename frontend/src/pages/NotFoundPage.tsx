import React from 'react';
import { Link } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { AlertTriangle, ArrowLeft } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <AppShell>
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-[#f8fafc] dark:bg-[#0a0d14]">
        <div className="w-full max-w-md p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0f141f] shadow-xs space-y-4">
          <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto" />
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
            Page Not Found
          </h2>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            The requested page does not exist in the CodeGuard workspace.
          </p>
          <div className="pt-2">
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Return to Dashboard</span>
            </Link>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
