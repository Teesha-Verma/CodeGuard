import React, { useState, useEffect } from 'react';
import { getStoredReviews } from '@/lib/storage/reviews';
import { apiClient, SecurityHealthResponse } from '@/lib/api/client';
import { SeverityBadge } from '@/components/common/Badges';
import {
  ShieldAlert,
  ShieldCheck,
  Activity,
  GitPullRequest,
  CheckCircle2,
  AlertTriangle,
  Cpu,
  Layers,
  ArrowRight,
  TrendingUp,
  Sparkles,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const SecurityHealthOverview: React.FC = () => {
  const reviews = getStoredReviews();
  const [backendHealth, setBackendHealth] = useState<SecurityHealthResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .getSecurityHealth()
      .then((data) => {
        if (!cancelled && data) {
          setBackendHealth(data);
        }
      })
      .catch(() => {
        // Fall back gracefully to local calculation
      });

    return () => {
      cancelled = true;
    };
  }, []);

  // Compute real aggregated KPIs across stored reviews
  let totalIssues = 0;
  let criticalCount = 0;
  let highCount = 0;
  let mediumCount = 0;
  let lowCount = 0;
  let styleCount = 0;
  let llmReasonedCount = 0;
  let staticReasonedCount = 0;

  const categoryMap: Record<string, number> = {};
  const fileImpactMap: Record<string, { critical: number; high: number; medium: number; low: number; total: number }> = {};

  reviews.forEach((record) => {
    const report = record.report;
    if (!report) return;

    const stats = report.summary_stats;
    if (stats) {
      totalIssues += stats.total_issues || 0;
      criticalCount += stats.by_severity?.critical || 0;
      highCount += stats.by_severity?.high || 0;
      mediumCount += stats.by_severity?.medium || 0;
      lowCount += stats.by_severity?.low || 0;
      styleCount += stats.style_findings || 0;
      llmReasonedCount += stats.reasoning_sources?.llm || 0;
      staticReasonedCount += stats.reasoning_sources?.static_analysis || 0;
    }

    report.file_reports?.forEach((file) => {
      if (!fileImpactMap[file.file_path]) {
        fileImpactMap[file.file_path] = { critical: 0, high: 0, medium: 0, low: 0, total: 0 };
      }
      file.issues?.forEach((issue) => {
        const cat = issue.category || issue.issue_type || 'Security';
        categoryMap[cat] = (categoryMap[cat] || 0) + 1;

        fileImpactMap[file.file_path].total += 1;
        if (issue.severity === 'critical') fileImpactMap[file.file_path].critical += 1;
        else if (issue.severity === 'high') fileImpactMap[file.file_path].high += 1;
        else if (issue.severity === 'medium') fileImpactMap[file.file_path].medium += 1;
        else fileImpactMap[file.file_path].low += 1;
      });
    });
  });

  const categories = Object.entries(categoryMap).sort((a, b) => b[1] - a[1]);
  const rankedFiles = Object.entries(fileImpactMap).sort((a, b) => {
    const scoreA = a[1].critical * 10 + a[1].high * 5 + a[1].medium * 2 + a[1].low;
    const scoreB = b[1].critical * 10 + b[1].high * 5 + b[1].medium * 2 + b[1].low;
    return scoreB - scoreA;
  });

  const effectiveCritical = backendHealth?.critical_issues ?? criticalCount;
  const effectiveHigh = backendHealth?.high_issues ?? highCount;
  const effectiveTotal = backendHealth?.total_issues ?? totalIssues;
  const effectiveScore = backendHealth?.health_score ?? (reviews.length > 0 ? Math.max(0, 100 - (criticalCount * 15 + highCount * 8 + mediumCount * 3 + lowCount * 1)) : 100);
  const effectiveGrade = backendHealth?.health_grade ?? (effectiveCritical > 0 ? 'C' : effectiveHigh > 0 ? 'B' : 'A');

  return (
    <div className="space-y-6">
      {/* Security Health Score Banner */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div className="space-y-1 max-w-xl">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-500" />
            <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
              Deterministic Security Health Score
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 font-semibold">
              Live Backend Telemetry
            </span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            Formula: {backendHealth?.formula_explanation || '100 - (15×crit + 8×high + 3×med + 1×low)'}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-3xl font-bold font-mono text-slate-900 dark:text-slate-100">
              {effectiveScore}
              <span className="text-xs text-slate-400 font-normal"> / 100</span>
            </div>
            <div className="text-xs font-mono font-semibold text-emerald-600 dark:text-emerald-400">
              Grade {effectiveGrade}
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Critical Vulnerabilities */}
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between text-rose-600 dark:text-rose-400 mb-2">
            <span className="text-[11px] font-mono uppercase font-bold tracking-wider">
              Critical Findings
            </span>
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100">
            {effectiveCritical}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Immediate remediation required (CWE injections / RCE)
          </p>
        </div>

        {/* High Severity */}
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between text-amber-600 dark:text-amber-400 mb-2">
            <span className="text-[11px] font-mono uppercase font-bold tracking-wider">
              High Severity
            </span>
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100">
            {effectiveHigh}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Sensitive parameter flows &amp; access controls
          </p>
        </div>

        {/* Total Meaningful Issues */}
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between text-blue-600 dark:text-blue-400 mb-2">
            <span className="text-[11px] font-mono uppercase font-bold tracking-wider">
              Total High-Signal
            </span>
            <Activity className="w-4 h-4" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100">
            {effectiveTotal}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Across {reviews.length} completed review scans
          </p>
        </div>

        {/* Reasoning Balance */}
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between text-purple-600 dark:text-purple-400 mb-2">
            <span className="text-[11px] font-mono uppercase font-bold tracking-wider">
              Analysis Engine
            </span>
            <Cpu className="w-4 h-4" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100">
            {llmReasonedCount} / {staticReasonedCount + llmReasonedCount || totalIssues}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            LLM grounded findings vs. deterministic AST rules
          </p>
        </div>
      </div>

      {/* Severity Breakdown & Category Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 shadow-xs">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500 mb-4">
            Finding Severity Distribution
          </h3>

          <div className="space-y-3">
            {[
              { label: 'Critical', count: criticalCount, color: 'bg-rose-500', text: 'text-rose-600' },
              { label: 'High', count: highCount, color: 'bg-amber-500', text: 'text-amber-600' },
              { label: 'Medium', count: mediumCount, color: 'bg-blue-500', text: 'text-blue-600' },
              { label: 'Low', count: lowCount, color: 'bg-slate-400', text: 'text-slate-500' },
            ].map((item, idx) => {
              const pct = totalIssues > 0 ? ((item.count / totalIssues) * 100).toFixed(0) : '0';
              return (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="font-semibold text-slate-700 dark:text-slate-300">
                      {item.label}
                    </span>
                    <span className="text-slate-500">
                      {item.count} ({pct}%)
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full ${item.color} rounded-full transition-all duration-300`}
                      style={{ width: `${Math.max(Number(pct), item.count > 0 ? 4 : 0)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recurring Issue Categories */}
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 shadow-xs">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500 mb-4">
            Recurring Issue Categories
          </h3>

          <div className="space-y-2.5">
            {categories.slice(0, 5).map(([cat, count], idx) => {
              const pct = totalIssues > 0 ? ((count / totalIssues) * 100).toFixed(0) : '0';
              return (
                <div
                  key={idx}
                  className="p-2.5 rounded border border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/40 flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-4 h-4 rounded flex items-center justify-center font-mono text-[10px] bg-slate-200 dark:bg-slate-800 font-bold text-slate-600 dark:text-slate-400">
                      {idx + 1}
                    </span>
                    <span className="font-medium text-slate-800 dark:text-slate-200">
                      {cat}
                    </span>
                  </div>
                  <span className="font-mono text-slate-500 text-[11px]">
                    {count} finding{count !== 1 ? 's' : ''} ({pct}%)
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Top Riskiest Files Preview */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
              High-Risk Modules (Action Required)
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Ranked by weighted severity of detected security vulnerabilities.
            </p>
          </div>
          <Link
            to="/security/risk"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline"
          >
            <span>Full Risk Matrix</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="space-y-2">
          {rankedFiles.slice(0, 4).map(([filePath, impact], idx) => {
            const riskLevel =
              impact.critical > 0 ? 'HIGH' : impact.high > 0 ? 'MEDIUM' : 'LOW';

            return (
              <div
                key={idx}
                className="p-3 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/40 flex flex-wrap items-center justify-between gap-3 text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <span
                    className={`px-1.5 py-0.5 rounded font-mono text-[10px] font-bold ${
                      riskLevel === 'HIGH'
                        ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400'
                        : riskLevel === 'MEDIUM'
                        ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400'
                        : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400'
                    }`}
                  >
                    {riskLevel} RISK
                  </span>
                  <span className="font-mono font-medium text-slate-800 dark:text-slate-200">
                    {filePath}
                  </span>
                </div>

                <div className="flex items-center gap-3 text-[11px] font-mono text-slate-500">
                  {impact.critical > 0 && (
                    <span className="text-rose-600 font-semibold">{impact.critical} critical</span>
                  )}
                  {impact.high > 0 && (
                    <span className="text-amber-600 font-semibold">{impact.high} high</span>
                  )}
                  <span>{impact.total} total issue{impact.total !== 1 ? 's' : ''}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
