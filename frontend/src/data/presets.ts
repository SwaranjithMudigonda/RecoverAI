import type { PaymentContext, FailureCategory } from '../types/recovery';

export const REASON_CATEGORIES: Record<FailureCategory, string[]> = {
  "SOFT_DECLINE": ["network_error", "bank_technical_error", "gateway_error", "payment_timed_out"],
  "FUNDS_ISSUE": ["insufficient_funds", "withdrawal_limit_exceeded"],
  "CUSTOMER_ACTION_REQUIRED": ["authentication_failed", "expired_card", "boleto_expired", "card_not_enrolled"],
  "HARD_DECLINE": ["stolen_card", "card_number_invalid", "compliance_violation"],
  "GENERIC_DECLINE": ["payment_cancelled", "payment_failed", "do_not_honor"]
};

export const PRESETS: Record<string, PaymentContext> = {
  "soft": {
    payment_type: "credit_card",
    payment_value: 250.00,
    payment_installments: 1,
    failure_category: "SOFT_DECLINE",
    failure_reason: "network_error",
    recovery_attempt_number: 1,
    hours_since_failure: 1.0,
    previous_order_count: 2,
    previous_payment_count: 2,
    previous_success_count: 2,
    previous_cancelled_count: 0,
    historical_payment_success_rate: 1.0,
    historical_average_payment: 250.00,
    customer_tenure_before_payment: 30,
    order_frequency_before_payment: 15.0
  },
  "boleto": {
    payment_type: "boleto",
    payment_value: 120.00,
    payment_installments: 1,
    failure_category: "CUSTOMER_ACTION_REQUIRED",
    failure_reason: "boleto_expired",
    recovery_attempt_number: 1,
    hours_since_failure: 2.0,
    previous_order_count: 1,
    previous_payment_count: 1,
    previous_success_count: 1,
    previous_cancelled_count: 0,
    historical_payment_success_rate: 1.0,
    historical_average_payment: 120.00,
    customer_tenure_before_payment: 10,
    order_frequency_before_payment: 10.0
  },
  "hard": {
    payment_type: "credit_card",
    payment_value: 500.00,
    payment_installments: 2,
    failure_category: "HARD_DECLINE",
    failure_reason: "card_number_invalid",
    recovery_attempt_number: 1,
    hours_since_failure: 0.5,
    previous_order_count: 5,
    previous_payment_count: 5,
    previous_success_count: 4,
    previous_cancelled_count: 1,
    historical_payment_success_rate: 0.80,
    historical_average_payment: 450.00,
    customer_tenure_before_payment: 90,
    order_frequency_before_payment: 18.0
  },
  "auth": {
    payment_type: "credit_card",
    payment_value: 300.00,
    payment_installments: 1,
    failure_category: "CUSTOMER_ACTION_REQUIRED",
    failure_reason: "authentication_failed",
    recovery_attempt_number: 1,
    hours_since_failure: 1.5,
    previous_order_count: 3,
    previous_payment_count: 3,
    previous_success_count: 3,
    previous_cancelled_count: 0,
    historical_payment_success_rate: 1.0,
    historical_average_payment: 300.00,
    customer_tenure_before_payment: 45,
    order_frequency_before_payment: 15.0
  }
};
