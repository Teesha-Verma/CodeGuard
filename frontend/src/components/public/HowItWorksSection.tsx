import React from 'react';
import { GitPullRequest, GitMerge, Cpu, ShieldAlert, CheckCircle2, Terminal } from 'lucide-react';

export const HowItWorksSection: React.FC = () => {
  const steps = [
    {
      number: '01',
      title: 'Queue Pull Request or Snippet',
      subtitle: 'Seamless ingestion',
      description:
        'Submit a public/private GitHub PR URL or paste raw source code. CodeGuard parses file diffs, commit context, and modified AST boundaries.',
      badge: 'Input Ingestion',
      icon: GitPullRequest,
    },
    {
      number: '02',
      title: 'AST & Call Graph Traversal',
      subtitle: 'Deterministic structure',
      description:
        'The static engine parses code into Python ASTs, extracts interprocedural call graphs, and constructs Control Flow Graphs (CFG) without hallucination.',
      badge: 'Deterministic Parsing',
      icon: Cpu,
    },
    {
      number: '03',
      title: 'Taint Analysis & Reasoning',
      subtitle: 'Hybrid verification',
      description:
        'Untrusted sources are traced across assignment boundaries into dangerous sinks. Groq reasoning filters out false positives with contextual security rules.',
      badge: 'Hybrid Pipeline',
      icon: ShieldAlert,
    },
    {
      number: '04',
      title: 'Inspect Evidence & Apply Fix',
      subtitle: 'Zero vague feedback',
      description:
        'Review findings mapped to exact line numbers with Root Cause, Detection Evidence, and a one-click replacement diff ready to commit.',
      badge: 'Actionable Remediation',
      icon: CheckCircle2,
    },
  ];

  return (
    <section className="py-20 md:py-28 border-t border-slate-200 dark:border-slate-800/80 bg-slate-50/60 dark:bg-[#090d14]" id="how-it-works">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="max-w-3xl mb-14 md:mb-18">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded text-xs font-mono font-medium bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 mb-3">
            <span>Pipeline Architecture</span>
          </div>
          <h2 className="text-2xl sm:text-4xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
            How CodeGuard inspects code
          </h2>
          <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-400 leading-relaxed">
            A 4-step hybrid pipeline combining deterministic static AST analysis with high-speed contextual reasoning.
          </p>
        </div>

        {/* 4 Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div
                key={step.number}
                className="relative flex flex-col justify-between p-6 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0d111a] hover:border-slate-300 dark:hover:border-slate-700 transition-colors shadow-xs group"
              >
                <div>
                  {/* Step Number & Badge */}
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-2xl font-bold text-slate-300 dark:text-slate-700 group-hover:text-blue-500 transition-colors">
                      {step.number}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                      {step.badge}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 mb-2">
                    <div className="p-1.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400">
                      <Icon className="w-4 h-4" />
                    </div>
                    <h3 className="font-semibold text-sm sm:text-base text-slate-900 dark:text-slate-100">
                      {step.title}
                    </h3>
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed mt-2">
                    {step.description}
                  </p>
                </div>

                <div className="mt-6 pt-3 border-t border-slate-100 dark:border-slate-800/60 flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <span>Step {idx + 1} of 4</span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-medium">Verified</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
