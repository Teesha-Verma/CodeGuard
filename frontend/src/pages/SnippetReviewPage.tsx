import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { apiClient } from '@/lib/api/client';
import { saveStoredReview } from '@/lib/storage/reviews';
import {
  Play,
  Trash2,
  Loader2,
  AlertCircle,
  ArrowLeft,
  Sparkles,
} from 'lucide-react';

const CODE_PRESETS = [
  {
    name: 'Dynamic Execution (Eval)',
    filename: 'snippet.py',
    code: `def query(user_input):
    eval(user_input)`,
  },
  {
    name: 'Tainted SQL Injection',
    filename: 'payments.py',
    code: `def get_invoice(request):
    account_id = request.args.get("id")
    query = f"SELECT * FROM invoices WHERE account_id='{account_id}'"
    cursor.execute(query)
    return cursor.fetchall()`,
  },
  {
    name: 'Mutable Default Argument',
    filename: 'invoice.py',
    code: `class Invoice:
    def __init__(self, invoice_id: str, items: list = []):
        self.invoice_id = invoice_id
        self.items = items

    def add_item(self, item):
        self.items.append(item)`,
  },
  {
    name: 'Unawaited Async Coroutine',
    filename: 'notify.py',
    code: `import asyncio

async def send_event(payload):
    await asyncio.sleep(0.1)

def dispatch(events):
    for event in events:
        send_event(event)  # Bug: unawaited coroutine`,
  },
];

export default function SnippetReviewPage() {
  const navigate = useNavigate();
  const [filename, setFilename] = useState('snippet.py');
  const [language, setLanguage] = useState('Python');
  const [code, setCode] = useState(`def query(user_input):
    eval(user_input)`);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!code.trim()) {
      setError('Please provide code to analyze.');
      return;
    }

    setLoading(true);

    try {
      const res = await apiClient.submitSnippetReview(
        code,
        language.toLowerCase(),
        filename
      );

      // Save initial local review record
      saveStoredReview({
        review_id: res.review_id,
        type: 'snippet',
        filename,
        language: language.toLowerCase(),
        status: 'running',
        created_at: new Date().toISOString(),
        total_issues: 0,
        meaningful_issues: 0,
      });

      // Navigate to review processing screen
      navigate(`/reviews/${res.review_id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to submit snippet review.';
      setError(msg);
      setLoading(false);
    }
  };

  const handleClear = () => {
    setCode('');
  };

  const handleSelectPreset = (preset: (typeof CODE_PRESETS)[0]) => {
    setFilename(preset.filename);
    setCode(preset.code);
  };

  return (
    <AppShell>
      <div className="p-4 sm:p-8 max-w-4xl mx-auto w-full space-y-6">
        {/* Navigation back */}
        <div>
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Dashboard</span>
          </Link>
        </div>

        {/* Header */}
        <div className="border-b border-slate-200 dark:border-slate-800/80 pb-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                New review
              </h1>
              <p className="text-xs text-slate-500 mt-1">
                Analyze a code snippet or queue an async review for a GitHub pull request.
              </p>
            </div>

            {/* Presets Quick Dropdown */}
            <div className="hidden sm:flex items-center gap-1.5">
              <span className="text-xs font-mono text-slate-500">Presets:</span>
              <div className="flex items-center gap-1">
                {CODE_PRESETS.map((p) => (
                  <button
                    key={p.name}
                    type="button"
                    onClick={() => handleSelectPreset(p)}
                    className="px-2 py-1 text-[11px] rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-mono transition-colors"
                  >
                    {p.name.split(' ')[0]}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Sub tabs */}
          <div className="flex items-center gap-4 mt-4 border-b border-slate-200 dark:border-slate-800">
            <span className="pb-2 text-xs font-semibold text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400">
              Snippet
            </span>
            <Link
              to="/review/pr"
              className="pb-2 text-xs font-medium text-slate-500 hover:text-slate-900 dark:hover:text-slate-300"
            >
              Pull request
            </Link>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3.5 rounded-lg border border-red-500/20 bg-red-500/10 text-red-700 dark:text-red-400 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold">Review Error</div>
                <div className="font-mono mt-0.5">{error}</div>
                <div className="mt-2 text-[11px] text-slate-600 dark:text-slate-400">
                  Ensure the backend is running on{' '}
                  <code className="px-1 py-0.5 rounded bg-slate-200 dark:bg-slate-800">
                    http://localhost:8000
                  </code>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-mono">
                Filename
              </label>
              <input
                type="text"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                required
                className="w-full px-3 py-2 text-xs rounded-md bg-white dark:bg-[#0c1017] border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-mono">
                Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-md bg-white dark:bg-[#0c1017] border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="Python">Python</option>
                <option value="JavaScript">JavaScript (AST)</option>
                <option value="TypeScript">TypeScript (AST)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-mono">
              Code
            </label>
            <div className="border border-slate-200 dark:border-slate-800 rounded-md overflow-hidden bg-white dark:bg-[#090d14]">
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                rows={12}
                required
                placeholder="def my_function():&#10;    pass"
                className="w-full p-3 font-mono text-xs text-slate-900 dark:text-slate-100 bg-transparent border-0 focus:outline-none resize-y leading-relaxed"
                spellCheck={false}
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-md bg-slate-900 text-white hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white disabled:opacity-50 text-xs font-semibold shadow-xs transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run review</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleClear}
              className="flex items-center gap-1.5 px-3 py-2 rounded-md border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-medium transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          </div>

          {/* Bottom Telemetry Grid */}
          <div className="pt-6 border-t border-slate-200 dark:border-slate-800/80 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
            <div>
              <div className="text-slate-500">LLM model</div>
              <div className="font-semibold text-slate-900 dark:text-slate-100 mt-0.5">
                llama-3.3-70b-versatile
              </div>
            </div>
            <div>
              <div className="text-slate-500">Budget per review</div>
              <div className="font-semibold text-slate-900 dark:text-slate-100 mt-0.5">
                25 requests
              </div>
            </div>
            <div>
              <div className="text-slate-500">Timeout</div>
              <div className="font-semibold text-slate-900 dark:text-slate-100 mt-0.5">
                300s
              </div>
            </div>
          </div>
        </form>
      </div>
    </AppShell>
  );
}
