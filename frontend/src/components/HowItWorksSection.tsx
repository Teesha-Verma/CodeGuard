import { Upload, Brain, CheckCircle } from "lucide-react";

const steps = [
  {
    icon: Upload,
    title: "Submit Code",
    description: "Upload your codebase or connect your repository",
    color: "from-glow-cyan to-glow-cyan",
    shadowColor: "hsl(187 100% 50% / 0.5)",
  },
  {
    icon: Brain,
    title: "AI Analysis",
    description: "Our AI scans for bugs, vulnerabilities, and root causes",
    color: "from-glow-cyan to-blue-500",
    shadowColor: "hsl(200 100% 50% / 0.5)",
  },
  {
    icon: CheckCircle,
    title: "Get Solutions",
    description: "Receive detailed reports with actionable fixes",
    color: "from-glow-purple to-glow-purple",
    shadowColor: "hsl(280 70% 60% / 0.5)",
  },
];

const HowItWorksSection = () => {
  return (
    <section className="py-24 relative">
      <div className="container mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="font-display text-4xl md:text-5xl font-bold text-foreground mb-4">
            How It Works
          </h2>
          <p className="text-lg text-muted-foreground">
            From Bug to Solution in Seconds
          </p>
        </div>
        
        {/* Steps */}
        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {steps.map((step, index) => (
            <div
              key={index}
              className="glass-card glow-border rounded-2xl p-8 text-center relative transition-all duration-300 hover:scale-[1.02]"
            >
              {/* Step number badge */}
              <div className="absolute -top-3 -right-3 step-badge">
                {index + 1}
              </div>
              
              {/* Icon */}
              <div
                className="icon-box-gradient mx-auto mb-6"
                style={{
                  background: `linear-gradient(135deg, ${step.color.includes('cyan') ? 'hsl(187 100% 50%)' : 'hsl(280 70% 60%)'}, ${step.color.includes('purple') ? 'hsl(280 70% 60%)' : 'hsl(200 100% 50%)'})`,
                  boxShadow: `0 0 30px ${step.shadowColor}`,
                }}
              >
                <step.icon className="w-8 h-8 text-foreground" />
              </div>
              
              <h3 className="font-display text-xl font-semibold text-foreground mb-3">
                {step.title}
              </h3>
              <p className="text-muted-foreground leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>
        
        {/* Analysis time badge */}
        <div className="flex justify-center mt-12">
          <div className="inline-flex items-center gap-2 px-6 py-3 rounded-full border border-primary/30 bg-primary/5">
            <span className="text-muted-foreground">Average analysis time:</span>
            <span className="text-foreground font-semibold">2.3 seconds</span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorksSection;
