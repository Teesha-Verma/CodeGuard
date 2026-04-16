import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Code2 } from "lucide-react";

const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-lg border-b border-border/30">
      <div className="container mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-glow-cyan to-glow-cyan/70 flex items-center justify-center shadow-[0_0_20px_hsl(var(--glow-cyan)/0.4)]">
            <Code2 className="w-5 h-5 text-primary-foreground" />
          </div>
          <span className="font-display text-xl font-semibold text-foreground">CodeGuard</span>
        </Link>
        
        <Link to="/login">
          <Button variant="nav" size="default">
            Get Started
          </Button>
        </Link>
      </div>
    </nav>
  );
};

export default Navbar;
