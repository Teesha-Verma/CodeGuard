import React from 'react';
import { Link } from 'react-router-dom';
import { CodeGuardLogo } from '@/components/common/Logo';
import { ThemeToggle } from '@/components/common/ThemeToggle';
import { ArrowLeft, Shield } from 'lucide-react';

interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle: string;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children, title, subtitle }) => {
  return (
    <div className="min-h-screen flex flex-col justify-between bg-slate-50 dark:bg-[#080c13] text-slate-900 dark:text-slate-100">
      {/* Top Navigation */}
      <header className="h-16 px-4 sm:px-8 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/70 dark:bg-[#0a0d14]/70 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link to="/" className="hover:opacity-90 transition-opacity">
            <CodeGuardLogo size="md" />
          </Link>
          <Link
            to="/"
            className="hidden sm:inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Home</span>
          </Link>
        </div>
        <ThemeToggle />
      </header>

      {/* Main Form Center Box */}
      <main className="flex-1 flex items-center justify-center p-4 sm:p-6 py-12">
        <div className="w-full max-w-md">
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-6 sm:p-8 shadow-xs">
            <div className="mb-6">
              <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
                {title}
              </h1>
              <p className="mt-1.5 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                {subtitle}
              </p>
            </div>

            {children}
          </div>

          <div className="mt-6 text-center text-xs text-slate-500 flex items-center justify-center gap-1.5 font-mono">
            <Shield className="w-3.5 h-3.5 text-slate-400" />
            <span>CodeGuard V2 Secure Session Gateway</span>
          </div>
        </div>
      </main>

      {/* Minimal Footer */}
      <footer className="py-4 text-center text-xs text-slate-500 border-t border-slate-200/50 dark:border-slate-800/50">
        <span>© {new Date().getFullYear()} CodeGuard. Deterministic static analysis and code review.</span>
      </footer>
    </div>
  );
};
