# RecoverAI Step 6C Implementation Report: Utility Calculation & Action Selection

## Executive Summary

This report documents the implementation and verification of **Step 6C: RecoverAI Utility Calculation & Action Selection** for **RecoverAI: Track 03 AI Revenue Recovery**.

The inference engine ([`RecoverAIAgent.recommend_action`](../src/recoverai_agent.py)) implements an end-to-end inference pipeline: context validation $\rightarrow$ guardrail filtering $\rightarrow$ LightGBM raw scoring $\rightarrow$ global Isotonic calibration $\rightarrow$ multi-factor expected utility calculation $\rightarrow$ argmax valid action selection.

Generated / Updated Artifacts:
1. Agent & Decision Engine Module: [`src/recoverai_agent.py`](../src/recoverai_agent.py)
2. Report Document: [`docs/step6c_utility_action_selection_report.md`](../docs/step6c_utility_action_selection_report.md)

---

## 1. Inference Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 RECOVERAI INFERENCE PIPELINE (STEP 6C)                  │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. VALIDATED CONTEXT                                                    │
│        │                                                                │
│        ▼                                                                │
│ 2. SAFETY GUARDRAIL ENGINE (Step 6B) -> Filter Valid Actions            │
│        │                                                                │
│        ▼                                                                │
│ 3. LIGHTGBM S-LEARNER RAW SCORING (Step 5E Model)                       │
│        │                                                                │
│        ▼                                                                │
│ 4. ISOTONIC PROBABILITY CALIBRATION (Step 5E Calibrator)                │
│        │                                                                │
│        ▼                                                                │
│ 5. MULTI-FACTOR EXPECTED UTILITY CALCULATION                            │
│    Utility(a) = [payment_value * P_calibrated(a)] - Costs(a)            │
│    (If BLOCKED: Effective P = 0.00, Utility = -999999.0)                │
│        │                                                                │
│        ▼                                                                │
│ 6. ARGMAX VALID ACTION SELECTION                                        │
│    selected_action = argmax_{a in ValidActions} Utility(a)             │
│        │                                                                │
│        ▼                                                                │
│ 7. STRUCTURED OUTPUT PAYLOAD + DETERMINISTIC SELECTION REASON           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Factor Expected Utility Formula

For each candidate action $a \in \{\text{RETRY}, \text{NUDGE}, \text{ESCALATE}\}$:

$$\text{ExpectedUtility}(a) = \left[ \text{payment\_value} \times P_{\text{calibrated}}(a) \right] - \text{InterventionCost}(a) - \text{RiskPenalty}(a) - \text{FrictionCost}(a)$$

### Operational Cost Parameters (Step 5F Alignment)
- **`RETRY`:** Cost = $0.50$ BRL. Friction = $3.00$ BRL if `category == 'CUSTOMER_ACTION_REQUIRED'`. Risk Penalty = $100.00$ BRL if `category == 'HARD_DECLINE'`.
- **`NUDGE`:** Cost = $1.50$ BRL. Friction = $1.00$ BRL (SMS / WhatsApp notification friction).
- **`ESCALATE`:** Cost = $15.00$ BRL (Manual agent / priority queue handling).
- **`STOP`:** Cost = $0.00$ BRL, $P = 0.00$, Expected Utility = $0.00$ BRL.

If `guardrail_result == 'BLOCKED'`, effective probability is forced to $0.00$ and utility is set to $-999999.0$ so the action can **NEVER** be selected.

---

## 3. Fallback & Action Selection Rules

1. **Argmax Selection:** `selected_action = argmax_{a \in \text{ValidActiveActions}} \text{Utility}(a)`.
2. **All Active Actions Blocked:** If all active actions are blocked by safety guardrails, `selected_action = STOP`, `fallback_triggered = True`, `selection_reason = "STOP selected: all active actions blocked"`.
3. **Negative Expected Utility Fallback:** If valid active actions exist but all yield negative expected utility:
   - If `payment_value > 500.0` and `ESCALATE` is valid $\rightarrow$ `selected_action = ESCALATE`.
   - Otherwise $\rightarrow$ `selected_action = STOP`, `fallback_triggered = True`.

---

## 4. Structured Output Payload Schema

```json
{
  "status": "VALID",
  "failure_category": "SOFT_DECLINE",
  "failure_reason": "network_error",
  "payment_type": "credit_card",
  "payment_value": 250.0,
  "guardrail_RETRY": "PASSED",
  "guardrail_NUDGE": "PASSED",
  "guardrail_ESCALATE": "PASSED",
  "guardrail_STOP": "PASSED",
  "guardrail_rules_RETRY": "NONE",
  "guardrail_rules_NUDGE": "NONE",
  "guardrail_rules_ESCALATE": "NONE",
  "guardrail_rules_STOP": "NONE",
  "model_probability_RETRY": 0.8123,
  "model_probability_NUDGE": 0.1245,
  "model_probability_ESCALATE": 0.0452,
  "calibrated_probability_RETRY": 0.8250,
  "calibrated_probability_NUDGE": 0.1310,
  "calibrated_probability_ESCALATE": 0.0480,
  "effective_probability_RETRY": 0.8250,
  "effective_probability_NUDGE": 0.1310,
  "effective_probability_ESCALATE": 0.0480,
  "utility_RETRY": 205.75,
  "utility_NUDGE": 30.25,
  "utility_ESCALATE": -3.00,
  "utility_STOP": 0.0,
  "selected_action": "RETRY",
  "selected_probability": 0.8250,
  "selected_expected_utility": 205.75,
  "fallback_triggered": false,
  "selection_reason": "RETRY selected: highest expected utility among valid actions"
}
```

---

## 5. Automated Safety Test Results

14 out of 14 automated safety and utility tests passed successfully in [`src/recoverai_agent.py`](../src/recoverai_agent.py):

```
============================================================
=== EXECUTING STEP 6C AUTOMATED SAFETY & UTILITY TESTS ===
============================================================
  Test 1 (Soft decline allows RETRY): PASSED
  Test 2 (Boleto blocks RETRY): PASSED
  Test 3 (Voucher blocks RETRY): PASSED
  Test 4 (Hard decline blocks RETRY): PASSED
  Test 5 (Authentication failure blocks RETRY): PASSED
  Test 6 (STOP probability is exactly 0.0): PASSED
  Test 7 (STOP utility is exactly 0.0): PASSED
  Test 8 (Blocked action cannot be selected): PASSED
  Test 9 (Selection equals argmax valid-action utility): PASSED
  Test 10 (Determinism - identical outputs): PASSED
  Test 11 (No forbidden leakage fields enter features): PASSED
  Test 12 (All active actions checked / fallback): PASSED
  Test 13 (MAX_RETRY_CAP attempt > 3 blocks RETRY): PASSED
  Test 14 (HIGH_VALUE value > 5000 blocks RETRY): PASSED
============================================================
```

---

## 6. Verification & Safety Audit Summary

- **Total Automated Tests:** `14`
- **Passed Tests:** `14` (100% Pass Rate)
- **Failed Tests:** `0`
- **Guardrail Safety Violations:** **`0`**
- **Blocked-Action Selection Violations:** **`0`**
- **STOP Violation Count:** **`0`**
- **Argmax Validation Result:** **PASSED**
- **Determinism Result:** **PASSED (100% deterministic)**
- **Leakage Validation Result:** **PASSED (Zero post-decision features in input matrix)**
- **Steps 4E–5F Integrity:** **100% UNTOUCHED AND UNMODIFIED**

---

## 7. Step Boundary Verdict

```
STEP 6C PASSED
```

```
STEP 6C — UTILITY CALCULATION & ACTION SELECTION: COMPLETE
```
