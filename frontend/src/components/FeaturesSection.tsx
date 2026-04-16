import { Code2, Bug, GitBranch, Sparkles, Shield, Zap } from "lucide-react";

const features = [
  {
    icon: Code2,
    title: "Smart Code Review",
    description: "AI analyzes patterns and best practices",
  },
  {
    icon: Bug,
    title: "Bug Detection",
    description: "Catches issues before they escalate",
  },
  {
    icon: GitBranch,
    title: "Root Cause Analysis",
    description: "Traces problems to their source",
  },
  {
    icon: Sparkles,
    title: "Auto Fix Suggestions",
    description: "Get AI-generated solutions instantly",
  },
  {
    icon: Shield,
    title: "Security Scanning",
    description: "Identifies vulnerabilities early",
  },
  {
    icon: Zap,
    title: "Lightning Fast",
    description: "Complete analysis in seconds",
  },
];

const FeaturesSection = () => {
  return (
    <section className="py-24 relative">
      <div className="container mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="font-display text-4xl md:text-5xl font-bold text-foreground mb-4">
            Powerful Features
          </h2>
          <p className="text-lg text-muted-foreground">
            Everything you need for perfect code
          </p>
        </div>
        
        {/* Features grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="group glass-card glow-border rounded-2xl p-6 transition-all duration-300 hover:bg-card/60 hover:scale-[1.02]"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="icon-box mb-5">
                <feature.icon className="w-6 h-6 text-primary-foreground" />
              </div>
              <h3 className="font-display text-xl font-semibold text-foreground mb-2">
                {feature.title}
              </h3>
              <p className="text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
