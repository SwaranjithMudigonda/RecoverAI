import React, { useState } from 'react';
import { ChevronDown, ChevronUp, CheckCircle2 } from 'lucide-react';

export const RecoveryPipeline: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  const steps = [
    {
      num: '01',
      title: 'Context Ingestion',
      desc: 'Validates 15 transaction features with sensitive credential stripping and schema defense.',
      tag: 'Ingestion',
    },
    {
      num: '02',
      title: 'ML S-Learner Estimation',
      desc: 'LightGBM S-Learner predicts raw recovery probability across candidate action vectors.',
      tag: 'Estimation',
    },
    {
      num: '03',
      title: 'Probability Calibration',
      desc: 'Isotonic Regression maps raw model scores to empirical observed frequencies (ECE = 0.0264).',
      tag: 'Calibration',
    },
    {
      num: '04',
      title: 'Guardrail Enforcement',
      desc: 'Central safety invariants (GR01–GR06) block non-viable actions prior to utility scoring.',
      tag: 'Safety Checks',
    },
    {
      num: '05',
      title: 'Net Expected Utility Scoring',
      desc: 'Computes EU(A, X) = P(A, X) · Value - Cost(A) to identify maximum revenue recovery return.',
      tag: 'Utility Scoring',
    },
    {
      num: '06',
      title: 'Action Selection & Audit',
      desc: 'Selects the argmax utility action and records a deterministic CSV audit log entry.',
      tag: 'Execution',
    },
  ];

  return (
    <section id="pipeline" className="bg-[#121820] border border-[#232D38] rounded-xl p-5 sm:p-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#232D38]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-[#F3F5F7]">
              Pipeline Trace
            </h3>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-[#16202C] text-blue-400 border border-[#263545]">
              6 STAGES
            </span>
          </div>
          <p className="text-xs text-[#8C9BAE] mt-0.5">
            Synchronous inference pipeline executed post-decline
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsExpanded(prev => !prev)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#16202C] border border-[#263545] text-xs font-semibold text-[#8C9BAE] hover:text-[#F3F5F7] transition-colors"
        >
          <span>{isExpanded ? 'Collapse Stage Details' : 'Expand Stage Details'}</span>
          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Compact Horizontal Pipeline Breadcrumb Bar */}
      <div className="bg-[#16202C] border border-[#263545] rounded-lg p-3.5">
        <div className="flex items-center justify-between gap-2 overflow-x-auto text-xs font-mono py-1">
          {steps.map((step, idx) => (
            <React.Fragment key={step.num}>
              <div className="flex items-center gap-2 shrink-0">
                <span className="w-5 h-5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[10px] font-bold flex items-center justify-center">
                  {step.num}
                </span>
                <span className="text-[#F3F5F7] font-sans font-medium">{step.title}</span>
              </div>
              {idx < steps.length - 1 && (
                <span className="text-[#667380] shrink-0 font-bold">→</span>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Detailed Stage Grid (Expanded View) */}
      {isExpanded && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 pt-2">
          {steps.map(step => (
            <div
              key={step.num}
              className="bg-[#16202C] border border-[#263545] rounded-lg p-4 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-xs font-mono font-bold text-blue-400">
                    STAGE {step.num}
                  </span>
                  <span className="text-[10px] font-mono text-[#8C9BAE] px-2 py-0.5 rounded bg-[#121820] border border-[#232D38]">
                    {step.tag}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-[#F3F5F7] mb-1">
                  {step.title}
                </h4>
                <p className="text-xs text-[#8C9BAE] leading-relaxed">
                  {step.desc}
                </p>
              </div>
              <div className="mt-3 pt-2 border-t border-[#232D38] flex items-center justify-between text-[11px] text-[#667380]">
                <span>Status:</span>
                <span className="text-emerald-400 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Active
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
};
