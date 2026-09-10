import React, { useState } from 'react';
import { SeverityBadge } from '@/components/common/Badges';
import {
  ShieldAlert,
  AlertTriangle,
  Code2,
  Terminal,
  Cpu,
  Layers,
  ArrowRight,
  Check,
  Copy,
  CheckCircle2,
} from 'lucide-react';

interface FindingExample {
  id: string;
  tabLabel: string;
  filename: string;
  lineFlagged: number;
  severity: 'critical' | 'high' | 'medium';
  cwe: string;
  title: string;
  detectionSources: string[];
  reasoningEngine: string;
  rootCause: string;
  impact: string;
  vulnerableCode: { line: number; text: string; isFlagged?: boolean }[];
  fixDiff: { type: 'comment' | 'rem' | 'add'; text: string }[];
  fixExplanation: string;
}

const EXAMPLES: FindingExample[] = [
  {
    id: 'sql-injection',
    tabLabel: 'SQL Injection (CWE-89)',
    filename: 'services/user_service.py',
    lineFlagged: 18,
    severity: 'critical',
    cwe: 'CWE-89 · OWASP A03:2021',
    title: 'Direct String Concatenation in SQL Query',
    detectionSources: ['AST BinOp Tracker', 'Taint Source: request.args', 'Security Rule R-SQL-01'],
    reasoningEngine: 'Groq Llama-3 Reasoning',
    rootCause:
      'User-supplied parameter username is formatted directly into a raw SQL query string without parameterized placeholders or escaping.',
    impact:
      'Full database authentication bypass and arbitrary read/write access to customer records.',
    vulnerableCode: [
      { line: 15, text: 'def get_user_profile(request):' },
      { line: 16, text: "    user_id = request.args.get('user_id')" },
      { line: 17, text: '    cursor = db.connection.cursor()' },
      {
        line: 18,
        text: '    query = f"SELECT * FROM users WHERE id = \'{user_id}\'"',
        isFlagged: true,
      },
      { line: 19, text: '    cursor.execute(query)' },
      { line: 20, text: '    return cursor.fetchone()' },
    ],
    fixDiff: [
      { type: 'comment', text: '# Use parameterized queries with db engine bind parameters' },
      { type: 'rem', text: '- query = f"SELECT * FROM users WHERE id = \'{user_id}\'"' },
      { type: 'rem', text: '- cursor.execute(query)' },
      { type: 'add', text: '+ query = "SELECT * FROM users WHERE id = %s"' },
      { type: 'add', text: '+ cursor.execute(query, (user_id,))' },
    ],
    fixExplanation:
      'Parameterized queries delegate input isolation to the database engine driver, preventing malicious SQL control tokens from changing the query AST.',
  },
  {
    id: 'pickle-deser',
    tabLabel: 'Insecure Deserialization (CWE-502)',
    filename: 'cache/session_loader.py',
    lineFlagged: 24,
    severity: 'critical',
    cwe: 'CWE-502 · OWASP A08:2021',
    title: 'Unsafe Deserialization via pickle.loads',
    detectionSources: ['AST Call Node: pickle.loads', 'Taint Source: redis_client', 'Groq Reasoning'],
    reasoningEngine: 'Groq Llama-3 Reasoning',
    rootCause:
      'Cached session data loaded directly using Python standard library pickle.loads without signature verification.',
    impact:
      'Remote Code Execution (RCE) if an attacker can write to or poison the cache storage layer.',
    vulnerableCode: [
      { line: 21, text: 'def restore_session(token: str):' },
      { line: 22, text: '    raw_bytes = redis_client.get(f"sess:{token}")' },
      { line: 23, text: '    if not raw_bytes: return None' },
      {
        line: 24,
        text: '    session_state = pickle.loads(raw_bytes)',
        isFlagged: true,
      },
      { line: 25, text: '    return session_state' },
    ],
    fixDiff: [
      { type: 'comment', text: '# Replace pickle with structured, non-executable JSON or safe serializer' },
      { type: 'rem', text: '- session_state = pickle.loads(raw_bytes)' },
      { type: 'add', text: '+ import json' },
      { type: 'add', text: '+ session_state = json.loads(raw_bytes.decode("utf-8"))' },
    ],
    fixExplanation:
      'JSON serializers deserialize data structures without executing arbitrary python __reduce__ object hooks.',
  },
  {
    id: 'ssrf',
    tabLabel: 'Server-Side Request Forgery (CWE-918)',
    filename: 'integrations/webhook_sender.py',
    lineFlagged: 31,
    severity: 'high',
    cwe: 'CWE-918 · OWASP A10:2021',
    title: 'Unvalidated Outbound HTTP Request',
    detectionSources: ['AST Call: httpx.get', 'Taint Tracker: webhook_url', 'IP Filter Check'],
    reasoningEngine: 'Groq Llama-3 Reasoning',
    rootCause:
      'The destination URL supplied by the user is requested directly without verifying internal IP address ranges (e.g., 169.254.169.254 or localhost).',
    impact:
      'Cloud metadata credential harvesting and internal infrastructure network port enumeration.',
    vulnerableCode: [
      { line: 28, text: 'async def dispatch_webhook(event_payload):' },
      { line: 29, text: "    target_url = event_payload.get('callback_url')" },
      { line: 30, text: '    async with httpx.AsyncClient() as client:' },
      {
        line: 31,
        text: '        response = await client.get(target_url, timeout=5.0)',
        isFlagged: true,
      },
      { line: 32, text: '    return response.status_code' },
    ],
    fixDiff: [
      { type: 'comment', text: '# Validate URL hostname and disallow loopback/private IPv4 ranges' },
      { type: 'rem', text: '- response = await client.get(target_url, timeout=5.0)' },
      { type: 'add', text: '+ safe_url = validate_public_url(target_url)' },
      { type: 'add', text: '+ response = await client.get(safe_url, timeout=5.0)' },
    ],
    fixExplanation:
      'DNS resolution and IP range validation ensures outbound requests never reach cloud metadata instances or internal VPC boundaries.',
  },
];

export const SecurityFindingDemo: React.FC = () => {
  const [selectedExample, setSelectedExample] = useState<FindingExample>(EXAMPLES[0]);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const diffText = selectedExample.fixDiff.map((d) => d.text).join('\n');
    navigator.clipboard.writeText(diffText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="py-20 md:py-28 border-t border-slate-200 dark:border-slate-800/80 bg-slate-50/50 dark:bg-[#070a0f]" id="demo">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="max-w-3xl mb-10 md:mb-14">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded text-xs font-mono font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 mb-3">
            <span>Product Demonstration Visual</span>
          </div>
          <h2 className="text-2xl sm:text-4xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
            Anatomy of a CodeGuard Finding
          </h2>
          <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-400 leading-relaxed">
            Every issue detected by CodeGuard connects vulnerable line numbers to concrete root cause analysis and a verified replacement fix.
          </p>
        </div>

        {/* Vulnerability Scenario Switcher */}
        <div className="flex flex-wrap gap-2 mb-6">
          {EXAMPLES.map((ex) => (
            <button
              key={ex.id}
              onClick={() => setSelectedExample(ex)}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-all ${
                selectedExample.id === ex.id
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
              }`}
            >
              {ex.tabLabel}
            </button>
          ))}
        </div>

        {/* Demonstration Workspace Container */}
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] shadow-sm overflow-hidden">
          {/* Header Bar */}
          <div className="px-4 sm:px-6 py-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-[#0a0d14] flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs font-mono text-slate-600 dark:text-slate-300">
              <Code2 className="w-4 h-4 text-blue-500" />
              <span>{selectedExample.filename}</span>
              <span className="text-slate-400">·</span>
              <span className="text-orange-500 font-semibold">Line {selectedExample.lineFlagged}</span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono text-slate-500">
                {selectedExample.reasoningEngine}
              </span>
              <SeverityBadge severity={selectedExample.severity} size="sm" />
            </div>
          </div>

          {/* Demonstration Content: Split Code vs Finding Analysis */}
          <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[380px]">
            {/* Left: Code Block with Highlight */}
            <div className="lg:col-span-6 p-4 sm:p-5 border-b lg:border-b-0 lg:border-r border-slate-200 dark:border-slate-800 bg-slate-950 text-slate-100 font-mono text-xs overflow-x-auto">
              <div className="text-[11px] text-slate-500 pb-2 mb-3 border-b border-slate-800 flex items-center justify-between">
                <span>Code Inspection</span>
                <span>Python AST Target</span>
              </div>

              <div className="space-y-1.5 leading-relaxed">
                {selectedExample.vulnerableCode.map((line) => (
                  <div
                    key={line.line}
                    className={`flex items-start gap-4 -mx-4 px-4 py-0.5 ${
                      line.isFlagged
                        ? 'bg-red-950/60 border-l-2 border-red-500 text-red-200 font-semibold'
                        : 'text-slate-400'
                    }`}
                  >
                    <span
                      className={`w-5 select-none text-right ${
                        line.isFlagged ? 'text-red-400 font-bold' : 'text-slate-600'
                      }`}
                    >
                      {line.line}
                    </span>
                    <span className="whitespace-pre">{line.text}</span>
                  </div>
                ))}
              </div>

              {/* Inline warning badge */}
              <div className="mt-6 p-2.5 rounded bg-red-900/20 border border-red-800/40 text-[11px] text-red-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                <span>Detection trigger: Unsanitized AST dataflow sink reached.</span>
              </div>
            </div>

            {/* Right: Detailed Finding Breakdown */}
            <div className="lg:col-span-6 p-4 sm:p-6 flex flex-col justify-between space-y-5 bg-white dark:bg-[#0d111a]">
              <div className="space-y-4">
                <div>
                  <div className="text-[10px] font-mono uppercase text-slate-500 mb-1">
                    {selectedExample.cwe}
                  </div>
                  <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                    {selectedExample.title}
                  </h3>
                </div>

                {/* Evidence Sources */}
                <div>
                  <span className="text-[10px] font-mono uppercase text-slate-500 tracking-wider block mb-1.5">
                    Detection Sources
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedExample.detectionSources.map((src) => (
                      <span
                        key={src}
                        className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                      >
                        {src}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Root Cause & Impact */}
                <div className="space-y-2 text-xs">
                  <div className="p-3 rounded bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
                    <span className="text-[10px] font-mono uppercase text-slate-500 font-bold block mb-1">
                      Root Cause
                    </span>
                    <p className="text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed">
                      {selectedExample.rootCause}
                    </p>
                  </div>

                  <div className="p-3 rounded bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
                    <span className="text-[10px] font-mono uppercase text-slate-500 font-bold block mb-1">
                      Impact
                    </span>
                    <p className="text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed">
                      {selectedExample.impact}
                    </p>
                  </div>
                </div>

                {/* Recommended Fix Diff */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono uppercase text-slate-500 font-bold">
                      Recommended Fix (Diff)
                    </span>
                    <button
                      onClick={handleCopy}
                      className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-500 hover:text-slate-900 dark:hover:text-slate-100"
                    >
                      {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                      <span>{copied ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>

                  <div className="p-3 rounded bg-slate-950 text-slate-100 font-mono text-[11px] leading-relaxed space-y-0.5 overflow-x-auto">
                    {selectedExample.fixDiff.map((d, i) => (
                      <div
                        key={i}
                        className={`${
                          d.type === 'rem'
                            ? 'bg-red-950/70 text-red-300'
                            : d.type === 'add'
                            ? 'bg-emerald-950/70 text-emerald-300 font-semibold'
                            : 'text-slate-500'
                        } px-1.5 py-0.5 rounded`}
                      >
                        {d.text}
                      </div>
                    ))}
                  </div>

                  <p className="text-[10px] text-slate-500 leading-relaxed">
                    {selectedExample.fixExplanation}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
