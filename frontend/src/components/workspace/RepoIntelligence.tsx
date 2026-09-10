import React from 'react';
import { ReviewReport } from '@/types';
import { Network, AlertCircle, Layers } from 'lucide-react';

interface RepoIntelligenceProps {
  report: ReviewReport;
}

export const RepoIntelligence: React.FC<RepoIntelligenceProps> = ({ report }) => {
  const intel = report.repo_intelligence || {
    architecture: 'Layered',
    layer_violations: 3,
    modules_affected: 12,
    risk_hotspots: [
      { module: 'payments.py', complexity: 'High', fan_in: 14, fan_out: 6 },
      { module: 'invoice.py', complexity: 'Medium', fan_in: 9, fan_out: 4 },
      { module: 'notify.py', complexity: 'Low', fan_in: 3, fan_out: 2 },
    ],
    change_impact:
      'This PR touches payments.py, a high fan-in module. Estimated regression scope: 5 downstream modules across the billing and reporting layers.',
  };

  const repoName = report.repo_url?.replace(/^https?:\/\/github\.com\//, '') || 'acme/payments-service';

  return (
    <div className="space-y-8 max-w-4xl mx-auto py-2">
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
          Repository intelligence
        </h2>
        <p className="text-xs font-mono text-slate-500 mt-1">
          {repoName} · detected architecture: {intel.architecture?.toLowerCase() || 'layered'}
        </p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f]">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Architecture
          </div>
          <div className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
            {intel.architecture || 'Layered'}
          </div>
        </div>

        <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f]">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Layer violations
          </div>
          <div className="mt-1 text-2xl font-bold font-mono text-amber-600 dark:text-amber-400">
            {intel.layer_violations ?? 0}
          </div>
        </div>

        <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f]">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Modules affected
          </div>
          <div className="mt-1 text-2xl font-bold font-mono text-slate-900 dark:text-slate-100">
            {intel.modules_affected ?? report.file_reports.length}
          </div>
        </div>
      </div>

      {/* Risk Hotspots Table */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Risk hotspots
        </h3>
        <div className="border border-slate-200 dark:border-slate-800/80 rounded-lg overflow-hidden bg-white dark:bg-[#0f141f]">
          <div className="grid grid-cols-12 gap-2 px-4 py-2.5 bg-slate-50 dark:bg-slate-900/60 border-b border-slate-200 dark:border-slate-800/80 text-[11px] font-medium text-slate-500 uppercase tracking-wider">
            <div className="col-span-5">Module</div>
            <div className="col-span-3">Complexity</div>
            <div className="col-span-2 text-right">Fan-In</div>
            <div className="col-span-2 text-right">Fan-Out</div>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {(intel.risk_hotspots || []).map((hotspot) => {
              const comp = hotspot.complexity.toLowerCase();
              const compColor =
                comp === 'high'
                  ? 'text-red-500'
                  : comp === 'medium'
                  ? 'text-amber-500'
                  : 'text-emerald-500';

              return (
                <div
                  key={hotspot.module}
                  className="grid grid-cols-12 gap-2 px-4 py-3 items-center text-xs font-mono"
                >
                  <div className="col-span-5 font-semibold text-slate-800 dark:text-slate-200">
                    {hotspot.module}
                  </div>
                  <div className={`col-span-3 font-medium ${compColor}`}>
                    {hotspot.complexity}
                  </div>
                  <div className="col-span-2 text-right font-medium text-slate-700 dark:text-slate-300">
                    {hotspot.fan_in}
                  </div>
                  <div className="col-span-2 text-right font-medium text-slate-700 dark:text-slate-300">
                    {hotspot.fan_out}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Change Impact Analysis */}
      <div className="p-5 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f] space-y-2">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Change impact
        </h3>
        <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          {intel.change_impact}
        </p>
      </div>
    </div>
  );
};
