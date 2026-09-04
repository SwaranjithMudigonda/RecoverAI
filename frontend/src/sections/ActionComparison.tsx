import React from 'react';
import { formatBRL, formatPercent } from '../lib/utils';
import type { RecommendationResponse, ActionType } from '../types/recovery';

interface ActionComparisonProps {
  recommendation: RecommendationResponse | null;
  isError: boolean;
}

export const ActionComparison: React.FC<ActionComparisonProps> = ({ recommendation, isError }) => {
  if (isError || !recommendation) {
    return (
      <section id="action-comparison" className="bg-[#121820] border border-[#232D38] rounded-xl p-5 sm:p-6 space-y-4">
        <div>
          <h3 className="text-base font-bold text-[#F3F5F7]">
            Alternative Actions Evaluation
          </h3>
          <p className="text-xs text-[#8C9BAE]">
            Comparison of candidate recovery actions, calibrated probabilities & expected utilities
          </p>
        </div>
        <p className="text-xs text-[#8C9BAE]">
          Select a quick scenario or click Run Recommendation to compare all 4 candidate recovery actions.
        </p>
      </section>
    );
  }

  const actions = recommendation.actions;
  const selectedAction = recommendation.decision?.selected_action;


  const actionMeta: Record<
    ActionType,
    { label: string; desc: string; cost: string }
  > = {
    RETRY: {
      label: 'Automated Retry',
      desc: 'Re-submits transaction via payment gateway rail',
      cost: 'R$ 0.50',
    },
    NUDGE: {
      label: 'Customer Nudge',
      desc: 'Prompts customer via SMS/WhatsApp to complete',
      cost: 'R$ 1.50',
    },
    ESCALATE: {
      label: 'Support Escalation',
      desc: 'Transfers to merchant support rep for outreach',
      cost: 'R$ 15.00',
    },
    STOP: {
      label: 'Halt Recovery',
      desc: 'Ceases recovery to avoid fee burn & churn',
      cost: 'R$ 0.00',
    },
  };

  const actionKeys: ActionType[] = ['RETRY', 'NUDGE', 'ESCALATE', 'STOP'];

  // Maximum utility for scaling visualization
  const maxUtil = Math.max(
    ...actionKeys.map(k => (actions?.[k]?.guardrail_result === 'BLOCKED' ? 0 : actions?.[k]?.utility ?? 0)),
    100
  );

  return (
    <section id="action-comparison" className="bg-[#121820] border border-[#232D38] rounded-xl p-5 sm:p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#232D38]">
        <div>
          <h3 className="text-base font-bold text-[#F3F5F7]">
            Alternative Actions Evaluation
          </h3>
          <p className="text-xs text-[#8C9BAE]">
            Comparison of candidate recovery actions, calibrated probabilities & expected utilities
          </p>
        </div>
        <span className="text-[11px] font-mono text-[#8C9BAE]">
          4 Candidate Actions
        </span>
      </div>

      {/* Consolidated Horizontal Expected Utility Visualization Bar */}
      <div className="bg-[#16202C] border border-[#263545] rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-[#F3F5F7]">Expected Utility Distribution (BRL)</span>
          <span className="text-[11px] text-[#8C9BAE]">Highest valid utility is selected</span>
        </div>

        <div className="space-y-2.5">
          {actionKeys.map(actKey => {
            const act = actions?.[actKey];
            const isSelected = selectedAction === actKey;
            const isBlocked = act?.guardrail_result === 'BLOCKED';
            const util = act?.utility ?? 0;
            const widthPct = isBlocked || util <= 0 ? 0 : Math.round((util / maxUtil) * 100);

            return (
              <div key={actKey} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className={`font-bold ${isSelected ? 'text-blue-400' : 'text-[#F3F5F7]'}`}>
                      {actKey}
                    </span>
                    {isSelected && (
                      <span className="text-[10px] font-sans font-semibold px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                        RECOMMENDED
                      </span>
                    )}
                    {isBlocked && (
                      <span className="text-[10px] font-sans font-semibold px-1.5 py-0.2 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        BLOCKED
                      </span>
                    )}
                  </div>
                  <span className={isBlocked ? 'text-rose-400 font-semibold' : isSelected ? 'text-emerald-400 font-bold' : 'text-[#D0D7DE]'}>
                    {isError ? '—' : isBlocked ? 'Blocked (-999k)' : formatBRL(util)}
                  </span>
                </div>

                <div className="h-2 w-full bg-[#121820] rounded-full overflow-hidden flex">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isBlocked
                        ? 'bg-rose-500/20'
                        : isSelected
                        ? 'bg-emerald-400'
                        : actKey === 'STOP'
                        ? 'bg-slate-600'
                        : 'bg-blue-500/60'
                    }`}
                    style={{ width: `${widthPct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Candidate Action Comparison Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {actionKeys.map(actKey => {
          const meta = actionMeta[actKey];
          const act = actions?.[actKey];
          const isSelected = selectedAction === actKey;
          const isBlocked = act?.guardrail_result === 'BLOCKED';
          const ruleIds = act?.guardrail_rule_ids || [];

          return (
            <div
              key={actKey}
              className={`rounded-lg border p-4 flex flex-col justify-between transition-all ${
                isSelected
                  ? 'bg-[#182434] border-blue-500/50 shadow-md ring-1 ring-blue-500/30'
                  : isBlocked
                  ? 'bg-[#121820] border-[#263545] opacity-80'
                  : 'bg-[#16202C] border-[#263545]'
              }`}
            >
              <div className="space-y-3">
                {/* Header */}
                <div className="flex items-center justify-between gap-2">
                  <span className={`text-base font-bold tracking-tight ${isSelected ? 'text-blue-400' : 'text-[#F3F5F7]'}`}>
                    {actKey}
                  </span>
                  {isSelected ? (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40 font-mono">
                      SELECTED
                    </span>
                  ) : isBlocked ? (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 font-mono">
                      BLOCKED
                    </span>
                  ) : (
                    <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-[#121820] text-[#8C9BAE] font-mono">
                      ELIGIBLE
                    </span>
                  )}
                </div>

                <div>
                  <div className="text-xs font-semibold text-[#D0D7DE] mb-0.5">{meta.label}</div>
                  <p className="text-[11px] text-[#8C9BAE] leading-relaxed min-h-[32px]">
                    {meta.desc}
                  </p>
                </div>

                {/* Metrics Table */}
                <div className="space-y-1.5 pt-3 border-t border-[#232D38] text-xs font-mono">
                  <div className="flex justify-between items-center">
                    <span className="text-[#8C9BAE] font-sans">Utility:</span>
                    <span className={`font-semibold ${isSelected ? 'text-emerald-400 font-bold' : isBlocked ? 'text-rose-400' : 'text-[#F3F5F7]'}`}>
                      {isError ? '—' : isBlocked ? 'Blocked' : act ? formatBRL(act.utility) : '—'}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-[#8C9BAE] font-sans">Probability:</span>
                    <span className={isBlocked ? 'text-rose-400' : 'text-[#F3F5F7]'}>
                      {isError ? '—' : isBlocked ? '0.0%' : act ? formatPercent(act.probability) : '—'}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-[#8C9BAE] font-sans">Guardrails:</span>
                    <span className={`font-semibold ${isBlocked ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {isBlocked ? 'Blocked' : 'Cleared'}
                    </span>
                  </div>

                  <div className="flex justify-between items-center text-[11px] text-[#667380]">
                    <span className="font-sans">Cost:</span>
                    <span>{meta.cost}</span>
                  </div>
                </div>
              </div>

              {isBlocked && ruleIds.length > 0 && (
                <div className="mt-3 pt-2 border-t border-rose-500/20 text-[10px] font-mono text-rose-400">
                  Trigger: {ruleIds.join(', ')}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
};
