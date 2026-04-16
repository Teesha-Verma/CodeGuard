import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { LucideIcon, ChevronRight } from "lucide-react";

interface PipelineStepProps {
  stepNumber: number;
  title: string;
  description: string;
  icon: LucideIcon;
  children: ReactNode;
  nextStep?: {
    label: string;
    onClick: () => void;
    disabled?: boolean;
  };
  status?: "idle" | "processing" | "complete" | "error";
}

export const PipelineStep = ({
  stepNumber,
  title,
  description,
  icon: Icon,
  children,
  nextStep,
  status = "idle"
}: PipelineStepProps) => {
  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <div className={cn(
          "w-12 h-12 rounded-xl flex items-center justify-center relative",
          status === "complete" && "bg-green-500/20",
          status === "processing" && "bg-primary/20 animate-pulse",
          status === "error" && "bg-destructive/20",
          status === "idle" && "bg-primary/20"
        )}>
          <Icon className={cn(
            "w-6 h-6",
            status === "complete" && "text-green-500",
            status === "processing" && "text-primary",
            status === "error" && "text-destructive",
            status === "idle" && "text-primary"
          )} />
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-secondary text-xs font-bold flex items-center justify-center text-foreground">
            {stepNumber}
          </span>
        </div>
        <div>
          <h2 className="font-display text-2xl font-bold text-foreground">{title}</h2>
          <p className="text-muted-foreground">{description}</p>
        </div>
      </div>

      {/* Content */}
      <div className="glass-card rounded-xl p-6 mb-6">
        {children}
      </div>

      {/* Next step button */}
      {nextStep && (
        <div className="flex justify-end">
          <button
            onClick={nextStep.onClick}
            disabled={nextStep.disabled}
            className={cn(
              "flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all",
              "bg-gradient-to-r from-primary to-accent text-primary-foreground",
              "hover:shadow-lg hover:shadow-primary/25",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {nextStep.label}
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
