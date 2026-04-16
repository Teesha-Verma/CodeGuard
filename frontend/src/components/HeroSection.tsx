import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

const HeroSection = () => {
  return (
    <section className="relative min-h-screen pt-24 pb-20 overflow-hidden grid-bg">
      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-background/95 to-background pointer-events-none" />
      
      <div className="container mx-auto px-6 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center min-h-[calc(100vh-8rem)]">
          {/* Left content */}
          <div className="space-y-8 animate-fade-in">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-primary/30 bg-primary/5">
              <span className="text-primary text-sm font-medium">AI-Powered Code Analysis</span>
            </div>
            
            {/* Heading */}
            <h1 className="font-display text-5xl md:text-6xl lg:text-7xl font-bold text-foreground leading-tight">
              CodeGuard<br />
              <span className="text-foreground/90">AI</span>
            </h1>
            
            {/* Subtitle */}
            <p className="text-lg md:text-xl text-muted-foreground max-w-lg leading-relaxed">
              Catch bugs before production. Root cause analysis in seconds.
            </p>
            
            {/* CTA Button */}
            <div className="pt-4">
              <Link to="/login">
                <Button variant="hero" size="lg" className="group">
                  Get Started
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </Button>
              </Link>
            </div>
          </div>
          
          {/* Right content - Node visualization */}
          <div className="relative flex items-center justify-center animate-float">
            <NetworkVisualization />
          </div>
        </div>
      </div>
    </section>
  );
};

const NetworkVisualization = () => {
  return (
    <div className="relative w-full max-w-md aspect-square">
      {/* Central node */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 rounded-full bg-gradient-to-br from-glow-cyan/40 to-glow-cyan/20 border-2 border-glow-cyan/60 animate-pulse-glow flex items-center justify-center">
        <div className="w-16 h-16 rounded-full bg-glow-cyan/30 border border-glow-cyan/50" />
      </div>
      
      {/* Orbiting nodes */}
      {[
        { x: '20%', y: '15%', size: 'w-10 h-10' },
        { x: '75%', y: '10%', size: 'w-8 h-8' },
        { x: '90%', y: '40%', size: 'w-12 h-12' },
        { x: '80%', y: '75%', size: 'w-9 h-9' },
        { x: '50%', y: '90%', size: 'w-10 h-10' },
        { x: '15%', y: '70%', size: 'w-8 h-8' },
        { x: '5%', y: '35%', size: 'w-11 h-11' },
      ].map((node, i) => (
        <div
          key={i}
          className={`absolute ${node.size} rounded-full bg-glow-cyan/20 border border-glow-cyan/40`}
          style={{ left: node.x, top: node.y }}
        >
          <div className="w-full h-full rounded-full bg-glow-cyan/10" />
        </div>
      ))}
      
      {/* Connection lines (SVG) */}
      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 400">
        <defs>
          <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="hsl(187 100% 50% / 0.3)" />
            <stop offset="100%" stopColor="hsl(187 100% 50% / 0.1)" />
          </linearGradient>
        </defs>
        {/* Lines from center to nodes */}
        <line x1="200" y1="200" x2="80" y2="60" stroke="url(#lineGradient)" strokeWidth="1" />
        <line x1="200" y1="200" x2="300" y2="40" stroke="url(#lineGradient)" strokeWidth="1" />
        <line x1="200" y1="200" x2="360" y2="160" stroke="url(#lineGradient)" strokeWidth="1" />
        <line x1="200" y1="200" x2="320" y2="300" stroke="url(#lineGradient)" strokeWidth="1" />
        <line x1="200" y1="200" x2="200" y2="360" stroke="url(#lineGradient)" strokeWidth="1" />
        <line x1="200" y1="200" x2="60" y2="280" stroke="url(#lineGradient)" strokeWidth="1" />
        <line x1="200" y1="200" x2="20" y2="140" stroke="url(#lineGradient)" strokeWidth="1" />
      </svg>
    </div>
  );
};

export default HeroSection;
