import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { FileCode, Plus, Minus, File, Loader2 } from "lucide-react";
import { PipelineStep } from "@/components/dashboard/PipelineStep";
import { cn } from "@/lib/utils";

const sampleDiffs = [
  {
    file: "src/components/Button.tsx",
    additions: 15,
    deletions: 3,
    changes: [
      { type: "add", line: 12, content: "  const [isLoading, setIsLoading] = useState(false);" },
      { type: "add", line: 13, content: "  const [error, setError] = useState<string | null>(null);" },
      { type: "del", line: 14, content: "  const handleClick = () => {" },
      { type: "add", line: 14, content: "  const handleClick = async () => {" },
      { type: "add", line: 15, content: "    setIsLoading(true);" },
      { type: "add", line: 16, content: "    try {" },
    ]
  },
  {
    file: "src/utils/api.ts",
    additions: 28,
    deletions: 12,
    changes: [
      { type: "del", line: 5, content: "export const fetchData = (url) => {" },
      { type: "add", line: 5, content: "export const fetchData = async (url: string): Promise<Response> => {" },
      { type: "add", line: 6, content: "  const response = await fetch(url, {" },
      { type: "add", line: 7, content: "    headers: { 'Content-Type': 'application/json' }," },
    ]
  },
  {
    file: "src/pages/Dashboard.tsx",
    additions: 45,
    deletions: 8,
    changes: [
      { type: "add", line: 1, content: "import { useEffect, useState } from 'react';" },
      { type: "add", line: 2, content: "import { useAuth } from '@/hooks/useAuth';" },
      { type: "del", line: 10, content: "  return <div>Dashboard</div>;" },
      { type: "add", line: 10, content: "  const { user } = useAuth();" },
    ]
  }
];

const DiffExtractor = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => {
      setIsLoading(false);
      setSelectedFile(sampleDiffs[0].file);
    }, 1200);
    return () => clearTimeout(timer);
  }, []);

  const selectedDiff = sampleDiffs.find(d => d.file === selectedFile);

  return (
    <PipelineStep
      stepNumber={2}
      title="Diff Extractor"
      description="Extracting code changes from the repository"
      icon={FileCode}
      status={isLoading ? "processing" : "complete"}
      nextStep={{
        label: "Run Static Analysis",
        onClick: () => navigate("/dashboard/ast"),
        disabled: isLoading,
      }}
    >
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
          <p className="text-muted-foreground">Extracting diffs from repository...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* File list */}
          <div className="lg:col-span-1 space-y-2">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
              Changed Files ({sampleDiffs.length})
            </p>
            {sampleDiffs.map((diff) => (
              <button
                key={diff.file}
                onClick={() => setSelectedFile(diff.file)}
                className={cn(
                  "w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all",
                  selectedFile === diff.file 
                    ? "bg-primary/10 border border-primary/30" 
                    : "bg-secondary/30 hover:bg-secondary/50 border border-transparent"
                )}
              >
                <File className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{diff.file}</p>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-green-500 flex items-center gap-0.5">
                      <Plus className="w-3 h-3" />{diff.additions}
                    </span>
                    <span className="text-red-500 flex items-center gap-0.5">
                      <Minus className="w-3 h-3" />{diff.deletions}
                    </span>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Diff preview */}
          <div className="lg:col-span-2">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
              Diff Preview
            </p>
            <div className="bg-background/50 rounded-lg border border-border/50 overflow-hidden">
              <div className="px-4 py-2 bg-secondary/30 border-b border-border/50">
                <p className="text-sm font-mono text-foreground">{selectedFile}</p>
              </div>
              <div className="p-4 font-mono text-sm overflow-x-auto">
                {selectedDiff?.changes.map((change, idx) => (
                  <div
                    key={idx}
                    className={cn(
                      "px-2 py-0.5 -mx-2",
                      change.type === "add" && "bg-green-500/10 text-green-400",
                      change.type === "del" && "bg-red-500/10 text-red-400"
                    )}
                  >
                    <span className="text-muted-foreground w-8 inline-block">{change.line}</span>
                    <span className={cn(
                      "w-4 inline-block",
                      change.type === "add" ? "text-green-500" : "text-red-500"
                    )}>
                      {change.type === "add" ? "+" : "-"}
                    </span>
                    {change.content}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </PipelineStep>
  );
};

export default DiffExtractor;
