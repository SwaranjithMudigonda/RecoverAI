# RecoverAI Step 6B Implementation Report: Safety Guardrail Engine

## Executive Summary

This report documents the implementation and automated verification of **Step 6B: RecoverAI Safety Guardrail Engine** for **RecoverAI: Track 03 AI Revenue Recovery**.

The guardrail engine ([`RecoverAIGuardrailEngine`](../src/recoverai_agent.py)) provides deterministic, non-bypassable safety evaluation across all candidate recovery actions (`RETRY`, `NUDGE`, `ESCALATE`, `STOP`).

Generated / Updated Artifacts:
1. Agent & Guardrail Module: [`src/recoverai_agent.py`](../src/recoverai_agent.py)
2. Report Document: [`docs/step6b_guardrail_engine_report.md`](../docs/step6b_guardrail_engine_report.md)

---

## 1. Guardrail Engine Architecture

The guardrail layer executes **BEFORE** ML model scoring and expected utility optimization. If an action is blocked by a guardrail rule, it is assigned `guardrail_result = 'BLOCKED'`, its effective probability is forced to `0.00`, and it is excluded from ML model scoring.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 RECOVERAI SAFETY GUARDRAIL ENGINE ARCHITECTURE          │
├─────────────────────────────────────────────────────────────────────────┤
│ Input: Validated Payment Context                                       │
│                                                                         │
│ Candidate Actions: [RETRY, NUDGE, ESCALATE, STOP]                       │
│                                                                         │
│ Evaluated Rules:                                                        │
│  • GR01_BOLETO      : payment_type == 'boleto' & RETRY    -> BLOCKED   │
│  • GR02_VOUCHER     : payment_type == 'voucher' & RETRY   -> BLOCKED   │
│  • GR03_HARD_DECLINE: category == 'HARD_DECLINE' & RETRY  -> BLOCKED   │
│  • GR04_AUTH_REQ    : reason in auth_reasons & RETRY      -> BLOCKED   │
│  • GR05_MAX_RETRY   : attempt > 3 & RETRY                 -> BLOCKED   │
│  • GR06_HIGH_VALUE  : value > 5000.0 & ambiguous & RETRY -> BLOCKED   │
│                                                                         │
│ Output per action: { action, guardrail_result, guardrail_rule_ids }     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Mandatory Guardrail Rules Definition

| Rule ID | Triggering Condition | Affected Action | Result | Business & Network Rationale |
|---|---|---|---|---|
| **`GR01_BOLETO`** | `payment_type == 'boleto'` | `RETRY` | **BLOCKED** | Boleto Bancário is an offline voucher; automated API retries are impossible. |
| **`GR02_VOUCHER`** | `payment_type == 'voucher'` | `RETRY` | **BLOCKED** | Meal/food voucher cards do not support automated recurring API retries. |
| **`GR03_HARD_DECLINE`** | `failure_category == 'HARD_DECLINE'` | `RETRY` | **BLOCKED** | Hard declines (stolen card, invalid card) are terminal network rejections. |
| **`GR04_AUTH_REQ`** | `reason \in \{auth\_failed, expired, boleto\_expired\}` | `RETRY` | **BLOCKED** | Requires customer authentication (3DS) or card details update before retry. |
| **`GR05_MAX_RETRY_CAP`** | `recovery_attempt_number > 3` | `RETRY` | **BLOCKED** | Prevents card association excessive retry penalties (Visa/Mastercard rules). |
| **`GR06_HIGH_VALUE`** | `payment_value > 5000.0` & ambiguous decline | `RETRY` | **BLOCKED** | High-value ambiguous declines require human escalation to avoid chargeback risk. |
| **`STOP`** | Always Terminal | `STOP` | **PASSED** | Terminal stop is always valid. Recovery $P = 0.0$, Expected Utility $= 0.0$. |

---

## 3. Evaluated Context Examples

### Example 1: Boleto Payment
- **Input:** `payment_type = 'boleto'`, `failure_category = 'CUSTOMER_ACTION_REQUIRED'`, `failure_reason = 'boleto_expired'`
- **Guardrail Results:**
  - `RETRY`: **BLOCKED** (`GR01_BOLETO|GR04_AUTH_REQ`)
  - `NUDGE`: **PASSED** (`NONE`)
  - `ESCALATE`: **PASSED** (`NONE`)
  - `STOP`: **PASSED** (`NONE`)

### Example 2: Hard Decline (Invalid Card)
- **Input:** `payment_type = 'credit_card'`, `failure_category = 'HARD_DECLINE'`, `failure_reason = 'card_number_invalid'`
- **Guardrail Results:**
  - `RETRY`: **BLOCKED** (`GR03_HARD_DECLINE`)
  - `NUDGE`: **PASSED** (`NONE`)
  - `ESCALATE`: **PASSED** (`NONE`)
  - `STOP`: **PASSED** (`NONE`)

### Example 3: Soft Decline (Network Error)
- **Input:** `payment_type = 'credit_card'`, `failure_category = 'SOFT_DECLINE'`, `failure_reason = 'network_error'`
- **Guardrail Results:**
  - `RETRY`: **PASSED** (`NONE`)
  - `NUDGE`: **PASSED** (`NONE`)
  - `ESCALATE`: **PASSED** (`NONE`)
  - `STOP`: **PASSED** (`NONE`)

### Example 4: Authentication Failed
- **Input:** `payment_type = 'credit_card'`, `failure_category = 'CUSTOMER_ACTION_REQUIRED'`, `failure_reason = 'authentication_failed'`
- **Guardrail Results:**
  - `RETRY`: **BLOCKED** (`GR04_AUTH_REQ`)
  - `NUDGE`: **PASSED** (`NONE`)
  - `ESCALATE`: **PASSED** (`NONE`)
  - `STOP`: **PASSED** (`NONE`)

---

## 4. Automated Self-Test Results

The automated self-test suite in [`src/recoverai_agent.py`](../src/recoverai_agent.py) executed 10 mandatory verification checks:

```
============================================================
=== EXECUTING STEP 6B AUTOMATED GUARDRAIL SELF-TESTS ===
============================================================
  Test 1 (Boleto + RETRY blocked): PASSED
  Test 2 (Voucher + RETRY blocked): PASSED
  Test 3 (Hard decline + RETRY blocked): PASSED
  Test 4 (Authentication failure + RETRY blocked): PASSED
  Test 5 (Soft decline + RETRY allowed): PASSED
  Test 6 (NUDGE allowed): PASSED
  Test 7 (ESCALATE allowed): PASSED
  Test 8 (STOP allowed): PASSED
  Test 9 (No unexpected guardrail rules): PASSED
  Test 10 (Deterministic repeated evaluation): PASSED
============================================================
```

- **Total Self-Tests:** `10`
- **Passed Tests:** `10` (100% Pass Rate)
- **Failed Tests:** `0`
- **Guardrail Safety Violations:** **`0`**

---

## 5. Artifact Protection & Integrity

- **Steps 4E–5F Files:** **100% UNTOUCHED AND UNMODIFIED.**
- **Model & Calibrator:** **NO retraining, tuning, or weight modification.**
- **Utility Optimization & Action Selection:** Deferred to Step 6C.

---

## 6. Step Boundary Verdict

```
STEP 6B PASSED
```

```
STEP 6B — RECOVERAI GUARDRAIL ENGINE: COMPLETE
```
