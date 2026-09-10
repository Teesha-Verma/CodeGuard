import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { SeverityBadge } from '@/components/common/Badges';
import {
  GitPullRequest,
  Code2,
  ShieldAlert,
  CheckCircle2,
  Terminal,
  Cpu,
  ArrowRight,
  Sparkles,
  Layers,
  FileCode2,
  AlertTriangle,
  Check,
  Copy,
} from 'lucide-react';

export const ProductPreviewHero: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'finding' | 'taint' | 'diff'>('finding');
  const [copied, setCopied] = useState(false);

  const copyFixCode = () => {
    navigator.clipboard.writeText(
      `# Safe parameterized command execution\nresult = subprocess.run(["ping", "-c", "4", target_host], shell=False, check=True, capture_output=True, text=True)`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="relative pt-12 pb-20 md:pt-20 md:pb-28 overflow-hidden" id="overview">
      {/* Background architectural grid lines - strictly engineering, zero fuzzy neon glow */}
      <div
        className="absolute inset-0 -z-10 pointer-events-none opacity-[0.03] dark:opacity-[0.07]"
        style={{
          backgroundImage: `linear-gradient(to right, currentColor 1px, transparent 1px), linear-gradient(to bottom, currentColor 1px, transparent 1px)`,
          backgroundSize: '32px 32px',
        }}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Eyebrow and Main Headline */}
        <div className="text-center max-w-3xl mx-auto mb-10 md:mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-medium border border-blue-500/20 bg-blue-500/10 text-blue-700 dark:text-blue-400 mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600 dark:bg-blue-400" />
            <span>Code Review &amp; Security Analysis</span>
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-slate-900 dark:text-slate-100 leading-[1.12]">
            Find the problems <br className="hidden sm:block" />
            <span className="text-blue-600 dark:text-blue-400">hiding in your code.</span>
          </h1>

          <p className="mt-5 text-base sm:text-lg text-slate-600 dark:text-slate-400 leading-relaxed max-w-2xl mx-auto">
            CodeGuard reviews pull requests and snippets with structural AST parsing, dataflow taint
            tracking, and contextual reasoning. You get actionable fixes with line-level evidence
            before code hits main.
          </p>

          {/* Primary Call to Action Buttons */}
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3.5">
            <Link
              to="/review/pr"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-md text-xs sm:text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white shadow-sm transition-all hover:shadow"
            >
              <GitPullRequest className="w-4 h-4" />
              <span>Review a Pull Request</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/review/snippet"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-md text-xs sm:text-sm font-medium border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900/80 text-slate-800 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
            >
              <Code2 className="w-4 h-4 text-slate-500" />
              <span>Analyze Snippet</span>
            </Link>
          </div>

          <div className="mt-4 text-xs text-slate-500 font-mono flex items-center justify-center gap-4">
            <span>No fake marketing claims</span>
            <span>•</span>
            <span>Deterministic static checks</span>
            <span>•</span>
            <span>CWE &amp; CVE mapped</span>
          </div>
        </div>

        {/* Product Workspace Preview - Real CodeGuard Experience */}
        <div className="relative mx-auto max-w-5xl rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] shadow-xl overflow-hidden">
          {/* Top Window Chrome */}
          <div className="h-10 px-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-[#0a0d14] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full bg-slate-300 dark:bg-slate-700" />
                <div className="w-3 h-3 rounded-full bg-slate-300 dark:bg-slate-700" />
                <div className="w-3 h-3 rounded-full bg-slate-300 dark:bg-slate-700" />
              </div>
              <div className="ml-3 hidden sm:flex items-center gap-2 text-xs font-mono text-slate-500">
                <FileCode2 className="w-3.5 h-3.5 text-blue-500" />
                <span>api/network_utils.py</span>
                <span className="text-slate-400">·</span>
                <span className="text-slate-400">PR #84 (network-health-check)</span>
              </div>
            </div>

            {/* Interactive Preview Tabs */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => setActiveTab('finding')}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  activeTab === 'finding'
                    ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-xs'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                Finding Detail
              </button>
              <button
                onClick={() => setActiveTab('taint')}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  activeTab === 'taint'
                    ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-xs'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                Taint Trace
              </button>
              <button
                onClick={() => setActiveTab('diff')}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  activeTab === 'diff'
                    ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-xs'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                Suggested Fix
              </button>
            </div>
          </div>

          {/* Workspace Body: Split View (Code on Left, Analysis on Right) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[400px]">
            {/* Left: Code Viewer with Vulnerability Highlight */}
            <div className="lg:col-span-7 p-4 sm:p-5 border-b lg:border-b-0 lg:border-r border-slate-200 dark:border-slate-800 bg-slate-900 text-slate-100 font-mono text-xs leading-relaxed overflow-x-auto">
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800 text-[11px] text-slate-400">
                <span>Vulnerable File: api/network_utils.py</span>
                <span className="text-orange-400 font-medium">Line 14 Flagged</span>
              </div>

              <div className="space-y-1">
                <div className="flex gap-4 text-slate-500">
                  <span className="w-5 select-none text-right">9</span>
                  <span className="text-slate-300">from flask import request, jsonify</span>
                </div>
                <div className="flex gap-4 text-slate-500">
                  <span className="w-5 select-none text-right">10</span>
                  <span className="text-slate-300">import subprocess</span>
                </div>
                <div className="flex gap-4 text-slate-500">
                  <span className="w-5 select-none text-right">11</span>
                  <span></span>
                </div>
                <div className="flex gap-4 text-slate-500">
                  <span className="w-5 select-none text-right">12</span>
                  <span className="text-slate-300"><span className="text-purple-400">def</span> <span className="text-blue-400">ping_diagnostic</span>():</span>
                </div>
                <div className="flex gap-4 text-slate-500">
                  <span className="w-5 select-none text-right">13</span>
                  <span className="text-slate-300">&nbsp;&nbsp;&nbsp;&nbsp;target_host = request.args.get(<span className="text-emerald-400">'host'</span>)</span>
                </div>

                {/* Highlighted Vulnerable Line */}
                <div className="flex gap-4 bg-red-950/40 -mx-4 px-4 py-1 border-l-2 border-red-500">
                  <span className="w-5 select-none text-right text-red-400 font-bold">14</span>
                  <span className="text-red-200 font-semibold">
                    &nbsp;&nbsp;&nbsp;&nbsp;proc = subprocess.Popen(<span className="text-emerald-300">f"ping -c 4 &#123;target_host&#125;"</span>, shell=<span className="text-amber-400">True</span>)
                  </span>
                </div>

                {/* Inline annotation callout */}
                <div className="ml-10 my-2 p-2 rounded bg-red-900/30 border border-red-800/60 text-[11px] text-red-300 flex items-start gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">HIGH: Subprocess Shell Injection (CWE-78)</span>
                    <p className="text-[10px] text-red-400/90 mt-0.5">
                      Untrusted input flows directly to shell execution. Arbitrary commands can be injected via delimiters (; & |).
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 text-slate-500">
                  <span className="w-5 select-none text-right">15</span>
                  <span className="text-slate-300">&nbsp;&nbsp;&nbsp;&nbsp;proc.wait()</span>
                </div>
                <div className="flex gap-4 text-slate-500">
                  <span className="w-5 select-none text-right">16</span>
                  <span className="text-slate-300">&nbsp;&nbsp;&nbsp;&nbsp;return jsonify(&#123;<span className="text-emerald-400">"status"</span>: proc.returncode&#125;)</span>
                </div>
              </div>
            </div>

            {/* Right: Structured Finding Drawer */}
            <div className="lg:col-span-5 p-4 sm:p-5 flex flex-col justify-between bg-slate-50/50 dark:bg-[#0d111a]/70">
              {activeTab === 'finding' && (
                <div className="space-y-4 text-xs">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <SeverityBadge severity="high" size="sm" />
                        <span className="text-[11px] font-mono text-slate-500">CWE-78 · OWASP A03</span>
                      </div>
                      <h4 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                        Unsafe Shell Command Execution
                      </h4>
                    </div>
                  </div>

                  {/* Detection Sources */}
                  <div>
                    <span className="text-[10px] font-mono uppercase text-slate-500 tracking-wider">
                      Detection Evidence Sources
                    </span>
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                        <Cpu className="w-3 h-3" />
                        AST Call Visitor
                      </span>
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
                        <Layers className="w-3 h-3" />
                        Taint Sink Tracker
                      </span>
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                        <Terminal className="w-3 h-3" />
                        Groq Llama-3 Reasoning
                      </span>
                    </div>
                  </div>

                  {/* Root Cause Analysis */}
                  <div className="p-3 rounded-md bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
                    <span className="text-[10px] font-mono uppercase text-slate-500 tracking-wider block mb-1">
                      Root Cause
                    </span>
                    <p className="text-slate-700 dark:text-slate-300 leading-relaxed text-[11px]">
                      The endpoint parameter <code className="font-mono bg-slate-100 dark:bg-slate-800 px-1 rounded">target_host</code> is formatted directly into a command string with <code className="font-mono bg-slate-100 dark:bg-slate-800 px-1 rounded">shell=True</code>. An attacker can append <code className="font-mono bg-slate-100 dark:bg-slate-800 px-1 rounded">; cat /etc/passwd</code> to execute arbitrary shell commands.
                    </p>
                  </div>

                  {/* Confidence and Impact */}
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="p-2.5 rounded bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
                      <span className="text-[10px] font-mono text-slate-500 block">Analysis Confidence</span>
                      <span className="font-semibold text-emerald-600 dark:text-emerald-400">98% (Static Proof)</span>
                    </div>
                    <div className="p-2.5 rounded bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
                      <span className="text-[10px] font-mono text-slate-500 block">Remediation Effort</span>
                      <span className="font-semibold text-blue-600 dark:text-blue-400">Immediate (&lt; 2 min)</span>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'taint' && (
                <div className="space-y-3 text-xs">
                  <h4 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                    Interprocedural Taint Flow
                  </h4>
                  <p className="text-[11px] text-slate-500">
                    CodeGuard traces untrusted taint from user-controlled entry points to sensitive execution sinks.
                  </p>

                  <div className="space-y-2 font-mono text-[11px] pt-1">
                    <div className="p-2 rounded bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-300">
                      <span className="text-[9px] uppercase tracking-wider block font-bold">1. Taint Source</span>
                      <code>request.args.get('host')</code> [Line 13]
                    </div>
                    <div className="text-center text-slate-400">↓ Dataflow</div>
                    <div className="p-2 rounded bg-blue-500/10 border border-blue-500/20 text-blue-700 dark:text-blue-300">
                      <span className="text-[9px] uppercase tracking-wider block font-bold">2. String Formatting</span>
                      <code>f"ping -c 4 &#123;target_host&#125;"</code>
                    </div>
                    <div className="text-center text-slate-400">↓ Unsanitized</div>
                    <div className="p-2 rounded bg-red-500/10 border border-red-500/20 text-red-700 dark:text-red-300">
                      <span className="text-[9px] uppercase tracking-wider block font-bold">3. Dangerous Sink</span>
                      <code>subprocess.Popen(..., shell=True)</code> [Line 14]
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'diff' && (
                <div className="space-y-3 text-xs">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                      Recommended Replacement
                    </h4>
                    <button
                      onClick={copyFixCode}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                    >
                      {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                      <span>{copied ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>

                  <div className="p-3 rounded-md bg-slate-900 text-slate-100 font-mono text-[11px] leading-relaxed space-y-1">
                    <div className="text-slate-500 select-none"># Remove shell=True, pass arguments as list</div>
                    <div className="bg-red-950/60 text-red-300 px-1 py-0.5 rounded">
                      - proc = subprocess.Popen(f"ping -c 4 &#123;target_host&#125;", shell=True)
                    </div>
                    <div className="bg-emerald-950/60 text-emerald-300 px-1 py-0.5 rounded">
                      + proc = subprocess.run(["ping", "-c", "4", target_host], shell=False, check=True)
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-500 leading-relaxed">
                    Passing arguments as a list with <code className="font-mono bg-slate-100 dark:bg-slate-800 px-1 rounded">shell=False</code> bypasses shell parameter interpretation and prevents command chaining.
                  </p>
                </div>
              )}

              {/* Bottom Quick-Action in Preview */}
              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <span className="text-[11px] text-slate-500 font-mono">
                  Sample Finding #RV-SEC-01
                </span>
                <Link
                  to="/review/snippet"
                  className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline"
                >
                  <span>Test with your snippet</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
