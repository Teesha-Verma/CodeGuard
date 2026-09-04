import React from 'react';
import { GitPullRequest, Search, AlertCircle, FileCheck, CheckCircle2, GitMerge } from 'lucide-react';

export const DeveloperWorkflowSection: React.FC = () => {
  const workflowNodes = [
    {
      title: 'GitHub Pull Request',
      step: '01',
      desc: 'Developer opens PR or commits new changes to a feature branch.',
      icon: GitPullRequest,
    },
    {
      title: 'CodeGuard Analysis',
      step: '02',
      desc: 'AST structural parser and taint tracker run across the diff set.',
      icon: Search,
    },
    {
      title: 'Contextual Findings',
      step: '03',
      desc: 'Findings synthesized with confidence ratings and zero AI hallucinations.',
      icon: AlertCircle,
    },
    {
      title: 'Line Evidence & Fix',
      step: '04',
      desc: 'Exact line-by-line diff recommendations presented in workspace.',
      icon: FileCheck,
    },
    {
      title: 'Developer Merges Safely',
      step: '05',
      desc: 'Remediation applied, reviewed, and merged cleanly into main.',
      icon: GitMerge,
    },
  ];

  return (
    <section className="py-20 md:py-28 border-t border-slate-200 dark:border-slate-800/80" id="workflow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mb-14">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded text-xs font-mono font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 mb-3">
            <span>Seamless Integration</span>
          </div>
          <h2 className="text-2xl sm:text-4xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
            Engineered for the daily developer loop
          </h2>
          <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-400 leading-relaxed">
            CodeGuard integrates into your review cadence without blocking shipping velocity or burying developers in irrelevant alerts.
          </p>
        </div>

        {/* Workflow Horizontal Chain */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {workflowNodes.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={item.step}
                className="relative p-5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] flex flex-col justify-between shadow-xs"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-mono font-bold text-blue-600 dark:text-blue-400">
                      {item.step}
                    </span>
                    <div className="p-1.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>

                  <h3 className="font-semibold text-sm text-slate-900 dark:text-slate-100 mb-2">
                    {item.title}
                  </h3>

                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    {item.desc}
                  </p>
                </div>

                {idx < workflowNodes.length - 1 && (
                  <div className="hidden md:block absolute -right-2.5 top-1/2 -translate-y-1/2 z-10 text-slate-400 dark:text-slate-600 font-mono text-xs select-none">
                    →
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
