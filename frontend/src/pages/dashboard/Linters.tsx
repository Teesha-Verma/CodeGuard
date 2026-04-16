import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Search, AlertTriangle, AlertCircle, Info, CheckCircle2, Loader2 } from "lucide-react";
import { PipelineStep } from "@/components/dashboard/PipelineStep";
import { cn } from "@/lib/utils";

const linterResults = [
  {
    linter: "ESLint",
    icon: "🔧",
    issues: [
      { severity: "error", message: "Unexpected any. Specify a different type.", file: "api.ts", line: 5 },
      { severity: "warning", message: "Missing return type on function.", file: "Button.tsx", line: 14 },
      { severity: "info", message: "Prefer const over let.", file: "Dashboard.tsx", line: 10 },
    ]
  },
  {
    linter: "TypeScript",
    icon: "📘",
    issues: [
      { severity: "error", message: "Property 'user' does not exist on type 'never'.", file: "Dashboard.tsx", line: 15 },
      { severity: "warning", message: "Type 'string | undefined' is not assignable.", file: "api.ts", line: 12 },
    ]
  },
  {
    linter: "Prettier",
    icon: "✨",
    issues: [
      { severity: "info", message: "Code style: expected semicolon.", file: "Button.tsx", line: 8 },
      { severity: "info", message: "Code style: trailing comma missing.", file: "api.ts", line: 20 },
    ]
  }
];

const Linters = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [selectedLinter, setSelectedLinter] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
      setSelectedLinter("ESLint");
    }, 1500);
    return () => clearTimeout(timer);
  }, []);

  const selectedResults = linterResults.find(l => l.linter === selectedLinter);

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "error": return <AlertCircle className="w-4 h-4 text-red-500" />;
      case "warning": return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case "info": return <Info className="w-4 h-4 text-blue-500" />;
      default: return null;
    }
  };

  const totalIssues = linterResults.reduce((acc, l) => acc + l.issues.length, 0);
  const errorCount = linterResults.reduce((acc, l) => acc + l.issues.filter(i => i.severity === "error").length, 0);
  const warningCount = linterResults.reduce((acc, l) => acc + l.issues.filter(i => i.severity === "warning").length, 0);

  return (
    <PipelineStep
      stepNumber={4}
      title="Traditional Linters"
      description="Running ESLint, TypeScript, and Prettier checks"
      icon={Search}
      status={isLoading ? "processing" : "complete"}
      nextStep={{
        label: "LLM Analysis",
        onClick: () => navigate("/dashboard/llm"),
        disabled: isLoading,
      }}
    >
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
          <p className="text-muted-foreground">Running linters on code...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Summary */}
          <div className="flex items-center gap-6 p-4 rounded-lg bg-secondary/30 border border-border/30">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-primary" />
              <span className="text-foreground font-medium">{totalIssues} issues found</span>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <span className="flex items-center gap-1 text-red-500">
                <AlertCircle className="w-4 h-4" /> {errorCount} errors
              </span>
              <span className="flex items-center gap-1 text-yellow-500">
                <AlertTriangle className="w-4 h-4" /> {warningCount} warnings
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Linter tabs */}
            <div className="space-y-2">
              {linterResults.map((linter) => (
                <button
                  key={linter.linter}
                  onClick={() => setSelectedLinter(linter.linter)}
                  className={cn(
                    "w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all",
                    selectedLinter === linter.linter
                      ? "bg-primary/10 border border-primary/30"
                      : "bg-secondary/30 hover:bg-secondary/50 border border-transparent"
                  )}
                >
                  <span className="text-xl">{linter.icon}</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">{linter.linter}</p>
                    <p className="text-xs text-muted-foreground">{linter.issues.length} issues</p>
                  </div>
                </button>
              ))}
            </div>

            {/* Issues list */}
            <div className="lg:col-span-2 space-y-2">
              {selectedResults?.issues.map((issue, idx) => (
                <div
                  key={idx}
                  className={cn(
                    "p-3 rounded-lg border",
                    issue.severity === "error" && "bg-red-500/5 border-red-500/20",
                    issue.severity === "warning" && "bg-yellow-500/5 border-yellow-500/20",
                    issue.severity === "info" && "bg-blue-500/5 border-blue-500/20"
                  )}
                >
                  <div className="flex items-start gap-3">
                    {getSeverityIcon(issue.severity)}
                    <div className="flex-1">
                      <p className="text-sm text-foreground">{issue.message}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {issue.file}:{issue.line}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </PipelineStep>
  );
};

export default Linters;
