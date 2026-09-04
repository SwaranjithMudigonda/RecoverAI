import { useState } from 'react';
import { useHealth } from './hooks/useHealth';
import { useRecommendation } from './hooks/useRecommendation';
import { Header } from './components/Header';
import { SimulationBanner } from './components/SimulationBanner';
import { DecisionHero as LiveDecisionCenter } from './components/DecisionHero';
import { PaymentInputForm } from './sections/PaymentInputForm';
import { WhyDecision } from './sections/WhyDecision';
import { ActionComparison } from './sections/ActionComparison';
import { RecoveryPipeline } from './sections/RecoveryPipeline';
import { BatchRunner } from './sections/BatchRunner';
import { TrustAndEvidencePage } from './sections/TrustAndEvidencePage';
import { useCurrency } from './lib/utils';

export function App() {
  const [activeTab, setActiveTab] = useState<'decide' | 'batch' | 'trust'>('decide');
  const { isOnline } = useHealth();
  const { currency } = useCurrency();
  const {
    context,
    activePreset,
    status,
    recommendation,
    error,
    lastRequestId,
    applyPreset,
    updateContextField,
    executeRecommendation,
  } = useRecommendation();

  return (
    <div className="min-h-screen flex flex-col bg-[#0B0E14] text-[#F3F5F7] font-sans selection:bg-blue-600 selection:text-white">
      {/* Top Main Navigation Header */}
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        isOnline={isOnline}
      />

      {/* Persistent Factual Simulation Disclaimer Banner */}
      <SimulationBanner />

      {/* Main Content Viewport */}
      <main key={currency} className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'decide' ? (
          <div className="space-y-8">
            {/* 1. DOMINANT PRIMARY DECISION HERO (LiveDecisionCenter) */}
            <LiveDecisionCenter
              status={status}
              recommendation={recommendation}
              error={error}
              paymentValue={context.payment_value}
              onRetry={() => executeRecommendation()}
            />

            {/* 2. SCENARIO INPUT (Quick Scenarios + Collapsed 13-Field Parameter Form) */}
            <PaymentInputForm
              context={context}
              activePreset={activePreset}
              status={status}
              onSelectPreset={applyPreset}
              onUpdateField={updateContextField}
              onSubmit={() => executeRecommendation()}
            />

            {/* 3. ALGORITHMIC EXPLAINABILITY & WHY THIS DECISION */}
            <WhyDecision
              recommendation={recommendation}
              context={context}
              isError={status === 'ERROR'}
            />

            {/* 4. ALTERNATIVE ACTIONS EVALUATION & CONSOLIDATED UTILITY BAR */}
            <ActionComparison
              recommendation={recommendation}
              isError={status === 'ERROR'}
            />

            {/* 5. COMPACT PIPELINE TRACE */}
            <RecoveryPipeline />
          </div>
        ) : activeTab === 'batch' ? (
          /* BATCH STREAMING & BULK RECOVERY ENGINE */
          <BatchRunner />
        ) : (
          /* TRUST & EVIDENCE CENTER (Guardrails, Benchmarks, Evaluation, Security & Audit) */
          <TrustAndEvidencePage
            recommendation={recommendation}
            lastRequestId={lastRequestId}
          />
        )}
      </main>

      {/* Clean Operations Footer */}
      <footer className="w-full border-t border-[#232D38] bg-[#0B0E14] py-6 px-4 text-center text-xs text-[#8C9BAE]">
        <div className="max-w-4xl mx-auto space-y-2">
          <div className="flex flex-wrap items-center justify-center gap-2 text-[#8C9BAE] font-mono text-[11px]">
            <span>RecoverAI Decision Engine</span>
            <span>•</span>
            <span>Razorpay AI Builder Internship 2026</span>
            <span>•</span>
            <span className="text-blue-400 font-semibold">Track 03: AI Revenue Recovery</span>
          </div>
          <p className="text-[11px] text-[#667380] leading-relaxed max-w-3xl mx-auto">
            RecoverAI is a decision-recommendation prototype. RETRY, NUDGE, ESCALATE, and STOP are recommendations. No real payment transaction or payment gateway is executed. No real customer communication is executed. Olist provides real transaction context. Recovery outcomes and failure reasons are simulated.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
