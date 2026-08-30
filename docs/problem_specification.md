# Problem Specification: RecoverAI

## System Overview & Purpose

RecoverAI is an AI-driven revenue recovery orchestrator developed for the Razorpay AI Builder Internship 2026 (Track 03: AI Revenue Recovery).

**Core System Purpose:**
> "RecoverAI detects revenue at risk from failed payments, diagnoses the likely failure context, estimates recoverability, chooses a bounded recovery intervention, and records the outcome."

---

## Core Workflow: Failed Payment Recovery

The system orchestrates recovery for failed payments through the following sequential pipeline:

```
Failed Payment
  │
  ▼
Revenue-at-Risk Detection
  │
  ▼
Failure Diagnosis
  │
  ▼
Recovery Probability Estimation
  │
  ▼
Recovery Decision
  │
  ▼
Guardrail Check
  │
  ▼
Action Execution
  │
  ▼
Payment Outcome
  │
  ▼
Revenue Recovered
  │
  ▼
Audit Record
```

---

## Key Diagnostic & Operational Questions

The system is designed to answer five fundamental questions for every failed transaction:

1. **How much revenue is at risk?**
2. **Why did the payment fail?**
3. **How likely is the payment to be recovered?**
4. **What recovery action should be taken?**
5. **Should the system stop or escalate instead?**

---

## Recovery Decisions

RecoverAI strictly evaluates every failed payment and chooses **exactly one** of four recovery decisions:

- **RETRY**: Trigger an automated payment retry (e.g., smart retry timing, alternative routing).
- **NUDGE**: Trigger a customer communication/nudge (e.g., email/SMS notification to update card or retry manually).
- **ESCALATE**: Route the failure to a human operator or support queue for manual intervention.
- **STOP**: Halt all further automated recovery attempts for this transaction.

---

## Initial Input Categories

To evaluate a failed payment, the system ingests data across the following categories:

- **Payment information**: Transaction IDs, gateway metadata, currency.
- **Transaction amount**: Numerical monetary value of the failed transaction.
- **Payment method**: Credit card, debit card, UPI, net banking, mandate/auto-debit.
- **Failure reason**: Raw error code, decline reason (e.g., insufficient funds, network failure, authentication error, expired card).
- **Previous payment attempts**: Count, timestamps, and outcomes of prior attempts for this transaction.
- **Customer payment history**: Past transaction reliability, account age, lifetime value.
- **Subscription status**: Active subscription details, billing cycle tier, past default history.
- **Timing information**: Time of day, day of week, days elapsed since billing due date.

---

## Expected Decision Output Schema

For each processed transaction, RecoverAI outputs a structured decision payload containing:

- `payment_id`: Unique identifier of the target payment.
- `revenue_at_risk`: Monetary value evaluated at risk.
- `recovery_probability`: Estimated probability score of successful recovery (0.00 to 1.00).
- `expected_recovered_amount`: Calculated expected value (`revenue_at_risk * recovery_probability`).
- `selected_action`: One of `RETRY`, `NUDGE`, `ESCALATE`, or `STOP`.
- `decision_reason`: Detailed textual/structural explanation of why the action was selected.
- `guardrail_result`: Pass/Fail status along with triggered guardrail rule identifiers.
- `execution_status`: Status of the attempted intervention (`PENDING`, `EXECUTED`, `BLOCKED`, `SKIPPED`).
- `recovered_amount`: Final actual monetary amount recovered.

---

## Initial Success Definition

> **A payment is considered successfully recovered when a subsequent authorized recovery attempt results in a successful payment and the recovered amount is recorded.**

---

## System Constraints & Operating Guarantees

RecoverAI operates under strict structural boundaries:

- **No Indefinite Retries**: RecoverAI must not retry payments indefinitely. Max retry caps and retry delay schedules are enforced.
- **Explicit Stopping Rules**: Clear criteria (e.g., max attempts reached, hard decline codes like stolen card) mandate an immediate `STOP`.
- **Human Escalation Support**: Edge cases, high-value defaults, or ambiguous failure modes mandate an `ESCALATE` decision.
- **Configurable Guardrails**: All automated actions are subject to safety checks (e.g., rate limits, customer communication throttle rules, threshold limits).
- **Comprehensive Audit Trail**: Every decision, guardrail check, and action execution generates an immutable audit record.
- **Financial Evaluation Metric**: The final evaluation must measure actual or reconstructed monetary recovery across a batch rather than only reporting classification accuracy.

---

## Out of Scope for Step 2

The following items are explicitly **out of scope** for this phase:

- Checkout abandonment
- B2B receivables
- Voice recovery
- Live production payments
- Unrestricted autonomous payment actions
