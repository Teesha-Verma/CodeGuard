import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@/lib/context/ThemeContext';
import { ActiveFindingProvider } from '@/lib/context/ActiveFindingContext';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DashboardPage from './pages/DashboardPage';
import PRReviewPage from './pages/PRReviewPage';
import SnippetReviewPage from './pages/SnippetReviewPage';
import ReviewsHistoryPage from './pages/ReviewsHistoryPage';
import ReviewDetailsPage from './pages/ReviewDetailsPage';
import SettingsPage from './pages/SettingsPage';
import NotFoundPage from './pages/NotFoundPage';

// Six Major Capabilities
import LearnerPage from './pages/LearnerPage';
import AssistantPage from './pages/AssistantPage';
import PlaygroundPage from './pages/PlaygroundPage';
import DataflowPage from './pages/DataflowPage';
import SecurityHealthPage from './pages/SecurityHealthPage';
import RiskViewPage from './pages/RiskViewPage';
import AcademyPage from './pages/AcademyPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';

export default function App() {
  return (
    <ThemeProvider>
      <ActiveFindingProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Marketing & Auth Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />

            {/* Authenticated Workspace Routes */}
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/review/pr" element={<PRReviewPage />} />
            <Route path="/review/snippet" element={<SnippetReviewPage />} />
            <Route path="/reviews" element={<ReviewsHistoryPage />} />
            <Route path="/reviews/:reviewId" element={<ReviewDetailsPage />} />
            <Route path="/settings" element={<SettingsPage />} />

            {/* Six Major Extended Capabilities */}
            <Route path="/learn" element={<LearnerPage />} />
            <Route path="/learn/academy" element={<AcademyPage />} />
            <Route path="/learn/knowledge" element={<KnowledgeBasePage />} />
            <Route path="/assistant" element={<AssistantPage />} />
            <Route path="/playground" element={<PlaygroundPage />} />
            <Route path="/dataflow" element={<DataflowPage />} />
            <Route path="/security" element={<SecurityHealthPage />} />
            <Route path="/security/risk" element={<RiskViewPage />} />

            {/* Catch-all */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </BrowserRouter>
      </ActiveFindingProvider>
    </ThemeProvider>
  );
}

