import React, { useState } from 'react';
import { ShieldCheck, BarChart3, Award, Lock } from 'lucide-react';
import { GuardrailMatrix } from './GuardrailMatrix';
import { ModelComparison } from './ModelComparison';
import { PolicyPerformance } from './PolicyPerformance';
import { BootstrapResults } from './BootstrapResults';
import { SecurityStatus } from './SecurityStatus';
import { ModelSignatures } from './ModelSignatures';
import { IntegrationVerification } from './IntegrationVerification';
import { Auditability } from './Auditability';
import type { RecommendationResponse } from '../types/recovery';

interface TrustAndEvidencePageProps {
  recommendation: RecommendationResponse | null;
  lastRequestId: string;
}

export const TrustAndEvidencePage: React.FC<TrustAndEvidencePageProps> = ({
  recommendation,
  lastRequestId,
}) => {
  const [activeSection, setActiveSection] = useState<'all' | 'guardrails' | 'benchmarks' | 'evaluation' | 'security'>('all');

  return (
    <div className="space-y-8">
      {/* Trust & Evidence Header Banner */}
      <div className="bg-[#121820] border border-[#232D38] rounded-xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-blue-400 px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/20">
              TECHNICAL PROVENANCE & EVIDENCE
            </span>
            <span className="text-xs text-[#8C9BAE] font-mono">• Step 5F / Step 7E Verified</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[#F3F5F7]">
            Trust & System Evidence Center
          </h1>
          <p className="text-xs text-[#8C9BAE] max-w-2xl leading-relaxed">
            Technical audit evidence, safety guardrail specifications, model benchmark comparisons, held-out evaluation results, statistical bootstrap confidence intervals, and defensive API security controls.
          </p>
        </div>

        {/* Filter Navigation Bar */}
        <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-lg bg-[#16202C] border border-[#263545] shrink-0 text-xs font-semibold text-[#8C9BAE]">
          <button
            type="button"
            onClick={() => setActiveSection('all')}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeSection === 'all' ? 'bg-blue-600 text-white' : 'hover:text-[#F3F5F7]'
            }`}
          >
            All Evidence
          </button>
          <button
            type="button"
            onClick={() => setActiveSection('guardrails')}
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 ${
              activeSection === 'guardrails' ? 'bg-blue-600 text-white' : 'hover:text-[#F3F5F7]'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Guardrails</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveSection('benchmarks')}
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 ${
              activeSection === 'benchmarks' ? 'bg-blue-600 text-white' : 'hover:text-[#F3F5F7]'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Benchmarks</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveSection('evaluation')}
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 ${
              activeSection === 'evaluation' ? 'bg-blue-600 text-white' : 'hover:text-[#F3F5F7]'
            }`}
          >
            <Award className="w-3.5 h-3.5" />
            <span>Evaluation</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveSection('security')}
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 ${
              activeSection === 'security' ? 'bg-blue-600 text-white' : 'hover:text-[#F3F5F7]'
            }`}
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Security & Audit</span>
          </button>
        </div>
      </div>

      {/* 1. GUARDRAILS */}
      {(activeSection === 'all' || activeSection === 'guardrails') && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-blue-400 uppercase tracking-wider">
            <span>SECTION 01</span>
            <span>•</span>
            <span>SAFETY GUARDRAIL CONTROL SYSTEM</span>
          </div>
          <GuardrailMatrix recommendation={recommendation} />
        </div>
      )}

      {/* 2. MODEL BENCHMARKS */}
      {(activeSection === 'all' || activeSection === 'benchmarks') && (
        <div className="space-y-4 pt-4 border-t border-[#232D38]">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-blue-400 uppercase tracking-wider">
            <span>SECTION 02</span>
            <span>•</span>
            <span>SUPPLEMENTARY MODEL BENCHMARKS</span>
          </div>
          <ModelComparison />
        </div>
      )}

      {/* 3. EVALUATION */}
      {(activeSection === 'all' || activeSection === 'evaluation') && (
        <div className="space-y-6 pt-4 border-t border-[#232D38]">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-blue-400 uppercase tracking-wider">
            <span>SECTION 03</span>
            <span>•</span>
            <span>HELD-OUT POLICY EVALUATION & BOOTSTRAP INFERENCE</span>
          </div>
          <PolicyPerformance />
          <BootstrapResults />
        </div>
      )}

      {/* 4. SECURITY & AUDIT */}
      {(activeSection === 'all' || activeSection === 'security') && (
        <div className="space-y-6 pt-4 border-t border-[#232D38]">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-blue-400 uppercase tracking-wider">
            <span>SECTION 04</span>
            <span>•</span>
            <span>DEFENSIVE API SECURITY, PROVENANCE & AUDIT</span>
          </div>
          <SecurityStatus />
          <ModelSignatures />
          <IntegrationVerification />
          <Auditability lastRequestId={lastRequestId} />
        </div>
      )}
    </div>
  );
};
