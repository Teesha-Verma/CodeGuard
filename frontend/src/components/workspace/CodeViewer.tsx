import React, { useRef, useEffect, useState } from 'react';
import { Copy, Check, ChevronUp, ChevronDown, Code, Sparkles } from 'lucide-react';
import { Severity } from '@/types';

interface CodeViewerProps {
  filePath: string;
  code: string;
  highlightLine?: number;
  highlightSeverity?: Severity | string;
  onNavigatePrev?: () => void;
  onNavigateNext?: () => void;
  totalFindingsInFile?: number;
  currentFindingIndexInFile?: number;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  filePath,
  code,
  highlightLine,
  highlightSeverity = 'critical',
  onNavigatePrev,
  onNavigateNext,
  totalFindingsInFile = 0,
  currentFindingIndexInFile = 0,
}) => {
  const [copied, setCopied] = useState(false);
  const lineRefs = useRef<Record<number, HTMLDivElement | null>>({});
  const containerRef = useRef<HTMLDivElement | null>(null);

  const lines = code ? code.split('\n') : ['# No file contents available for preview'];

  // Scroll target line into view smoothly whenever highlightLine changes
  useEffect(() => {
    if (highlightLine && lineRefs.current[highlightLine]) {
      lineRefs.current[highlightLine]?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [highlightLine]);

  const handleCopy = () => {
    if (!code) return;
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const sev = (highlightSeverity || 'critical').toLowerCase();
  const highlightStyles: Record<string, string> = {
    critical: 'bg-red-500/15 border-l-4 border-l-red-500 text-red-950 dark:text-red-100',
    high: 'bg-orange-500/15 border-l-4 border-l-orange-500 text-orange-950 dark:text-orange-100',
    medium: 'bg-amber-500/15 border-l-4 border-l-amber-500 text-amber-950 dark:text-amber-100',
    low: 'bg-emerald-500/15 border-l-4 border-l-emerald-500 text-emerald-950 dark:text-emerald-100',
    info: 'bg-blue-500/15 border-l-4 border-l-blue-500 text-blue-950 dark:text-blue-100',
  };

  return (
    <div className="h-full flex flex-col bg-white dark:bg-[#090d14] overflow-hidden">
      {/* Code Viewer Header */}
      <div className="h-10 px-4 border-b border-slate-200 dark:border-slate-800/80 flex items-center justify-between bg-slate-50 dark:bg-[#0c1017] shrink-0">
        <div className="flex items-center gap-2 font-mono text-xs text-slate-700 dark:text-slate-300 truncate">
          <Code className="w-3.5 h-3.5 text-slate-400" />
          <span className="font-semibold text-slate-900 dark:text-slate-100">{filePath}</span>
          {highlightLine && (
            <span className="text-slate-600 dark:text-slate-400 font-mono text-[11px]">
              (Target line: {highlightLine})
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          {totalFindingsInFile > 0 && (
            <div className="flex items-center gap-1 mr-2 text-[11px] font-mono text-slate-500">
              <span>
                {currentFindingIndexInFile + 1} of {totalFindingsInFile}
              </span>
              <div className="flex items-center">
                <button
                  type="button"
                  onClick={onNavigatePrev}
                  className="p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 disabled:opacity-30"
                  disabled={currentFindingIndexInFile <= 0}
                  title="Previous finding in this file"
                >
                  <ChevronUp className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={onNavigateNext}
                  className="p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 disabled:opacity-30"
                  disabled={currentFindingIndexInFile >= totalFindingsInFile - 1}
                  title="Next finding in this file"
                >
                  <ChevronDown className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1 px-2 py-1 rounded text-xs font-mono text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
            title="Copy file contents"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-emerald-500" />
                <span className="text-emerald-500">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Code Editor / Line Viewer */}
      <div
        ref={containerRef}
        className="flex-1 overflow-auto font-mono text-xs leading-relaxed select-text p-1"
      >
        <div className="min-w-full inline-block">
          {lines.map((lineContent, index) => {
            const lineNum = index + 1;
            const isTarget = lineNum === highlightLine;

            return (
              <div
                key={lineNum}
                ref={(el) => {
                  lineRefs.current[lineNum] = el;
                }}
                className={`flex items-stretch group transition-colors ${
                  isTarget
                    ? highlightStyles[sev] || highlightStyles.critical
                    : 'hover:bg-slate-100/50 dark:hover:bg-slate-800/30'
                }`}
              >
                {/* Gutter / Line Number */}
                <div
                  className={`w-12 py-0.5 pr-3 text-right shrink-0 select-none text-[11px] font-mono border-r border-slate-200 dark:border-slate-800/80 ${
                    isTarget
                      ? 'text-red-600 dark:text-red-400 font-bold bg-red-500/10'
                      : 'text-slate-500 dark:text-slate-600 bg-slate-50/50 dark:bg-[#0a0d14]'
                  }`}
                >
                  {lineNum}
                </div>

                {/* Line Code Content */}
                <div className="flex-1 py-0.5 pl-3 whitespace-pre font-mono overflow-x-visible">
                  <span
                    className={
                      isTarget
                        ? 'font-semibold text-slate-950 dark:text-white'
                        : 'text-slate-800 dark:text-slate-300'
                    }
                  >
                    {lineContent || ' '}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
