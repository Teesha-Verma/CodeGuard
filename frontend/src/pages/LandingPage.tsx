import React, { useEffect } from 'react';
import { PublicNavbar } from '@/components/public/PublicNavbar';
import { ProductPreviewHero } from '@/components/public/ProductPreviewHero';
import { HowItWorksSection } from '@/components/public/HowItWorksSection';
import { CapabilitiesSection } from '@/components/public/CapabilitiesSection';
import { SecurityFindingDemo } from '@/components/public/SecurityFindingDemo';
import { DeveloperWorkflowSection } from '@/components/public/DeveloperWorkflowSection';
import { FinalCTASection } from '@/components/public/FinalCTASection';
import { PublicFooter } from '@/components/public/PublicFooter';

export default function LandingPage() {
  useEffect(() => {
    document.title = 'CodeGuard — Intelligent Code Review & Security Analysis';

    // Update meta description
    let metaDescription = document.querySelector('meta[name="description"]');
    if (!metaDescription) {
      metaDescription = document.createElement('meta');
      metaDescription.setAttribute('name', 'description');
      document.head.appendChild(metaDescription);
    }
    metaDescription.setAttribute(
      'content',
      'Professional code review and security analysis platform for developers. Analyzes pull requests using static AST analysis, control flow graphs, dataflow taint tracking, and contextual reasoning.'
    );
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-[#0a0d14] text-slate-900 dark:text-slate-100">
      <PublicNavbar />
      <main className="flex-1">
        <ProductPreviewHero />
        <HowItWorksSection />
        <CapabilitiesSection />
        <SecurityFindingDemo />
        <DeveloperWorkflowSection />
        <FinalCTASection />
      </main>
      <PublicFooter />
    </div>
  );
}
