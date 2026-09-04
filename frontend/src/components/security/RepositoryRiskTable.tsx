import React, { useState } from 'react';
import { getStoredReviews } from '@/lib/storage/reviews';
import { SeverityBadge } from '@/components/common/Badges';
import {
  ShieldAlert,
  AlertTriangle,
  FileCode,
  ArrowUpDown,
  Filter,
  Layers,
  Search,
  ExternalLink,
} from 'lucide-react';

interface FileRiskRow {
  filePath: string;
  repoUrl: string;
  prNumber?: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  total: number;
  riskScore: number;
  riskTier: 'HIGH' | 'MEDIUM' | 'LOW';
  complexity: string;
  fanIn: number;
  fanOut: number;
  categories: string[];
}

export const RepositoryRiskTable: React.FC = () => {
  const reviews = getStoredReviews();
  const [filterTier, setFilterTier] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Build risk rows from stored reviews
  const fileMap: Record<string, FileRiskRow> = {};

  reviews.forEach((record) => {
    const report = record.report;
    if (!report) return;

    const hotspots = report.repo_intelligence?.risk_hotspots || [];

    report.file_reports?.forEach((file) => {
      const baseName = file.file_path.split('/').pop() || file.file_path;
      const hotspot = hotspots.find((h) => h.module === baseName || file.file_path.includes(h.module));

      let critical = 0;
      let high = 0;
      let medium = 0;
      let low = 0;
      const catSet = new Set<string>();

      file.issues?.forEach((issue) => {
        if (issue.severity === 'critical') critical++;
        else if (issue.severity === 'high') high++;
        else if (issue.severity === 'medium') medium++;
        else low++;

        if (issue.category) catSet.add(issue.category);
      });

      const fanIn = hotspot?.fan_in || (critical > 0 ? 12 : 4);
      const fanOut = hotspot?.fan_out || 4;
      const complexity = hotspot?.complexity || (critical > 0 ? 'High' : high > 0 ? 'Medium' : 'Low');

      const riskScore = critical * 15 + high * 8 + medium * 3 + low * 1 + fanIn;
      const riskTier: FileRiskRow['riskTier'] =
        riskScore >= 25 || critical > 0 ? 'HIGH' : riskScore >= 12 || high > 0 ? 'MEDIUM' : 'LOW';

      if (!fileMap[file.file_path]) {
        fileMap[file.file_path] = {
          filePath: file.file_path,
          repoUrl: report.repo_url || 'Active Repository',
          prNumber: report.pr_number,
          critical,
          high,
          medium,
          low,
          total: file.issues?.length || 0,
          riskScore,
          riskTier,
          complexity,
          fanIn,
          fanOut,
          categories: Array.from(catSet),
        };
      } else {
        // Aggregate if present in multiple reviews
        fileMap[file.file_path].critical += critical;
        fileMap[file.file_path].high += high;
        fileMap[file.file_path].medium += medium;
        fileMap[file.file_path].low += low;
        fileMap[file.file_path].total += file.issues?.length || 0;
        fileMap[file.file_path].riskScore += riskScore;
      }
    });
  });

  const rows = Object.values(fileMap).sort((a, b) => b.riskScore - a.riskScore);

  const filteredRows = rows.filter((row) => {
    if (filterTier !== 'ALL' && row.riskTier !== filterTier) return false;
    if (searchQuery && !row.filePath.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Search and Tier Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search module or file path..."
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-1.5 self-start sm:self-auto text-xs">
          {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((tier) => (
            <button
              key={tier}
              type="button"
              onClick={() => setFilterTier(tier)}
              className={`px-3 py-1 rounded-md font-mono text-[11px] font-medium transition-colors cursor-pointer ${
                filterTier === tier
                  ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 font-bold'
                  : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
              }`}
            >
              {tier}
            </button>
          ))}
        </div>
      </div>

      {/* Table Container */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] shadow-xs overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-900/50 text-[11px] font-mono text-slate-500">
              <th className="py-3 px-4 font-semibold">RISK TIER</th>
              <th className="py-3 px-4 font-semibold">FILE / MODULE PATH</th>
              <th className="py-3 px-4 font-semibold">SEVERITY FINDINGS</th>
              <th className="py-3 px-4 font-semibold">FAN-IN / FAN-OUT</th>
              <th className="py-3 px-4 font-semibold">COMPLEXITY</th>
              <th className="py-3 px-4 font-semibold text-right">WEIGHTED SCORE</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-[11.5px]">
            {filteredRows.map((row, idx) => (
              <tr key={idx} className="hover:bg-slate-50/60 dark:hover:bg-slate-900/30 transition-colors">
                <td className="py-3 px-4">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                      row.riskTier === 'HIGH'
                        ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400'
                        : row.riskTier === 'MEDIUM'
                        ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400'
                        : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400'
                    }`}
                  >
                    {row.riskTier}
                  </span>
                </td>

                <td className="py-3 px-4 font-medium text-slate-900 dark:text-slate-100">
                  <div className="flex items-center gap-1.5">
                    <FileCode className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{row.filePath}</span>
                  </div>
                  {row.categories.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1 font-sans text-[10.5px] text-slate-500">
                      {row.categories.slice(0, 3).map((c, ci) => (
                        <span key={ci} className="px-1.5 py-0.2 rounded bg-slate-100 dark:bg-slate-800">
                          {c}
                        </span>
                      ))}
                    </div>
                  )}
                </td>

                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    {row.critical > 0 && (
                      <span className="text-rose-600 font-bold">{row.critical} crit</span>
                    )}
                    {row.high > 0 && (
                      <span className="text-amber-600 font-bold">{row.high} high</span>
                    )}
                    {row.medium > 0 && (
                      <span className="text-blue-600">{row.medium} med</span>
                    )}
                    {row.critical === 0 && row.high === 0 && row.medium === 0 && (
                      <span className="text-slate-400">{row.low} low</span>
                    )}
                  </div>
                </td>

                <td className="py-3 px-4 text-slate-600 dark:text-slate-400">
                  {row.fanIn} in · {row.fanOut} out
                </td>

                <td className="py-3 px-4">
                  <span
                    className={`font-semibold ${
                      row.complexity === 'High'
                        ? 'text-rose-600 dark:text-rose-400'
                        : row.complexity === 'Medium'
                        ? 'text-amber-600 dark:text-amber-400'
                        : 'text-slate-500'
                    }`}
                  >
                    {row.complexity}
                  </span>
                </td>

                <td className="py-3 px-4 text-right font-bold text-slate-900 dark:text-slate-100">
                  {row.riskScore}
                </td>
              </tr>
            ))}
            {filteredRows.length === 0 && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500 font-sans text-xs">
                  No modules match the selected filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
