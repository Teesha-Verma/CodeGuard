import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { TreeDeciduous, Box, FunctionSquare, Variable, Loader2, CheckCircle } from "lucide-react";
import { PipelineStep } from "@/components/dashboard/PipelineStep";
import { cn } from "@/lib/utils";

const astNodes = [
  { type: "FunctionDeclaration", name: "handleClick", line: 14, children: 3 },
  { type: "VariableDeclaration", name: "isLoading", line: 12, children: 0 },
  { type: "VariableDeclaration", name: "error", line: 13, children: 0 },
  { type: "CallExpression", name: "useState", line: 12, children: 1 },
  { type: "CallExpression", name: "useState", line: 13, children: 1 },
  { type: "ArrowFunction", name: "fetchData", line: 5, children: 2 },
  { type: "AwaitExpression", name: "fetch", line: 6, children: 1 },
  { type: "ImportDeclaration", name: "react", line: 1, children: 2 },
];

const analysisResults = [
  { category: "Functions", count: 12, icon: FunctionSquare },
  { category: "Variables", count: 34, icon: Variable },
  { category: "Components", count: 8, icon: Box },
  { category: "Imports", count: 15, icon: TreeDeciduous },
];

const StaticAnalysis = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [progress, setProgress] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsLoading(false);
          return 100;
        }
        return prev + 10;
      });
    }, 150);
    return () => clearInterval(interval);
  }, []);

  return (
    <PipelineStep
      stepNumber={3}
      title="Static Analysis (AST)"
      description="Parsing code into Abstract Syntax Tree for deep analysis"
      icon={TreeDeciduous}
      status={isLoading ? "processing" : "complete"}
      nextStep={{
        label: "Run Linters",
        onClick: () => navigate("/dashboard/linters"),
        disabled: isLoading,
      }}
    >
      {isLoading ? (
        <div className="space-y-6">
          <div className="flex flex-col items-center justify-center py-8">
            <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
            <p className="text-muted-foreground mb-4">Building Abstract Syntax Tree...</p>
            <div className="w-full max-w-md h-2 bg-secondary rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-sm text-primary mt-2">{progress}%</p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {analysisResults.map((result) => (
              <div
                key={result.category}
                className="p-4 rounded-lg bg-secondary/30 border border-border/30"
              >
                <result.icon className="w-5 h-5 text-primary mb-2" />
                <p className="text-2xl font-bold text-foreground">{result.count}</p>
                <p className="text-sm text-muted-foreground">{result.category}</p>
              </div>
            ))}
          </div>

          {/* AST Nodes */}
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
              AST Nodes Detected
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {astNodes.map((node, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-3 p-3 rounded-lg bg-background/50 border border-border/30"
                >
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <div className="flex-1">
                    <p className="text-sm font-mono text-foreground">{node.type}</p>
                    <p className="text-xs text-muted-foreground">
                      {node.name} • Line {node.line}
                    </p>
                  </div>
                  <span className="text-xs px-2 py-1 rounded bg-secondary text-muted-foreground">
                    {node.children} children
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </PipelineStep>
  );
};

export default StaticAnalysis;
