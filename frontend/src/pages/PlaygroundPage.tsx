import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { FixPlaygroundView } from '@/components/playground/FixPlaygroundView';
import { Code2, BookOpen, Bot, Terminal } from 'lucide-react';

export default function PlaygroundPage() {
  const navigate = useNavigate();

  useEffect(() => {
    document.title = 'Fix Playground — CodeGuard V2';
  }, []);

  return (
    <AppShell>
      <div className="flex-1 flex flex-col min-h-0 bg-slate-50/50 dark:bg-[#0a0d14]">
        {/* Top Header */}
        <div className="border-b border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0d111a] px-4 sm:px-8 py-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="p-1 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400">
                  <Code2 className="w-4 h-4" />
                </div>
                <span className="text-xs font-mono font-medium text-slate-500">
                  Interactive Remediation Sandbox
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                Fix Playground
              </h1>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => navigate('/learn')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                <BookOpen className="w-3.5 h-3.5 text-blue-500" />
                <span>Learner Mode</span>
              </button>
              <button
                type="button"
                onClick={() => navigate('/assistant')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                <Bot className="w-3.5 h-3.5 text-purple-500" />
                <span>AI Assistant</span>
              </button>
            </div>
          </div>
        </div>

        {/* Main Editor Body */}
        <div className="flex-1 p-4 sm:p-6 overflow-hidden flex flex-col max-w-7xl mx-auto w-full">
          <FixPlaygroundView />
        </div>
      </div>
    </AppShell>
  );
}
