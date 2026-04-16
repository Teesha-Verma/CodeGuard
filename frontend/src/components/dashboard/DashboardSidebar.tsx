import { NavLink } from "@/components/NavLink";
import { useLocation, useNavigate } from "react-router-dom";
import { 
  Bug, 
  GitBranch, 
  FileCode, 
  TreeDeciduous, 
  Search, 
  Brain, 
  Award, 
  FileText, 
  MessageSquare,
  LogOut,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { Button } from "@/components/ui/button";

const menuItems = [
  { 
    title: "Repository Input", 
    path: "/dashboard", 
    icon: GitBranch,
    description: "Enter GitHub repo URL"
  },
  { 
    title: "Diff Extractor", 
    path: "/dashboard/diff", 
    icon: FileCode,
    description: "Extract code changes"
  },
  { 
    title: "Static Analysis", 
    path: "/dashboard/ast", 
    icon: TreeDeciduous,
    description: "AST analysis"
  },
  { 
    title: "Linters", 
    path: "/dashboard/linters", 
    icon: Search,
    description: "Traditional linting"
  },
  { 
    title: "LLM Reasoning", 
    path: "/dashboard/llm", 
    icon: Brain,
    description: "AI-powered analysis"
  },
  { 
    title: "Evaluator", 
    path: "/dashboard/scorer", 
    icon: Award,
    description: "Score & evaluate"
  },
  { 
    title: "Review Output", 
    path: "/dashboard/review", 
    icon: FileText,
    description: "PR-style review"
  },
  { 
    title: "Report & Fixes", 
    path: "/dashboard/report", 
    icon: MessageSquare,
    description: "GitHub comments"
  },
];

export const DashboardSidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    navigate("/login");
  };

  return (
    <aside 
      className={cn(
        "h-screen bg-card/50 backdrop-blur-xl border-r border-border/50 flex flex-col transition-all duration-300",
        collapsed ? "w-20" : "w-72"
      )}
    >
      {/* Logo */}
      <div className="p-4 border-b border-border/50 flex items-center justify-between">
        <div className={cn("flex items-center gap-3", collapsed && "justify-center w-full")}>
          <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
            <Bug className="w-6 h-6 text-primary" />
          </div>
          {!collapsed && (
            <div>
              <h1 className="font-display text-lg font-bold text-foreground">CodeGuard</h1>
              <p className="text-xs text-muted-foreground">Code Review AI</p>
            </div>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(!collapsed)}
          className={cn("text-muted-foreground hover:text-foreground", collapsed && "absolute right-2")}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </Button>
      </div>

      {/* Pipeline title */}
      {!collapsed && (
        <div className="px-4 py-3">
          <p className="text-xs font-semibold text-primary uppercase tracking-wider">Pipeline Steps</p>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 overflow-y-auto">
        <ul className="space-y-1">
          {menuItems.map((item, index) => {
            const isActive = location.pathname === item.path;
            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  end={item.path === "/dashboard"}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group",
                    "hover:bg-secondary/50",
                    collapsed && "justify-center px-2"
                  )}
                  activeClassName="bg-primary/10 border border-primary/30 text-primary"
                >
                  <div className={cn(
                    "flex items-center justify-center w-8 h-8 rounded-md transition-colors",
                    isActive ? "bg-primary/20" : "bg-secondary/50 group-hover:bg-secondary"
                  )}>
                    <span className={cn(
                      "text-xs font-bold",
                      isActive ? "text-primary" : "text-muted-foreground"
                    )}>
                      {index + 1}
                    </span>
                  </div>
                  {!collapsed && (
                    <div className="flex-1 min-w-0">
                      <p className={cn(
                        "text-sm font-medium truncate",
                        isActive ? "text-primary" : "text-foreground"
                      )}>
                        {item.title}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">{item.description}</p>
                    </div>
                  )}
                  {!collapsed && (
                    <item.icon className={cn(
                      "w-4 h-4 flex-shrink-0",
                      isActive ? "text-primary" : "text-muted-foreground"
                    )} />
                  )}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Logout button */}
      <div className="p-3 border-t border-border/50">
        <button
          onClick={handleLogout}
          className={cn(
            "flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors",
            collapsed && "justify-center"
          )}
        >
          <LogOut className="w-5 h-5" />
          {!collapsed && <span className="text-sm font-medium">Logout</span>}
        </button>
      </div>
    </aside>
  );
};
