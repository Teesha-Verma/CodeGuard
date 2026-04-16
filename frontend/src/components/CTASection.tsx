import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowRight, Code2 } from "lucide-react";

const CTASection = () => {
  return (
    <section className="py-32 relative grid-bg">
      <div className="absolute inset-0 bg-gradient-to-b from-background via-background/95 to-background pointer-events-none" />
      
      <div className="container mx-auto px-6 relative z-10 text-center">
        <h2 className="font-display text-4xl md:text-5xl lg:text-6xl font-bold text-foreground mb-8">
          Ready to Ship Better Code?
        </h2>
        
        <Link to="/login">
          <Button variant="cta" size="lg" className="group">
            Get Started Free
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </Button>
        </Link>
      </div>
    </section>
  );
};

const Footer = () => {
  return (
    <footer className="py-8 border-t border-border/30">
      <div className="container mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-glow-cyan to-glow-cyan/70 flex items-center justify-center">
            <Code2 className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="font-display text-lg font-semibold text-foreground">CodeGuard AI</span>
        </div>
        
        <p className="text-sm text-muted-foreground">
          © 2026 CodeGuard. All rights reserved.
        </p>
      </div>
    </footer>
  );
};

export { CTASection, Footer };
