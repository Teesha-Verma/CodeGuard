import React, { createContext, useContext, useState, useEffect } from 'react';
import { ReviewIssue, ReviewReport } from '@/types';
import { getStoredReviews } from '@/lib/storage/reviews';
import { SAMPLE_REPORT_PR42 } from '@/lib/data/sampleReviews';

export interface ActiveFindingContextType {
  activeIssue: ReviewIssue | null;
  activeFilePath: string;
  activeFileContent: string;
  activeReport: ReviewReport | null;
  activeInitialPrompt?: string;
  setActiveFinding: (
    issue: ReviewIssue,
    filePath: string,
    fileContent: string,
    report?: ReviewReport | null,
    initialPrompt?: string
  ) => void;
  clearActiveFinding: () => void;
}

const ActiveFindingContext = createContext<ActiveFindingContextType | undefined>(undefined);

export const ActiveFindingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeIssue, setActiveIssue] = useState<ReviewIssue | null>(null);
  const [activeFilePath, setActiveFilePath] = useState<string>('');
  const [activeFileContent, setActiveFileContent] = useState<string>('');
  const [activeReport, setActiveReport] = useState<ReviewReport | null>(null);
  const [activeInitialPrompt, setActiveInitialPrompt] = useState<string | undefined>(undefined);

  // Initialize with a default finding from stored reviews so direct sidebar entry has context
  useEffect(() => {
    if (!activeIssue) {
      const stored = getStoredReviews();
      const firstReport = stored.find((r) => r.report && r.report.file_reports?.length > 0)?.report || SAMPLE_REPORT_PR42;

      if (firstReport && firstReport.file_reports.length > 0) {
        const fileReport = firstReport.file_reports.find((f) => f.issues.length > 0) || firstReport.file_reports[0];
        if (fileReport && fileReport.issues.length > 0) {
          setActiveReport(firstReport);
          setActiveFilePath(fileReport.file_path);
          setActiveFileContent(fileReport.file_content || '');
          setActiveIssue(fileReport.issues[0]);
        }
      }
    }
  }, [activeIssue]);

  const setActiveFinding = (
    issue: ReviewIssue,
    filePath: string,
    fileContent: string,
    report?: ReviewReport | null,
    initialPrompt?: string
  ) => {
    setActiveIssue(issue);
    setActiveFilePath(filePath);
    setActiveFileContent(fileContent);
    if (report !== undefined) {
      setActiveReport(report);
    }
    setActiveInitialPrompt(initialPrompt);
  };

  const clearActiveFinding = () => {
    setActiveIssue(null);
    setActiveFilePath('');
    setActiveFileContent('');
    setActiveReport(null);
    setActiveInitialPrompt(undefined);
  };

  return (
    <ActiveFindingContext.Provider
      value={{
        activeIssue,
        activeFilePath,
        activeFileContent,
        activeReport,
        activeInitialPrompt,
        setActiveFinding,
        clearActiveFinding,
      }}
    >
      {children}
    </ActiveFindingContext.Provider>
  );
};

export function useActiveFinding(): ActiveFindingContextType {
  const context = useContext(ActiveFindingContext);
  if (!context) {
    throw new Error('useActiveFinding must be used within an ActiveFindingProvider');
  }
  return context;
}
