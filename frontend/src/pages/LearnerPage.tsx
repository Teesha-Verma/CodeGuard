import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { useActiveFinding } from '@/lib/context/ActiveFindingContext';
import { LearnerCard } from '@/components/learner/LearnerCard';
import { getStoredReviews } from '@/lib/storage/reviews';
import { ReviewIssue } from '@/types';
import { BookOpen, Code2, Terminal, MessageSquare, ChevronDown, ListFilter, Sparkles } from 'lucide-react';

export default function LearnerPage() {
  const navigate = useNavigate();
  const { activeIssue, activeFilePath, activeFileContent, activeReport, setActiveFinding } =
    useActiveFinding();

  const [availableReviews] = useState(() => getStoredReviews());
  const [selectedReviewId, setSelectedReviewId] = useState<string>(
    activeReport?.review_id || availableReviews[0]?.review_id || ''
  );

  useEffect(() => {
    document.title = 'Learner Mode — CodeGuard V2';
  }, []);

  const currentReview =
    availableReviews.find((r) => r.review_id === selectedReviewId)?.report || activeReport;

  // Flatten all issues from the selected review
  const allReviewIssues: { filePath: string; issue: ReviewIssue }[] = [];
  if (currentReview && Array.isArray(currentReview.file_reports)) {
    currentReview.file_reports.forEach((f) => {
      if (Array.isArray(f?.issues)) {
        f.issues.forEach((iss) => {
          allReviewIssues.push({ filePath: f.file_path, issue: iss });
        });
      }
    });
  }

  const handleSelectFinding = (filePath: string, issue: ReviewIssue) => {
    const fileContent =
      currentReview?.file_reports.find((f) => f.file_path === filePath)?.file_content || '';
    setActiveFinding(issue, filePath, fileContent, currentReview);
  };

  return (
    <AppShell>
      <div className="flex-1 flex flex-col min-h-0 bg-slate-50/50 dark:bg-[#0a0d14]">
        {/* Page Top Banner */}
        <div className="border-b border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0d111a] px-4 sm:px-8 py-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="p-1 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400">
                  <BookOpen className="w-4 h-4" />
                </div>
                <span className="text-xs font-mono font-medium text-slate-500">
                  Developer Learning &amp; Remediation
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                Learner Mode
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1">
                Master security principles through deep contextual analysis of your real CodeGuard findings.
              </p>
            </div>

            {/* Quick Finding Selector */}
            {allReviewIssues.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 font-mono hidden sm:inline">Active Finding:</span>
                <div className="relative">
                  <select
                    value={activeIssue ? `${activeFilePath}:${activeIssue.line}` : ''}
                    onChange={(e) => {
                      const [path, lineStr] = e.target.value.split(':');
                      const line = Number(lineStr);
                      const match = allReviewIssues.find(
                        (item) => item.filePath === path && item.issue.line === line
                      );
                      if (match) handleSelectFinding(match.filePath, match.issue);
                    }}
                    className="appearance-none pl-3 pr-8 py-1.5 text-xs font-mono rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 max-w-[280px] truncate"
                  >
                    {allReviewIssues.map((item, idx) => (
                      <option key={idx} value={`${item.filePath}:${item.issue.line}`}>
                        [{item.issue.severity.toUpperCase()}] {item.issue.issue} ({item.filePath}:{item.issue.line})
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-8 max-w-5xl mx-auto w-full">
          {activeIssue ? (
            <LearnerCard
              issue={activeIssue}
              filePath={activeFilePath || 'snippet.py'}
              onFixInPlayground={() => navigate('/playground')}
              onShowDataflow={() => navigate('/dataflow')}
              onAskAssistant={() => navigate('/assistant')}
            />
          ) : (
            <div className="p-8 text-center rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a]">
              <BookOpen className="w-8 h-8 text-slate-400 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200">
                No Finding Loaded
              </h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                Select a finding from the dropdown above or click [ Learn Why ] on any issue inside the review workspace.
              </p>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
