import React, { useState, useEffect } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { apiClient, API_BASE_URL } from '@/lib/api/client';
import { ThemeToggle } from '@/components/common/ThemeToggle';
import {
  Settings,
  Server,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  Lock,
} from 'lucide-react';

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState(API_BASE_URL);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionResult, setConnectionResult] = useState<{
    status: 'connected' | 'error';
    latencyMs?: number;
    service?: string;
    version?: string;
    message?: string;
  } | null>(null);

  const testConnection = async () => {
    setTestingConnection(true);
    setConnectionResult(null);
    const start = performance.now();

    try {
      apiClient.setBaseUrl(apiUrl);
      const res = await apiClient.checkHealth();
      const latencyMs = Math.round(performance.now() - start);

      setConnectionResult({
        status: 'connected',
        latencyMs,
        service: res.service,
        version: res.version,
      });
    } catch (err: unknown) {
      setConnectionResult({
        status: 'error',
        message: err instanceof Error ? err.message : 'Connection failed',
      });
    } finally {
      setTestingConnection(false);
    }
  };

  useEffect(() => {
    testConnection();
  }, []);

  return (
    <AppShell>
      <div className="p-4 sm:p-8 max-w-3xl mx-auto w-full space-y-8">
        {/* Header */}
        <div className="border-b border-slate-200 dark:border-slate-800/80 pb-4">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-blue-500" />
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              Settings
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            System configuration, appearance preferences, and backend telemetry.
          </p>
        </div>

        {/* Section: API Connection */}
        <div className="p-5 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f] space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
            <Server className="w-4 h-4 text-blue-500" />
            <span>API Connection</span>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-400">
            Target FastAPI backend service URL. Default is determined by{' '}
            <code className="font-mono text-blue-600 dark:text-blue-400 bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">
              VITE_API_URL
            </code>
            .
          </p>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              placeholder="http://localhost:8000"
              className="flex-1 px-3 py-2 text-xs rounded-md bg-white dark:bg-[#0c1017] border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button
              type="button"
              onClick={testConnection}
              disabled={testingConnection}
              className="flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 text-xs font-semibold shrink-0 transition-colors"
            >
              {testingConnection ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Pinging...</span>
                </>
              ) : (
                <>
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Test Connection</span>
                </>
              )}
            </button>
          </div>

          {/* Test Status Feedback */}
          {connectionResult && (
            <div
              className={`p-3 rounded-md text-xs font-mono border ${
                connectionResult.status === 'connected'
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-700 dark:text-emerald-400'
                  : 'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-400'
              }`}
            >
              {connectionResult.status === 'connected' ? (
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 font-semibold">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    Connected to {connectionResult.service || 'CodeGuard'} (v
                    {connectionResult.version || '2.0.0'})
                  </span>
                  <span>{connectionResult.latencyMs}ms latency</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <XCircle className="w-4 h-4 text-red-500 shrink-0" />
                  <span>
                    Backend offline: {connectionResult.message || 'Unable to connect to http://localhost:8000'}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Section: Appearance */}
        <div className="p-5 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f] space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                Appearance & Theme
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Toggle between dark and light modes.
              </p>
            </div>
            <ThemeToggle />
          </div>
        </div>

        {/* Section: Security & Trust Notice */}
        <div className="p-5 rounded-lg border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0f141f] space-y-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
            <Lock className="w-4 h-4 text-emerald-500" />
            <span>Security & Secrets Isolation</span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            In compliance with strict security architecture, this frontend never requests, stores, or handles raw server credentials. Tokens such as{' '}
            <code className="font-mono text-slate-700 dark:text-slate-300">GROQ_API_KEY</code>,{' '}
            <code className="font-mono text-slate-700 dark:text-slate-300">GEMINI_API_KEY</code>, and database credentials remain isolated within backend environment variables.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
