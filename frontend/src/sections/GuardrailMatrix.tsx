import React from 'react';
import type { RecommendationResponse } from '../types/recovery';

interface GuardrailMatrixProps {
  recommendation: RecommendationResponse | null;
}

export const GuardrailMatrix: React.FC<GuardrailMatrixProps> = ({ recommendation }) => {
  const retryBlockedRules = recommendation?.actions?.RETRY?.guardrail_rule_ids || [];

  const rules = [
    {
      id: 'GR01_BOLETO',
      name: 'Boleto Method Invariant',
      condition: "payment_type == 'boleto'",
      action: 'RETRY',
      desc: 'Boleto vouchers cannot be re-debited automatically via payment gateway.',
    },
    {
      id: 'GR02_VOUCHER',
      name: 'Voucher Method Invariant',
      condition: "payment_type == 'voucher'",
      action: 'RETRY',
      desc: 'Single-use vouchers cannot be re-charged on network rails.',
    },
    {
      id: 'GR03_HARD_DECLINE',
      name: 'Hard Decline Invariant',
      condition: "failure_category == 'HARD_DECLINE'",
      action: 'RETRY',
      desc: 'Blocks retries on stolen cards, invalid numbers, or compliance violations.',
    },
    {
      id: 'GR04_AUTH_REQ',
      name: 'Authentication Required Invariant',
      condition: "failure_reason in ['authentication_failed', 'expired_card', 'boleto_expired']",
      action: 'RETRY',
      desc: 'Customer intervention strictly required before re-attempting payment.',
    },
    {
      id: 'GR05_MAX_RETRY_CAP',
      name: 'Max Retry Frequency Cap',
      condition: 'recovery_attempt_number > 3',
      action: 'RETRY',
      desc: 'Halts repeated retries to prevent cardholder fatigue and merchant risk penalties.',
    },
    {
      id: 'GR06_HIGH_VALUE',
      name: 'High-Value Decline Constraint',
      condition: "payment_value > 5,000 AND failure_reason in ['do_not_honor', 'payment_failed']",
      action: 'RETRY',
      desc: 'High-value transactions with generic declines require human agent review.',
    },
  ];

  return (
    <section id="guardrails" className="bg-[#111820] border border-[#26313D] rounded-xl p-5 sm:p-6">
      <div className="pb-4 mb-4 border-b border-[#26313D]">
        <h2 className="text-base font-semibold text-[#F3F5F7]">
          Safety Guardrail Control System
        </h2>
        <p className="text-xs text-[#9AA6B2] mt-1">
          Guardrails constrain the actions available to the decision policy. Central safety constraints are evaluated strictly before ML action selection. If blocked, actions are assigned negative utility (-999,999.00) to prevent execution.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-[#26313D] text-[#9AA6B2] text-[11px] font-medium">
              <th className="py-2.5 px-3">Guardrail ID</th>
              <th className="py-2.5 px-3">Constraint Name</th>
              <th className="py-2.5 px-3">Trigger Condition</th>
              <th className="py-2.5 px-3">Affected Action</th>
              <th className="py-2.5 px-3 text-right">Current Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#26313D]/60 text-xs">
            {rules.map(rule => {
              const isTriggered = retryBlockedRules.some(r => r.includes(rule.id.split('_')[0]));

              return (
                <tr
                  key={rule.id}
                  className={`hover:bg-[#141B23] transition-colors ${
                    isTriggered ? 'bg-rose-500/5' : ''
                  }`}
                >
                  <td className="py-3 px-3 font-mono font-medium text-[#F3F5F7]">
                    {rule.id}
                  </td>
                  <td className="py-3 px-3 text-[#F3F5F7] font-medium">
                    {rule.name}
                  </td>
                  <td className="py-3 px-3 font-mono text-[#9AA6B2] text-[11px]">
                    {rule.condition}
                  </td>
                  <td className="py-3 px-3 font-mono text-blue-400">
                    {rule.action}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${
                        isTriggered
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      }`}
                    >
                      {isTriggered ? 'BLOCKED' : 'PASSED'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
};
