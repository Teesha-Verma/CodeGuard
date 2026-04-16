import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, MessageCircle, AlertTriangle, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { PipelineStep } from "@/components/dashboard/PipelineStep";
import { cn } from "@/lib/utils";

const reviewComments = [
  {
    id: 1,
    type: "request_changes",
    file: "src/utils/api.ts",
    line: 5,
    title: "Add type safety to fetchData function",
    body: "The `fetchData` function currently uses `any` type which defeats TypeScript's type safety. Please add proper type annotations.",
    suggestion: `export const fetchData = async <T>(url: string): Promise<T> => {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(\`HTTP error! status: \${response.status}\`);
  }
  return response.json() as Promise<T>;
};`,
  },
  {
    id: 2,
    type: "request_changes",
    file: "src/components/Button.tsx",
    line: 14,
    title: "Wrap callback in useCallback",
    body: "The `handleClick` function is recreated on every render. This can cause unnecessary re-renders in child components.",
    suggestion: `const handleClick = useCallback(async () => {
  setIsLoading(true);
  try {
    await onSubmit();
  } catch (err) {
    setError(err.message);
  } finally {
    setIsLoading(false);
  }
}, [onSubmit]);`,
  },
  {
    id: 3,
    type: "comment",
    file: "src/pages/Dashboard.tsx",
    line: 1,
    title: "Consider using barrel exports",
    body: "Multiple imports from the same module could be consolidated using barrel exports for cleaner code organization.",
    suggestion: null,
  },
  {
    id: 4,
    type: "approve",
    file: "src/components/Button.tsx",
    line: 12,
    title: "Good use of useState for loading state",
    body: "Nice implementation of loading state management. The naming convention is clear and follows React best practices.",
    suggestion: null,
  },
];

const ReviewOutput = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [selectedComment, setSelectedComment] = useState<number | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
      setSelectedComment(1);
    }, 1200);
    return () => clearTimeout(timer);
  }, []);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "request_changes": return <XCircle className="w-4 h-4 text-red-500" />;
      case "comment": return <MessageCircle className="w-4 h-4 text-blue-500" />;
      case "approve": return <CheckCircle className="w-4 h-4 text-green-500" />;
      default: return null;
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type) {
      case "request_changes": return "Changes Requested";
      case "comment": return "Comment";
      case "approve": return "Approved";
      default: return "";
    }
  };

  const selected = reviewComments.find(c => c.id === selectedComment);

  return (
    <PipelineStep
      stepNumber={7}
      title="PR-style Review Output"
      description="Code review in familiar GitHub PR format"
      icon={FileText}
      status={isLoading ? "processing" : "complete"}
      nextStep={{
        label: "Generate Report",
        onClick: () => navigate("/dashboard/report"),
        disabled: isLoading,
      }}
    >
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
          <p className="text-muted-foreground">Generating PR-style review...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Comments list */}
          <div className="space-y-2">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
              Review Comments ({reviewComments.length})
            </p>
            {reviewComments.map((comment) => (
              <button
                key={comment.id}
                onClick={() => setSelectedComment(comment.id)}
                className={cn(
                  "w-full text-left p-3 rounded-lg transition-all border",
                  selectedComment === comment.id
                    ? "bg-primary/10 border-primary/30"
                    : "bg-secondary/30 border-transparent hover:bg-secondary/50"
                )}
              >
                <div className="flex items-start gap-3">
                  {getTypeIcon(comment.type)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{comment.title}</p>
                    <p className="text-xs text-muted-foreground">{comment.file}:{comment.line}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Selected comment detail */}
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
              Comment Detail
            </p>
            {selected && (
              <div className="bg-background/50 rounded-lg border border-border/50 overflow-hidden">
                {/* Header */}
                <div className="px-4 py-3 bg-secondary/30 border-b border-border/50 flex items-center justify-between">
                  <span className="text-sm font-mono text-foreground">{selected.file}</span>
                  <span className={cn(
                    "text-xs px-2 py-1 rounded-full",
                    selected.type === "request_changes" && "bg-red-500/20 text-red-500",
                    selected.type === "comment" && "bg-blue-500/20 text-blue-500",
                    selected.type === "approve" && "bg-green-500/20 text-green-500"
                  )}>
                    {getTypeBadge(selected.type)}
                  </span>
                </div>

                {/* Content */}
                <div className="p-4 space-y-4">
                  <div>
                    <h4 className="text-sm font-semibold text-foreground mb-2">{selected.title}</h4>
                    <p className="text-sm text-muted-foreground">{selected.body}</p>
                  </div>

                  {/* Code suggestion */}
                  {selected.suggestion && (
                    <div>
                      <p className="text-xs font-semibold text-primary mb-2 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" />
                        Suggested Fix
                      </p>
                      <pre className="p-3 rounded-lg bg-green-500/5 border border-green-500/20 text-xs font-mono text-green-400 overflow-x-auto">
                        {selected.suggestion}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </PipelineStep>
  );
};

export default ReviewOutput;
