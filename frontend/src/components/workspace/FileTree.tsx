import React from 'react';
import { FileReport } from '@/types';
import { FileCode, Folder, ChevronDown } from 'lucide-react';

interface FileTreeProps {
  files: FileReport[];
  selectedFilePath: string;
  onSelectFile: (filePath: string) => void;
}

export const FileTree: React.FC<FileTreeProps> = ({
  files,
  selectedFilePath,
  onSelectFile,
}) => {
  return (
    <div className="h-full flex flex-col border-r border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0c1017]">
      {/* Header */}
      <div className="px-3 py-2.5 border-b border-slate-200 dark:border-slate-800/80 flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
          Changed Files ({files.length})
        </span>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {files.map((file) => {
          const isSelected = file.file_path === selectedFilePath;
          const issueCount = file.issues?.length || 0;
          const statusChar = file.status === 'added' ? 'A' : file.status === 'deleted' ? 'D' : 'M';
          const statusColor =
            statusChar === 'A'
              ? 'text-emerald-500'
              : statusChar === 'D'
              ? 'text-rose-500'
              : 'text-amber-500';

          return (
            <button
              key={file.file_path}
              type="button"
              onClick={() => onSelectFile(file.file_path)}
              className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left font-mono transition-colors ${
                isSelected
                  ? 'bg-blue-50 dark:bg-blue-500/15 text-blue-700 dark:text-blue-300 font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-2 truncate min-w-0">
                <span className={`text-[10px] font-bold ${statusColor}`}>{statusChar}</span>
                <FileCode className="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span className="truncate" title={file.file_path}>
                  {file.file_path}
                </span>
              </div>
              {issueCount > 0 && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ml-1.5 shrink-0 ${
                    isSelected
                      ? 'bg-blue-200 dark:bg-blue-900/60 text-blue-800 dark:text-blue-200'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                  }`}
                >
                  {issueCount}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
