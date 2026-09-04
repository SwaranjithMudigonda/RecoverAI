import React from 'react';

export const HeroSection: React.FC = () => {
  return (
    <section className="bg-[#111820] border border-[#26313D] rounded-xl p-6 sm:p-8">
      <div className="flex flex-col md:flex-row items-start justify-between gap-6 pb-6 border-b border-[#26313D]">
        <div className="max-w-3xl">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Simulated Recovery Environment
            </span>
            <span className="text-xs text-[#9AA6B2]">
              LightGBM + Isotonic Calibration
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#F3F5F7] mb-2">
            RecoverAI Decision Engine
          </h1>
          <p className="text-base font-medium text-blue-400 mb-2">
            AI-assisted recovery decisions for failed payments
          </p>
          <p className="text-sm text-[#9AA6B2] leading-relaxed max-w-2xl">
            Evaluates post-decline transaction context through a calibrated ML S-learner, enforces central business safety guardrails (GR01–GR06), and selects the highest net expected utility recovery action. Replaces blind retries with an optimal policy maximizing recovered revenue while minimizing execution fees.
          </p>
        </div>

        <div className="bg-[#141B23] border border-[#26313D] rounded-lg p-4 max-w-xs shrink-0 text-xs">
          <div className="font-semibold text-amber-400 mb-1">
            Simulated Prototype Only
          </div>
          <p className="text-[#9AA6B2] leading-relaxed">
            Olist provides real transaction context. Failure reasons, actions, and recovery outcomes are simulated for policy evaluation.
          </p>
        </div>
      </div>

      {/* Clean KPI Spec Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6">
        <div className="border-l-2 border-l-blue-500 pl-3">
          <div className="text-xs font-medium text-[#9AA6B2]">Architecture</div>
          <div className="text-base font-semibold text-[#F3F5F7] mt-0.5">S-Learner</div>
          <div className="text-xs text-[#667380]">LightGBM + Isotonic</div>
        </div>

        <div className="border-l-2 border-l-emerald-500 pl-3">
          <div className="text-xs font-medium text-[#9AA6B2]">Safety Guardrails</div>
          <div className="text-base font-semibold text-[#F3F5F7] mt-0.5">6 Invariants</div>
          <div className="text-xs text-[#667380]">GR01–GR06 Central Path</div>
        </div>

        <div className="border-l-2 border-l-purple-500 pl-3">
          <div className="text-xs font-medium text-[#9AA6B2]">Candidate Actions</div>
          <div className="text-base font-semibold text-[#F3F5F7] mt-0.5">4 Actions</div>
          <div className="text-xs text-[#667380]">RETRY • NUDGE • ESCALATE • STOP</div>
        </div>

        <div className="border-l-2 border-l-slate-500 pl-3">
          <div className="text-xs font-medium text-[#9AA6B2]">Held-Out Test Set</div>
          <div className="text-base font-semibold text-[#F3F5F7] mt-0.5">2,283 Cases</div>
          <div className="text-xs text-[#667380]">R$ 345,292.12 Revenue at Risk</div>
        </div>
      </div>
    </section>
  );
};
