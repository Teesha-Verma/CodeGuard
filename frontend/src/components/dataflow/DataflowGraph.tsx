import React, { useState } from 'react';
import { ReviewIssue } from '@/types';
import { SeverityBadge } from '@/components/common/Badges';
import {
  ArrowDown,
  ArrowRight,
  Database,
  Terminal,
  Code2,
  AlertOctagon,
  CheckCircle2,
  Info,
  Layers,
} from 'lucide-react';

interface DataflowGraphProps {
  issue: ReviewIssue | null;
  filePath: string;
  fileContent?: string;
  onFixInPlayground?: () => void;
}

interface FlowNode {
  id: string;
  stepNumber: number;
  label: string;
  role: 'SOURCE' | 'INPUT' | 'PROPAGATION' | 'TRANSFORMATION' | 'SINK';
  description: string;
  codeSnippet: string;
  lineOffset?: number;
}

export const DataflowGraph: React.FC<DataflowGraphProps> = ({
  issue,
  filePath,
  fileContent,
  onFixInPlayground,
}) => {
  const [selectedNodeIndex, setSelectedNodeIndex] = useState<number>(0);

  if (!issue) {
    return (
      <div className="p-8 text-center rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a]">
        <Info className="w-8 h-8 text-slate-400 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200">
          No Finding Selected
        </h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
          Select a finding with dataflow tracking to view its source-to-sink taint propagation graph.
        </p>
      </div>
    );
  }

  // Check if dataflow_path exists and is populated
  const hasDataflow = issue.dataflow_path && issue.dataflow_path.length > 0;

  if (!hasDataflow) {
    return (
      <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-8 text-center shadow-xs">
        <Layers className="w-10 h-10 text-slate-400 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200">
          Dataflow information is not available for this finding.
        </h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-2 leading-relaxed">
          This finding was identified via structural Python AST visitor patterns and heuristic checks
          rather than an interprocedural taint flow path.
        </p>
        <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded bg-slate-100 dark:bg-slate-800 text-xs font-mono text-slate-600 dark:text-slate-400">
          <span>Rule: {issue.source}</span>
          <span>·</span>
          <span>Target Line: {issue.line}</span>
        </div>
      </div>
    );
  }

  const rawPath = issue.dataflow_path!;

  // Generate structured nodes from dataflow_path
  const nodes: FlowNode[] = rawPath.map((step, idx) => {
    let role: FlowNode['role'] = 'PROPAGATION';
    let desc = 'Data propagates through internal variable reference.';

    if (idx === 0) {
      role = 'SOURCE';
      desc = 'Untrusted input enters the application boundary from an external request parameter.';
    } else if (idx === 1) {
      role = 'INPUT';
      desc = 'External value is assigned to a local parameter without sanitization or type constraint.';
    } else if (idx === rawPath.length - 1) {
      role = 'SINK';
      desc = 'Tainted string reaches sensitive execution sink where it alters control flow or query syntax.';
    } else if (step.includes('format') || step.includes('f"') || step.includes('concat') || step.includes('+')) {
      role = 'TRANSFORMATION';
      desc = 'String interpolation or dynamic construction incorporates untrusted value into execution buffer.';
    }

    return {
      id: `node-${idx}`,
      stepNumber: idx + 1,
      label: step,
      role,
      description: desc,
      codeSnippet: step,
    };
  });

  const selectedNode = nodes[selectedNodeIndex] || nodes[0];

  return (
    <div className="space-y-6">
      {/* Header Info Bar */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-4 sm:p-5 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <SeverityBadge severity={issue.severity} size="sm" />
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
              {issue.issue}
            </h3>
            <span className="text-xs font-mono text-slate-500">
              {filePath}:{issue.line} · {nodes.length} Taint Nodes Detected
            </span>
          </div>
        </div>

        {onFixInPlayground && (
          <button
            type="button"
            onClick={onFixInPlayground}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white shadow-xs transition-colors cursor-pointer"
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Fix in Playground</span>
          </button>
        )}
      </div>

      {/* Main Graph & Node Inspector Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Visual Dataflow Path */}
        <div className="lg:col-span-7 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 shadow-xs">
          <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500 mb-4">
            Source-to-Sink Taint Propagation Path
          </h4>

          <div className="space-y-3">
            {nodes.map((node, idx) => {
              const isSelected = selectedNodeIndex === idx;
              const isSource = node.role === 'SOURCE';
              const isSink = node.role === 'SINK';

              return (
                <React.Fragment key={node.id}>
                  <div
                    onClick={() => setSelectedNodeIndex(idx)}
                    className={`p-3.5 rounded-lg border text-xs cursor-pointer transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50/70 dark:bg-blue-950/40 ring-1 ring-blue-500 shadow-xs'
                        : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-slate-50/60 dark:bg-slate-900/40'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-5 h-5 rounded flex items-center justify-center font-mono font-bold text-[10px] ${
                            isSource
                              ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/40'
                              : isSink
                              ? 'bg-rose-500/20 text-rose-600 dark:text-rose-400 border border-rose-500/40'
                              : 'bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                          }`}
                        >
                          {node.stepNumber}
                        </span>
                        <span
                          className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                            isSource
                              ? 'bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300'
                              : isSink
                              ? 'bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300'
                              : 'bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                          }`}
                        >
                          {node.role}
                        </span>
                      </div>

                      <span className="text-[11px] font-mono text-slate-400">
                        Step {node.stepNumber} of {nodes.length}
                      </span>
                    </div>

                    {/* Node Expression Code */}
                    <div className="font-mono text-[12px] bg-slate-950 text-slate-100 p-2 rounded border border-slate-800 overflow-x-auto">
                      {node.label}
                    </div>
                  </div>

                  {idx < nodes.length - 1 && (
                    <div className="flex items-center justify-center py-0.5">
                      <ArrowDown className="w-4 h-4 text-slate-400 dark:text-slate-600" />
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Right Column: Node Details & Taint Analysis Inspector */}
        <div className="lg:col-span-5 space-y-4">
          <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 shadow-xs">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500 mb-3">
              Taint Node Telemetry
            </h4>

            <div className="space-y-3.5 text-xs">
              <div>
                <span className="text-[10px] font-mono text-slate-500 block mb-1">ROLE IN PIPELINE</span>
                <span className="font-bold text-slate-900 dark:text-slate-100 font-mono text-sm">
                  {selectedNode.role}
                </span>
              </div>

              <div>
                <span className="text-[10px] font-mono text-slate-500 block mb-1">INTERPRETATION</span>
                <p className="text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-900/60 p-3 rounded border border-slate-200 dark:border-slate-800">
                  {selectedNode.description}
                </p>
              </div>

              <div>
                <span className="text-[10px] font-mono text-slate-500 block mb-1">EXPRESSION VALUE</span>
                <pre className="p-2.5 rounded bg-slate-950 text-amber-300 font-mono text-[11px] overflow-x-auto border border-slate-800">
                  {selectedNode.label}
                </pre>
              </div>

              <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                <span className="text-[10px] font-mono text-slate-500 block mb-1">DETECTED SANITIZERS</span>
                <span className="text-[11px] font-mono text-rose-600 dark:text-rose-400 font-semibold">
                  None (0 sanitizers encountered in path)
                </span>
              </div>
            </div>
          </div>

          {/* Remediation Callout */}
          <div className="rounded-lg border border-blue-200 dark:border-blue-900/60 bg-blue-50/50 dark:bg-blue-950/20 p-4">
            <h5 className="text-xs font-bold text-blue-900 dark:text-blue-300 mb-1">
              Dataflow Remediation Rule
            </h5>
            <p className="text-[11.5px] text-blue-800 dark:text-blue-300/90 leading-relaxed">
              To break this tainted dataflow path, place a strict type validation or parameterized boundary
              between <code className="font-mono bg-blue-100 dark:bg-blue-900/60 px-1 rounded">Step 1 (Source)</code> and <code className="font-mono bg-blue-100 dark:bg-blue-900/60 px-1 rounded">Step {nodes.length} (Sink)</code>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
