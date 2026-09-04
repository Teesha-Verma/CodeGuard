import React from 'react';

interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showVersion?: boolean;
}

export const CodeGuardLogo: React.FC<LogoProps> = ({
  className = '',
  size = 'md',
  showVersion = false,
}) => {
  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  const textSizes = {
    sm: 'text-sm',
    md: 'text-base font-semibold',
    lg: 'text-lg font-bold',
  };

  return (
    <div className={`flex items-center gap-2.5 select-none ${className}`}>
      {/* Minimal geometric shield and code angle glyph */}
      <div className="relative flex items-center justify-center p-1.5 rounded-md bg-blue-600/10 dark:bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={iconSizes[size]}
        >
          {/* Outer Shield Outline */}
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          {/* Inner Code Bracket */}
          <path d="M9.5 9l-2.5 3 2.5 3" />
          <path d="M14.5 9l2.5 3-2.5 3" />
        </svg>
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className={`tracking-tight text-slate-900 dark:text-slate-100 ${textSizes[size]}`}>
          CodeGuard
        </span>
        <span className="text-xs font-mono font-medium px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
          V2
        </span>
        {showVersion && (
          <span className="text-[10px] text-slate-500 font-mono">2.0.0</span>
        )}
      </div>
    </div>
  );
};
