import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import RepoInput from "./pages/dashboard/RepoInput";
import DiffExtractor from "./pages/dashboard/DiffExtractor";
import StaticAnalysis from "./pages/dashboard/StaticAnalysis";
import Linters from "./pages/dashboard/Linters";
import LLMReasoning from "./pages/dashboard/LLMReasoning";
import Evaluator from "./pages/dashboard/Evaluator";
import ReviewOutput from "./pages/dashboard/ReviewOutput";
import Report from "./pages/dashboard/Report";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<Dashboard />}>
            <Route index element={<RepoInput />} />
            <Route path="diff" element={<DiffExtractor />} />
            <Route path="ast" element={<StaticAnalysis />} />
            <Route path="linters" element={<Linters />} />
            <Route path="llm" element={<LLMReasoning />} />
            <Route path="scorer" element={<Evaluator />} />
            <Route path="review" element={<ReviewOutput />} />
            <Route path="report" element={<Report />} />
          </Route>
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
