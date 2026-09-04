import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { CodeGuardLogo } from '@/components/common/Logo';
import { BackendStatusBadge } from '@/components/common/BackendStatusBadge';
import {
  LayoutDashboard,
  GitPullRequest,
  Code2,
  ListFilter,
  Settings,
  PlusCircle,
  ShieldCheck,
  ShieldAlert,
  Terminal,
  BookOpen,
  GraduationCap,
  Layers,
  Bot,
  PlayCircle,
} from 'lucide-react';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen = false, onClose }) => {
  const { pathname } = useLocation();

  const navSections = [
    {
      section: null,
      items: [{ label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard }],
    },
    {
      section: 'Reviews',
      items: [
        { label: 'PR reviews', href: '/review/pr', icon: GitPullRequest },
        { label: 'Snippet review', href: '/review/snippet', icon: Code2 },
        { label: 'Review History', href: '/reviews', icon: ListFilter },
      ],
    },
    {
      section: 'Security',
      items: [
        { label: 'Security Health', href: '/security', icon: ShieldCheck },
        { label: 'Risk View', href: '/security/risk', icon: ShieldAlert },
        { label: 'Dataflow', href: '/dataflow', icon: Terminal },
      ],
    },
    {
      section: 'Learn',
      items: [
        { label: 'Learner Mode', href: '/learn', icon: BookOpen },
        { label: 'Academy', href: '/learn/academy', icon: GraduationCap },
        { label: 'Knowledge Base', href: '/learn/knowledge', icon: Layers },
      ],
    },
    {
      section: 'Assistant & Tools',
      items: [
        { label: 'AI Assistant', href: '/assistant', icon: Bot },
        { label: 'Fix Playground', href: '/playground', icon: PlayCircle },
        { label: 'Settings', href: '/settings', icon: Settings },
      ],
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-xs md:hidden"
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 border-r border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0d111a] flex flex-col transition-transform duration-200 ease-in-out md:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Top Logo */}
        <div className="h-14 px-5 border-b border-slate-200 dark:border-slate-800/80 flex items-center justify-between">
          <Link to="/dashboard" className="hover:opacity-90 transition-opacity">
            <CodeGuardLogo size="md" />
          </Link>
        </div>

        {/* Quick Action Button */}
        <div className="p-3">
          <Link
            to="/review/snippet"
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium rounded-md bg-slate-900 text-white hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white transition-colors shadow-xs"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>New review</span>
          </Link>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 px-3 space-y-4 overflow-y-auto pb-4">
          {navSections.map((group, gIdx) => (
            <div key={gIdx} className="space-y-1">
              {group.section && (
                <div className="px-3 pt-2 pb-1 text-[10px] font-mono uppercase font-bold tracking-wider text-slate-400 dark:text-slate-500">
                  {group.section}
                </div>
              )}
              {group.items.map((item) => {
                const isActive =
                  item.href === '/dashboard' ||
                  item.href === '/security' ||
                  item.href === '/learn' ||
                  item.href === '/reviews'
                    ? pathname === item.href
                    : pathname === item.href || pathname.startsWith(item.href + '/');
                const Icon = item.icon;

                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    onClick={onClose}
                    className={`flex items-center gap-3 px-3 py-2 text-xs font-medium rounded-md transition-colors ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400 font-semibold'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200'
                    }`}
                  >
                    <Icon
                      className={`w-4 h-4 ${
                        isActive
                          ? 'text-blue-600 dark:text-blue-400'
                          : 'text-slate-400 dark:text-slate-500'
                      }`}
                    />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Bottom Metadata & System Status */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800/80 space-y-3 bg-slate-50/50 dark:bg-[#0b0e16]/50">
          <BackendStatusBadge />
          <div className="flex items-center justify-between text-[11px] text-slate-600 dark:text-slate-400 font-mono">
            <span>Engine V2.0</span>
            <span className="text-slate-600 dark:text-slate-400">llama-3.3-70b</span>
          </div>
        </div>
      </aside>
    </>
  );
};
