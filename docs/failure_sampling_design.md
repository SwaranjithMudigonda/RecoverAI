# RecoverAI Failure Sampling and Recovery Probability Design

## Document Overview

This document specifies the deterministic failure sampling strategy, action-conditional recovery probability model, guardrail interaction logic, expected utility decision framework, and monetary recovery simulation architecture for **RecoverAI: Track 03 AI Revenue Recovery**.

This document reflects **REVISION 2** following external technical review.

This is a **design specification document ONLY**. No data files, scripts, models, or pipeline executions are generated in this step.

---

## 1. Objective & Provenance Boundaries

The objective of this design is to specify a deterministic, mathematically sound simulation layer that transforms eligible real-world Olist payment contexts into controlled payment recovery evaluation cases.

### Provenance Pipeline & Data Isolation Boundary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           EMPIRICAL REAL DATA                           │
├─────────────────────────────────────────────────────────────────────────┤
│  REAL OLIST DATA (payment_value, payment_type, timestamps)              │
│        │                                                                │
│        ▼                                                                │
│  Leakage-Free Customer History (calculated prior to T0)                │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   CONTROLLED SIMULATION LAYER ONLY                      │
├─────────────────────────────────────────────────────────────────────────┤
│  Simulated Failure Reason Assignment (taxonomy-driven & weighted)       │
│        │                                                                │
│        ▼                                                                │
│  Action-Conditional Model Probability: P_model(rec | context, action)  │
│        │                                                                │
│        ▼                                                                │
│  Guardrail Validation -> Effective Probability P_effective(action)      │
│        │                                                                │
│        ▼                                                                │
│  Expected Utility Maximization Engine -> Selected Decision Action       │
│        │                                                                │
│        ▼                                                                │
│  Simulated Recovery Outcome & Monetary Realization                      │
└─────────────────────────────────────────────────────────────────────────┘
```

> **Core Provenance Guarantee**: Simulated failure reasons, recovery probabilities, candidate actions, guardrail evaluations, and post-intervention recovery outcomes are **CONTROLLED SIMULATION CONSTRUCTS** created for policy evaluation. They are **NOT** historical Olist observations.

---

## 2. Failure Sampling Unit & Core Definitions

All sampling logic operates at the **payment-level recovery case** unit defined in Step 4E-2:

$$\text{case\_id} = \text{order\_id} + \text{"\_"} + \text{str}(\text{payment\_sequential})$$

### Core Operational Definitions
1. **Eligible Payment Case**: A real Olist payment record satisfying `payment_value > 0`, valid table joins, supported `payment_type`, and complete purchase timestamp data.
2. **Simulated Failed Payment Case**: An eligible payment case selected by the deterministic sampling strategy to undergo simulated payment failure and recovery orchestration.
3. **Recovery Attempt**: A single, bounded intervention attempt (`recovery_attempt_number`) initiated by RecoverAI following a payment failure.
4. **Recovery Outcome**: The resulting binary outcome (`recovered` $\in \{0, 1\}$) and monetary realization (`recovered_amount`) following action execution.

### Disambiguation: `payment_sequential` vs. `recovery_attempt_number`
- **`payment_sequential` (Real Olist Attribute)**: Multi-tender sequence index of payment records within an order at checkout (e.g., payment #1 via voucher, payment #2 via credit card).
- **`recovery_attempt_number` (Simulated Attribute)**: Independent simulation counter tracking automated recovery attempt sequences.
- **Strict Constraint**: `recovery_attempt_number` must **never** be derived from or confused with `payment_sequential`. They are completely independent variables.

---

## 3. Failure Sampling Strategy

To construct a realistic evaluation batch without corrupting empirical distributions, RecoverAI employs a stratified, deterministic failure sampling strategy.

### Sampling Parameters & Stratification

| Parameter | Value / Setting | Provenance Classification |
|---|---|---|
| **Failure-Case Sampling Rate** | `15.0%` of eligible Olist cases | `SIMULATION PARAMETER — NOT HISTORICAL OLIST FACT` |
| **Random Seed** | `SEED = 42` | `SIMULATION_CONFIGURATION` |
| **Sampling Method** | Stratified Random Sampling | `SIMULATION_CONFIGURATION` |
| **Stratification Axis** | `payment_type` | Ingested from `REAL_OLIST` |

### Clarification on the 15% Sampling Parameter
The 15.0% sampling rate is a **`SIMULATION PARAMETER`** explicitly chosen to yield a statistically robust evaluation batch (~15,000 cases) across all payment-method strata and minority failure classes.
- It does **NOT** represent the historical failure rate of Olist.
- It does **NOT** represent Razorpay's production failure rate.
- It does **NOT** represent unverified industry-wide failure benchmarks.

### Stratified Sampling Allocation Matrix

```
Total Eligible Olist Payments: ~103,000 cases
Target Simulated Failure Batch: ~15,000 cases (15% sample rate)
```

| Payment Type (`payment_type`) | Empirical Olist % | Target Failure Sample Allocation % | Min Required Sample Count |
|---|---|---|---|
| `credit_card` | 74.0% | 70.0% | ~10,500 cases |
| `boleto` | 19.0% | 20.0% | ~3,000 cases |
| `voucher` | 5.5% | 7.0% | ~1,000 cases |
| `debit_card` | 1.5% | 3.0% (over-sampled for balance) | ~500 cases |

---

## 4. Corrected Payment-Method-Conditional Failure Compatibility Matrix

Simulated failure reasons must strictly adhere to payment-method technical capabilities.

### Technical Corrections Applied:
- **Debit Cards**: In the revised matrix below, debit cards **CAN** receive `expired_card`, `stolen_card`, and `card_number_invalid` failure reasons because physical and virtual debit cards have expiration dates, can be stolen, or can suffer input errors.
- **Boleto & Voucher Protection**: Boleto and Voucher remain strictly protected from card-specific failure reasons (e.g., `stolen_card`, `expired_card`, `card_number_invalid`, `insufficient_funds`).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               REVISED PAYMENT-METHOD FAILURE COMPATIBILITY MATRIX                      │
├─────────────────┬──────────────┬──────────────┬───────────────────┬────────────────────┤
│ Failure Reason  │ Credit Card  │ Debit Card   │ Boleto (Bank Slip)│ Voucher (Gift Card)│
├─────────────────┼──────────────┼──────────────┼───────────────────┼────────────────────┤
│ network_error   │ COMPATIBLE   │ COMPATIBLE   │ INCOMPATIBLE      │ INCOMPATIBLE       │
│ bank_tech_error │ COMPATIBLE   │ COMPATIBLE   │ INCOMPATIBLE      │ INCOMPATIBLE       │
│ gateway_error   │ COMPATIBLE   │ COMPATIBLE   │ INCOMPATIBLE      │ INCOMPATIBLE       │
│ insuff_funds    │ COMPATIBLE   │ COMPATIBLE   │ INCOMPATIBLE      │ INCOMPATIBLE       │
│ auth_failed     │ COMPATIBLE   │ COMPATIBLE   │ INCOMPATIBLE      │ INCOMPATIBLE       │
│ expired_card    │ COMPATIBLE   │ COMPATIBLE*  │ PROHIBITED        │ PROHIBITED         │
│ stolen_card     │ COMPATIBLE   │ COMPATIBLE*  │ PROHIBITED        │ PROHIBITED         │
│ card_invalid    │ COMPATIBLE   │ COMPATIBLE*  │ PROHIBITED        │ PROHIBITED         │
│ boleto_expired  │ PROHIBITED   │ PROHIBITED   │ COMPATIBLE**      │ PROHIBITED         │
│ pay_timed_out   │ COMPATIBLE   │ COMPATIBLE   │ COMPATIBLE        │ COMPATIBLE         │
│ pay_cancelled   │ COMPATIBLE   │ COMPATIBLE   │ COMPATIBLE        │ COMPATIBLE         │
│ payment_failed  │ COMPATIBLE   │ COMPATIBLE   │ COMPATIBLE        │ COMPATIBLE         │
└─────────────────┴──────────────┴──────────────┴───────────────────┴────────────────────┘
```
*\* Corrected: Debit cards possess card credentials and can experience expiration, theft blocks, or invalid card numbers.*
*\*\* Terminology Note: `boleto_expired` is retained as the explicit simulation failure code for Boleto payment slips due to Brazilian Olist domain context. `payment_timed_out` remains available as a broader timeout category.*

---

## 5. Failure-Reason Sampling Weights & Taxonomy Scoping

Within each payment-method stratum, failure reasons are sampled using probability weights based on `docs/failure_taxonomy.md`:

### Sampling Weight Specifications

#### A. Credit & Debit Card Failure Weights
- **SOFT_DECLINE** (35% total): `network_error` (15%), `bank_technical_error` (10%), `gateway_error` (10%)
- **FUNDS_ISSUE** (25% total): `insufficient_funds` (20%), `withdrawal_limit_exceeded` (5%)
- **CUSTOMER_ACTION_REQUIRED** (25% total): `authentication_failed` (15%), `expired_card` (5%), `payment_cancelled` (5%)
- **HARD_DECLINE** (10% total): `stolen_card` (4%), `card_number_invalid` (4%), `compliance_violation` (2%)
- **GENERIC_DECLINE** (5% total): `do_not_honor` (3%), `payment_failed` (2%)

#### B. Boleto Failure Weights
- **CUSTOMER_ACTION_REQUIRED** (70% total): `boleto_expired` (50%), `payment_cancelled` (20%)
- **CUSTOMER_TIMEOUT** (20% total): `payment_timed_out` (20%)
- **GENERIC_DECLINE** (10% total): `payment_failed` (10%)

#### C. Voucher Failure Weights
- **CUSTOMER_ACTION_REQUIRED** (50% total): `payment_cancelled` (30%), `payment_timed_out` (20%)
- **GENERIC_DECLINE** (50% total): `payment_failed` (50%)

---

## 6. Action-Conditional Probability Model with Time-Decay

RecoverAI models unconstrained candidate recovery likelihood using a logit scoring model:

$$P_{\text{model}}(\text{recovered} = 1 \mid \text{context}, \text{failure\_reason}, \text{action})$$

> **Classification**: `CONTROLLED SIMULATION / POLICY EVALUATION MODEL`.

### Mathematical Formulation
The logit score combines base action-failure compatibility, leakage-free historical features, attempt decay, and **time-decay**:

$$\text{logit}(P) = \beta_0 + \beta_{\text{action, failure}} + \beta_{\text{hist}} \cdot \text{success\_rate} + \beta_{\text{tenure}} \cdot \log(\text{tenure} + 1) - \beta_{\text{attempt}} \cdot (\text{attempt} - 1) - \beta_{\text{time}} \cdot \text{hours\_since\_failure}$$

$$P_{\text{model}}(\text{recovered} \mid \text{context}, \text{action}) = \sigma(\text{logit}(P)) = \frac{1}{1 + e^{-\text{logit}(P)}}$$

### Complete Failure Reason Mapping:
- **SOFT_DECLINE (`network_error`, `bank_technical_error`, `gateway_error`)**: `RETRY` action receives high base logit ($\beta_{\text{RETRY, SOFT}} = +2.2$), yielding high model probability.
- **CUSTOMER_ACTION_REQUIRED (`authentication_failed`, `expired_card`, `boleto_expired`)**: `NUDGE` action receives high base logit ($\beta_{\text{NUDGE, AUTH}} = +2.0$), while `RETRY` receives low base logit ($\beta_{\text{RETRY, AUTH}} = -2.5$).
- **Time Decay Effect ($\beta_{\text{time}} = 0.02$)**: As `hours_since_failure` increases, recovery likelihood decays smoothly. `TIME DECAY IS A SIMULATION ASSUMPTION` and is not learned from Olist.

### End-to-End Nudge Probability Clarification
$P_{\text{model}}(\text{recovered} \mid \text{NUDGE})$ represents the **end-to-end probability** that:
$$\text{Customer receives nudge} \land \text{Customer engages/opens prompt} \land \text{Customer completes payment successfully}$$
It is NOT merely a message-open rate.

---

## 7. Effective Recovery Probability & Guardrail Overrides

To enforce strict safety, RecoverAI distinguishes between raw `model_probability` and `effective_recovery_probability`:

$$\text{effective\_recovery\_probability}(\text{action}) = \begin{cases} 0.00 & \text{if } \text{guardrail}(\text{action}) == \text{BLOCKED} \\ P_{\text{model}}(\text{recovered} \mid \text{context}, \text{action}) & \text{if } \text{guardrail}(\text{action}) == \text{PASSED} \end{cases}$$

### Strict Guardrail Override Rule:
> **A high `model_probability` can NEVER override a hard guardrail.**

#### Concrete Example:
- Context: `failure_reason = stolen_card`
- `model_probability(RETRY) = 0.85` (Hypothetical unconstrained score)
- Guardrail: Hard decline guardrail triggers $\rightarrow$ `guardrail(RETRY) = BLOCKED`
- **`effective_recovery_probability(RETRY) = 0.00`**
- Result: Automated `RETRY` is forced to 0.00 effective probability and cannot be selected.

### Mandatory Retry Safety Rules for Boleto & Voucher
- **Boleto**: Automated backend `RETRY` is permanently **`BLOCKED`** $\rightarrow$ $\text{effective\_recovery\_probability}(\text{RETRY}) = 0.00$.
- **Voucher**: Automated backend `RETRY` is permanently **`BLOCKED`** $\rightarrow$ $\text{effective\_recovery\_probability}(\text{RETRY}) = 0.00$.

---

## 8. Multi-Factor Expected Utility Objective Function

To prevent large `payment_value` transactions from blindly dominating decisions, RecoverAI evaluates actions using a multi-factor **Expected Utility Function**:

$$\text{ExpectedUtility}(\text{action}) = \left[ \text{payment\_value} \times \text{effective\_recovery\_probability}(\text{action}) \right] - \text{cost}_{\text{intervention}}(\text{action}) - \text{penalty}_{\text{risk}}(\text{action}) - \text{cost}_{\text{friction}}(\text{action})$$

### Component Definitions & Simulation Parameters

1. **Revenue at Risk ($\text{revenue\_at\_risk} = \text{payment\_value}$)**: Ingested directly from real Olist payment records (`REAL_OLIST`).
2. **Effective Recovery Probability ($\text{effective\_recovery\_probability}$)**: Post-guardrail probability ($0.00$ if blocked).
3. **Intervention Cost ($\text{cost}_{\text{intervention}}$)**: Operational/messaging API cost.
   - `RETRY`: $0.50$ BRL (low API execution cost)
   - `NUDGE`: $1.50$ BRL (SMS/WhatsApp communication cost)
   - `ESCALATE`: $15.00$ BRL (Human support agent operational cost)
   - `STOP`: $0.00$ BRL (Zero action cost)
4. **Risk Penalty ($\text{penalty}_{\text{risk}}$)**: Financial/regulatory downside penalty for inappropriate actions (e.g., retrying hard declines risks chargebacks/gateway fines).
5. **Customer Friction Cost ($\text{cost}_{\text{friction}}$)**: Quantification of customer annoyance/churn risk from excessive nudges or repeated retries.

> **Classification Note**: All cost, penalty, and friction values are **`SIMULATION PARAMETERS`**. They are not claimed to be actual Razorpay production fees.

---

## 9. Action Selection Pipeline Engine

RecoverAI selects **exactly one** action from $\{\text{RETRY}, \text{NUDGE}, \text{ESCALATE}, \text{STOP}\}$ for every recovery case via the following deterministic pipeline:

```
                  ┌─────────────────────────────────────┐
                  │ All Candidate Actions {RETRY, NUDGE,│
                  │           ESCALATE, STOP}           │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 1. Payment-Method Compatibility Filter│
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 2. Guardrail Engine Validation       │
                  │    (Blocks unsafe/prohibited actions)│
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 3. Compute Effective Probabilities  │
                  │    (P_effective = 0.00 for BLOCKED) │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 4. Calculate Expected Utility       │
                  │    Utility(a) = V*P_eff - Cost -    │
                  │                 Penalty - Friction  │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 5. Select Action with Max Utility   │
                  │    Selected = argmax Utility(a)     │
                  └──────────────────┬──────────────────┘
                                     │
                     Is highest Utility < 0 OR All Blocked?
                     ├── YES ──► Select STOP or ESCALATE by policy
                     └── NO
                         │
                         ▼
                  ┌─────────────────────────────────────┐
                  │ EXACTLY ONE SELECTED ACTION         │
                  └─────────────────────────────────────┘
```

### Operational Roles of ESCALATE and STOP:
- **`ESCALATE`**: Selected when contextual risk, high monetary exposure (`payment_value > 5,000 BRL`), model uncertainty (`conflicting_signals`), or high customer LTV combined with ambiguous decline make automated intervention inappropriate.
- **`STOP`**: Terminal recovery decision for the target payment instrument/transaction. Prevents further automated recovery retries on that instrument. *(Note: A `STOP` decision on a compromised card instrument does not prohibit sending an alternate-payment-method `NUDGE` if policy permits).*

---

## 10. Retry Lifecycle & Hard Stop Rules

- **Initial Attempt**: `recovery_attempt_number = 1`
- **Max Retries**: Hard cap of 3 automated retries for `SOFT_DECLINE` cases.
- **Immediate Hard Stop**: Hard decline reasons (`stolen_card`, `card_number_invalid`, `compliance_violation`) trigger an immediate `STOP` decision on `recovery_attempt_number = 1`.

---

## 11. Determinism and Reproducibility

1. **Global Seed**: `SEED = 42` enforced across all pseudo-random calculations.
2. **Deterministic Utility**: Action selection given identical input features produces 100% identical outputs.

---

## 12. Data Provenance Classification Table

All dataset fields carry explicit provenance tags:

| Field Name | Provenance Classification | Description |
|---|---|---|
| `order_id` | `REAL_OLIST` | Original Olist order identifier |
| `payment_value` | `REAL_OLIST` | Original transaction monetary value |
| `payment_type` | `REAL_OLIST` | Original payment channel |
| `customer_unique_id` | `REAL_OLIST` | Original customer identity key |
| `previous_order_count` | `DERIVED_FROM_REAL_OLIST` | Leakage-free customer order history before $T_0$ |
| `historical_payment_success_rate` | `DERIVED_FROM_REAL_OLIST` | Leakage-free customer success ratio before $T_0$ |
| `failure_reason` | `SIMULATED_RECOVERY` | Simulated decline reason from taxonomy |
| `recovery_attempt_number` | `SIMULATED_RECOVERY` | Simulated attempt sequence index |
| `model_probability` | `SIMULATED_RECOVERY` | Raw unconstrained model probability score |
| `effective_recovery_probability` | `SIMULATED_RECOVERY` | Post-guardrail probability ($0.00$ if blocked) |
| `candidate_action` | `SIMULATED_RECOVERY` | Evaluated recovery action decision |
| `expected_utility` | `SIMULATED_RECOVERY` | Computed utility score |
| `guardrail_result` | `SIMULATED_RECOVERY` | Pass/Fail status of guardrail policy checks |
| `recovered` | `SIMULATED_RECOVERY` | Simulated binary outcome ($0$ or $1$) |
| `recovered_amount` | `SIMULATED_RECOVERY` | Realized monetary recovery amount |
| `simulation_seed` | `SIMULATION_CONFIGURATION` | Random seed parameter (`42`) |

---

## 13. Validation Requirements for Step 4E-4

The dataset generation pipeline in Step 4E-4 must validate all 14 mandatory invariants:

1. **Probability Bounds**: $0.00 \le \text{effective\_recovery\_probability} \le 1.00$ across all records.
2. **Guardrail Zero-Effective Rule**: `effective_recovery_probability == 0.00` for all guardrail-blocked actions.
3. **Valid Compatibility**: Zero invalid payment-method/failure-reason combinations (e.g., no card codes on Boleto).
4. **Boleto RETRY Safety**: Zero automated `RETRY` actions executed on `boleto`.
5. **Voucher RETRY Safety**: Zero automated `RETRY` actions executed on `voucher`.
6. **Hard Decline Prohibitions**: Zero automated `RETRY` actions executed on hard decline codes (`stolen_card`, `card_number_invalid`).
7. **Non-Negative Amounts**: $0.00 \le \text{recovered\_amount} \le \text{payment\_value}$.
8. **Amount Cap**: $\text{recovered\_amount} \le \text{payment\_value}$ for all rows.
9. **Attempt Independence**: `recovery_attempt_number` is strictly independent of `payment_sequential`.
10. **Zero Temporal Leakage**: No customer history features computed using records where $T \ge T_0$.
11. **Raw Data Protection**: Raw Olist files are unchanged and uncommitted.
12. **Determinism**: Identical outputs produced for identical inputs using `SEED = 42`.
13. **Lineage Integrity**: 100% of generated cases map to valid raw Olist records via `case_id`.
14. **Formula Accuracy**: $\text{expected\_recovered\_amount} == \text{payment\_value} \times \text{effective\_recovery\_probability}$.

---

## 14. Simulation vs. Real-World Evidence Statement

```
┌────────────────────────────────────────────────────────────────────────┐
│                 SIMULATION VS. REAL-WORLD EVIDENCE                     │
├────────────────────────────────────────────────────────────────────────┤
│ REAL OLIST EVIDENCE:                                                   │
│ • Transaction monetary values (payment_value)                          │
│ • Payment method channels (payment_type)                               │
│ • Order purchase and approval timestamps                               │
│ • Customer identity links (customer_unique_id) and order history       │
│ • Order status and split payment sequences                             │
│                                                                        │
│ SIMULATION ASSUMPTIONS (NOT HISTORICAL FACTS):                         │
│ • 15% failure sampling rate & failure reason weights                   │
│ • Recovery probability models & time-decay coefficients                │
│ • Action intervention costs, risk penalties, and friction costs       │
│ • Retry caps, guardrail thresholds, and recovery outcomes              │
│                                                                        │
│ RecoverAI is evaluated as an AI decision & orchestration framework,     │
│ NOT as a model trained on historical production Razorpay recoveries.   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 15. Step Boundary & Document Status

```
STEP 4E-3 STATUS: DESIGN COMPLETE — REVISED AFTER EXTERNAL REVIEW
```

### EXPLICIT CONFIRMATION:
- **NO DATASET HAS BEEN GENERATED.**
- **NO AUGMENTATION CODE HAS BEEN EXECUTED.**
- **NO ML MODEL HAS BEEN TRAINED.**
- **NO RECOVERY AGENT HAS BEEN EXECUTED.**

**NEXT STEP:**
`STEP 4E-4 — Recovery Case Dataset Generation`
