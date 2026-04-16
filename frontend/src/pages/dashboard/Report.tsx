import { useState, useEffect } from "react";
import { MessageSquare, Github, Download, Copy, Check, Loader2, Sparkles, Wand2 } from "lucide-react";
import { PipelineStep } from "@/components/dashboard/PipelineStep";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

const suggestedFixes = [
  {
    id: 1,
    file: "src/utils/api.ts",
    issue: "Missing type safety",
    originalCode: `export const fetchData = (url) => {
  return fetch(url);
}`,
    fixedCode: `export const fetchData = async <T>(url: string): Promise<T> => {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(\`HTTP error! status: \${response.status}\`);
  }
  return response.json() as Promise<T>;
};`,
    explanation: "Added TypeScript generics for type-safe responses, proper error handling, and async/await syntax.",
  },
  {
    id: 2,
    file: "src/components/Button.tsx",
    issue: "Performance optimization needed",
    originalCode: `const handleClick = async () => {
  setIsLoading(true);
  // ... logic
}`,
    fixedCode: `const handleClick = useCallback(async () => {
  setIsLoading(true);
  try {
    await onSubmit();
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Unknown error');
  } finally {
    setIsLoading(false);
  }
}, [onSubmit]);`,
    explanation: "Wrapped in useCallback to prevent unnecessary re-renders. Added proper error handling with type checking.",
  },
  {
    id: 3,
    file: "src/pages/Dashboard.tsx",
    issue: "Missing error boundary",
    originalCode: `const Dashboard = () => {
  const { user } = useAuth();
  return <div>{user.name}</div>;
}`,
    fixedCode: `const Dashboard = () => {
  const { user, isLoading, error } = useAuth();
  
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!user) return <Navigate to="/login" />;
  
  return <div>{user.name}</div>;
}`,
    explanation: "Added loading state, error handling, and authentication redirect for better UX and security.",
  },
];

const Report = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState<number | null>(null);
  const [selectedFix, setSelectedFix] = useState<number | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
      setSelectedFix(1);
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  const handleCopy = (id: number, code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
    toast({
      title: "Copied to clipboard",
      description: "The fixed code has been copied.",
    });
  };

  const handlePostToGithub = () => {
    toast({
      title: "Posted to GitHub!",
      description: "Review comments have been added to the PR.",
    });
  };

  const handleDownloadReport = () => {
    toast({
      title: "Report downloaded",
      description: "Full analysis report saved as PDF.",
    });
  };

  const selected = suggestedFixes.find(f => f.id === selectedFix);

  return (
    <PipelineStep
      stepNumber={8}
      title="Report & LLM Fixes"
      description="AI-generated fixes and GitHub integration"
      icon={MessageSquare}
      status={isLoading ? "processing" : "complete"}
    >
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
          <p className="text-muted-foreground">Generating AI-powered fixes...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={handlePostToGithub}
              className="bg-gradient-to-r from-primary to-accent text-primary-foreground"
            >
              <Github className="w-4 h-4 mr-2" />
              Post Comments to GitHub
            </Button>
            <Button variant="outline" onClick={handleDownloadReport}>
              <Download className="w-4 h-4 mr-2" />
              Download Report
            </Button>
          </div>

          {/* AI Fixes section */}
          <div className="p-4 rounded-lg bg-gradient-to-r from-primary/10 to-accent/10 border border-primary/20">
            <div className="flex items-center gap-2 mb-2">
              <Wand2 className="w-5 h-5 text-primary" />
              <h3 className="font-semibold text-foreground">AI-Suggested Fixes</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              {suggestedFixes.length} automated fixes generated based on analysis
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Fixes list */}
            <div className="space-y-2">
              {suggestedFixes.map((fix) => (
                <button
                  key={fix.id}
                  onClick={() => setSelectedFix(fix.id)}
                  className={cn(
                    "w-full text-left p-3 rounded-lg transition-all border",
                    selectedFix === fix.id
                      ? "bg-primary/10 border-primary/30"
                      : "bg-secondary/30 border-transparent hover:bg-secondary/50"
                  )}
                >
                  <div className="flex items-start gap-3">
                    <Sparkles className="w-4 h-4 text-primary mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{fix.issue}</p>
                      <p className="text-xs text-muted-foreground">{fix.file}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {/* Selected fix detail */}
            <div className="lg:col-span-2">
              {selected && (
                <div className="space-y-4">
                  {/* Explanation */}
                  <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                    <p className="text-sm text-blue-400">
                      <span className="font-semibold">💡 Explanation:</span> {selected.explanation}
                    </p>
                  </div>

                  {/* Before/After */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Original */}
                    <div className="rounded-lg border border-red-500/20 overflow-hidden">
                      <div className="px-3 py-2 bg-red-500/10 border-b border-red-500/20 flex items-center justify-between">
                        <span className="text-xs font-semibold text-red-500">BEFORE</span>
                      </div>
                      <pre className="p-3 text-xs font-mono text-muted-foreground overflow-x-auto">
                        {selected.originalCode}
                      </pre>
                    </div>

                    {/* Fixed */}
                    <div className="rounded-lg border border-green-500/20 overflow-hidden">
                      <div className="px-3 py-2 bg-green-500/10 border-b border-green-500/20 flex items-center justify-between">
                        <span className="text-xs font-semibold text-green-500">AFTER (AI Fix)</span>
                        <button
                          onClick={() => handleCopy(selected.id, selected.fixedCode)}
                          className="text-green-500 hover:text-green-400"
                        >
                          {copied === selected.id ? (
                            <Check className="w-4 h-4" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                      <pre className="p-3 text-xs font-mono text-green-400 overflow-x-auto">
                        {selected.fixedCode}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Summary */}
          <div className="p-4 rounded-lg bg-secondary/30 border border-border/30">
            <h4 className="font-semibold text-foreground mb-2">🎉 Analysis Complete!</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Analyzed 3 files with 88 total lines changed</li>
              <li>• Found 7 issues (2 errors, 3 warnings, 2 suggestions)</li>
              <li>• Generated 3 automated fix suggestions</li>
              <li>• Overall code quality score: 74/100</li>
            </ul>
          </div>
        </div>
      )}
    </PipelineStep>
  );
};

export default Report;
