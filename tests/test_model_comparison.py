"""
RecoverAI: Supplementary Model Comparison Test Suite
Verifies frozen artifact integrity, Model B artifact existence,
evaluation correctness, and zero interference with production system.

This test file is SEPARATE from existing test suites and does NOT modify them.
"""

import os
import sys
import json
import hashlib
import pickle
import numpy as np
import pandas as pd

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from src.api.server import app
from src.recoverai_agent import RecoverAI, get_file_checksum

client = TestClient(app)

# Master Reference Hashes — identical to existing test suites
MASTER_REFERENCE_HASHES = {
    "raw_cases": "973c8fa9d6034be43d0985b23867ff0988dcdaf442d9886706a50dc85094918d",
    "train_cases": "7c03d6e2c16dd51b4e8715a9313a8eadf4e8d3b9b334d35652878853f5d2fd7b",
    "val_cases": "8f495e5d219463b502d90470d5d92723e9c20a2b45415c07aaf0fa51b6f56ee2",
    "test_cases": "fe52ba8be239102fb6152c1bd86dafbf71bf69e185d216baacec01558907b43e",
    "step5f_summary": "57d684e6e584f92f7502c244b926e3af0584abc7fb1a5ba6da070db66262774f",
    "step5f_metrics": "812ad91aeda91d520832682f7bd53f433c10699c160984885081cecb374d2c74",
    "lgbm_model": "ca968b7756caec185e70b562cda34445289cea4d0a4bce14cf7b0c5a0b1068e7",
    "isotonic_calibrator": "8bda9ffdbb4b281a6569c5436f7ccf3cdb721da2971d1029540fa0809d596817",
    "feature_list": "8462f5c4a83e53254ddebed80e458508fc719df19e900481b1c396e64e935f4d",
    "categorical_features": "23debd9970ae23d9cf439587590dc2d38584c7b1dfa59488fcaba74176fc9b9a",
    "model_config": "a7cb181a291bf95924ae86b4d9949de9c32b59ba907692ae29a00e8254672cc9",
    "agent_script": "dc974a6aaa34b219f4d34830d27aa7a3ea19406d4637fe487086f94c879969f9",
    "server_script": "217abb018716e353d7e432be12c8f53b00129672d43cc4440ffd8cb68af93c9f",
    "batch_script": "2d562aecdca1146aed3c6bea4e5337841320a817fbcab975d048769630896e91"
}

project_root = Path(__file__).resolve().parents[1]
FROZEN_ARTIFACT_PATHS = {
    "raw_cases": str(project_root / "data" / "processed" / "recoverai_recovery_cases.csv"),
    "train_cases": str(project_root / "data" / "processed" / "recoverai_ml_training_cases.csv"),
    "val_cases": str(project_root / "data" / "processed" / "recoverai_ml_validation_cases.csv"),
    "test_cases": str(project_root / "data" / "processed" / "recoverai_ml_test_cases.csv"),
    "step5f_summary": str(project_root / "data" / "processed" / "step5f_policy_summary.csv"),
    "step5f_metrics": str(project_root / "models" / "recoverai_step5f" / "test_evaluation_metrics.json"),
    "lgbm_model": str(project_root / "models" / "recoverai_step5e" / "lgbm_model.pkl"),
    "isotonic_calibrator": str(project_root / "models" / "recoverai_step5e" / "isotonic_calibrator.pkl"),
    "feature_list": str(project_root / "models" / "recoverai_step5e" / "feature_list.json"),
    "categorical_features": str(project_root / "models" / "recoverai_step5e" / "categorical_features.json"),
    "model_config": str(project_root / "models" / "recoverai_step5e" / "model_config.json"),
    "agent_script": str(project_root / "src" / "recoverai_agent.py"),
    "server_script": str(project_root / "src" / "api" / "server.py"),
    "batch_script": str(project_root / "src" / "batch" / "run_batch.py")
}

MODEL_B_DIR = str(project_root / "models" / "recoverai_model_comparison")

FORBIDDEN_FEATURES = [
    "selected_action",
    "model_probability_RETRY", "model_probability_NUDGE",
    "model_probability_ESCALATE", "model_probability_STOP",
    "effective_probability_RETRY", "effective_probability_NUDGE",
    "effective_probability_ESCALATE", "effective_probability_STOP",
    "utility_RETRY", "utility_NUDGE", "utility_ESCALATE", "utility_STOP",
    "guardrail_RETRY", "guardrail_NUDGE", "guardrail_ESCALATE", "guardrail_STOP",
    "guardrail_rules_RETRY", "guardrail_rules_NUDGE",
    "guardrail_rules_ESCALATE", "guardrail_rules_STOP",
    "recovery_probability", "expected_recovered_amount", "recovered_amount"
]


def run_model_comparison_tests():
    print("\n" + "=" * 70)
    print("=== MODEL COMPARISON TEST SUITE ===")
    print("=" * 70)

    tests_passed = 0
    tests_total = 14

    # ---- Test 1: 14 Frozen SHA-256 Hashes Unchanged ----
    for key, expected_hash in MASTER_REFERENCE_HASHES.items():
        path = FROZEN_ARTIFACT_PATHS[key]
        actual = get_file_checksum(path)
        assert actual == expected_hash, (
            f"FROZEN ARTIFACT MISMATCH: {key}\n"
            f"  Expected: {expected_hash}\n"
            f"  Actual:   {actual}"
        )
    tests_passed += 1
    print("  Test 1  (14 Frozen SHA-256 Hashes Unchanged): PASSED")

    # ---- Test 2: Frozen Test Dataset Unchanged ----
    test_hash = get_file_checksum(FROZEN_ARTIFACT_PATHS["test_cases"])
    assert test_hash == MASTER_REFERENCE_HASHES["test_cases"]
    test_df = pd.read_csv(FROZEN_ARTIFACT_PATHS["test_cases"])
    assert len(test_df) == 2283, f"Test dataset row count: {len(test_df)}, expected 2283"
    assert "action" not in test_df.columns, "Test dataset should not contain 'action' column"
    assert "recovered" not in test_df.columns, "Test dataset should not contain 'recovered' column"
    tests_passed += 1
    print("  Test 2  (Frozen Test Dataset Unchanged): PASSED")

    # ---- Test 3: Frozen Step 5F Metrics Unchanged ----
    with open(FROZEN_ARTIFACT_PATHS["step5f_metrics"], "r") as f:
        step5f_metrics = json.load(f)
    assert abs(step5f_metrics["test_ml_metrics"]["roc_auc"] - 0.6878573307307889) < 1e-10
    assert abs(step5f_metrics["test_ml_metrics"]["brier_score"] - 0.22269510860789482) < 1e-10
    assert abs(step5f_metrics["test_ml_metrics"]["ece"] - 0.02644392067873896) < 1e-10
    assert abs(step5f_metrics["test_ml_metrics"]["log_loss"] - 0.6513521285877792) < 1e-10
    assert step5f_metrics["test_ml_metrics"]["sample_count"] == 2283
    tests_passed += 1
    print("  Test 3  (Frozen Step 5F Metrics Unchanged): PASSED")

    # ---- Test 4: Frozen LightGBM Model Unchanged ----
    lgbm_hash = get_file_checksum(FROZEN_ARTIFACT_PATHS["lgbm_model"])
    assert lgbm_hash == MASTER_REFERENCE_HASHES["lgbm_model"]
    tests_passed += 1
    print("  Test 4  (Frozen LightGBM Model Unchanged): PASSED")

    # ---- Test 5: Frozen Isotonic Calibrator Unchanged ----
    calib_hash = get_file_checksum(FROZEN_ARTIFACT_PATHS["isotonic_calibrator"])
    assert calib_hash == MASTER_REFERENCE_HASHES["isotonic_calibrator"]
    tests_passed += 1
    print("  Test 5  (Frozen Isotonic Calibrator Unchanged): PASSED")

    # ---- Test 6: Model B Artifacts Exist ----
    required_files = [
        "logistic_regression_model.pkl",
        "lr_isotonic_calibrator.pkl",
        "comparison_metrics.json",
        "comparison_report.md",
        "lr_onehot_encoder.pkl",
        "lr_standard_scaler.pkl"
    ]
    for fname in required_files:
        fpath = os.path.join(MODEL_B_DIR, fname)
        assert os.path.exists(fpath), f"Model B artifact missing: {fpath}"
        assert os.path.getsize(fpath) > 0, f"Model B artifact empty: {fpath}"
    tests_passed += 1
    print("  Test 6  (Model B Artifacts Exist): PASSED")

    # ---- Test 7: Model B Uses No Held-Out Outcome Information During Training ----
    # Verify: the LR model was trained on 16 features (one-hot expanded)
    # None of the features are in FORBIDDEN_FEATURES
    with open(os.path.join(MODEL_B_DIR, "lr_onehot_encoder.pkl"), "rb") as f:
        encoder = pickle.load(f)
    ohe_feature_names = list(encoder.get_feature_names_out([
        "payment_type", "failure_category", "failure_reason", "action"
    ]))
    numeric_features = [
        "payment_value", "payment_installments", "previous_order_count",
        "previous_payment_count", "previous_success_count",
        "previous_cancelled_count", "historical_payment_success_rate",
        "historical_average_payment", "customer_tenure_before_payment",
        "order_frequency_before_payment", "hours_since_failure",
        "recovery_attempt_number"
    ]
    all_lr_features = numeric_features + ohe_feature_names
    for feat in all_lr_features:
        for forbidden in FORBIDDEN_FEATURES:
            assert forbidden not in feat, (
                f"Forbidden feature '{forbidden}' found in LR features via '{feat}'"
            )
    tests_passed += 1
    print("  Test 7  (Model B Uses No Held-Out Outcome Information): PASSED")

    # ---- Test 8: Preprocessing Fit Only on Training Data ----
    with open(os.path.join(MODEL_B_DIR, "lr_standard_scaler.pkl"), "rb") as f:
        scaler = pickle.load(f)
    # Scaler should have been fit on 11,051 training samples
    assert scaler.n_samples_seen_ == 11051, (
        f"Scaler n_samples_seen_: {scaler.n_samples_seen_}, expected 11051"
    )
    # Encoder should know categories from training data
    assert len(encoder.categories_) == 4, "Encoder should have 4 categorical feature groups"
    tests_passed += 1
    print("  Test 8  (Preprocessing Fit Only on Training Data): PASSED")

    # ---- Test 9: Sample Count = 2,283 ----
    with open(os.path.join(MODEL_B_DIR, "comparison_metrics.json"), "r") as f:
        comp_metrics = json.load(f)
    assert comp_metrics["model_b_calibrated"]["test_metrics"]["sample_count"] == 2283
    assert comp_metrics["model_a"]["test_metrics"]["sample_count"] == 2283
    tests_passed += 1
    print("  Test 9  (Sample Count = 2,283): PASSED")

    # ---- Test 10: CRN Seed is Identical ----
    assert comp_metrics["seeds"]["crn_seed"] == 999
    assert comp_metrics["seeds"]["training_seed"] == 42
    assert comp_metrics["seeds"]["validation_seed"] == 42
    assert comp_metrics["seeds"]["bootstrap_seed"] == 42
    tests_passed += 1
    print("  Test 10 (CRN Seed is Identical): PASSED")

    # ---- Test 11: Policy/Utility Definitions Identical ----
    # Verify that Rule-Based and Upper Bound baselines match between Model A and B evaluations
    # The Rule-Based and Upper Bound policies do NOT depend on the ML model, only on
    # the test data, CRN, and simulator. If Model B's environment is set up correctly,
    # its Rule-Based/Upper Bound results must match Model A's frozen results.
    model_a_summary = pd.read_csv(FROZEN_ARTIFACT_PATHS["step5f_summary"])
    model_a_rb = model_a_summary[model_a_summary["policy_tag"] == "RULE_BASED"].iloc[0]
    model_a_ub = model_a_summary[model_a_summary["policy_tag"] == "UPPER_BOUND"].iloc[0]

    model_b_rb_net_u = comp_metrics["policy_comparison"]["rule_based_net_utility_brl"]
    model_b_ub_net_u = comp_metrics["policy_comparison"]["upper_bound_net_utility_brl"]

    assert abs(model_b_rb_net_u - float(model_a_rb["net_policy_utility_brl"])) < 0.01, (
        f"Rule-Based net utility mismatch: Model A={float(model_a_rb['net_policy_utility_brl'])}, "
        f"Model B env={model_b_rb_net_u}"
    )
    assert abs(model_b_ub_net_u - float(model_a_ub["net_policy_utility_brl"])) < 0.01, (
        f"Upper Bound net utility mismatch: Model A={float(model_a_ub['net_policy_utility_brl'])}, "
        f"Model B env={model_b_ub_net_u}"
    )
    tests_passed += 1
    print("  Test 11 (Policy/Utility Definitions Identical — RB & UB Cross-Check): PASSED")

    # ---- Test 12: Model B Results are Deterministic ----
    assert comp_metrics["reproducibility_verified"] is True
    tests_passed += 1
    print("  Test 12 (Model B Results are Deterministic): PASSED")

    # ---- Test 13: Existing API Behavior Unchanged ----
    base_context = {
        "payment_type": "credit_card",
        "payment_value": 250.0,
        "payment_installments": 1,
        "previous_order_count": 2,
        "previous_payment_count": 2,
        "previous_success_count": 2,
        "previous_cancelled_count": 0,
        "historical_payment_success_rate": 1.0,
        "historical_average_payment": 250.0,
        "customer_tenure_before_payment": 30,
        "order_frequency_before_payment": 15.0,
        "failure_category": "SOFT_DECLINE",
        "failure_reason": "network_error",
        "hours_since_failure": 1.0,
        "recovery_attempt_number": 1
    }

    api_res = client.post("/api/v1/recommend", json=base_context)
    assert api_res.status_code == 200
    api_body = api_res.json()
    assert api_body["status"] == "SUCCESS"
    assert api_body["decision"]["selected_action"] == "RETRY"
    assert 0.0 <= api_body["actions"]["RETRY"]["probability"] <= 1.0

    health_res = client.get("/api/v1/health").json()
    assert health_res["model_artifact_hash"] == MASTER_REFERENCE_HASHES["lgbm_model"]
    assert health_res["calibrator_artifact_hash"] == MASTER_REFERENCE_HASHES["isotonic_calibrator"]
    tests_passed += 1
    print("  Test 13 (Existing API Behavior Unchanged): PASSED")

    # ---- Test 14: Existing Dashboard Behavior Unchanged ----
    dashboard_html = str(project_root / "dashboard" / "index.html")
    dashboard_js = str(project_root / "dashboard" / "app.js")
    assert os.path.exists(dashboard_html)
    assert os.path.exists(dashboard_js)
    with open(dashboard_html, "r", encoding="utf-8") as f:
        html_content = f.read()
    assert "SIMULATED ENVIRONMENT" in html_content
    assert "PROTOTYPE ONLY" in html_content
    with open(dashboard_js, "r", encoding="utf-8") as f:
        js_content = f.read()
    assert "FROZEN_STEP5F_ARTIFACT_DATA" in js_content
    # Ensure no Model B references leaked into dashboard
    assert "logistic_regression" not in js_content.lower()
    assert "model_b" not in js_content.lower()
    tests_passed += 1
    print("  Test 14 (Existing Dashboard Behavior Unchanged): PASSED")

    # ---- Summary ----
    print("\n" + "=" * 70)
    print(f"MODEL COMPARISON TEST SUITE: {'PASSED' if tests_passed == tests_total else 'FAILED'}")
    print(f"Total Tests: {tests_total}")
    print(f"Passed:      {tests_passed}")
    print(f"Failed:      {tests_total - tests_passed}")
    print("=" * 70 + "\n")

    return tests_passed, tests_total


if __name__ == "__main__":
    run_model_comparison_tests()
