import React, { useState } from 'react';
import { Loader2, ChevronDown, ChevronUp, Zap, Sliders } from 'lucide-react';
import { REASON_CATEGORIES } from '../data/presets';
import type { PaymentContext, PaymentMethod, FailureCategory, RequestStatus } from '../types/recovery';

interface PaymentInputFormProps {
  context: PaymentContext;
  activePreset: string;
  status: RequestStatus;
  onSelectPreset: (key: string) => void;
  onUpdateField: <K extends keyof PaymentContext>(field: K, value: PaymentContext[K]) => void;
  onSubmit: () => void;
}

interface NumberFieldProps {
  label: string;
  value: number;
  onChange: (val: number) => void;
  isFloat?: boolean;
  min?: number;
  max?: number;
  disabled?: boolean;
}

const NumberField: React.FC<NumberFieldProps> = ({
  label,
  value,
  onChange,
  isFloat = false,
  min = 0,
  max,
  disabled,
}) => {
  const [localVal, setLocalVal] = useState<string>(String(value));
  const isFocused = React.useRef(false);

  React.useEffect(() => {
    if (!isFocused.current) {
      setLocalVal(String(value));
    }
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const text = e.target.value;
    // Allow empty string so user can completely delete the number without 0 sticking around
    setLocalVal(text);

    if (text.trim() === '') {
      return;
    }

    const parsed = isFloat ? parseFloat(text) : parseInt(text, 10);
    if (!isNaN(parsed)) {
      if (max !== undefined && parsed > max) {
        onChange(max);
      } else {
        onChange(parsed);
      }
    }
  };

  const handleBlur = () => {
    isFocused.current = false;
    if (localVal.trim() === '' || isNaN(Number(localVal))) {
      setLocalVal(String(min));
      onChange(min);
    } else {
      const parsed = isFloat ? parseFloat(localVal) : parseInt(localVal, 10);
      let clamped = parsed;
      if (min !== undefined && clamped < min) clamped = min;
      if (max !== undefined && clamped > max) clamped = max;
      setLocalVal(String(clamped));
      onChange(clamped);
    }
  };

  return (
    <div>
      <label className="block text-[11px] text-[#8C9BAE] mb-1">{label}</label>
      <input
        type="text"
        inputMode={isFloat ? 'decimal' : 'numeric'}
        value={localVal}
        onFocus={() => {
          isFocused.current = true;
        }}
        onChange={handleChange}
        onBlur={handleBlur}
        disabled={disabled}
        className="w-full bg-[#16202C] border border-[#263545] rounded-md px-2.5 py-1.5 text-xs text-[#F3F5F7] font-mono focus:border-blue-500 focus:outline-none"
        required
      />
    </div>
  );
};

export const PaymentInputForm: React.FC<PaymentInputFormProps> = ({
  context,
  activePreset,
  status,
  onSelectPreset,
  onUpdateField,
  onSubmit,
}) => {
  const [isAdvancedExpanded, setIsAdvancedExpanded] = useState(false);
  const isSubmitting = status === 'REQUESTING';

  const handleCategoryChange = (cat: FailureCategory) => {
    onUpdateField('failure_category', cat);
    const availableReasons = REASON_CATEGORIES[cat] || [];
    if (availableReasons.length > 0 && !availableReasons.includes(context.failure_reason)) {
      onUpdateField('failure_reason', availableReasons[0]);
    }
  };

  const handlePaymentTypeChange = (pt: PaymentMethod) => {
    onUpdateField('payment_type', pt);
    if (context.failure_reason === 'boleto_expired' && pt !== 'boleto') {
      const available = REASON_CATEGORIES[context.failure_category] || [];
      const alternative = available.find(r => r !== 'boleto_expired') || available[0];
      if (alternative) onUpdateField('failure_reason', alternative);
    }
  };

  const currentReasons = (REASON_CATEGORIES[context.failure_category] || []).filter(r => {
    if (r === 'boleto_expired' && context.payment_type !== 'boleto') return false;
    return true;
  });

  return (
    <div className="bg-[#121820] border border-[#232D38] rounded-xl p-5 sm:p-6 space-y-4">
      {/* Header & Quick Scenarios Primary Interaction */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#232D38]">
        <div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-400 mb-0.5">
            <Zap className="w-3.5 h-3.5 shrink-0" />
            <span>Quick Scenarios</span>
          </div>
          <p className="text-xs text-[#8C9BAE]">
            Select a failed payment scenario to evaluate RecoverAI policy recommendations
          </p>
        </div>
      </div>

      {/* Quick Preset Buttons */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {[
          { key: 'soft', label: 'Soft Decline', badge: 'Retriable' },
          { key: 'boleto', label: 'Boleto Expired', badge: 'GR01 Block' },
          { key: 'hard', label: 'Hard Decline', badge: 'GR03 Block' },
          { key: 'auth', label: 'Auth Failed', badge: 'GR04 Block' },
        ].map(p => {
          const isActive = activePreset === p.key;
          return (
            <button
              key={p.key}
              type="button"
              disabled={isSubmitting}
              onClick={() => onSelectPreset(p.key)}
              className={`p-3 rounded-lg border text-left transition-all flex flex-col justify-between min-h-[64px] ${
                isActive
                  ? 'bg-blue-600/15 border-blue-500/50 text-blue-300 shadow-sm'
                  : 'bg-[#16202C] border-[#263545] text-[#8C9BAE] hover:text-[#F3F5F7] hover:bg-[#1C2837]'
              }`}
            >
              <span className="text-xs font-semibold text-[#F3F5F7]">{p.label}</span>
              <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded w-fit ${
                isActive
                  ? 'bg-blue-500/20 text-blue-300'
                  : 'bg-[#121820] text-[#667380]'
              }`}>
                {p.badge}
              </span>
            </button>
          );
        })}
      </div>

      {/* Advanced Parameters Accordion Button */}
      <div className="pt-2">
        <button
          type="button"
          onClick={() => setIsAdvancedExpanded(prev => !prev)}
          className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg bg-[#16202C] border border-[#263545] text-xs font-medium text-[#8C9BAE] hover:text-[#F3F5F7] hover:bg-[#1C2837] transition-colors"
        >
          <div className="flex items-center gap-2">
            <Sliders className="w-3.5 h-3.5 text-blue-400" />
            <span>Advanced Scenario Parameters (13 Context Fields)</span>
          </div>
          <div className="flex items-center gap-1 font-mono text-[11px]">
            <span>{isAdvancedExpanded ? 'Hide' : 'Expand'}</span>
            {isAdvancedExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </div>
        </button>
      </div>

      {/* Collapsible 13-Field Parameter Form */}
      {isAdvancedExpanded && (
        <form
          onSubmit={e => {
            e.preventDefault();
            onSubmit();
          }}
          className="space-y-4 pt-2 border-t border-[#232D38]"
        >
          {/* Group A: Payment Parameters */}
          <div className="space-y-2">
            <div className="text-xs font-mono uppercase tracking-wider text-blue-400 font-semibold">
              Payment Parameters
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] text-[#8C9BAE] mb-1">Method</label>
                <select
                  value={context.payment_type}
                  onChange={e => handlePaymentTypeChange(e.target.value as PaymentMethod)}
                  disabled={isSubmitting}
                  className="w-full bg-[#16202C] border border-[#263545] rounded-md px-2.5 py-1.5 text-xs text-[#F3F5F7] focus:border-blue-500 focus:outline-none"
                >
                  <option value="credit_card">credit_card</option>
                  <option value="debit_card">debit_card</option>
                  <option value="boleto">boleto</option>
                  <option value="voucher">voucher</option>
                </select>
              </div>

              <NumberField
                label="Value (R$)"
                value={context.payment_value}
                onChange={v => onUpdateField('payment_value', v)}
                isFloat
                min={0.01}
                disabled={isSubmitting}
              />

              <NumberField
                label="Installments"
                value={context.payment_installments}
                onChange={v => onUpdateField('payment_installments', v)}
                min={1}
                max={24}
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* Group B: Customer History */}
          <div className="space-y-2">
            <div className="text-xs font-mono uppercase tracking-wider text-blue-400 font-semibold">
              Customer Profile
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <NumberField
                label="Orders"
                value={context.previous_order_count}
                onChange={v => onUpdateField('previous_order_count', v)}
                min={0}
                disabled={isSubmitting}
              />

              <NumberField
                label="Payments"
                value={context.previous_payment_count}
                onChange={v => onUpdateField('previous_payment_count', v)}
                min={0}
                disabled={isSubmitting}
              />

              <NumberField
                label="Successes"
                value={context.previous_success_count}
                onChange={v => onUpdateField('previous_success_count', v)}
                min={0}
                disabled={isSubmitting}
              />

              <NumberField
                label="Cancels"
                value={context.previous_cancelled_count}
                onChange={v => onUpdateField('previous_cancelled_count', v)}
                min={0}
                disabled={isSubmitting}
              />
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <NumberField
                label="Success Rate"
                value={context.historical_payment_success_rate}
                onChange={v => onUpdateField('historical_payment_success_rate', v)}
                isFloat
                min={0}
                max={1}
                disabled={isSubmitting}
              />

              <NumberField
                label="Avg Ticket (R$)"
                value={context.historical_average_payment}
                onChange={v => onUpdateField('historical_average_payment', v)}
                isFloat
                min={0}
                disabled={isSubmitting}
              />

              <NumberField
                label="Tenure (Days)"
                value={context.customer_tenure_before_payment}
                onChange={v => onUpdateField('customer_tenure_before_payment', v)}
                min={0}
                disabled={isSubmitting}
              />

              <NumberField
                label="Freq (Days)"
                value={context.order_frequency_before_payment}
                onChange={v => onUpdateField('order_frequency_before_payment', v)}
                isFloat
                min={0}
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* Group C: Decline Context */}
          <div className="space-y-2">
            <div className="text-xs font-mono uppercase tracking-wider text-blue-400 font-semibold">
              Decline Context
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] text-[#8C9BAE] mb-1">Category</label>
                <select
                  value={context.failure_category}
                  onChange={e => handleCategoryChange(e.target.value as FailureCategory)}
                  disabled={isSubmitting}
                  className="w-full bg-[#16202C] border border-[#263545] rounded-md px-2.5 py-1.5 text-xs text-[#F3F5F7] focus:border-blue-500 focus:outline-none"
                >
                  <option value="SOFT_DECLINE">SOFT_DECLINE</option>
                  <option value="FUNDS_ISSUE">FUNDS_ISSUE</option>
                  <option value="CUSTOMER_ACTION_REQUIRED">CUSTOMER_ACTION_REQUIRED</option>
                  <option value="HARD_DECLINE">HARD_DECLINE</option>
                  <option value="GENERIC_DECLINE">GENERIC_DECLINE</option>
                </select>
              </div>

              <NumberField
                label="Attempt #"
                value={context.recovery_attempt_number}
                onChange={v => onUpdateField('recovery_attempt_number', v)}
                min={1}
                max={10}
                disabled={isSubmitting}
              />

              <NumberField
                label="Hours Elapsed"
                value={context.hours_since_failure}
                onChange={v => onUpdateField('hours_since_failure', v)}
                isFloat
                min={0}
                disabled={isSubmitting}
              />
            </div>

            <div>
              <label className="block text-[11px] text-[#8C9BAE] mb-1">Gateway Reason</label>
              <select
                value={context.failure_reason}
                onChange={e => onUpdateField('failure_reason', e.target.value)}
                disabled={isSubmitting}
                className="w-full bg-[#16202C] border border-[#263545] rounded-md px-2.5 py-1.5 text-xs text-[#F3F5F7] font-mono focus:border-blue-500 focus:outline-none"
              >
                {currentReasons.map(r => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Form Submit Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2.5 px-4 rounded-md text-xs transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Running AI Orchestration...</span>
                </>
              ) : (
                <span>Run Recommendation with Custom Parameters →</span>
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
