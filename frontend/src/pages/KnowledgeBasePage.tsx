import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { SECURITY_TOPICS } from '@/lib/data/securityKnowledge';
import { apiClient } from '@/lib/api/client';
import {
  BookOpen,
  Search,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  GraduationCap,
  Code2,
  Sparkles,
} from 'lucide-react';

export default function KnowledgeBasePage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [topics, setTopics] = useState(SECURITY_TOPICS);

  useEffect(() => {
    document.title = 'Security Knowledge Base — CodeGuard V2';
  }, []);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .getKnowledgeTopics({
        category: selectedCategory !== 'ALL' ? selectedCategory : undefined,
        query: searchQuery || undefined,
      })
      .then((topicList) => {
        if (!cancelled && Array.isArray(topicList) && topicList.length > 0) {
          const remoteList = topicList.map((rt) => {
            const localMatch = SECURITY_TOPICS.find((st) => st.id === rt.id || st.cwe === rt.cwe);
            return (
              localMatch || {
                id: rt.id,
                title: rt.title,
                cwe: rt.cwe,
                owasp: rt.owasp,
                category: rt.category as any,
                severity: rt.severity as any,
                summary: rt.summary,
                whyItMatters: '',
                mechanics: '',
                vulnerableExample: '',
                secureExample: '',
                preventiveGuidelines: [] as string[],
                codeguardDetection: { astRule: '', taintBehavior: '', reasoningPattern: '' },
                quiz: { question: '', options: [] as string[], correctIndex: 0, explanation: '' },
              }
            );
          });
          setTopics(remoteList);
        }
      })
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, [searchQuery, selectedCategory]);

  const categories = ['ALL', 'Injection', 'Authentication', 'Memory & Deserialization', 'Network', 'Data Protection', 'Configuration'];

  const filteredTopics = topics.filter((t) => {
    if (selectedCategory !== 'ALL' && t.category !== selectedCategory) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        t.title.toLowerCase().includes(q) ||
        t.cwe.toLowerCase().includes(q) ||
        t.summary.toLowerCase().includes(q) ||
        t.category.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <AppShell>
      <div className="flex-1 flex flex-col min-h-0 bg-slate-50/50 dark:bg-[#0a0d14]">
        {/* Top Header */}
        <div className="border-b border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0d111a] px-4 sm:px-8 py-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="p-1 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400">
                  <BookOpen className="w-4 h-4" />
                </div>
                <span className="text-xs font-mono font-medium text-slate-500">
                  Vulnerability &amp; Standards Knowledge Base
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                Security Knowledge Base
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1">
                Searchable database of CWE standards, vulnerability root causes, and verified remediations.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Link
                to="/learn/academy"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-slate-900 text-white hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white transition-colors"
              >
                <GraduationCap className="w-3.5 h-3.5" />
                <span>Academy Lessons</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <div className="border-b border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0d111a] px-4 sm:px-8 py-3.5">
          <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="relative w-full sm:w-96">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by keyword, CWE-89, category..."
                className="w-full pl-9 pr-3 py-1.5 text-xs rounded-md border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex flex-wrap items-center gap-1.5 self-start sm:self-auto text-xs overflow-x-auto">
              {categories.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2.5 py-1 rounded-md font-mono text-[11px] font-medium transition-colors cursor-pointer ${
                    selectedCategory === cat
                      ? 'bg-blue-600 text-white font-bold'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Topic Grid */}
        <div className="flex-1 p-4 sm:p-8 overflow-y-auto max-w-6xl mx-auto w-full">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredTopics.map((topic) => (
              <div
                key={topic.id}
                className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 shadow-xs flex flex-col justify-between hover:border-blue-400 dark:hover:border-blue-700 transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-1.5">
                      <span className="px-2 py-0.5 rounded font-mono text-[11px] font-bold bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300">
                        {topic.cwe}
                      </span>
                      <span className="text-xs font-mono text-slate-500">
                        {topic.category}
                      </span>
                    </div>
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                        topic.severity === 'critical'
                          ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300'
                          : 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300'
                      }`}
                    >
                      {topic.severity.toUpperCase()}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-2 leading-snug">
                    {topic.title}
                  </h3>

                  <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-3 leading-relaxed">
                    {topic.summary}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                  <span className="text-[11px] font-mono text-slate-400">
                    {topic.owasp}
                  </span>
                  <Link
                    to={`/learn/academy?topic=${topic.id}`}
                    className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    <span>View lesson &amp; fix</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>

          {filteredTopics.length === 0 && (
            <div className="p-8 text-center rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a]">
              <p className="text-xs text-slate-500">
                No security topics found matching your query.
              </p>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
