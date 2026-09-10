import React, { useState, useEffect } from 'react';
import { ReviewReport, ReviewIssue } from '@/types';
import { ReviewHeader } from './ReviewHeader';
import { ExecutiveOverview } from './ExecutiveOverview';
import { RepoIntelligence } from './RepoIntelligence';
import { FileTree } from './FileTree';
import { FindingList } from './FindingList';
import { CodeViewer } from './CodeViewer';
import { FindingDetails } from './FindingDetails';

interface ReviewWorkspaceProps {
  report: ReviewReport;
  onRefresh?: () => void;
}

export const ReviewWorkspace: React.FC<ReviewWorkspaceProps> = ({
  report,
  onRefresh,
}) => {
  const [activeView, setActiveView] = useState<'workspace' | 'overview' | 'intelligence'>('workspace');
  const [viewMode, setViewMode] = useState<'meaningful' | 'style' | 'suppressed'>('meaningful');

  // Initial file and finding
  const initialFile = report.file_reports[0]?.file_path || 'snippet.py';
  const [selectedFilePath, setSelectedFilePath] = useState<string>(initialFile);

  const initialIssues = report.file_reports?.[0]?.issues || [];
  const [selectedIssue, setSelectedIssue] = useState<ReviewIssue | null>(
    initialIssues[0] || null
  );

  // When selected file changes, ensure selected issue is in that file if possible
  const currentFileReport = report.file_reports?.find(
    (f) => f.file_path === selectedFilePath
  );
  const currentFileCode = currentFileReport?.file_content || '';
  const currentFileIssues = currentFileReport?.issues || [];

  const currentFindingIndex = selectedIssue
    ? currentFileIssues.findIndex(
        (i) => i.line === selectedIssue.line && i.issue === selectedIssue.issue
      )
    : -1;

  const handleSelectIssue = (filePath: string, issue: ReviewIssue) => {
    setSelectedFilePath(filePath);
    setSelectedIssue(issue);
  };

  const handleSelectFile = (filePath: string) => {
    setSelectedFilePath(filePath);
    const targetFile = report.file_reports?.find((f) => f.file_path === filePath);
    if (targetFile && Array.isArray(targetFile.issues) && targetFile.issues.length > 0) {
      setSelectedIssue(targetFile.issues[0]);
    } else {
      setSelectedIssue(null);
    }
  };

  const handleNavigateNext = () => {
    if (currentFindingIndex < currentFileIssues.length - 1) {
      setSelectedIssue(currentFileIssues[currentFindingIndex + 1]);
    }
  };

  const handleNavigatePrev = () => {
    if (currentFindingIndex > 0) {
      setSelectedIssue(currentFileIssues[currentFindingIndex - 1]);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#f8fafc] dark:bg-[#0a0d14]">
      {/* Review Header Bar */}
      <ReviewHeader
        report={report}
        activeView={activeView}
        onViewChange={setActiveView}
        onRefresh={onRefresh}
      />

      {/* Main View Area */}
      <div className="flex-1 flex flex-col min-h-0">
        {activeView === 'overview' && (
          <div className="flex-1 overflow-y-auto p-4 sm:p-6">
            <ExecutiveOverview
              report={report}
              onSelectFinding={(filePath, issue) => {
                handleSelectIssue(filePath, issue);
                setActiveView('workspace');
              }}
            />
          </div>
        )}

        {activeView === 'intelligence' && (
          <div className="flex-1 overflow-y-auto p-4 sm:p-6">
            <RepoIntelligence report={report} />
          </div>
        )}

        {activeView === 'workspace' && (
          <div className="flex-1 flex flex-col lg:flex-row min-h-0 border-t border-slate-200 dark:border-slate-800/80">
            {/* Left Column: File Tree & Finding List (Split vertically) */}
            <div className="w-full lg:w-80 xl:w-96 flex flex-col shrink-0 border-b lg:border-b-0 lg:border-r border-slate-200 dark:border-slate-800/80 min-h-[360px] lg:min-h-0">
              {/* Top: File Tree (35% height if multiple files) */}
              {report.file_reports.length > 1 ? (
                <>
                  <div className="h-44 shrink-0 overflow-hidden">
                    <FileTree
                      files={report.file_reports}
                      selectedFilePath={selectedFilePath}
                      onSelectFile={handleSelectFile}
                    />
                  </div>
                  <div className="flex-1 overflow-hidden border-t border-slate-200 dark:border-slate-800/80">
                    <FindingList
                      report={report}
                      selectedFilePath={selectedFilePath}
                      selectedIssue={selectedIssue}
                      onSelectIssue={handleSelectIssue}
                      mode={viewMode}
                      onModeChange={setViewMode}
                    />
                  </div>
                </>
              ) : (
                <div className="flex-1 overflow-hidden">
                  <FindingList
                    report={report}
                    selectedFilePath={selectedFilePath}
                    selectedIssue={selectedIssue}
                    onSelectIssue={handleSelectIssue}
                    mode={viewMode}
                    onModeChange={setViewMode}
                  />
                </div>
              )}
            </div>

            {/* Middle Column: Code Viewer */}
            <div className="flex-1 flex flex-col min-h-[400px] lg:min-h-0 overflow-hidden">
              <CodeViewer
                filePath={selectedFilePath}
                code={currentFileCode}
                highlightLine={selectedIssue?.line}
                highlightSeverity={selectedIssue?.severity}
                onNavigateNext={handleNavigateNext}
                onNavigatePrev={handleNavigatePrev}
                totalFindingsInFile={currentFileIssues.length}
                currentFindingIndexInFile={currentFindingIndex}
              />
            </div>

            {/* Right Column: Finding Details & Evidence */}
            <div className="w-full lg:w-96 xl:w-[420px] flex flex-col shrink-0 border-t lg:border-t-0 lg:border-l border-slate-200 dark:border-slate-800/80 min-h-[380px] lg:min-h-0">
              <FindingDetails
                filePath={selectedFilePath}
                issue={selectedIssue}
                fileContent={currentFileCode}
                report={report}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
