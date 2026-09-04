import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { AssistantChat } from '@/components/assistant/AssistantChat';
import { useActiveFinding } from '@/lib/context/ActiveFindingContext';
import { SeverityBadge } from '@/components/common/Badges';
import { Bot, BookOpen, Code2, Terminal, Shield, ArrowRight } from 'lucide-react';

export default function AssistantPage() {
  const navigate = useNavigate();
  const { activeIssue, activeFilePath } = useActiveFinding();

  useEffect(() => {
    document.title = 'AI Assistant — CodeGuard V2';
  }, []);

  return (
    <AppShell>
      <div className="flex-1 flex flex-col min-h-0 bg-slate-50/50 dark:bg-[#0a0d14]">
        {/* Page Header */}
        <div className="border-b border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0d111a] px-4 sm:px-8 py-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="p-1 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400">
                  <Bot className="w-4 h-4" />
                </div>
                <span className="text-xs font-mono font-medium text-slate-500">
                  Context-Aware Assistant
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                CodeGuard Assistant
              </h1>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => navigate('/playground')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                <Code2 className="w-3.5 h-3.5 text-blue-500" />
                <span>Fix Playground</span>
              </button>
              <button
                type="button"
                onClick={() => navigate('/learn')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                <BookOpen className="w-3.5 h-3.5 text-emerald-500" />
                <span>Learner Mode</span>
              </button>
            </div>
          </div>
        </div>

        {/* Main Chat Workspace */}
        <div className="flex-1 p-4 sm:p-6 overflow-hidden flex flex-col max-w-5xl mx-auto w-full">
          <AssistantChat />
        </div>
      </div>
    </AppShell>
  );
}
