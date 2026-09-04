import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, ChevronRight, GitPullRequest, Code2 } from 'lucide-react';
import { ThemeToggle } from '@/components/common/ThemeToggle';

interface TopHeaderProps {
  onOpenMobileMenu?: () => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({ onOpenMobileMenu }) => {
  const { pathname } = useLocation();

  // Generate simple breadcrumb pieces
  const pathSegments = pathname.split('/').filter(Boolean);

  return (
    <header className="sticky top-0 z-30 h-14 border-b border-slate-200 dark:border-slate-800/80 bg-white/80 dark:bg-[#0a0d14]/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileMenu}
          className="md:hidden p-1.5 rounded-md text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Breadcrumb Navigation */}
        <nav className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
          <Link to="/dashboard" className="hover:text-slate-900 dark:hover:text-slate-200">
            CodeGuard
          </Link>
          {pathSegments.map((segment, idx) => {
            const isLast = idx === pathSegments.length - 1;
            const href = '/' + pathSegments.slice(0, idx + 1).join('/');

            return (
              <React.Fragment key={href}>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                {isLast ? (
                  <span className="text-slate-900 dark:text-slate-100 font-semibold truncate max-w-[180px] sm:max-w-none">
                    {segment.startsWith('rv_') ? segment : segment.replace(/-/g, ' ')}
                  </span>
                ) : (
                  <Link
                    to={href}
                    className="hover:text-slate-900 dark:hover:text-slate-200 capitalize"
                  >
                    {segment.replace(/-/g, ' ')}
                  </Link>
                )}
              </React.Fragment>
            );
          })}
        </nav>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-2 sm:gap-3">
        <Link
          to="/review/pr"
          className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-md border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors"
        >
          <GitPullRequest className="w-3.5 h-3.5 text-slate-500" />
          <span>Queue PR</span>
        </Link>
        <ThemeToggle />
      </div>
    </header>
  );
};
