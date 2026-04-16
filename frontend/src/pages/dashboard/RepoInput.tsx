import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { GitBranch, Github, Link as LinkIcon, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { PipelineStep } from "@/components/dashboard/PipelineStep";
import { useToast } from "@/hooks/use-toast";

const RepoInput = () => {
  const [repoUrl, setRepoUrl] = useState("");
  const [prNumber, setPrNumber] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleAnalyze = () => {
    if (!repoUrl.trim()) {
      toast({
        title: "Repository URL required",
        description: "Please enter a valid GitHub repository URL",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    
    // Simulate fetching repo data
    setTimeout(() => {
      toast({
        title: "Repository loaded!",
        description: "Proceeding to extract diffs...",
      });
      setIsLoading(false);
      navigate("/dashboard/diff");
    }, 1500);
  };

  return (
    <PipelineStep
      stepNumber={1}
      title="GitHub Repository"
      description="Enter a GitHub repository URL or PR link to begin analysis"
      icon={GitBranch}
      nextStep={{
        label: "Extract Diffs",
        onClick: handleAnalyze,
        disabled: !repoUrl.trim() || isLoading,
      }}
    >
      <div className="space-y-6">
        {/* Repo URL input */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground flex items-center gap-2">
            <Github className="w-4 h-4" />
            Repository URL
          </label>
          <div className="relative">
            <Input
              type="url"
              placeholder="https://github.com/owner/repository"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              className="bg-muted/30 border-border/40 h-12 pl-10"
            />
            <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          </div>
        </div>

        {/* PR Number (optional) */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            Pull Request Number <span className="text-muted-foreground">(optional)</span>
          </label>
          <Input
            type="number"
            placeholder="e.g., 42"
            value={prNumber}
            onChange={(e) => setPrNumber(e.target.value)}
            className="bg-muted/30 border-border/40 h-12 max-w-xs"
          />
        </div>

        {/* Quick examples */}
        <div className="pt-4 border-t border-border/30">
          <p className="text-xs text-muted-foreground mb-3">Quick examples:</p>
          <div className="flex flex-wrap gap-2">
            {[
              "https://github.com/facebook/react",
              "https://github.com/microsoft/vscode",
              "https://github.com/vercel/next.js",
            ].map((url) => (
              <button
                key={url}
                onClick={() => setRepoUrl(url)}
                className="px-3 py-1.5 text-xs rounded-full bg-secondary/50 hover:bg-secondary text-foreground transition-colors"
              >
                {url.split("/").slice(-2).join("/")}
              </button>
            ))}
          </div>
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center gap-3 p-4 rounded-lg bg-primary/10 border border-primary/20">
            <Loader2 className="w-5 h-5 text-primary animate-spin" />
            <span className="text-sm text-primary">Connecting to repository...</span>
          </div>
        )}
      </div>
    </PipelineStep>
  );
};

export default RepoInput;
