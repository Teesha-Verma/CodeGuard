import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Award, TrendingUp, Shield, Zap, Code, Loader2 } from "lucide-react";
import { PipelineStep } from "@/components/dashboard/PipelineStep";
import { cn } from "@/lib/utils";

const scores = [
  { category: "Code Quality", score: 78, icon: Code, color: "from-blue-500 to-cyan-500" },
  { category: "Security", score: 65, icon: Shield, color: "from-red-500 to-orange-500" },
  { category: "Performance", score: 82, icon: Zap, color: "from-yellow-500 to-amber-500" },
  { category: "Maintainability", score: 71, icon: TrendingUp, color: "from-green-500 to-emerald-500" },
];

const breakdown = [
  { metric: "Type Safety", value: 85, max: 100 },
  { metric: "Error Handling", value: 60, max: 100 },
  { metric: "Documentation", value: 45, max: 100 },
  { metric: "Test Coverage", value: 72, max: 100 },
  { metric: "Complexity Score", value: 68, max: 100 },
  { metric: "Dependencies", value: 90, max: 100 },
];

const Evaluator = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [animatedScores, setAnimatedScores] = useState(scores.map(() => 0));
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!isLoading) {
      scores.forEach((score, idx) => {
        let current = 0;
        const interval = setInterval(() => {
          current += 2;
          if (current >= score.score) {
            current = score.score;
            clearInterval(interval);
          }
          setAnimatedScores(prev => {
            const newScores = [...prev];
            newScores[idx] = current;
            return newScores;
          });
        }, 20);
      });
    }
  }, [isLoading]);

  const overallScore = Math.round(scores.reduce((acc, s) => acc + s.score, 0) / scores.length);

  return (
    <PipelineStep
      stepNumber={6}
      title="Evaluator & Scorer"
      description="Comprehensive scoring across multiple dimensions"
      icon={Award}
      status={isLoading ? "processing" : "complete"}
      nextStep={{
        label: "Generate Review",
        onClick: () => navigate("/dashboard/review"),
        disabled: isLoading,
      }}
    >
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
          <p className="text-muted-foreground">Calculating scores...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Overall score */}
          <div className="flex items-center justify-center p-8 rounded-xl bg-gradient-to-br from-primary/10 to-accent/10 border border-primary/20">
            <div className="text-center">
              <div className="relative w-32 h-32 mx-auto mb-4">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle
                    className="stroke-secondary"
                    strokeWidth="8"
                    fill="none"
                    r="42"
                    cx="50"
                    cy="50"
                  />
                  <circle
                    className="stroke-primary transition-all duration-1000"
                    strokeWidth="8"
                    fill="none"
                    r="42"
                    cx="50"
                    cy="50"
                    strokeDasharray={`${overallScore * 2.64} 264`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-4xl font-bold text-foreground">{overallScore}</span>
                </div>
              </div>
              <p className="text-lg font-semibold text-foreground">Overall Score</p>
              <p className="text-sm text-muted-foreground">Based on {scores.length} categories</p>
            </div>
          </div>

          {/* Category scores */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {scores.map((score, idx) => (
              <div
                key={score.category}
                className="p-4 rounded-lg bg-secondary/30 border border-border/30"
              >
                <div className={cn(
                  "w-10 h-10 rounded-lg flex items-center justify-center mb-3 bg-gradient-to-br",
                  score.color
                )}>
                  <score.icon className="w-5 h-5 text-white" />
                </div>
                <p className="text-2xl font-bold text-foreground">{animatedScores[idx]}</p>
                <p className="text-sm text-muted-foreground">{score.category}</p>
              </div>
            ))}
          </div>

          {/* Detailed breakdown */}
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-4">
              Detailed Breakdown
            </p>
            <div className="space-y-3">
              {breakdown.map((item) => (
                <div key={item.metric} className="flex items-center gap-4">
                  <span className="text-sm text-foreground w-32">{item.metric}</span>
                  <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all duration-1000",
                        item.value >= 80 ? "bg-green-500" : item.value >= 60 ? "bg-yellow-500" : "bg-red-500"
                      )}
                      style={{ width: `${item.value}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-foreground w-12 text-right">
                    {item.value}%
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

export default Evaluator;
