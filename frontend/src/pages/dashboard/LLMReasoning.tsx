import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Brain, Sparkles, Loader2, MessageSquare, Lightbulb } from "lucide-react";
import { PipelineStep } from "@/components/dashboard/PipelineStep";
import { cn } from "@/lib/utils";

const reasoningSteps = [
  { id: 1, text: "Analyzing code patterns and anti-patterns...", complete: false },
  { id: 2, text: "Checking for potential security vulnerabilities...", complete: false },
  { id: 3, text: "Evaluating code complexity and maintainability...", complete: false },
  { id: 4, text: "Identifying performance bottlenecks...", complete: false },
  { id: 5, text: "Generating improvement suggestions...", complete: false },
];

const insights = [
  {
    type: "security",
    title: "Potential XSS Vulnerability",
    description: "The fetchData function doesn't sanitize user input before making API calls. Consider adding input validation.",
    severity: "high",
    file: "api.ts",
    line: 6,
  },
  {
    type: "performance",
    title: "Unnecessary Re-renders",
    description: "The handleClick function creates a new reference on each render. Consider using useCallback for optimization.",
    severity: "medium",
    file: "Button.tsx",
    line: 14,
  },
  {
    type: "best-practice",
    title: "Missing Error Boundary",
    description: "The async function lacks proper error handling. This could lead to unhandled promise rejections.",
    severity: "medium",
    file: "Dashboard.tsx",
    line: 10,
  },
  {
    type: "architecture",
    title: "Tight Coupling Detected",
    description: "The component directly imports from multiple layers. Consider using dependency injection or context.",
    severity: "low",
    file: "Dashboard.tsx",
    line: 1,
  },
];

const LLMReasoning = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);
  const [steps, setSteps] = useState(reasoningSteps);
  const navigate = useNavigate();

  useEffect(() => {
    if (currentStep < steps.length) {
      const timer = setTimeout(() => {
        setSteps(prev => prev.map((s, i) => 
          i === currentStep ? { ...s, complete: true } : s
        ));
        setCurrentStep(prev => prev + 1);
      }, 800);
      return () => clearTimeout(timer);
    } else if (currentStep >= steps.length) {
      setIsLoading(false);
    }
  }, [currentStep, steps.length]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high": return "text-red-500 bg-red-500/10 border-red-500/30";
      case "medium": return "text-yellow-500 bg-yellow-500/10 border-yellow-500/30";
      case "low": return "text-blue-500 bg-blue-500/10 border-blue-500/30";
      default: return "";
    }
  };

  return (
    <PipelineStep
      stepNumber={5}
      title="LLM Reasoning Layer"
      description="AI-powered deep analysis using advanced language models"
      icon={Brain}
      status={isLoading ? "processing" : "complete"}
      nextStep={{
        label: "Evaluate & Score",
        onClick: () => navigate("/dashboard/scorer"),
        disabled: isLoading,
      }}
    >
      {isLoading ? (
        <div className="space-y-6">
          <div className="flex items-center gap-3 p-4 rounded-lg bg-primary/10 border border-primary/20">
            <Brain className="w-6 h-6 text-primary animate-pulse" />
            <div>
              <p className="text-sm font-medium text-foreground">AI Analysis in Progress</p>
              <p className="text-xs text-muted-foreground">Using GPT-4 for deep code reasoning</p>
            </div>
          </div>

          <div className="space-y-3">
            {steps.map((step, idx) => (
              <div
                key={step.id}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-lg transition-all",
                  step.complete 
                    ? "bg-green-500/10 border border-green-500/30" 
                    : idx === currentStep 
                      ? "bg-primary/10 border border-primary/30" 
                      : "bg-secondary/30 border border-transparent"
                )}
              >
                {step.complete ? (
                  <Sparkles className="w-4 h-4 text-green-500" />
                ) : idx === currentStep ? (
                  <Loader2 className="w-4 h-4 text-primary animate-spin" />
                ) : (
                  <div className="w-4 h-4 rounded-full border-2 border-muted-foreground/30" />
                )}
                <span className={cn(
                  "text-sm",
                  step.complete ? "text-foreground" : "text-muted-foreground"
                )}>
                  {step.text}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* AI insights header */}
          <div className="flex items-center gap-3 p-4 rounded-lg bg-gradient-to-r from-primary/10 to-accent/10 border border-primary/20">
            <Lightbulb className="w-6 h-6 text-primary" />
            <div>
              <p className="text-sm font-medium text-foreground">{insights.length} AI Insights Generated</p>
              <p className="text-xs text-muted-foreground">Deep analysis complete</p>
            </div>
          </div>

          {/* Insights list */}
          <div className="space-y-4">
            {insights.map((insight, idx) => (
              <div
                key={idx}
                className={cn(
                  "p-4 rounded-lg border",
                  getSeverityColor(insight.severity)
                )}
              >
                <div className="flex items-start gap-3">
                  <MessageSquare className="w-5 h-5 mt-0.5" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold">{insight.title}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-background/50 uppercase">
                        {insight.severity}
                      </span>
                    </div>
                    <p className="text-sm opacity-80 mb-2">{insight.description}</p>
                    <p className="text-xs opacity-60">
                      📍 {insight.file}:{insight.line}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </PipelineStep>
  );
};

export default LLMReasoning;
