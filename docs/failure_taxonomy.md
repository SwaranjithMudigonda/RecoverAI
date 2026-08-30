# RecoverAI Failure Taxonomy and Recovery Action Design

## Document Overview

This document specifies the finalized failure taxonomy, payment-method compatibility matrix, contextual feature scoping, recovery action definitions, guardrail framework, and simulation assumptions for **RecoverAI: Track 03 AI Revenue Recovery**.

---

## 1. Strict Separation of Concepts

To prevent architectural ambiguity and model input corruption, RecoverAI strictly segregates system logic into four non-overlapping layers:

```
┌───────────────────────────┐     ┌───────────────────────────┐
│  A. Root Cause / Failure  │     │   B. Contextual Features  │
│          Reason           │     │    (Customer & Order)     │
└─────────────┬─────────────┘     └─────────────┬─────────────┘
              │                                 │
              └────────────────┬────────────────┘
                               │
                               ▼
                  ┌───────────────────────────┐
                  │ C. Risk / Guardrail State │
                  └────────────┬──────────────┘
                               │
                               ▼
                  ┌───────────────────────────┐
                  │    D. Recovery Action     │
                  │ (RETRY, NUDGE, ESCALATE,  │
                  │           STOP)           │
                  └───────────────────────────┘
```

1. **Root Cause / Failure Reason**: The underlying bank, network, or gateway decline trigger (e.g., `insufficient_funds`, `bank_technical_error`, `stolen_card`).
2. **Contextual Features**: Quantitative and categorical metadata observing customer history, transaction amount, timing, payment channel, and attempt sequence.
3. **Risk / Guardrail State**: Derived operational states, policy thresholds, and safety bounds (e.g., maximum retry caps, communication limits).
4. **Recovery Action**: The bounded intervention selected by the orchestrator (`RETRY`, `NUDGE`, `ESCALATE`, `STOP`).

### Explicit Constraints
- A bank/gateway failure reason must **NOT** be represented as a contextual feature.
- Derived contextual or risk states (such as `repeated_failure`, `high_value`, and `conflicting_signals`) must **NOT** be categorized as bank/gateway failure reasons.

---

## 2. Final Root-Cause Taxonomy

RecoverAI categorizes all payment failure reasons into five functional categories:

### A. `SOFT_DECLINE`
- **Failure Reasons**: `network_error`, `bank_technical_error`, `gateway_error`
- **Preferred Recovery Action**: `RETRY`
- **Description**: Transient technical, network, or infrastructure issues where the customer's account/credential remains valid. An automated retry is appropriate, subject to payment-method capabilities and guardrail checks.

### B. `FUNDS_ISSUE`
- **Failure Reasons**: `insufficient_funds`, `withdrawal_limit_exceeded`
- **Preferred Recovery Action**: Delayed `RETRY` or `NUDGE`
- **Description**: Temporary financial liquidity or daily spending limit constraints. **Immediate blind retries are prohibited**; recovery requires delayed scheduling (e.g., aligning with salary cycles) or customer nudges.

### C. `CUSTOMER_ACTION_REQUIRED`
- **Failure Reasons**: `authentication_failed`, `payment_cancelled`, `payment_timed_out`, `card_not_enrolled`, `expired_card`, `boleto_expired`
- **Preferred Recovery Action**: `NUDGE`
- **Description**: Requires active customer intervention, such as completing 3DS authentication, updating an expired card, or initiating a new payment link.

### D. `HARD_DECLINE`
- **Failure Reasons**: `card_number_invalid`, `bank_account_invalid`, `stolen_card`, `compliance_violation`
- **Preferred Recovery Action**: `STOP` (for the failing payment instrument)
- **Description**: Permanent failure modes or security blocks where retrying the specific instrument will never succeed and risks regulatory sanctions. A customer-facing `NUDGE` may be dispatched to request a completely different payment instrument.

### E. `GENERIC_DECLINE`
- **Failure Reasons**: `payment_failed`, `do_not_honor`
- **Preferred Recovery Action**: **Context-Dependent AI Decision**
- **Description**: Unspecified or ambiguous bank decline codes. The system evaluates contextual features (customer tenure, attempt history, transaction value) to dynamically choose among `RETRY`, `NUDGE`, `ESCALATE`, or `STOP`.

---

## 3. Razorpay Error Structure Alignment

To align with payment gateway standards, RecoverAI's simulated failure representation preserves the multi-dimensional error structure used by Razorpay:

```json
{
  "code": "BAD_REQUEST_ERROR",
  "source": "bank",
  "step": "payment_authentication",
  "reason": "authentication_failed",
  "metadata": {
    "payment_id": "pay_K3j9f2N8xL",
    "gateway": "razorpay"
  }
}
```

- **Code**: Top-level API error classification (e.g., `BAD_REQUEST_ERROR`, `GATEWAY_ERROR`).
- **Source**: Entity where the error originated (`bank`, `gateway`, `customer`, `network`).
- **Step**: Pipeline stage where failure occurred (`payment_initiation`, `payment_authentication`, `payment_authorization`).
- **Reason**: Specific granular failure code from RecoverAI's taxonomy.
- **Metadata**: Contextual key-value pairs (gateway IDs, error descriptions).

### Terminology & Scope Clarification
- **Razorpay Terminology**: Concepts such as `code`, `source`, `step`, and `reason` mirror Razorpay's structural API design.
- **Generic Payment Terminology**: Standard industry decline terms (e.g., `do_not_honor`, `insufficient_funds`).
- **Simulation Labels**: Abstracted labels created for policy evaluation. Not all taxonomy labels are exact Razorpay API enum values; internal gateway rules are not fabricated.

---

## 4. Contextual Features Scoping

The following features represent transaction context and operational risk states, and are strictly classified as **Model Input Features**, NOT failure reasons:

| Feature Name | Category | Role & Description |
|---|---|---|
| `payment_method` | Transaction Context | Payment rail (`credit_card`, `debit_card`, `boleto`, `voucher`) |
| `amount` / `amount_inr` | Transaction Context | Numerical monetary value of the transaction |
| `previous_successes` | Customer History | Count of past successful payments by customer |
| `previous_failures` | Customer History | Count of past failed payment attempts by customer |
| `historical_payment_success_rate` | Customer History | Ratio of successful payments over total attempts |
| `attempt_count` | Attempt Context | Sequence number of the current recovery attempt |
| `time_since_failure` | Timing Context | Hours elapsed since the initial payment decline |
| `customer_tenure` | Customer History | Age of customer relationship in days |
| `customer_value` / `LTV` | Customer History | Cumulative customer lifetime value |
| `hour_of_day`, `day_of_week` | Timing Context | Temporal features at time of transaction |
| `repeated_failure` | Derived Risk State | **Derived state**: True if multiple consecutive attempts have failed |
| `high_value` | Risk / Policy Feature | **Transaction-risk feature**: True if transaction exceeds high-value threshold |
| `conflicting_signals` | Model / Risk State | **Model state**: True if contextual features yield conflicting model predictions |

> **Explicit Rule**: `repeated_failure`, `high_value`, and `conflicting_signals` are operational and model risk states. They must **never** be used or logged as bank/gateway decline reasons.

---

## 5. Payment-Method Compatibility Matrix

Recovery logic and failure reasons must respect payment-method technical capabilities:

### A. Credit Card
- **Compatible Failure Reasons**: `network_error`, `bank_technical_error`, `gateway_error`, `insufficient_funds`, `authentication_failed`, `card_not_enrolled`, `expired_card`, `card_number_invalid`, `stolen_card`, `compliance_violation`, `payment_failed`, `do_not_honor`, `payment_cancelled`, `payment_timed_out`.

### B. Debit Card
- **Compatible Failure Reasons**: `network_error`, `bank_technical_error`, `gateway_error`, `insufficient_funds`, `authentication_failed`, `card_number_invalid`, `payment_failed`, `do_not_honor`.

### C. Boleto (Voucher / Bank Slip)
- **Compatible Failure Reasons**: `boleto_expired`, `payment_timed_out`, `payment_cancelled`, `payment_failed`.
- **Incompatible Failure Reasons (Prohibited)**: Card-specific error codes must **NEVER** be assigned to Boleto (`stolen_card`, `expired_card`, `card_number_invalid`, `insufficient_funds`, `card_not_enrolled`).

### D. Voucher (Gift/Prepaid Voucher)
- **Compatible Failure Reasons**: `payment_timed_out`, `payment_cancelled`, `payment_failed`.
- **Incompatible Failure Reasons (Prohibited)**: Card-specific decline reasons must **NEVER** be assigned to vouchers.

---

## 6. Recovery Action Definitions

RecoverAI defines exactly four bounded operational decisions:

1. **`RETRY`**: Trigger an automated, background payment re-authorization attempt for an eligible payment context using an authorized, stored payment credential.
2. **`NUDGE`**: Dispatch an interactive customer communication (email, SMS, or in-app push) directing the customer to complete 3DS authentication, update card details, or pay via an alternative method.
3. **`ESCALATE`**: Suspend automated recovery actions and route the case to a human operations or customer support queue for manual evaluation due to elevated risk, high transaction value, or model uncertainty.
4. **`STOP`**: Cease all further automated recovery attempts for the target payment instrument or transaction.

### Critical Distinction: Instrument STOP vs. Customer Communication
- **"STOP the failing payment instrument"**: Prohibits any further automated retry attempts against the specific declined card or account.
- **"STOP all communication with the customer"**: Prohibits outreach entirely.
- *Note*: A `STOP` decision on a compromised card instrument does **not** prohibit sending a customer-facing `NUDGE` requesting a new, valid payment method.

---

## 7. Action Decision Matrix

The baseline mapping from failure categories to preferred recovery decisions:

| Failure Category | Preferred Action | Operational Notes |
|---|---|---|
| **`SOFT_DECLINE`** | `RETRY` | Subject to retry attempt caps and rate limits |
| **`FUNDS_ISSUE`** | Delayed `RETRY` / `NUDGE` | Avoid immediate retries; schedule based on timing or prompt user |
| **`CUSTOMER_ACTION_REQUIRED`** | `NUDGE` | Requires active customer participation (e.g., 3DS, updating card) |
| **`HARD_DECLINE`** | `STOP` | Stop failing instrument; alternate-method `NUDGE` permitted |
| **`GENERIC_DECLINE`** | **AI DECISION** | Model evaluates context (tenure, amount, history) to choose action |

### Escalation Trigger Logic
`ESCALATE` is not restricted to a single failure code. It is dynamically triggered whenever contextual risk or uncertainty criteria are met (e.g., transaction amount > high-value threshold, high customer LTV combined with ambiguous decline, or `conflicting_signals` across model outputs).

---

## 8. Guardrails and Bounded Recovery

To prevent financial loss, customer spam, and gateway sanctions, RecoverAI enforces strict operational guardrails:

- **Maximum Retry Attempts**: Hard cap on automated retries (e.g., maximum 3 retries per transaction).
- **Retry Spacing / Delays**: Enforced exponential or schedule-aware backoff intervals between retries.
- **Maximum Customer Nudges**: Cap on customer communications (e.g., max 2 nudges per failed order).
- **High-Value Escalation Threshold**: Mandatory human escalation for transactions exceeding specified monetary limits.
- **Hard-Decline Stopping Rules**: Immediate `STOP` triggered upon receiving hard decline codes (e.g., `stolen_card`).
- **Repeated-Failure Rules**: Automated halt after consecutive failed attempts across billing cycles.
- **Rate Limits & Communication Throttling**: Frequency bounds to prevent customer fatigue.

> **Production Note**: Production payment network rules (e.g., Visa/Mastercard retry limits) require authoritative verification and configurable policy engine implementation rather than hardcoded assumptions.

---

## 9. Olist Dataset Scope & Limitations

The Kaggle Olist dataset serves as RecoverAI's empirical real-data backbone.

### Real Data Provided by Olist:
- Authentic payment method distributions (`credit_card`, `debit_card`, `boleto`, `voucher`)
- Transaction amounts (`payment_value`)
- High-resolution order timestamps (`order_purchase_timestamp`, `order_approved_at`)
- Customer identity links across repeat orders (`customer_unique_id`)
- Order statuses (`delivered`, `canceled`, `unavailable`)
- Multi-tender split payment records (`payment_sequential`)

### Data NOT Provided by Olist (Simulated Layer):
- Gateway decline error codes (e.g., `insufficient_funds`, `authentication_failed`)
- Bank decline reasons
- Recovery intervention logs (`RETRY`, `NUDGE`, `ESCALATE`, `STOP`)
- Post-intervention recovery outcomes and probabilities
- Card-on-file vault authorization flags

> **Explicit Limitation**: Failure reasons and recovery outcomes generated in subsequent steps are **SIMULATED / CONTROLLED** data layers anchored on Olist context. They must never be misattributed as historical Olist records.

---

## 10. Card-on-File Simulation Assumption

- **Fact**: The Olist dataset contains e-commerce checkout records and does **not** prove the existence of vaulted, card-on-file credentials.
- **Simulation Assumption**: For the purpose of RecoverAI's controlled simulation, eligible card-based payment recovery cases are assumed to possess an authorized stored credential permitting bounded, asynchronous background retries.
- **Boundary**: This assumption is strictly a simulation construct and must not be presented as a native attribute of the Olist dataset.

---

## 11. Concrete Operational Examples

### Example 1: Soft Technical Decline
- `failure_reason`: `bank_technical_error`
- `payment_method`: `credit_card`
- `attempt_count`: 1
- `customer_history`: Strong (high success rate, tenure > 180 days)
- $\rightarrow$ **Preferred Action**: **`RETRY`** (Automated background retry scheduled)

### Example 2: Authentication Failure
- `failure_reason`: `authentication_failed`
- `payment_method`: `credit_card`
- `attempt_count`: 1
- $\rightarrow$ **Preferred Action**: **`NUDGE`** (Customer prompted to complete 3DS authentication)

### Example 3: Expired Payment Slip
- `failure_reason`: `boleto_expired`
- `payment_method`: `boleto`
- $\rightarrow$ **Preferred Action**: **`NUDGE`** (Customer sent a new payment link/Boleto barcode)

### Example 4: Stolen Card Fraud Block
- `failure_reason`: `stolen_card`
- `payment_method`: `credit_card`
- $\rightarrow$ **Preferred Action**: **`STOP`** on the compromised credit card instrument. *(Optionally, a separate `NUDGE` may be sent asking the customer to provide a different payment method).*

### Example 5: High-Value Ambiguous Decline
- `failure_reason`: `do_not_honor`
- `payment_method`: `credit_card`
- `amount`: High (exceeds high-value threshold)
- `previous_failures`: Multiple
- $\rightarrow$ **Preferred Action**: **`ESCALATE`** (Routed to human operations review due to high value and elevated risk)

---

## 12. Important Terminology Distinctions

To ensure technical precision across docs and code, the following terms are explicitly distinguished:

1. **Failure Reasons vs. Contextual States**: `repeated_failure`, `high_value`, and `conflicting_signals` are **derived contextual/risk states**, NOT bank failure reasons.
2. **Split Payments vs. Retries**: `payment_sequential` in Olist represents **multi-tender split payments** at checkout (e.g., voucher + credit card), NOT automated retry attempts over time.
3. **Order Status vs. Gateway Failure**: `order_status = canceled` in Olist represents **general e-commerce order cancellation** (buyer cancellation, inventory issue), NOT a verified payment gateway failure.

---

## 13. Document Status

```
STEP 4E-1 STATUS: APPROVED
```

**Next Step:**
`STEP 4E-2 — Olist-to-Recovery-Case Augmentation Design`
