import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { SECURITY_TOPICS, SecurityTopic, getTopicById } from '@/lib/data/securityKnowledge';
import { MiniQuiz } from '@/components/learner/MiniQuiz';
import { useActiveFinding } from '@/lib/context/ActiveFindingContext';
import {
  GraduationCap,
  BookOpen,
  Code2,
  ShieldCheck,
  AlertTriangle,
  Terminal,
  CheckCircle2,
  ArrowRight,
  Search,
} from 'lucide-react';

export default function AcademyPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setActiveFinding } = useActiveFinding();

  const initialTopicId = searchParams.get('topic') || SECURITY_TOPICS[0].id;
  const [selectedTopic, setSelectedTopic] = useState<SecurityTopic>(() => {
    return getTopicById(initialTopicId) || SECURITY_TOPICS[0];
  });

  const [activeTab, setActiveTab] = useState<'concepts' | 'code' | 'detection' | 'quiz'>('concepts');

  useEffect(() => {
    const topicParam = searchParams.get('topic');
    if (topicParam) {
      const match = getTopicById(topicParam);
      if (match) setSelectedTopic(match);
    }
  }, [searchParams]);

  useEffect(() => {
    document.title = `${selectedTopic.title} — Security Academy | CodeGuard V2`;
  }, [selectedTopic]);

  const handlePracticeInPlayground = () => {
    // Preload playground with the vulnerable example
    setActiveFinding(
      {
        line: 6,
        severity: selectedTopic.severity,
        confidence: 0.94,
        issue: selectedTopic.title,
        root_cause: selectedTopic.summary,
        fix: selectedTopic.preventiveGuidelines[0],
        issue_type: 'security',
        source: selectedTopic.codeguardDetection.astRule,
        standards: [selectedTopic.cwe, selectedTopic.owasp],
        category: selectedTopic.category,
      },
      `${selectedTopic.id}.py`,
      selectedTopic.vulnerableExample
    );
    navigate('/playground');
  };

  return (
    <AppShell>
      <div className="flex-1 flex flex-col min-h-0 bg-slate-50/50 dark:bg-[#0a0d14]">
        {/* Top Header */}
        <div className="border-b border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0d111a] px-4 sm:px-8 py-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="p-1 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400">
                  <GraduationCap className="w-4 h-4" />
                </div>
                <span className="text-xs font-mono font-medium text-slate-500">
                  Developer Security Curriculum
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                Security Academy
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1">
                Master vulnerability patterns, exploitation mechanics, and AST/taint detection signatures.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handlePracticeInPlayground}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white shadow-xs transition-colors cursor-pointer"
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>Practice in Fix Playground</span>
              </button>
            </div>
          </div>
        </div>

        {/* Academy Main Grid */}
        <div className="flex-1 p-4 sm:p-6 overflow-hidden flex flex-col lg:flex-row gap-6 max-w-7xl mx-auto w-full">
          {/* Left Sidebar: Modules & Lessons */}
          <div className="w-full lg:w-72 shrink-0 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-4 flex flex-col overflow-y-auto">
            <span className="text-[10px] font-mono uppercase font-bold text-slate-500 tracking-wider mb-3">
              Curriculum Lessons ({SECURITY_TOPICS.length})
            </span>

            <div className="space-y-1.5">
              {SECURITY_TOPICS.map((topic) => {
                const isSelected = selectedTopic.id === topic.id;
                return (
                  <button
                    key={topic.id}
                    type="button"
                    onClick={() => {
                      setSelectedTopic(topic);
                      setActiveTab('concepts');
                    }}
                    className={`w-full text-left p-2.5 rounded-md text-xs transition-colors cursor-pointer flex items-start justify-between gap-2 ${
                      isSelected
                        ? 'bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400 font-semibold border border-blue-200 dark:border-blue-800/80'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60'
                    }`}
                  >
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 block mb-0.5">
                        {topic.cwe}
                      </span>
                      <span className="line-clamp-1 leading-snug">{topic.title}</span>
                    </div>
                    {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-blue-500 shrink-0 mt-1" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Main Panel: Lesson Content */}
          <div className="flex-1 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] flex flex-col overflow-hidden">
            {/* Topic Header */}
            <div className="p-5 border-b border-slate-200 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/30">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className="px-2 py-0.5 rounded font-mono text-xs font-bold bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300">
                  {selectedTopic.cwe}
                </span>
                <span className="px-2 py-0.5 rounded font-mono text-xs text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                  {selectedTopic.owasp}
                </span>
                <span className="px-2 py-0.5 rounded font-mono text-xs text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                  {selectedTopic.category}
                </span>
              </div>

              <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100">
                {selectedTopic.title}
              </h2>

              {/* Subtabs */}
              <div className="flex items-center gap-2 mt-4 pt-3 border-t border-slate-200 dark:border-slate-800 text-xs font-mono">
                {[
                  { id: 'concepts', label: '1. Concepts & Mechanics' },
                  { id: 'code', label: '2. Vulnerable vs Secure Code' },
                  { id: 'detection', label: '3. How CodeGuard Detects It' },
                  { id: 'quiz', label: '4. Knowledge Check' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`px-3 py-1.5 rounded-md transition-colors cursor-pointer ${
                      activeTab === tab.id
                        ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 font-bold'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Tab Contents */}
            <div className="flex-1 p-5 sm:p-6 overflow-y-auto space-y-6">
              {activeTab === 'concepts' && (
                <div className="space-y-5 text-xs">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-1.5">
                      Vulnerability Summary
                    </h3>
                    <p className="text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-900/50 p-3.5 rounded border border-slate-200 dark:border-slate-800">
                      {selectedTopic.summary}
                    </p>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-1.5">
                      Exploitation Mechanics
                    </h3>
                    <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                      {selectedTopic.mechanics}
                    </p>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-1.5">
                      Why It Matters (Impact)
                    </h3>
                    <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                      {selectedTopic.whyItMatters}
                    </p>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-2">
                      Core Preventive Guidelines
                    </h3>
                    <ul className="space-y-1.5">
                      {selectedTopic.preventiveGuidelines.map((guide, gidx) => (
                        <li key={gidx} className="flex items-start gap-2 text-slate-700 dark:text-slate-300">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                          <span>{guide}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {activeTab === 'code' && (
                <div className="space-y-5">
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-mono font-bold text-rose-600 dark:text-rose-400">
                        VULNERABLE PATTERN
                      </span>
                    </div>
                    <pre className="p-3.5 rounded-md bg-slate-950 text-rose-300 font-mono text-xs overflow-x-auto leading-relaxed border border-rose-900/40">
                      {selectedTopic.vulnerableExample}
                    </pre>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400">
                        SECURE REMEDIATION
                      </span>
                    </div>
                    <pre className="p-3.5 rounded-md bg-slate-950 text-emerald-300 font-mono text-xs overflow-x-auto leading-relaxed border border-emerald-900/40">
                      {selectedTopic.secureExample}
                    </pre>
                  </div>

                  <div className="pt-2">
                    <button
                      type="button"
                      onClick={handlePracticeInPlayground}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors cursor-pointer"
                    >
                      <Code2 className="w-3.5 h-3.5" />
                      <span>Open this snippet in Fix Playground</span>
                    </button>
                  </div>
                </div>
              )}

              {activeTab === 'detection' && (
                <div className="space-y-4 text-xs">
                  <div className="p-4 rounded border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40">
                    <span className="font-mono text-[10px] text-slate-500 font-bold uppercase block mb-1">
                      1. AST Visitor Detection Rule
                    </span>
                    <p className="text-slate-800 dark:text-slate-200 leading-relaxed font-mono text-[11.5px]">
                      {selectedTopic.codeguardDetection.astRule}
                    </p>
                  </div>

                  <div className="p-4 rounded border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40">
                    <span className="font-mono text-[10px] text-slate-500 font-bold uppercase block mb-1">
                      2. Taint Flow Behavior
                    </span>
                    <p className="text-slate-800 dark:text-slate-200 leading-relaxed">
                      {selectedTopic.codeguardDetection.taintBehavior}
                    </p>
                  </div>

                  <div className="p-4 rounded border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40">
                    <span className="font-mono text-[10px] text-slate-500 font-bold uppercase block mb-1">
                      3. Groq LLM Grounded Reasoning Pattern
                    </span>
                    <p className="text-slate-800 dark:text-slate-200 leading-relaxed">
                      {selectedTopic.codeguardDetection.reasoningPattern}
                    </p>
                  </div>
                </div>
              )}

              {activeTab === 'quiz' && (
                <MiniQuiz quiz={selectedTopic.quiz} />
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
