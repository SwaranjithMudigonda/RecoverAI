import React, { useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Loader2,
  AlertCircle,
  RefreshCw,
  Sparkles,
  Copy,
  Check,
  Zap,
  TrendingUp
} from 'lucide-react';
import { formatBRL, formatPercent } from '../lib/utils';
import type { RecommendationResponse, RequestStatus } from '../types/recovery';

interface DecisionHeroProps {
  status: RequestStatus;
  recommendation: RecommendationResponse | null;
  error: string | null;
  paymentValue: number;
  onRetry?: () => void;
}

export const DecisionHero: React.FC<DecisionHeroProps> = ({
  status,
  recommendation,
  error,
  paymentValue,
  onRetry,
}) => {
  const [copied, setCopied] = useState(false);
  const isRequesting = status === 'REQUESTING';
  const isError = status === 'ERROR';

  const decision = recommendation?.decision;
  const actions = recommendation?.actions;
  const selectedAction = decision?.selected_action;

  // Calculate guardrail passed count
  const allActionKeys = ['RETRY', 'NUDGE', 'ESCALATE', 'STOP'] as const;
  const totalActions = allActionKeys.length;
  const passedActionsCount = actions
    ? allActionKeys.filter(k => actions[k]?.guardrail_result === 'PASSED').length
    : totalActions;
  const retryBlocked = actions?.RETRY?.guardrail_result === 'BLOCKED';

  // Copy cURL command handler
  const handleCopyCurl = () => {
    const curlCommand = `curl -X POST http://127.0.0.1:8000/api/v1/recommend \\
  -H "Content-Type: application/json" \\
  -d '{"payment_type":"credit_card","payment_value":${paymentValue.toFixed(2)},"payment_installments":1,"previous_order_count":1,"previous_payment_count":1,"previous_success_count":1,"previous_cancelled_count":0,"historical_payment_success_rate":1.0,"historical_average_payment":${paymentValue.toFixed(2)},"customer_tenure_before_payment":30,"order_frequency_before_payment":0.03,"failure_category":"SOFT_DECLINE","failure_reason":"transient_issuer_system_timeout","hours_since_failure":1.0,"recovery_attempt_number":1}'`;

    navigator.clipboard.writeText(curlCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Action badge color styling
  const getActionColor = (action?: string) => {
    if (!action) return 'text-[#8C9BAE] border-[#263545] bg-[#141E2A]';
    if (action === 'STOP') return 'text-[#D0D7DE] border-[#384452] bg-[#1F2732]';
    if (action === 'RETRY') return 'text-blue-400 border-blue-500/30 bg-blue-500/10';
    if (action === 'NUDGE') return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    if (action === 'ESCALATE') return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
    return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
  };

  const netYieldPercent = decision && paymentValue > 0
    ? ((decision.expected_utility / paymentValue) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="relative bg-[#121820] border border-[#232D38] rounded-xl p-6 sm:p-8 shadow-2xl overflow-hidden transition-all">
      {/* Background Subtle Accent glow */}
      <div className="absolute -top-24 -right-24 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Meta Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-6 border-b border-[#232D38]">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#8C9BAE] flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-blue-400" />
            PRIMARY DECISION HERO
          </span>
          <span className="text-[#232D38]">•</span>
          <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 text-[10px] font-mono font-semibold">
            SIMULATED
          </span>
        </div>

        {/* Action Buttons & Guardrail Summary Strip */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Copy cURL Button */}
          <button
            type="button"
            onClick={handleCopyCurl}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#16202C] hover:bg-[#1E2B3B] text-xs text-[#8C9BAE] hover:text-[#F3F5F7] border border-[#263545] font-mono transition-colors"
            title="Copy API cURL command to clipboard"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-300 font-semibold text-[11px]">Copied cURL!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span className="text-[11px]">cURL Payload</span>
              </>
            )}
          </button>

          {actions && (
            <div
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium border font-mono ${
                retryBlocked
                  ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                  : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
              }`}
            >
              {retryBlocked ? (
                <>
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                  <span>Guardrail Constraint Active ({actions.RETRY.guardrail_rule_ids[0] || 'Rule'})</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>{passedActionsCount}/6 Guardrails Cleared</span>
                </>
              )}
            </div>
          )}

          {/* ECE Calibration Badge */}
          <div className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded bg-[#16202C] border border-[#263545] text-xs text-[#8C9BAE] font-mono">
            <span>ECE</span>
            <span className="text-[#F3F5F7] font-semibold">0.0264</span>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {isRequesting ? (
        /* Polished Loading State inside Decision Hero */
        <div className="py-12 flex flex-col items-center justify-center text-center space-y-4">
          <div className="relative">
            <Loader2 className="w-10 h-10 text-blue-400 animate-spin" />
            <Sparkles className="w-4 h-4 text-blue-300 absolute top-0 right-0 animate-ping" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-[#F3F5F7] font-mono tracking-wide">
              ANALYZING PAYMENT CONTEXT
            </h3>
            <p className="text-xs text-[#8C9BAE] mt-1">
              Evaluating LightGBM probability, Isotonic calibration & Guardrails...
            </p>
          </div>
          {/* Pipeline Sequence */}
          <div className="flex items-center gap-2 text-xs font-mono text-[#667380] bg-[#16202C] px-4 py-2 rounded-md border border-[#263545]">
            <span className="text-blue-400">Context</span>
            <span>→</span>
            <span className="text-blue-400">ML S-Learner</span>
            <span>→</span>
            <span className="text-blue-400">Calibration</span>
            <span>→</span>
            <span className="text-blue-400">Guardrails</span>
            <span>→</span>
            <span className="text-[#F3F5F7] font-bold">Action</span>
          </div>
        </div>
      ) : isError ? (
        /* Polished Error State inside Decision Hero */
        <div className="py-8 space-y-4">
          <div className="flex items-start gap-3 p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-400" />
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-rose-200">Unable to complete orchestration</h4>
              <p className="text-xs text-rose-300/90 leading-relaxed">
                {error || 'RecoverAI REST API is offline or unreachable on http://127.0.0.1:8000.'}
              </p>
            </div>
          </div>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Recommendation</span>
            </button>
          )}
        </div>
      ) : (
        /* Primary Decision Hero Display */
        <div className="space-y-6">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            {/* Recommended Action Box */}
            <div>
              <div className="text-xs uppercase font-mono tracking-widest text-[#8C9BAE] font-medium mb-1">
                RECOMMENDED ACTION
              </div>
              <div className={`text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight uppercase ${getActionColor(selectedAction)}`}>
                {selectedAction || 'IDLE'}
              </div>
              <div className="text-xs text-[#8C9BAE] font-mono mt-1 flex items-center gap-2">
                <span>Cost-Optimal Strategy</span>
                <span>•</span>
                <span className="text-blue-400 font-semibold">Max Net Expected Utility</span>
              </div>
            </div>

            {/* Metrics Group */}
            <div className="flex flex-wrap items-center gap-4 sm:gap-6 bg-[#16202C] border border-[#263545] p-4 sm:p-5 rounded-lg shadow-inner">
              <div>
                <div className="text-xs font-medium text-[#8C9BAE] mb-1">Expected Recovery</div>
                <div className="text-2xl sm:text-3xl font-bold font-mono text-emerald-400">
                  {decision ? formatBRL(decision.expected_utility) : 'R$ 0.00'}
                </div>
                <div className="text-[11px] text-[#8C9BAE] mt-0.5">
                  Gross Value: {formatBRL(paymentValue)}
                </div>
              </div>

              <div className="w-px h-12 bg-[#232D38] hidden sm:block" />

              <div>
                <div className="text-xs font-medium text-[#8C9BAE] mb-1">Calibrated Confidence</div>
                <div className="text-2xl sm:text-3xl font-bold font-mono text-[#F3F5F7]">
                  {decision ? formatPercent(decision.recovery_probability) : '0.0%'}
                </div>
                <div className="text-[11px] text-[#8C9BAE] mt-0.5">
                  Recovery Probability
                </div>
              </div>

              <div className="w-px h-12 bg-[#232D38] hidden sm:block" />

              <div>
                <div className="text-xs font-medium text-[#8C9BAE] mb-1 flex items-center gap-1">
                  <TrendingUp className="w-3.5 h-3.5 text-blue-400" />
                  <span>Net Yield</span>
                </div>
                <div className="text-2xl sm:text-3xl font-bold font-mono text-blue-400">
                  {decision ? `${netYieldPercent}%` : '0.0%'}
                </div>
                <div className="text-[11px] text-[#8C9BAE] mt-0.5">
                  Value Efficiency
                </div>
              </div>
            </div>
          </div>

          {/* Selection Reason Statement */}
          <div className="bg-[#16202C] border-l-2 border-l-blue-500 rounded-r-md p-4 text-xs sm:text-sm text-[#F3F5F7] leading-relaxed shadow-sm">
            <span className="font-semibold text-blue-400 mr-2">Orchestration Decision:</span>
            {decision?.selection_reason || 'Awaiting evaluation of payment scenario context...'}
          </div>
        </div>
      )}
    </div>
  );
};
