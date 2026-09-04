import React from 'react';
import {
  Code2,
  GitFork,
  Layers,
  Database,
  ShieldCheck,
  Terminal,
  Search,
  Cpu,
  ArrowUpRight,
} from 'lucide-react';

export const CapabilitiesSection: React.FC = () => {
  const capabilities = [
    {
      title: 'Python AST & Structural Parsing',
      category: 'Static Engine',
      description:
        'Parses python modules into an abstract syntax tree without runtime execution. Detects dangerous patterns like dynamic code execution, unsafe deserialization, and dangerous standard library calls.',
      codeSnippet: `class UnsafeCallVisitor(ast.NodeVisitor):\n    def visit_Call(self, node):\n        if self.is_dangerous_sink(node):\n            self.record_finding(node)`,
      icon: Code2,
    },
    {
      title: 'Control Flow Graph & Call Graphs',
      category: 'Graph Traversal',
      description:
        'Constructs interprocedural call graphs across functions and modules. Traces branch conditions, loop bounds, and exit points to ensure analysis accounts for actual runtime paths.',
      codeSnippet: `graph.add_edge(caller_node, callee_node,\n    type="call", is_conditional=True)`,
      icon: GitFork,
    },
    {
      title: 'Interprocedural Taint Tracking',
      category: 'Dataflow Analysis',
      description:
        'Follows untrusted user input from entrypoints (HTTP parameters, environment variables, files) down to execution sinks (SQL queries, system calls, template renders).',
      codeSnippet: `source = request.args['input']\ntarget = sanitize(source)  # Checked\nsink.execute(target)       # Safe`,
      icon: Layers,
    },
    {
      title: 'Repository Intelligence',
      category: 'Context Awareness',
      description:
        'Analyzes broader repository dependencies, imports, configuration files, and utility helpers to understand whether custom sanitizers or middleware protect the call site.',
      codeSnippet: `resolve_import("core.security.sanitize")\n-> Middlewares: [AuthMiddleware, CSRF]`,
      icon: Database,
    },
    {
      title: 'Security Knowledge & RAG Rulesets',
      category: 'Rule Engine',
      description:
        'Correlates code findings against industry standards including CWE definitions, OWASP Top 10 categories, and curated vulnerability benchmarks to provide context.',
      codeSnippet: `Rule: CWE-89 (SQL Injection)\nSeverity: CRITICAL | Impact: Data Leakage`,
      icon: ShieldCheck,
    },
    {
      title: 'Groq Contextual Reasoning',
      category: 'False Positive Filter',
      description:
        'Combines deterministic static findings with high-speed LLM reasoning on Groq hardware. Synthesizes concise root causes, impact assessments, and verified fix diffs.',
      codeSnippet: `Synthesizing root cause & diff...\nFalse positive check: PASS (Confidence 98%)`,
      icon: Cpu,
    },
  ];

  return (
    <section className="py-20 md:py-28 border-t border-slate-200 dark:border-slate-800/80" id="capabilities">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-14 md:mb-18">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded text-xs font-mono font-medium bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 mb-3">
              <span>Deep Technical Capabilities</span>
            </div>
            <h2 className="text-2xl sm:text-4xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
              Built on rigorous static analysis, <br className="hidden sm:block" />
              not shallow regexes.
            </h2>
            <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-400 leading-relaxed">
              Every layer of the CodeGuard analysis engine is designed to minimize false alarms and deliver actionable code diffs developers can trust.
            </p>
          </div>
        </div>

        {/* Capabilities Editorial Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {capabilities.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className="flex flex-col justify-between p-6 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] hover:border-slate-300 dark:hover:border-slate-700 transition-colors shadow-xs"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
                      {item.category}
                    </span>
                    <div className="p-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                  </div>

                  <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-2">
                    {item.title}
                  </h3>

                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    {item.description}
                  </p>
                </div>

                {/* Mini Code Snippet / Telemetry Box */}
                <div className="mt-6 pt-3 border-t border-slate-100 dark:border-slate-800/80">
                  <pre className="p-2.5 rounded bg-slate-50 dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 text-[10px] font-mono text-slate-700 dark:text-slate-300 overflow-x-auto whitespace-pre leading-relaxed">
                    <code>{item.codeSnippet}</code>
                  </pre>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
