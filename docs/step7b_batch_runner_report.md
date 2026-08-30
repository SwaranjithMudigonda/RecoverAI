# RecoverAI Step 7B Implementation Report: Batch Recommendation Runner (Audited & Hardened)

## Executive Summary

This report documents the implementation, security controls, review hardening fixes, and automated verification of **Step 7B: RecoverAI Batch Recommendation Runner** for **RecoverAI: Track 03 AI Revenue Recovery**.

The batch recommendation runner ([`src/batch/run_batch.py`](../src/batch/run_batch.py)) operates as an external, zero-knowledge batch client that ingests payment failure dataset CSVs, extracts valid pre-decision context fields while stripping forbidden post-decision leakage and sensitive credentials, delegates recommendation calls to the frozen Step 6D decision engine ([`src/recoverai_agent.py`](../src/recoverai_agent.py)), and streams complete audited decision traces incrementally to a new CSV file.

Generated / Modified Files:
1. Batch Runner Script: [`src/batch/run_batch.py`](../src/batch/run_batch.py) (Hardened)
2. Automated Test Suite: [`tests/test_step7b_batch.py`](../tests/test_step7b_batch.py) (Hardened)
3. Report Document: [`docs/step7b_batch_runner_report.md`](../docs/step7b_batch_runner_report.md) (Updated)

---

## 1. Technical Review Hardening Fixes Implemented

Following an independent technical audit, three critical performance and error-handling fixes were implemented in [`src/batch/run_batch.py`](../src/batch/run_batch.py):

### FIX 1 — Incremental Streaming Output (`csv.DictWriter`)
- Replaced end-of-batch DataFrame memory accumulation with standard-library `csv.DictWriter`.
- Opens output CSV once, writes header once, and streams each decision record immediately to disk via `writer.writerow()`.
- Processed output records are written incrementally to disk, preventing accumulation of the output dataset in memory (verified via 500-row scalability test).

### FIX 2 — Pre-Initialized Context Variables (`UnboundLocalError` Prevention)
- Pre-initializes `clean_context = {}` and `metadata = {}` before entering the per-row `try...except` block.
- Prevents `UnboundLocalError` inside exception handlers if row reading or dictionary parsing fails.

### FIX 3 — Safe Error Reporting (Zero Credential & Stack Trace Exposure)
- Writes safe error code (`ROW_PROCESSING_ERROR` / `VALIDATION_ERROR`) and sanitized diagnostic (`Row processing error.`) to output CSV records.
- Detailed raw Python exception stack traces are written strictly to server `stderr` application logs.
- Guarantees sensitive credential values or internal system paths never appear in output CSV files.

---

## 2. CLI Usage & Interface Specification

```bash
python src/batch/run_batch.py --input <path_to_input.csv> --output <path_to_output.csv>
```

### CLI Arguments
- `--input`: Path to source input CSV file containing payment failure records.
- `--output`: Path to destination output CSV file where recommendation traces will be written.

---

## 3. Input/Output Schema Specification

### 3.1 Allowed Input Context Attributes
The runner extracts **ONLY** valid pre-decision context features:
`payment_type`, `payment_value`, `payment_installments`, `previous_order_count`, `previous_payment_count`, `previous_success_count`, `previous_cancelled_count`, `historical_payment_success_rate`, `historical_average_payment`, `customer_tenure_before_payment`, `order_frequency_before_payment`, `failure_category`, `failure_reason`, `hours_since_failure`, `recovery_attempt_number`.

### 3.2 Preserved Source Identifiers (Output Metadata Only)
Tracing identifiers (`case_id`, `order_id`, `customer_unique_id`, `customer_id`) are preserved in output CSV records strictly as metadata columns; they are **NEVER** forwarded into `RecoverAI.recommend()` or the ML feature matrix.

### 3.3 Output CSV Schema (Destination File)
Every record written to the `--output` CSV contains:
- `request_id`: Generated batch request identifier (`batch-req-000001`).
- `timestamp`: Execution timestamp.
- `case_id`, `order_id`, `customer_unique_id`: Source metadata identifiers.
- `status`: Recommendation status (`SUCCESS`, `INVALID_INPUT`, or `SYSTEM_ERROR`).
- `error_code`, `error_message`: Error code and sanitized error message.
- `payment_type`, `payment_value`, `failure_category`, `failure_reason`: Input context attributes.
- `selected_action`: Agent's chosen action (`RETRY`, `NUDGE`, `ESCALATE`, `STOP`).
- `selected_probability`, `selected_expected_utility`: Chosen action's calibrated probability and net expected utility.
- `selection_reason`: Human-readable selection rationale.
- `fallback_triggered`: Boolean indicator if negative utility or all-blocked fallback occurred.
- `guardrail_RETRY`, `guardrail_NUDGE`, `guardrail_ESCALATE`, `guardrail_STOP`: Safety guardrail evaluation results (`PASSED` or `BLOCKED`).
- `guardrail_rules_RETRY`, `guardrail_rules_NUDGE`, `guardrail_rules_ESCALATE`, `guardrail_rules_STOP`: Triggering guardrail rule IDs.
- `model_probability_*`, `calibrated_probability_*`, `effective_probability_*`: Per-action probabilities.
- `utility_RETRY`, `utility_NUDGE`, `utility_ESCALATE`, `utility_STOP`: Per-action net expected utilities.
- `model_artifact_hash`, `calibrator_artifact_hash`: SHA-256 model provenance checksums.

---

## 4. Security & Leakage Controls

1. **Post-Decision Feature Stripping:** The runner explicitly excludes post-decision features (`selected_action`, `candidate_action`, `model_probability_*`, `effective_probability_*`, `utility_*`, `guardrail_*`, `recovery_probability`, `expected_recovered_amount`, `recovered_amount`, `recovered`).
2. **Sensitive Credential Stripping:** The runner explicitly strips sensitive credential fields (`card_number`, `cvv`, `cvc`, `otp`, `pin`, `bank_account_number`, `password`, `auth_secret`, `payment_token`).
3. **Single-Threaded Execution:** The batch runner executes sequentially to ensure predictable execution, zero concurrency race conditions, and clean progress tracking.
4. **Input CSV Protection:** The input CSV file is read-only; output is written to a completely new file (`--output`).

---

## 5. Automated Test Results (15/15 Passed)

The automated test suite ([`tests/test_step7b_batch.py`](../tests/test_step7b_batch.py)) executed 15 comprehensive batch, review hardening, scalability, and integrity tests:

```
============================================================
=== EXECUTING STEP 7B BATCH RUNNER & HARDENING TESTS ===
============================================================
  Test 1 (Normal multi-row batch execution): PASSED
  Test 2 (Output row count equals input row count): PASSED
  Test 3 (FIX 1 - Incremental csv.DictWriter streaming output): PASSED
  Test 4 (Malformed context does not crash the batch): PASSED
  Test 5 (FIX 2 - clean_context initialization prevents UnboundLocalError): PASSED
  Test 6, 7 & 8 (FIX 3 - Sanitized error record with zero stack trace or paths): PASSED
  Test 9 (Sensitive input values never appear in output CSV): PASSED
  Test 10 (Input CSV remains byte-identical): PASSED
  Test 11 (Frozen Steps 4E-6D remain 100% unchanged): PASSED
  Test 12 (Step 5F artifacts/results remain 100% unchanged): PASSED
  Test 13 (Runner remains single-threaded/synchronous): PASSED
  Test 14 (Existing leakage & sensitive protections remain intact): PASSED
  Test 15 (Scalability smoke test - 500 rows streamed incrementally): PASSED
============================================================
```

---

## 6. Artifact Integrity Hashes (Steps 4E–6D & Step 5F Protection)

| Artifact File | Pre-Execution SHA256 Checksum | Post-Execution SHA256 Checksum | Integrity Result |
|---|---|---|---|
| `recoverai_ml_test_cases.csv` | `fe52ba8be239102fb6152c1bd86dafbf71bf69e185d216baacec01558907b43e` | `fe52ba8be239102fb6152c1bd86dafbf71bf69e185d216baacec01558907b43e` | **MATCHED (100%)** |
| `step5f_policy_summary.csv` | `37ed2ccebe7b2fb0a811ef78f0b7ee871922c2a0750c1f5dd5c4efbe9dd32616` | `37ed2ccebe7b2fb0a811ef78f0b7ee871922c2a0750c1f5dd5c4efbe9dd32616` | **MATCHED (100%)** |
| `test_evaluation_metrics.json` | `e05b55dd3f38e68cf9042b3fc28db40e7968dbbc0cb7d4cbeaa5c9ff809b4db7` | `e05b55dd3f38e68cf9042b3fc28db40e7968dbbc0cb7d4cbeaa5c9ff809b4db7` | **MATCHED (100%)** |
| `lgbm_model.pkl` | `ca968b7756caec185e70b562cda34445289cea4d0a4bce14cf7b0c5a0b1068e7` | `ca968b7756caec185e70b562cda34445289cea4d0a4bce14cf7b0c5a0b1068e7` | **MATCHED (100%)** |
| `isotonic_calibrator.pkl` | `8bda9ffdbb4b281a6569c5436f7ccf3cdb721da2971d1029540fa0809d596817` | `8bda9ffdbb4b281a6569c5436f7ccf3cdb721da2971d1029540fa0809d596817` | **MATCHED (100%)** |
| `feature_list.json` | `8462f5c4a83e53254ddebed80e458508fc719df19e900481b1c396e64e935f4d` | `8462f5c4a83e53254ddebed80e458508fc719df19e900481b1c396e64e935f4d` | **MATCHED (100%)** |
| `categorical_features.json` | `23debd9970ae23d9cf439587590dc2d38584c7b1dfa59488fcaba74176fc9b9a` | `23debd9970ae23d9cf439587590dc2d38584c7b1dfa59488fcaba74176fc9b9a` | **MATCHED (100%)** |

---

## 7. Mandatory Limitation & Disclaimer Statements

> **RecoverAI Batch Recommendation Runner is a decision-recommendation prototype tool. RETRY, NUDGE, ESCALATE, and STOP are recommendations produced by the orchestration engine; no real payment transaction, customer communication, or payment gateway operation is executed by Step 7B.**

> **All failure reasons, recovery actions and recovery outcomes used for model development and policy evaluation are simulated. Olist provides real transaction context but does not provide gateway decline or recovery labels.**

---

## 8. Step Boundary Verdict

```
STEP 7B PASSED
```

```
STEP 7B — RECOVERAI BATCH RECOMMENDATION RUNNER: COMPLETE
```
