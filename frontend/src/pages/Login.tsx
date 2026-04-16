import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Bug, Eye, EyeOff } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import loginBg from "@/assets/login-bg.jpg";

// Sample credentials
const SAMPLE_EMAIL = "demo@codeguard.dev";
const SAMPLE_PASSWORD = "codeguard123";

const Login = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Simulate login delay
    setTimeout(() => {
      if (email === SAMPLE_EMAIL && password === SAMPLE_PASSWORD) {
        toast({
          title: "Login successful!",
          description: "Redirecting to dashboard...",
        });
        navigate("/dashboard");
      } else {
        toast({
          title: "Invalid credentials",
          description: `Try: ${SAMPLE_EMAIL} / ${SAMPLE_PASSWORD}`,
          variant: "destructive",
        });
      }
      setIsLoading(false);
    }, 800);
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{
        backgroundImage: `url(${loginBg})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-background/80 backdrop-blur-[2px]" />
      
      {/* Bottom glow effect */}
      <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-gradient-to-r from-transparent via-glow-cyan to-transparent shadow-[0_0_60px_hsl(var(--glow-cyan)/0.9)]" />
      
      {/* Login card */}
      <div className="relative z-10 w-full max-w-md mx-4">
        {/* Bug icon with glow and glitch lines */}
        <div className="flex justify-center mb-4">
          <div className="relative">
            {/* Glitch line left */}
            <div className="absolute left-1/2 top-1/2 -translate-y-1/2 -translate-x-full w-32 h-[3px]">
              <div className="w-full h-full bg-gradient-to-l from-destructive via-destructive/60 to-transparent" 
                   style={{ 
                     clipPath: 'polygon(0 0, 100% 20%, 95% 50%, 100% 80%, 0 100%)',
                     filter: 'blur(0.5px)'
                   }} />
            </div>
            
            {/* Glitch line right */}
            <div className="absolute left-1/2 top-1/2 -translate-y-1/2 w-32 h-[3px]">
              <div className="w-full h-full bg-gradient-to-r from-destructive via-destructive/60 to-transparent"
                   style={{ 
                     clipPath: 'polygon(0 20%, 100% 0, 100% 100%, 0 80%)',
                     filter: 'blur(0.5px)'
                   }} />
            </div>
            
            {/* Bug icon */}
            <div 
              className="w-32 h-32 rounded-full bg-destructive/30 flex items-center justify-center relative"
              style={{ 
                boxShadow: '0 0 100px hsl(0 84% 60% / 0.8), 0 0 150px hsl(0 84% 60% / 0.5)',
              }}
            >
              <Bug className="w-20 h-20 text-destructive" strokeWidth={1.5} />
            </div>
          </div>
        </div>
        
        {/* Card */}
        <div 
          className="rounded-xl p-8 border border-border/40"
          style={{
            background: 'linear-gradient(180deg, hsl(var(--muted)/0.4) 0%, hsl(var(--muted)/0.2) 100%)',
            backdropFilter: 'blur(20px)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05)'
          }}
        >
          <h1 className="font-display text-3xl font-bold text-foreground">
            Login
          </h1>
          
          {/* Sample credentials hint */}
          <div className="mt-3 p-3 rounded-lg bg-primary/10 border border-primary/20">
            <p className="text-xs text-primary">
              <span className="font-semibold">Demo:</span> {SAMPLE_EMAIL} / {SAMPLE_PASSWORD}
            </p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-5 mt-5">
            {/* Email */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                Email:
              </label>
              <Input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-muted/30 border-border/40 h-11 placeholder:text-muted-foreground/50"
              />
            </div>
            
            {/* Password */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                Password:
              </label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-muted/30 border-border/40 pr-10 h-11 placeholder:text-muted-foreground/50"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            
            {/* Login button */}
            <Button 
              type="submit" 
              size="lg" 
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-semibold h-12 mt-2 shadow-lg shadow-blue-500/25 disabled:opacity-50"
            >
              {isLoading ? "Logging in..." : "Login"}
            </Button>
            
            {/* Forgot password */}
            <div className="text-center pt-1">
              <Link 
                to="#" 
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Forgot Password?
              </Link>
            </div>
          </form>
        </div>
        
        {/* Back to home */}
        <div className="text-center mt-6">
          <Link 
            to="/" 
            className="text-sm text-muted-foreground hover:text-primary transition-colors inline-flex items-center gap-2"
          >
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Login;
