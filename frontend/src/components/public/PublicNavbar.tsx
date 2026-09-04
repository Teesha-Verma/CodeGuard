import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { CodeGuardLogo } from '@/components/common/Logo';
import { ThemeToggle } from '@/components/common/ThemeToggle';
import { Menu, X, ArrowRight, GitPullRequest, Code2, ShieldCheck } from 'lucide-react';

export const PublicNavbar: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  return (
    <header
      className={`sticky top-0 z-40 w-full transition-all duration-200 ${
        scrolled
          ? 'border-b border-slate-200/90 dark:border-slate-800/90 bg-white/90 dark:bg-[#0a0d14]/90 backdrop-blur-md shadow-xs'
          : 'border-b border-slate-200/50 dark:border-slate-800/50 bg-white/70 dark:bg-[#0a0d14]/70 backdrop-blur-xs'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-15 flex items-center justify-between">
        {/* Left: Brand Logo */}
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center hover:opacity-90 transition-opacity" aria-label="CodeGuard Home">
            <CodeGuardLogo size="md" />
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-6" aria-label="Public Navigation">
            <a
              href="#overview"
              className="text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              Overview
            </a>
            <a
              href="#how-it-works"
              className="text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              How It Works
            </a>
            <a
              href="#capabilities"
              className="text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              Capabilities
            </a>
            <a
              href="#demo"
              className="text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              Live Demo
            </a>
            <a
              href="#workflow"
              className="text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              Workflow
            </a>
          </nav>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-3">
          <ThemeToggle />

          <div className="hidden sm:flex items-center gap-2">
            <Link
              to="/login"
              className="px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              Sign In
            </Link>

            <Link
              to="/review/pr"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-medium bg-slate-900 text-white hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-500 dark:text-white shadow-xs transition-colors"
            >
              <GitPullRequest className="w-3.5 h-3.5" />
              <span>Review a PR</span>
            </Link>
          </div>

          {/* Mobile Menu Toggle Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            type="button"
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
            className="md:hidden p-1.5 rounded-md text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] px-4 pt-3 pb-5 space-y-3">
          <nav className="flex flex-col space-y-2">
            <a
              href="#overview"
              onClick={() => setMobileMenuOpen(false)}
              className="px-2.5 py-1.5 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60"
            >
              Overview
            </a>
            <a
              href="#how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="px-2.5 py-1.5 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60"
            >
              How It Works
            </a>
            <a
              href="#capabilities"
              onClick={() => setMobileMenuOpen(false)}
              className="px-2.5 py-1.5 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60"
            >
              Capabilities
            </a>
            <a
              href="#demo"
              onClick={() => setMobileMenuOpen(false)}
              className="px-2.5 py-1.5 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60"
            >
              Live Demo
            </a>
            <a
              href="#workflow"
              onClick={() => setMobileMenuOpen(false)}
              className="px-2.5 py-1.5 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60"
            >
              Workflow
            </a>
          </nav>

          <div className="pt-3 border-t border-slate-200 dark:border-slate-800/80 flex flex-col gap-2">
            <Link
              to="/review/pr"
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium rounded-md bg-blue-600 text-white hover:bg-blue-500 transition-colors shadow-xs"
            >
              <GitPullRequest className="w-3.5 h-3.5" />
              <span>Review a Pull Request</span>
            </Link>
            <Link
              to="/review/snippet"
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium rounded-md border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Analyze Snippet</span>
            </Link>
            <div className="flex items-center justify-between px-2 pt-2 text-xs text-slate-500">
              <Link to="/login" className="hover:text-slate-900 dark:hover:text-slate-200 font-medium">
                Already have an account? Sign In
              </Link>
              <Link to="/signup" className="text-blue-600 dark:text-blue-400 font-medium hover:underline">
                Sign Up
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
