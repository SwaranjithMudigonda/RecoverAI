# Razorpay Test Mode Schema Mapping & Validation Specification

> **Scope & Purpose**: This document establishes the formal schema mapping between **Razorpay Test Mode** payment failure responses and **RecoverAI's internal failure taxonomy**. It serves as an isolated architectural bridge demonstrating schema compatibility for payment failure diagnostics without altering RecoverAI's frozen machine learning pipeline, dataset, or evaluation benchmarks.

---

## 1. Rigorous Data Provenance Classification

To prevent ambiguity regarding dataset origin and evaluation validity, RecoverAI maintains four strictly separated tiers of data provenance:

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                          RECOVERAI DATA PROVENANCE MATRIX                         │
├──────────────────────────┬────────────────────────────────────────────────────────┤
│ Provenance Tier            │ Description & Boundary Scope                           │
├────────────────────────────┼────────────────────────────────────────────────────────┤
│ 1. REAL HISTORICAL DATA    │ • Real-world transaction metadata sourced from Olist   │
│                            │ • Real customer IDs, order values, installment counts  │
│                            │ • Real timestamps, order frequency, customer tenure    │
├────────────────────────────┼────────────────────────────────────────────────────────┤
│ 2. DERIVED DATA            │ • Mathematical aggregations derived from Olist history │
│                            │ • Historical success rates, average order values       │
│                            │ • Customer lifetime order and payment frequencies      │
├────────────────────────────┼────────────────────────────────────────────────────────┤
│ 3. SIMULATED DATA          │ • Post-decline failure categories & decline reasons   │
│                            │ • Counterfactual candidate recovery actions            │
│                            │ • Recovery outcomes, recovered amounts, net utility   │
│                            │ • Calibrated ML model training targets & Step 5F benchmarks│
├────────────────────────────┼────────────────────────────────────────────────────────┤
│ 4. RAZORPAY TEST MODE DATA │ • Sandbox API payment and error response structures   │
│                            │ • Captured from Razorpay Test Mode (`rzp_test_...`)    │
│                            │ • Used EXCLUSIVELY for static schema-validation evidence│
│                            │ • ZERO interaction with live production transactions   │
│                            │ • NEVER used for model training or Step 5F benchmarks  │
└────────────────────────────┴────────────────────────────────────────────────────────┘

### Tier Definitions & Distinctions

#### REAL HISTORICAL DATA
- Olist transaction context, order amounts, installment counts, customer identifiers, timestamps, and seller metadata.

#### RAZORPAY TEST MODE DATA
- Sandbox payment and error responses captured from Razorpay Test Mode (`rzp_test_...`). Used exclusively for schema validation evidence.

#### DERIVED DATA
- Customer lifetime features, historical success rates, and order frequencies aggregated from historical Olist records.

#### SIMULATED DATA
- Failure labels used by our existing simulation where applicable, recovery attempts, recovery probabilities, candidate actions, recovery outcomes, recovered amounts, and utility.
```

> [!IMPORTANT]
> **Strict Non-Production Disclaimer:**
> - Razorpay Test Mode data represents **simulated sandbox testing payloads**, NOT real financial movements and NOT production transaction data.
> - The RecoverAI dataset must **never** be described as a *"Razorpay production dataset"*.
> - RecoverAI's Step 5F policy evaluation measures performance in a controlled, simulated recovery environment, not real-world Razorpay gateway performance.

---

## 2. Decoupled Architecture Diagram

RecoverAI deliberately decouples the **ML Decision Pipeline** from the **Gateway Schema Validation Layer**:

```
[ Tier A: Primary ML & Policy Evaluation Path ] (FROZEN)
Olist Historical E-Commerce Context
        │
        ▼
RecoverAI Processed Feature Vectors (15 Features)
        │
        ▼
Simulation Environment (Synthetic Failure Labels & Actions)
        │
        ▼
LightGBM S-Learner + Isotonic Calibration (models/recoverai_step5f/)
        │
        ▼
Central Guardrails Engine (GR01–GR06) ──► Argmax Net Expected Utility
        │
        ▼
Step 5F Frozen Benchmark Evaluation (Test N = 2,283 Cases)


────────────────────────── STRICT DECOUPLING BOUNDARY ──────────────────────────


[ Tier B: Supporting Gateway Schema Validation Path ] (OFFLINE EVIDENCE)
Razorpay Test Mode Sandbox Environment (`rzp_test_...`)
        │
        ▼
Real Sandbox Error Scenarios (Mock Bank Declines, Bad OTP, Expired Cards, UPI)
        │
        ▼
Offline Sanitization Utility (`tools/collect_razorpay_samples.py`)
        │
        ▼
Sanitized Static Fixtures (`data/test_mode_examples/*.json`)
        │
        ▼
Offline Schema Contract Verification (`tests/test_razorpay_schema.py`)
        │
        ▼
Taxonomy Mapping Documentation (`docs/razorpay_schema_mapping.md`)
```

---

## 3. Razorpay Error Schema Specification

Razorpay returns payment failures across two primary formats: **Direct API Errors** and **Failed Payment Entities**.

### 3.1 Direct API Error Payload (`POST /v1/orders`, etc.)
When an API request is malformed, rejected by business rules, or fails authentication, Razorpay returns an HTTP 4xx/5xx with an `error` wrapper:

```json
{
  "error": {
    "code": "BAD_REQUEST_ERROR",
    "description": "Authentication failed due to incorrect OTP",
    "field": "otp",
    "source": "customer",
    "step": "payment_authentication",
    "reason": "invalid_otp",
    "metadata": {
      "payment_id": "pay_K3j9f2N8xL9876",
      "order_id": "order_DBJKIP31Y4jl8a"
    }
  }
}
```

### 3.2 Failed Payment Entity (`GET /v1/payments/{payment_id}` or `payment.failed` Webhook)
When a transaction is initiated through checkout and subsequently rejected by the bank or gateway, the payment resource transitions to `"status": "failed"` and contains flattened error fields:

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique payment identifier | `"pay_K3j9f2N8xL9876"` |
| `order_id` | string | Associated Razorpay order | `"order_DBJKIP31Y4jl8a"` |
| `amount` | integer | Transaction value in smallest currency unit (paise) | `25000` (R$ 250.00 / ₹250.00) |
| `currency` | string | ISO currency code | `"INR"` |
| `status` | string | Terminal payment state | `"failed"` |
| `method` | string | Payment rail | `"card"`, `"upi"`, `"netbanking"` |
| `error_code` | string | High-level failure category | `"BAD_REQUEST_ERROR"`, `"GATEWAY_ERROR"` |
| `error_description`| string | Human-readable explanation | `"The customer entered an incorrect OTP"` |
| `error_source` | string | Originating entity | `"customer"`, `"bank"`, `"gateway"`, `"business"` |
| `error_step` | string | Lifecycle stage of failure | `"payment_authentication"`, `"payment_authorization"` |
| `error_reason` | string | Machine-readable failure token | `"invalid_otp"`, `"insufficient_funds"` |
| `error_field` | string/null| Request parameter triggering error | `"otp"`, `"card[number]"`, `null` |

---

## 4. Formal Taxonomy Mapping Table

> [!NOTE]
> **Mapping Clarification:**
> - RecoverAI's `failure_category` (`SOFT_DECLINE`, `FUNDS_ISSUE`, `CUSTOMER_ACTION_REQUIRED`, `HARD_DECLINE`, `GENERIC_DECLINE`) is our own **decision-oriented clustering** designed to route payments to optimal recovery actions.
> - They are NOT official Razorpay categories. Rather, Razorpay's `{error_source, error_step, error_reason}` provide the external gateway diagnostics that map into RecoverAI's decision categories.

### 4.1 Structural Concept Mapping

| Razorpay Concept | RecoverAI Concept | Mapping Nature | Technical Role |
| :--- | :--- | :--- | :--- |
| `error_source` | `failure_category` (Derived) | Aggregated Mapping | Identifies if failure is customer-remediable, banking, or network |
| `error_step` | `failure_category` (Derived) | State Phase Mapping | Differentiates 3DS authentication vs bank balance authorization |
| `error_reason` | `failure_reason` | 1-to-1 / N-to-1 Mapping | Specific root-cause failure token evaluated by safety guardrails |
| `error_code` | Diagnostic Context | Informational Reference| Top-level HTTP/API classification |
| `error_description`| Diagnostic Context | Informational Reference| Explanatory narrative for merchant support logging |
| `amount` | `payment_value` | Normalized Value | Transaction value in currency units |

### 4.2 Granular Reason Translation Matrix (Documented Reference Contract)

| Razorpay `error_source` | Razorpay `error_step` | Razorpay `error_reason` | RecoverAI `failure_category` | RecoverAI `failure_reason` | Applicable Guardrails |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `bank` | `payment_authorization` | `payment_failed` (Network) | `SOFT_DECLINE` | `network_error` / `gateway_error` | None (Eligible for `RETRY`) |
| `gateway` | `payment_authorization` | `gateway_error` | `SOFT_DECLINE` | `gateway_error` | None (Eligible for `RETRY`) |
| `gateway` | `payment_authorization` | `timed_out` | `SOFT_DECLINE` | `payment_timed_out` | None (Eligible for `RETRY`) |
| `customer` | `payment_authorization` | `insufficient_funds` / `insufficient_fund` | `FUNDS_ISSUE` | `insufficient_funds` | None (Eligible for `RETRY`/`NUDGE`) |
| `customer` | `payment_authorization` | `withdrawal_limit_exceeded` | `FUNDS_ISSUE` | `withdrawal_limit_exceeded` | None (Eligible for `NUDGE`) |
| `customer` | `payment_authentication` | `invalid_otp` / `authentication_failed` | `CUSTOMER_ACTION_REQUIRED` | `authentication_failed` | `GR04_AUTH_REQ` (Blocks `RETRY`) |
| `customer` | `payment_authentication` | `expired_card` | `CUSTOMER_ACTION_REQUIRED` | `expired_card` | `GR04_AUTH_REQ` (Blocks `RETRY`) |
| `customer` | `payment_initiation` | `payment_cancelled` | `GENERIC_DECLINE` | `payment_cancelled` | Evaluated by Model |
| `bank` | `payment_authorization` | `do_not_honor` | `GENERIC_DECLINE` | `do_not_honor` | `GR06_HIGH_VALUE` (if Value > 5000) |
| `customer` | `payment_initiation` | `card_number_invalid` | `HARD_DECLINE` | `card_number_invalid` | `GR03_HARD_DECLINE` (Blocks `RETRY`) |
| `business` | `payment_authorization` | `compliance_violation` | `HARD_DECLINE` | `compliance_violation` | `GR03_HARD_DECLINE` (Blocks `RETRY`) |

---

### 4.3 Official Documented Test Cards vs. Empirical Test Mode Observations

To maintain uncompromising scientific and data provenance standards, RecoverAI rigorously separates **official documentation claims** from **actual observed empirical responses** in our live Razorpay Test Mode account.

#### Documented Expected Behavior
Razorpay's official *Test Cards for Indian Payments* documentation details dedicated card numbers mapped to specific failure reasons (e.g., `4100 2800 0008 0001` for `insufficient_fund`, `4100 2800 0000 0009` for `authentication_failed`). The documentation states that selecting `Failure` on the Mock Bank page will produce the corresponding error reason.

#### Empirical Observations in Live Test Mode Sandbox
We tested this via automated, headless Google Chrome Playwright checkouts using live `rzp_test_...` credentials:
1. **PoC 1 (`insufficient_fund`)**:
   - Official test card: `4100 2800 0008 0001`
   - Flow: Payment link → Contact filled → Cards selected → Card entry → RBI tokenization bypassed → 3DS Mock Bank popup → `Failure` clicked.
   - Result: Payment `pay_TXED7xqSUjfFzD` was created with `status: "failed"`.
   - **Observed error fields**: `error_source: "gateway"`, `error_step: "payment_authorization"`, `error_reason: "payment_failed"`.
   - **Verification Verdict**: Strict mismatch (`payment_failed` != `insufficient_fund`). **Fixture was strictly rejected and not saved.**

2. **PoC 2 (`authentication_failed`)**:
   - Official test card: `4100 2800 0000 0009`
   - Flow: Payment link → Contact filled → Cards selected → Card entry → RBI tokenization bypassed → 3DS Mock Bank popup → `Failure` clicked.
   - Result: Payment `pay_TXEJN5HJmBPGCa` was created with `status: "failed"`.
   - **Observed error fields**: `error_source: "gateway"`, `error_step: "payment_authorization"`, `error_reason: "payment_failed"`.
   - **Verification Verdict**: Strict mismatch (`payment_failed` != `authentication_failed`). **Fixture was strictly rejected and not saved.**

#### Key Empirical Takeaways:
- **Aggregated Error Reason**: In our live Razorpay Test Mode account, the 3DS Mock Bank failure flow emits an aggregated `error_reason: "payment_failed"` at `error_step: "payment_authorization"`, rather than the granular sub-reason string (`insufficient_fund` or `authentication_failed`) listed in the test card table.
- **Zero False Claims**: RecoverAI makes **zero claim** that our Test Mode account produces `insufficient_fund` or `authentication_failed`.
- **Retention of Documented Specs**: The official translation matrix is retained as the theoretical contract mapping, while empirical evidence clearly reflects what the live sandbox emits.
- **Strict Verification Invariant**: Any collector run enforces `actual_error_reason == expected_error_reason`. If the gateway emits `payment_failed`, granular scenario tags are never applied to fixtures.
- **Proven Automation Engine**: The Playwright + Chrome browser automation code is preserved in `tools/collect_razorpay_samples.py` because it successfully solved dynamic DOM barriers, contact submission, RBI tokenization modals, and multi-page 3DS popups.

---

## 5. Security & Sanitization Boundaries

All test mode examples captured from Razorpay must pass strict sanitization before being committed to static repository storage:

### 5.1 Strictly Prohibited Credentials (NEVER Stored)
- ❌ `key_secret` (Razorpay API Secret)
- ❌ Real credit/debit card numbers (PAN)
- ❌ CVV / CVC
- ❌ OTP / PIN values
- ❌ Real customer Personally Identifiable Information (PII)
- ❌ Webhook signature secrets, bearer tokens, or private keys

### 5.2 Mandatory Redactions for Test Fixtures
- Phone numbers (`contact`) → Masked to `"+9198765*****"`
- Customer email (`email`) → Generalized to `"test_customer@example.com"`
- Acquirer identifiers (`acquirer_data`) → Purged of internal gateway transaction references
- Merchant tokens (`customer_id`, `token_id`) → Replaced with synthetic placeholder strings

---

## 6. Offline Verification Invariant

The schema validation layer is verified through `tests/test_razorpay_schema.py`. This test suite is guaranteed to:
1. Run **100% offline** without requiring internet access or active gateway connectivity.
2. Require **zero API credentials** or environment variables to pass in continuous integration.
3. Keep core engine scripts (`src/recoverai_agent.py`, `src/api/server.py`, `src/batch/run_batch.py`, `dashboard/app.js`) completely free of gateway SDK imports, preserving all Step 7E release certifications.
