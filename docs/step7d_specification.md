# RecoverAI Step 7D Specification: End-to-End System Integration & Verification (Audited & Revised)

## Executive Summary

This document defines the technical specification and verification strategy for **Step 7D: End-to-End System Integration & Verification** of **RecoverAI: Track 03 AI Revenue Recovery**.

The objective of Step 7D is to execute comprehensive end-to-end integration tests across all completed RecoverAI components (**Step 6D Agent Engine**, **Step 7A REST API**, **Step 7B Batch Runner**, and **Step 7C Interactive Dashboard**) under concurrent load, API failure scenarios, and malicious inputs without modifying any pre-existing code, ML models, isotonic calibrators, datasets, or policy evaluation artifacts.

---

## 1. System Integration Architecture & Verification Boundaries

```
                         [ CLIENT ENTRYPOINTS ]
       ┌───────────────────────────┬───────────────────────────┐
       │                           │                           │
  Step 7C Dashboard        Step 7B Batch Runner       External HTTP Clients
  (Interactive Web UI)     (CLI Streaming Runner)    (Concurrency & Load)
       │                           │                           │
       └───────────────────────────┼───────────────────────────┘
                                   │
                     Step 7A FastAPI REST API Server
                        (/api/v1/recommend, /health)
                                   │
                        Synchronous Threadpool
                                   │
                   Step 6D RecoverAI Decision Engine
                                   │
       ┌───────────────────────────┼───────────────────────────┐
       ▼                           ▼                           ▼
Step 6B Guardrails         Step 5E LightGBM + Isotonic     Step 6C Expected Utility
(GR01–GR06 Central Path)   (Frozen Calibrated ML)         (Argmax Selection)
       │                           │                           │
       └───────────────────────────┼───────────────────────────┘
                                   │
                  Thread-Safe Audit Logger (CSV Writer)
```

### 1.1 Centralized Guardrail Routing Mandate
All client entrypoints (Dashboard UI, Batch Runner, REST API) must route decision recommendations exclusively through the centralized `RecoverAI.recommend()` engine path. Neither the Dashboard nor the Batch Runner shall implement duplicate or secondary guardrail evaluation logic.

### 1.2 Isolated Test File Mandate & Frozen Artifact Protection
Integration tests are strictly prohibited from writing to any frozen artifact or historical audit path. All test-generated files must be written to isolated temporary directories (`tempfile.mkdtemp()`).

The following preceding workspace artifacts must remain 100% byte-identical:
- `data/processed/recoverai_recovery_cases.csv`
- `data/processed/recoverai_ml_training_cases.csv`
- `data/processed/recoverai_ml_validation_cases.csv`
- `data/processed/recoverai_ml_test_cases.csv`
- `data/processed/step5f_policy_summary.csv`
- `models/recoverai_step5f/test_evaluation_metrics.json`
- `models/recoverai_step5e/lgbm_model.pkl`
- `models/recoverai_step5e/isotonic_calibrator.pkl`
- `models/recoverai_step5e/feature_list.json`
- `models/recoverai_step5e/categorical_features.json`
- `models/recoverai_step5e/model_config.json`
- `src/recoverai_agent.py`
- `src/api/server.py`
- `src/batch/run_batch.py`

---

## 2. Step 7D Verification Components & Test Requirements

### 2.1 50 Concurrent API Request Load Test & Rate-Limiter Isolation
- **Rate-Limiter Isolation:** Before executing the concurrency test, the test harness must explicitly reset the rate-limiter sliding window state (`ip_request_history.clear()`) so that the 50 concurrent requests execute within a fresh IP quota and cannot fail due to quota consumed by prior test cases.
- **Execution Strategy:** Execute 50 concurrent threadpool workers hitting `POST /api/v1/recommend` simultaneously using FastAPI `TestClient` / `ThreadPoolExecutor`.
- **Validation Criteria:**
  - 100% of valid requests complete with HTTP 200 OK.
  - Zero thread deadlocks or race conditions.
  - Audit logger concurrency verification: Exactly 50 new valid audit records are appended to the audit log (`after_row_count - before_row_count == 50`), verified by unique request IDs without clearing historical audit logs.

### 2.2 Guardrail Invariants Verification Matrix
Verify that all client entrypoints route through the centralized RecoverAI guardrail engine to enforce:
1. `GR01_BOLETO`: `boleto` + `RETRY` $\rightarrow$ `BLOCKED` (Always selects NUDGE/STOP)
2. `GR02_VOUCHER`: `voucher` + `RETRY` $\rightarrow$ `BLOCKED` (Always selects NUDGE/STOP)
3. `GR03_HARD_DECLINE`: `HARD_DECLINE` + `RETRY` $\rightarrow$ `BLOCKED` (Always selects NUDGE/STOP)
4. `GR04_AUTH_REQ`: `authentication_failed` + `RETRY` $\rightarrow$ `BLOCKED` (Always selects NUDGE/STOP)
5. `GR05_MAX_RETRY_CAP`: `recovery_attempt_number > 3` + `RETRY` $\rightarrow$ `BLOCKED`
6. `GR06_HIGH_VALUE`: `payment_value > 5000.0` + `RETRY` $\rightarrow$ `BLOCKED`
7. `STOP Invariant`: `STOP` recovery probability $P = 0.0$ and expected utility $EU = 0.0$.

### 2.3 Memory-Bounded Streaming Criteria (Batch Runner Integration)
- Verify that Step 7B Batch Runner processes input datasets using memory-bounded streaming via standard-library `csv.DictWriter`.
- **Measurable Criteria:**
  - Incremental disk writing (`writerow()`) per record.
  - Output file row count matches input row count.
  - Memory consumption remains flat across multi-row datasets (e.g. 500-row batch execution).

### 2.4 API & Network Failure Handling & Error Sanitization
- **Oversized Requests (HTTP 413):** Payloads $> 2$ MB with and without `Content-Length` headers rejected safely.
- **Rate Limit Exceeded (HTTP 429):** Requests exceeding 100 req/min/IP sliding window return HTTP 429.
- **Sanitized 500 SYSTEM_ERROR (Monkeypatched Exception Test):** Inject artificial exceptions during test execution using test-time monkeypatching/mocking ONLY (e.g., patching `predict_proba` inside the test function). Do NOT add production test hooks or modify server source code. Verify HTTP 500 JSON contains **ZERO** stack traces, filesystem paths (`S:\...`), Python exception details, or model internals.

### 2.5 Cross-Component Leakage & Security Protection
- **Sensitive Credential Stripping:** Requests containing `card_number`, `cvv`, `otp`, `bank_account_number`, `password`, `auth_secret`, `payment_token`, `pin` return HTTP 400 (`SENSITIVE_FIELD_REJECTED`). Confirm zero credential values enter audit logs, batch outputs, or API responses.
- **Post-Decision Leakage Protection:** Requests containing `selected_action`, `candidate_action`, `utility_*`, `model_probability_*`, `recovered` return HTTP 400 (`LEAKAGE_FIELD_REJECTED`).

### 2.6 Model & Calibrator Provenance Hash Verification
- Verify that Step 7B batch output fields (`OUTPUT_FIELDNAMES`), API recommendation responses, and health check endpoints contain the exact SHA-256 provenance hashes:
  - Model Artifact Hash: `ca968b7756caec185e70b562cda34445289cea4d0a4bce14cf7b0c5a0b1068e7`
  - Calibrator Artifact Hash: `8bda9ffdbb4b281a6569c5436f7ccf3cdb721da2971d1029540fa0809d596817`
- Step 7B code (`run_batch.py`) will NOT be modified solely to satisfy this test, as it already writes these provenance hashes.

---

## 3. Automated Test Suite Specification (`tests/test_step7d_integration.py`)

The test suite will execute 18 comprehensive integration tests:

| Test ID | Verification Target | Expected Result |
|---|---|---|
| **Test 1** | 50 Concurrent API Requests Load Test | Rate-limiter isolated first; all 50 requests succeed (HTTP 200) |
| **Test 2** | Audit Logger Concurrency Safety | Exactly 50 new valid audit records added (`delta == 50`) |
| **Test 3** | GR01_BOLETO Guardrail Invariant | RETRY blocked via centralized RecoverAI path |
| **Test 4** | GR02_VOUCHER Guardrail Invariant | RETRY blocked via centralized RecoverAI path |
| **Test 5** | GR03_HARD_DECLINE Guardrail Invariant | RETRY blocked via centralized RecoverAI path |
| **Test 6** | GR04_AUTH_REQ Guardrail Invariant | RETRY blocked via centralized RecoverAI path |
| **Test 7** | GR05_MAX_RETRY_CAP Guardrail Invariant | RETRY blocked when attempt count > 3 |
| **Test 8** | GR06_HIGH_VALUE Guardrail Invariant | RETRY blocked when payment value > R$ 5,000.00 |
| **Test 9** | STOP Invariant Integrity | P(recovery) = 0.0 and EU = 0.0 for all STOP actions |
| **Test 10** | Sensitive Credential Rejection | HTTP 400 SENSITIVE_FIELD_REJECTED, 0 credentials stored |
| **Test 11** | Post-Decision Leakage Rejection | HTTP 400 LEAKAGE_FIELD_REJECTED across all entrypoints |
| **Test 12** | Oversized Payload Rejection (> 2 MB) | HTTP 413 PAYLOAD_TOO_LARGE streamed safely |
| **Test 13** | Client Rate Limiter Enforcement | HTTP 429 RATE_LIMIT_EXCEEDED when > 100 req/min |
| **Test 14** | Global Sanitized Error Response | Monkeypatched exception returns HTTP 500 with zero stack trace |
| **Test 15** | Model & Calibrator SHA-256 Provenance | Provenance hashes match frozen artifact SHA-256 values |
| **Test 16** | Memory-Bounded Batch Streaming | Memory-bounded streaming via csv.DictWriter in temp dir |
| **Test 17** | Dashboard Integration & Static Metrics | Dashboard loads frozen Step 5F metrics without recalculation |
| **Test 18** | Preceding Artifacts SHA-256 Integrity | All 14 preceding workspace files remain 100% byte-identical |

---

## 4. Mandatory Limitation & Disclaimer Statements

> **RecoverAI Integration Testing Suite is a decision-recommendation prototype verification tool. RETRY, NUDGE, ESCALATE, and STOP are recommendations produced by the decision orchestration engine; no real payment transaction, customer communication, or payment gateway operation is executed by Step 7D.**

> **All failure reasons, recovery actions and recovery outcomes used for model development and policy evaluation are simulated. Olist provides real transaction context but does not provide gateway decline or recovery labels.**

---

## 5. Specification Verdict

```
STEP 7D SPECIFICATION REVISED — READY FOR USER APPROVAL TO IMPLEMENT
```
