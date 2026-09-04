import React from 'react';
import { formatBRL, formatPercent } from '../lib/utils';
import type { RecommendationResponse, PaymentContext } from '../types/recovery';

interface WhyDecisionProps {
  recommendation: RecommendationResponse | null;
  context: PaymentContext;
  isError: boolean;
}

export const WhyDecision: React.FC<WhyDecisionProps> = ({
  recommendation,
  context,
  isError,
}) => {
  if (isError || !recommendation) {
    return (
      <section className="bg-[#111820] border border-[#26313D] rounded-xl p-5">
        <h3 className="text-sm font-semibold text-[#F3F5F7] mb-1">
          Why this decision?
        </h3>
        <p className="text-xs text-[#9AA6B2]">
          Execute a scenario recommendation to generate real-time policy explainability.
        </p>
      </section>
    );
  }

  const decision = recommendation.decision;
  const actions = recommendation.actions;
  const selectedAction = decision.selected_action;

  const retryInfo = actions.RETRY;
  const retryBlocked = retryInfo && retryInfo.guardrail_result === 'BLOCKED';
  const retryRules = (retryInfo && retryInfo.guardrail_rule_ids) || [];

  let reasoningText = '';
  if (selectedAction === 'RETRY') {
    reasoningText = `All safety guardrails passed. Because ${context.failure_reason.replace(/_/g, ' ')} is a transient soft decline on a ${context.payment_type.replace(/_/g, ' ')} transaction, automated payment retry is safe and delivers the highest net expected utility (${formatBRL(decision.expected_utility)}) after accounting for the R$ 1.50 gateway retry fee.`;
  } else if (selectedAction === 'NUDGE') {
    if (retryBlocked) {
      reasoningText = `Automated RETRY is blocked by safety guardrail (${retryRules.join(', ')}). Among remaining valid actions, NUDGE has the highest expected utility (${formatBRL(decision.expected_utility)}) by prompting the customer to complete payment directly without incurring further gateway penalties.`;
    } else {
      reasoningText = `NUDGE delivers higher net expected utility (${formatBRL(decision.expected_utility)}) than RETRY after balancing the low channel execution cost (R$ 0.50) against the customer payment completion probability.`;
    }
  } else if (selectedAction === 'ESCALATE') {
    reasoningText = `For this transaction value (${formatBRL(context.payment_value)}), manual merchant support escalation delivers optimal net expected utility (${formatBRL(decision.expected_utility)}) to protect high-value customer conversion despite higher outreach costs.`;
  } else {
    reasoningText = `STOP was selected to prevent further fee expenditure. Recovery attempts have been exhausted or net expected utility across all candidate actions is non-positive.`;
  }

  return (
    <section className="bg-[#111820] border border-[#26313D] rounded-xl p-5 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 mb-3 border-b border-[#26313D]">
        <div>
          <h3 className="text-base font-semibold text-[#F3F5F7]">
            Why this decision?
          </h3>
          <span className="text-xs text-[#9AA6B2]">
            Algorithmic policy explainability and constraint resolution
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-[#9AA6B2]">Selected Action:</span>
          <span className="px-2.5 py-0.5 rounded bg-blue-600/15 text-blue-400 border border-blue-500/30 text-xs font-semibold">
            {selectedAction}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 bg-[#141B23] border border-[#26313D] rounded-lg p-3">
        <div>
          <span className="block text-[11px] text-[#667380] mb-0.5">Decision</span>
          <span className="text-sm font-semibold text-[#F3F5F7]">{selectedAction}</span>
        </div>
        <div>
          <span className="block text-[11px] text-[#667380] mb-0.5">Recovery Probability</span>
          <span className="text-sm font-semibold text-[#F3F5F7]">{formatPercent(decision.recovery_probability)}</span>
        </div>
        <div>
          <span className="block text-[11px] text-[#667380] mb-0.5">Expected Utility</span>
          <span className="text-sm font-semibold text-blue-400">{formatBRL(decision.expected_utility)}</span>
        </div>
        <div>
          <span className="block text-[11px] text-[#667380] mb-0.5">Guardrail Constraint</span>
          <span className={`text-sm font-semibold ${retryBlocked ? 'text-rose-400' : 'text-emerald-400'}`}>
            {retryBlocked ? `RETRY Blocked (${retryRules[0] || 'Rule'})` : 'All Rules Passed'}
          </span>
        </div>
      </div>

      <p className="text-xs sm:text-sm text-[#F3F5F7] leading-relaxed bg-[#141B23] border-l-2 border-l-blue-500 p-3 rounded-r">
        {reasoningText}
      </p>
    </section>
  );
};
