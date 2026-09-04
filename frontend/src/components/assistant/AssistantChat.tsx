import React, { useState, useEffect, useRef } from 'react';
import { useActiveFinding } from '@/lib/context/ActiveFindingContext';
import { queryAssistant, ChatMessage } from '@/lib/api/assistant';
import { SeverityBadge } from '@/components/common/Badges';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Terminal,
  Code2,
  BookOpen,
  HelpCircle,
  RotateCcw,
  Check,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';

export const AssistantChat: React.FC = () => {
  const { activeIssue, activeFilePath, activeReport, activeInitialPrompt } = useActiveFinding();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize conversation with welcome message or initial prompt
  useEffect(() => {
    if (messages.length === 0) {
      if (activeInitialPrompt && activeIssue) {
        handleUserSend(activeInitialPrompt);
      } else if (activeIssue) {
        setMessages([
          {
            id: 'init-1',
            role: 'assistant',
            content: `I have loaded finding **"${activeIssue.issue}"** at \`${activeFilePath}:${activeIssue.line}\`.\n\n` +
              `How can I help you? Choose one of the quick actions below or ask any specific technical question.`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      } else {
        setMessages([
          {
            id: 'init-2',
            role: 'assistant',
            content: `Welcome to **CodeGuard Assistant**.\n\n` +
              `I am grounded in CodeGuard's AST analysis, dataflow taint tracking, and repository intelligence.\n\n` +
              `Select a review or finding from the workspace to begin contextual investigation.`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }
    }
  }, [activeIssue, activeFilePath]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleUserSend = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || isTyping) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputQuery('');
    setIsTyping(true);

    try {
      const response = await queryAssistant({
        query,
        issue: activeIssue,
        filePath: activeFilePath,
        report: activeReport,
      });

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: 'Unable to process assistant query. Please try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const quickChips = [
    { label: 'Explain Finding', query: 'Explain this finding in detail' },
    { label: 'How to Fix', query: 'How do I fix this issue?' },
    { label: 'Show Taint Flow', query: 'Show me the dataflow and taint propagation' },
    { label: 'Teach Me Concept', query: 'Teach me the core security concept behind this' },
    { label: 'Summarize', query: 'Summarize the impact and severity of this finding' },
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-white dark:bg-[#0d111a] rounded-lg border border-slate-200 dark:border-slate-800 shadow-xs overflow-hidden">
      {/* Context Badge Bar */}
      <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800/80 bg-slate-50/70 dark:bg-slate-900/50 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs font-mono text-slate-700 dark:text-slate-300 truncate">
          <span className="font-bold text-slate-500 uppercase tracking-wider text-[10px]">Context:</span>
          {activeIssue ? (
            <>
              <SeverityBadge severity={activeIssue.severity} size="sm" />
              <span className="truncate font-semibold">{activeIssue.issue}</span>
              <span className="text-slate-400">·</span>
              <span className="text-slate-500 truncate">{activeFilePath}:{activeIssue.line}</span>
            </>
          ) : (
            <span className="text-slate-500">Repository Review Overview</span>
          )}
        </div>

        <span className="text-[11px] font-mono text-slate-400 dark:text-slate-500 hidden sm:inline">
          Grounded on CodeGuard AST &amp; Taint Engine
        </span>
      </div>

      {/* Message Conversation Stream */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser && (
                <div className="w-7 h-7 rounded-md bg-slate-900 text-white dark:bg-blue-600 dark:text-white flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold font-mono">
                  CG
                </div>
              )}

              <div
                className={`max-w-[85%] sm:max-w-[75%] rounded-lg p-3.5 text-xs sm:text-[13px] leading-relaxed ${
                  isUser
                    ? 'bg-blue-600 text-white rounded-br-xs'
                    : 'bg-slate-50 dark:bg-slate-900/80 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-800 rounded-bl-xs'
                }`}
              >
                {/* Parse Markdown blocks simply */}
                <div className="space-y-2 whitespace-pre-wrap font-sans">
                  {msg.content.split('\n\n').map((paragraph, pIdx) => {
                    if (paragraph.startsWith('```')) {
                      const lines = paragraph.replace(/```[a-z]*/g, '').trim();
                      return (
                        <pre
                          key={pIdx}
                          className="p-2.5 rounded bg-slate-950 text-slate-100 font-mono text-[11px] overflow-x-auto leading-relaxed border border-slate-800"
                        >
                          {lines}
                        </pre>
                      );
                    }
                    return (
                      <p key={pIdx} className="leading-relaxed">
                        {paragraph}
                      </p>
                    );
                  })}
                </div>

                <div
                  className={`mt-1.5 text-[10px] font-mono ${
                    isUser ? 'text-blue-200 text-right' : 'text-slate-400'
                  }`}
                >
                  {msg.timestamp}
                </div>
              </div>

              {isUser && (
                <div className="w-7 h-7 rounded-md bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300 flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold font-mono">
                  YOU
                </div>
              )}
            </div>
          );
        })}

        {isTyping && (
          <div className="flex items-center gap-2 text-slate-400 text-xs font-mono pl-10">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse" />
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse delay-100" />
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse delay-200" />
            <span>Analyzing code context...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Contextual Action Chips */}
      <div className="px-4 py-2 border-t border-slate-100 dark:border-slate-800/60 bg-slate-50/50 dark:bg-slate-900/30 overflow-x-auto">
        <div className="flex items-center gap-1.5 text-xs whitespace-nowrap">
          {quickChips.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleUserSend(chip.query)}
              disabled={isTyping}
              className="px-2.5 py-1 rounded-full text-[11px] font-medium border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:border-blue-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {chip.label}
            </button>
          ))}
        </div>
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleUserSend();
        }}
        className="p-3 border-t border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0d111a] flex items-center gap-2"
      >
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder={
            activeIssue
              ? `Ask about line ${activeIssue.line} (${activeIssue.issue})...`
              : 'Ask about this review or security concepts...'
          }
          className="flex-1 px-3 py-2 text-xs rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={!inputQuery.trim() || isTyping}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-md text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed shrink-0"
        >
          <Send className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Send</span>
        </button>
      </form>
    </div>
  );
};
