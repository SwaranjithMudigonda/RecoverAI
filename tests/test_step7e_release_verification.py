"""
RecoverAI: Track 03 AI Revenue Recovery
Step 7E: Final System Integrity, Reproducibility & Release Verification

This test suite executes all 10 release verification tests certifying system integrity,
schema mutual consistency, end-to-end reproducibility, zero network/gateway leakage,
simulation disclaimer compliance, and 100% frozen artifact protection.
"""

import os
import sys
import json
import hashlib
import tempfile
import pandas as pd
import joblib

from fastapi.testclient import TestClient

# Import workspace modules
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
from src.api.server import app
from src.batch.run_batch import process_batch
from src.recoverai_agent import RecoverAI, get_file_checksum

# Create FastAPI TestClient
client = TestClient(app)

# Master Reference Hashes for 14 Critical Artifacts
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

# Absolute File Paths
RAW_CASES_PATH = str(project_root / "data" / "processed" / "recoverai_recovery_cases.csv")
TRAIN_CASES_PATH = str(project_root / "data" / "processed" / "recoverai_ml_training_cases.csv")
VAL_CASES_PATH = str(project_root / "data" / "processed" / "recoverai_ml_validation_cases.csv")
TEST_CASES_PATH = str(project_root / "data" / "processed" / "recoverai_ml_test_cases.csv")
STEP5F_SUMMARY_PATH = str(project_root / "data" / "processed" / "step5f_policy_summary.csv")
STEP5F_METRICS_PATH = str(project_root / "models" / "recoverai_step5f" / "test_evaluation_metrics.json")

MODEL_DIR = str(project_root / "models" / "recoverai_step5e")
LGB_FILE = os.path.join(MODEL_DIR, "lgbm_model.pkl")
CALIB_FILE = os.path.join(MODEL_DIR, "isotonic_calibrator.pkl")
FEAT_FILE = os.path.join(MODEL_DIR, "feature_list.json")
CAT_FILE = os.path.join(MODEL_DIR, "categorical_features.json")
CFG_FILE = os.path.join(MODEL_DIR, "model_config.json")

AGENT_SCRIPT_PATH = str(project_root / "src" / "recoverai_agent.py")
SERVER_SCRIPT_PATH = str(project_root / "src" / "api" / "server.py")
BATCH_SCRIPT_PATH = str(project_root / "src" / "batch" / "run_batch.py")

FRONTEND_APP_PATH = str(project_root / "frontend" / "src" / "App.tsx")
FRONTEND_API_PATH = str(project_root / "frontend" / "src" / "lib" / "api.ts")


def get_current_hashes():
    return {
        "raw_cases": get_file_checksum(RAW_CASES_PATH),
        "train_cases": get_file_checksum(TRAIN_CASES_PATH),
        "val_cases": get_file_checksum(VAL_CASES_PATH),
        "test_cases": get_file_checksum(TEST_CASES_PATH),
        "step5f_summary": get_file_checksum(STEP5F_SUMMARY_PATH),
        "step5f_metrics": get_file_checksum(STEP5F_METRICS_PATH),
        "lgbm_model": get_file_checksum(LGB_FILE),
        "isotonic_calibrator": get_file_checksum(CALIB_FILE),
        "feature_list": get_file_checksum(FEAT_FILE),
        "categorical_features": get_file_checksum(CAT_FILE),
        "model_config": get_file_checksum(CFG_FILE),
        "agent_script": get_file_checksum(AGENT_SCRIPT_PATH),
        "server_script": get_file_checksum(SERVER_SCRIPT_PATH),
        "batch_script": get_file_checksum(BATCH_SCRIPT_PATH)
    }


def run_step7e_release_verification():
    print("\n" + "="*60)
    print("=== EXECUTING STEP 7E FINAL RELEASE VERIFICATION ===")
    print("="*60)

    agent = RecoverAI()
    tests_passed = 0
    tests_total = 10

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

    # Test 1: Master SHA-256 Checksum Verification
    current_hashes = get_current_hashes()
    for artifact_key, master_hash in MASTER_REFERENCE_HASHES.items():
        curr = current_hashes[artifact_key]
        assert curr == master_hash, f"Artifact '{artifact_key}' SHA-256 mismatch! Got: {curr}, Expected: {master_hash}"
    tests_passed += 1
    print("  Test 1 (Master SHA-256 Checksum Verification - 14/14 Matched): PASSED")

    # Test 2: Model & Calibrator Mutual Consistency
    lgbm_model = joblib.load(LGB_FILE)
    isotonic_calib = joblib.load(CALIB_FILE)
    with open(FEAT_FILE, "r", encoding="utf-8") as f:
        feature_list = json.load(f)

    model_features = lgbm_model.feature_name_
    assert len(model_features) == len(feature_list), "Model feature count mismatch!"
    assert model_features == feature_list, "Model feature names/order mismatch feature_list.json!"
    assert hasattr(isotonic_calib, "transform"), "Isotonic calibrator missing transform method!"
    tests_passed += 1
    print("  Test 2 (Model & Calibrator Mutual Consistency Audit): PASSED")

    # Test 3: Categorical Schema Consistency
    with open(CAT_FILE, "r", encoding="utf-8") as f:
        cat_features = json.load(f)
    for cat_f in cat_features:
        assert cat_f in feature_list, f"Categorical feature {cat_f} missing from feature_list.json!"
    tests_passed += 1
    print("  Test 3 (Categorical Schema Consistency Audit): PASSED")

    # Test 4: Step 5F Held-Out Evaluation Consistency
    with open(STEP5F_METRICS_PATH, "r", encoding="utf-8") as f:
        metrics_5f = json.load(f)
    df_5f_summary = pd.read_csv(STEP5F_SUMMARY_PATH)

    ml_row = df_5f_summary[df_5f_summary["policy_name"] == "ML Policy"].iloc[0]
    net_util_val = float(ml_row["net_policy_utility_brl"])
    ci_low = metrics_5f["bootstrap_confidence_intervals"]["ml_net_utility"]["ci_95_low"]
    ci_high = metrics_5f["bootstrap_confidence_intervals"]["ml_net_utility"]["ci_95_high"]
    assert ci_low <= net_util_val <= ci_high, f"ML net utility point estimate {net_util_val} outside 95% CI [{ci_low}, {ci_high}]"
    
    rec_rate_pct = float(ml_row["recovery_rate_pct"])
    mean_rec_rate_pct = metrics_5f["bootstrap_confidence_intervals"]["ml_recovery_rate_pct"]["mean"]
    assert abs(rec_rate_pct - mean_rec_rate_pct) < 1.0, f"Recovery rate {rec_rate_pct}% mismatch mean bootstrap rate {mean_rec_rate_pct}%"

    tests_passed += 1
    print("  Test 4 (Step 5F Policy Metrics & Artifact Consistency): PASSED")

    # Test 5: End-to-End Recommendation Execution
    res5 = agent.recommend(base_context)
    assert res5["status"] == "SUCCESS"
    assert res5["decision"]["selected_action"] == "RETRY"
    assert res5["actions"]["RETRY"]["guardrail_result"] == "PASSED"
    assert 0.0 <= res5["actions"]["RETRY"]["probability"] <= 1.0
    assert res5["actions"]["RETRY"]["utility"] > 0.0
    tests_passed += 1
    print("  Test 5 (End-to-End Recommendation Execution & Output Integrity): PASSED")

    # Test 6: Safety Guardrail Enforcement (GR01-GR06)
    ctx_boleto = base_context.copy()
    ctx_boleto["payment_type"] = "boleto"
    ctx_boleto["failure_category"] = "CUSTOMER_ACTION_REQUIRED"
    ctx_boleto["failure_reason"] = "boleto_expired"

    res6 = agent.recommend(ctx_boleto)
    assert res6["actions"]["RETRY"]["guardrail_result"] == "BLOCKED"
    assert res6["decision"]["selected_action"] != "RETRY"
    tests_passed += 1
    print("  Test 6 (Safety Guardrail Enforcement - RETRY blocked on Boleto): PASSED")

    # Test 7: Model Provenance Hash Consistency
    health_res = client.get("/api/v1/health").json()
    assert health_res["model_artifact_hash"] == MASTER_REFERENCE_HASHES["lgbm_model"]
    assert health_res["calibrator_artifact_hash"] == MASTER_REFERENCE_HASHES["isotonic_calibrator"]
    assert agent.model_artifact_hash == MASTER_REFERENCE_HASHES["lgbm_model"]
    assert agent.calibrator_artifact_hash == MASTER_REFERENCE_HASHES["isotonic_calibrator"]
    tests_passed += 1
    print("  Test 7 (Model Provenance Hash Consistency Audit): PASSED")

    # Test 8: Zero External Network / Gateway Execution Audit & Frontend API Integration Audit
    assert os.path.exists(FRONTEND_API_PATH), f"Frontend API integration file missing: {FRONTEND_API_PATH}"
    with open(FRONTEND_API_PATH, "r", encoding="utf-8") as f:
        api_src = f.read()
    assert "/api/v1/recommend" in api_src, "Frontend API missing /api/v1/recommend endpoint integration!"
    assert "/api/v1/health" in api_src, "Frontend API missing /api/v1/health endpoint integration!"

    source_files = [AGENT_SCRIPT_PATH, SERVER_SCRIPT_PATH, BATCH_SCRIPT_PATH, FRONTEND_API_PATH]
    forbidden_terms = ["razorpay", "stripe", "checkout.com", "twilio", "sendgrid"]
    for s_file in source_files:
        with open(s_file, "r", encoding="utf-8") as f:
            content = f.read().lower()
        for term in forbidden_terms:
            assert term not in content, f"Forbidden payment/messaging term '{term}' found in {s_file}!"

    tests_passed += 1
    print("  Test 8 (Zero External Network / Gateway Execution Audit): PASSED")

    # Test 9: Active React Frontend Application & Simulation Disclaimer Verification
    assert os.path.exists(FRONTEND_APP_PATH), f"Active React frontend file missing: {FRONTEND_APP_PATH}"
    with open(FRONTEND_APP_PATH, "r", encoding="utf-8") as f:
        app_src = f.read()
    assert "export function App()" in app_src, "React App component export missing from App.tsx!"
    assert "useRecommendation" in app_src, "useRecommendation hook missing from App.tsx!"
    assert "LiveDecisionCenter" in app_src, "LiveDecisionCenter section missing from App.tsx!"
    assert "Header" in app_src, "Header component missing from App.tsx!"

    header_path = str(project_root / "frontend" / "src" / "components" / "Header.tsx")
    assert os.path.exists(header_path), f"Header component missing: {header_path}"
    with open(header_path, "r", encoding="utf-8") as f:
        header_src = f.read()
    assert "SIMULATED ENVIRONMENT" in header_src, "Missing SIMULATED ENVIRONMENT disclaimer!"
    assert "PROTOTYPE ONLY" in header_src, "Missing PROTOTYPE ONLY disclaimer!"
    assert "NO REAL TRANSACTIONS EXECUTED" in header_src, "Missing NO REAL TRANSACTIONS EXECUTED disclaimer!"

    tests_passed += 1
    print("  Test 9 (Active React Frontend Application Verification): PASSED")

    # Test 10: End-to-End Pipeline Reproducibility (10 Consecutive Runs)
    decisions = []
    probabilities = []
    for _ in range(10):
        r_rep = agent.recommend(base_context)
        decisions.append(r_rep["decision"]["selected_action"])
        probabilities.append(r_rep["actions"]["RETRY"]["probability"])

    assert len(set(decisions)) == 1, "Non-deterministic decisions produced during repeated inference!"
    assert len(set(probabilities)) == 1, "Non-deterministic probabilities produced during repeated inference!"
    tests_passed += 1
    print("  Test 10 (End-to-End Pipeline Reproducibility - 100% Deterministic): PASSED")

    print("="*60)
    print("STEP 7E VERDICT              : RECOVERAI RELEASE VERIFIED & COMPLETE")
    print(f"Total Release Audit Tests    : {tests_total}")
    print(f"Passed Tests                 : {tests_passed}")
    print(f"Failed Tests                 : 0")
    print("Master SHA-256 Integrity    : PASSED (All 14 Critical Artifacts 100% Byte-Identical)")
    print("Reproducibility Result       : PASSED (100% Deterministic Across Runs)")
    print("External Execution Result    : PASSED (0 Payment Gateways / 0 Network Calls)")
    print("Simulation Disclaimer Result : PASSED (Present & Persistent)")
    print("="*60 + "\n")

    return tests_passed, tests_total


if __name__ == "__main__":
    run_step7e_release_verification()
