import React from 'react';
import { formatBRL, formatPercent } from '../lib/utils';
import type { RecommendationResponse, RequestStatus } from '../types/recovery';

interface LiveDecisionCenterProps {
  status: RequestStatus;
  recommendation: RecommendationResponse | null;
  error: string | null;
  paymentValue: number;
}

export const LiveDecisionCenter: React.FC<LiveDecisionCenterProps> = ({
  status,
  recommendation,
  error,
  paymentValue,
}) => {
  const isRequesting = status === 'REQUESTING';
  const isError = status === 'ERROR';

  const decision = recommendation?.decision;
  const actions = recommendation?.actions;
  const selectedAction = decision?.selected_action;

  return (
    <div className="bg-[#111820] border border-[#26313D] rounded-xl p-5 sm:p-6 flex flex-col justify-between h-full">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between gap-3 pb-4 mb-4 border-b border-[#26313D]">
          <div>
            <h2 className="text-base font-semibold text-[#F3F5F7]">
              AI Recovery Recommendation
            </h2>
            <span className="text-xs text-[#9AA6B2]">
              Live API policy decision output
            </span>
          </div>

          <div
            className={`text-xs font-medium px-2.5 py-0.5 rounded border ${
              isRequesting
                ? 'bg-blue-500/10 text-blue-400 border-blue-500/20 animate-pulse'
                : isError
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                : status === 'SUCCESS'
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-[#18212B] text-[#9AA6B2] border-[#26313D]'
            }`}
          >
            {status}
          </div>
        </div>

        {/* Selected Action Decision HUD */}
        <div className="bg-[#141B23] border border-[#26313D] rounded-lg p-5 mb-5">
          {/* Subtle Pipeline Breadcrumb */}
          <div className="flex items-center gap-1.5 text-[11px] text-[#667380] mb-3 pb-2.5 border-b border-[#26313D] overflow-x-auto">
            <span>Context</span>
            <span>→</span>
            <span>ML S-Learner</span>
            <span>→</span>
            <span>Calibration</span>
            <span>→</span>
            <span>Guardrails</span>
            <span>→</span>
            <span className="text-[#F3F5F7] font-medium">Optimal Action</span>
          </div>

          {/* Action Header */}
          <div className="flex items-center justify-between gap-3 mb-3">
            <span className="text-xs font-medium text-[#9AA6B2]">
              Selected Action
            </span>

            {isError ? (
              <span className="px-3 py-1 rounded bg-rose-500/15 border border-rose-500/30 text-rose-400 font-semibold text-sm">
                API UNAVAILABLE
              </span>
            ) : selectedAction ? (
              <span className="px-3.5 py-1 rounded bg-blue-600/15 border border-blue-500/40 text-blue-400 font-bold text-base tracking-wide">
                {selectedAction}
              </span>
            ) : (
              <span className="text-xs text-[#667380]">
                Connecting...
              </span>
            )}
          </div>

          {/* Selection Reason */}
          <p className="text-xs text-[#F3F5F7] bg-[#111820] border-l-2 border-l-blue-500 p-3 rounded-r mb-4 leading-relaxed">
            {isError
              ? error || 'RecoverAI API is offline. Start the uvicorn server to run inference.'
              : decision?.selection_reason || 'Awaiting live inference...'}
          </p>

          {/* Metrics Strip */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-[#111820] border border-[#26313D] rounded p-2.5 text-center">
              <span className="block text-[11px] text-[#9AA6B2] mb-0.5">Recovery Probability</span>
              <span className="text-base font-bold text-[#F3F5F7]">
                {decision ? formatPercent(decision.recovery_probability) : '0.0%'}
              </span>
            </div>

            <div className="bg-[#111820] border border-[#26313D] rounded p-2.5 text-center">
              <span className="block text-[11px] text-[#9AA6B2] mb-0.5">Expected Utility</span>
              <span className="text-base font-bold text-blue-400">
                {decision ? formatBRL(decision.expected_utility) : 'R$ 0.00'}
              </span>
            </div>

            <div className="bg-[#111820] border border-[#26313D] rounded p-2.5 text-center">
              <span className="block text-[11px] text-[#9AA6B2] mb-0.5">Fallback State</span>
              <span className="text-xs font-semibold text-[#F3F5F7] leading-6">
                {isError ? 'OFFLINE' : recommendation?.fallback_triggered ? 'ACTIVE' : 'FALSE'}
              </span>
            </div>
          </div>
        </div>

        {/* Dual Visual Distribution Bars */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mb-5">
          {/* Calibrated Probability Bar Chart */}
          <div className="bg-[#141B23] border border-[#26313D] rounded-lg p-3.5 space-y-2">
            <div className="text-xs font-medium text-[#9AA6B2]">
              Calibrated Probability
            </div>
            <div className="space-y-2">
              {(['RETRY', 'NUDGE', 'ESCALATE', 'STOP'] as const).map(actKey => {
                const act = actions?.[actKey];
                const isBlocked = act?.guardrail_result === 'BLOCKED';
                const prob = act?.probability ?? 0;
                const probWidth = isBlocked ? 0 : Math.round(prob * 100);

                return (
                  <div key={actKey} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-[#9AA6B2]">{actKey}</span>
                      <span className={isBlocked ? 'text-rose-400 font-mono text-[11px]' : 'text-[#F3F5F7]'}>
                        {isBlocked ? 'Blocked (0.0%)' : `${(prob * 100).toFixed(1)}%`}
                      </span>
                    </div>
                    <div className="h-1.5 w-full bg-[#111820] rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${isBlocked ? 'bg-rose-500' : 'bg-blue-500'}`}
                        style={{ width: `${probWidth}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Expected Utility Bar Chart */}
          <div className="bg-[#141B23] border border-[#26313D] rounded-lg p-3.5 space-y-2">
            <div className="text-xs font-medium text-[#9AA6B2]">
              Expected Utility (BRL)
            </div>
            <div className="space-y-2">
              {(['RETRY', 'NUDGE', 'ESCALATE', 'STOP'] as const).map(actKey => {
                const act = actions?.[actKey];
                const isBlocked = act?.guardrail_result === 'BLOCKED';
                const util = act?.utility ?? 0;
                const utilWidth = isBlocked ? 0 : util > 0 ? Math.min(100, Math.round((util / (paymentValue || 250)) * 100)) : 0;

                return (
                  <div key={actKey} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-[#9AA6B2]">{actKey}</span>
                      <span className={isBlocked ? 'text-rose-400 font-mono text-[11px]' : 'text-[#F3F5F7]'}>
                        {isBlocked ? 'Blocked' : formatBRL(util)}
                      </span>
                    </div>
                    <div className="h-1.5 w-full bg-[#111820] rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${isBlocked ? 'bg-rose-500' : 'bg-emerald-500'}`}
                        style={{ width: `${utilWidth}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Guardrail Check Matrix Row */}
        <div className="pt-3 border-t border-[#26313D]">
          <div className="text-xs font-medium text-[#9AA6B2] mb-2">
            Action Guardrail Clearance
          </div>
          <div className="grid grid-cols-4 gap-2 text-center">
            {(['RETRY', 'NUDGE', 'ESCALATE', 'STOP'] as const).map(actKey => {
              const act = actions?.[actKey];
              const isBlocked = act?.guardrail_result === 'BLOCKED';

              return (
                <div key={actKey} className="bg-[#141B23] border border-[#26313D] rounded p-2">
                  <div className="text-xs font-medium text-[#F3F5F7] mb-1">{actKey}</div>
                  <span
                    className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                      isBlocked ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'
                    }`}
                  >
                    {isBlocked ? 'BLOCKED' : 'PASSED'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
