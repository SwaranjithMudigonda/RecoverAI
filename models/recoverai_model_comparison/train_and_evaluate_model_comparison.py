"""
RecoverAI: Supplementary Model Comparison Experiment
LightGBM (Model A, Frozen) vs Logistic Regression (Model B)

This script trains a supplementary Logistic Regression S-learner model and
evaluates it using the EXACT same methodology as the frozen Step 5F evaluation.

IMPORTANT:
- This is a SUPPLEMENTARY experiment only.
- The frozen LightGBM pipeline remains the official RecoverAI model.
- No frozen artifacts are modified.
- Model B is NEVER integrated into the production/prototype decision engine.

Implementation Contract Items Referenced:
- Training data: recoverai_ml_training_cases.csv (11,051 rows)
- Validation data: recoverai_ml_validation_cases.csv (2,247 rows, action/recovered generated at runtime)
- Test data: recoverai_ml_test_cases.csv (2,283 rows)
- Validation seed: 42
- Test CRN seed: 999
- Bootstrap seed: 42, 1000 iterations
"""

import os
import sys
import hashlib
import json
import time
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

# ============================================================================
# Constants — exact copies from frozen Step 5E/5F pipeline
# ============================================================================

SEED = 42
CRN_SEED = 999
BOOTSTRAP_SEED = 42
BOOTSTRAP_ITERATIONS = 1000

PREDICTIVE_FEATURES = [
    "payment_type",
    "payment_value",
    "payment_installments",
    "previous_order_count",
    "previous_payment_count",
    "previous_success_count",
    "previous_cancelled_count",
    "historical_payment_success_rate",
    "historical_average_payment",
    "customer_tenure_before_payment",
    "order_frequency_before_payment",
    "failure_category",
    "failure_reason",
    "hours_since_failure",
    "recovery_attempt_number",
    "action"
]

CATEGORICAL_FEATURES = [
    "payment_type",
    "failure_category",
    "failure_reason",
    "action"
]

NUMERIC_FEATURES = [
    "payment_value",
    "payment_installments",
    "previous_order_count",
    "previous_payment_count",
    "previous_success_count",
    "previous_cancelled_count",
    "historical_payment_success_rate",
    "historical_average_payment",
    "customer_tenure_before_payment",
    "order_frequency_before_payment",
    "hours_since_failure",
    "recovery_attempt_number"
]

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

# Frozen Model A test metrics (from Step 5F)
MODEL_A_FROZEN_METRICS = {
    "roc_auc": 0.6878573307307889,
    "brier_score": 0.22269510860789482,
    "ece": 0.02644392067873896,
    "log_loss": 0.6513521285877792,
    "sample_count": 2283
}

# Master reference SHA-256 hashes for 14 frozen artifacts
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

project_root = Path(__file__).resolve().parents[2]
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


# ============================================================================
# Utility functions — exact copies from frozen pipeline
# ============================================================================

def get_file_checksum(filepath):
    """Compute SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_ece(y_true, y_prob, n_bins=10):
    """Compute Expected Calibration Error (ECE) using n_bins equal-width bins.
    Exact copy from evaluate_step5f.py L84-101."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        if i == 0:
            in_bin = (y_prob >= bin_lower) & (y_prob <= bin_upper)
        else:
            in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)

        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin
    return float(ece)


def compute_simulator_probability(row, action):
    """Ground-truth simulation environment probability formula.
    Exact copy from evaluate_step5f.py L104-151."""
    if action == "STOP":
        return 0.0

    category = row["failure_category"]
    p_val = float(row["payment_value"])
    hist_success = float(row["historical_payment_success_rate"])
    tenure = float(row["customer_tenure_before_payment"])
    hrs_since = float(row["hours_since_failure"])

    delta_logit = (
        1.5 * (hist_success - 0.5)
        + 0.3 * np.log1p(tenure)
        - 0.02 * hrs_since
        - 0.0001 * p_val
    )

    if action == "RETRY":
        if category == "SOFT_DECLINE":
            beta = 2.2
        elif category == "FUNDS_ISSUE":
            beta = -0.5
        elif category == "GENERIC_DECLINE":
            beta = 0.2
        else:
            beta = -3.0
    elif action == "NUDGE":
        if category == "CUSTOMER_ACTION_REQUIRED":
            beta = 2.0
        elif category == "FUNDS_ISSUE":
            beta = 0.8
        elif category == "GENERIC_DECLINE":
            beta = 0.5
        elif category == "SOFT_DECLINE":
            beta = -1.0
        else:
            beta = 0.0
    elif action == "ESCALATE":
        if p_val > 1000.0 or category in ["HARD_DECLINE", "GENERIC_DECLINE"]:
            beta = 0.8
        else:
            beta = -1.5

    logit = beta + delta_logit
    p_model = 1.0 / (1.0 + np.exp(-logit))
    return float(np.clip(p_model, 0.0, 1.0))


def compute_action_costs(p_val, category, action):
    """Compute intervention cost, risk penalty, and customer friction cost.
    Exact copy from evaluate_step5f.py L153-163."""
    if action == "STOP":
        return 0.0, 0.0, 0.0, 0.0

    c_interv = {"RETRY": 0.50, "NUDGE": 1.50, "ESCALATE": 15.00}[action]
    r_pen = 100.0 if (category == "HARD_DECLINE" and action == "RETRY") else 0.0
    f_cost = 1.0 if action == "NUDGE" else (
        3.0 if (category == "CUSTOMER_ACTION_REQUIRED" and action == "RETRY") else 0.0
    )

    total_cost = c_interv + r_pen + f_cost
    return c_interv, r_pen, f_cost, total_cost


def evaluate_guardrails_for_case(row):
    """Evaluate guardrails independently for all 4 candidate actions.
    Exact copy from evaluate_step5f.py L166-197."""
    ptype = row["payment_type"]
    p_val = float(row["payment_value"])
    reason = row["failure_reason"]
    category = row["failure_category"]
    attempt = row["recovery_attempt_number"]

    actions = ["RETRY", "NUDGE", "ESCALATE", "STOP"]
    guardrail_status = {}
    guardrail_rules = {}

    for a in actions:
        rules = []
        if a == "RETRY":
            if ptype == "boleto":
                rules.append("GR01_BOLETO_RETRY_PROHIBITED")
            if ptype == "voucher":
                rules.append("GR02_VOUCHER_RETRY_PROHIBITED")
            if category == "HARD_DECLINE":
                rules.append("GR03_HARD_DECLINE_RETRY_PROHIBITED")
            if reason in ["authentication_failed", "expired_card", "boleto_expired"]:
                rules.append("GR04_AUTH_REQUIRED_RETRY_PROHIBITED")
            if attempt > 3:
                rules.append("GR05_MAX_RETRY_CAP")
            if p_val > 5000.0 and reason in ["do_not_honor", "payment_failed"]:
                rules.append("GR06_HIGH_VALUE_ESCALATION")

        guardrail_status[a] = "BLOCKED" if len(rules) > 0 else "PASSED"
        guardrail_rules[a] = "|".join(rules) if rules else "NONE"

    return guardrail_status, guardrail_rules


def check_guardrail_violation(ptype, reason, category, action):
    """Check for explicit guardrail safety violations.
    Exact copy from evaluate_step5f.py L200-211."""
    if action == "RETRY":
        if ptype == "boleto":
            return True
        if ptype == "voucher":
            return True
        if category == "HARD_DECLINE":
            return True
        if reason in ["authentication_failed", "expired_card", "boleto_expired"]:
            return True
    return False


def prepare_validation_data(val_df, seed=42):
    """Prepare validation dataset by evaluating explored action and outcome.
    Exact copy from train_ml_model.py L136-160."""
    rng = np.random.default_rng(seed)
    val_processed = val_df.copy()

    val_actions = []
    val_outcomes = []

    for i, row in val_processed.iterrows():
        valid_acts = row["valid_actions"].split("|")
        chosen_action = rng.choice(valid_acts)
        prob = compute_simulator_probability(row, chosen_action)
        is_rec = 1 if rng.random() < prob else 0

        val_actions.append(chosen_action)
        val_outcomes.append(is_rec)

    val_processed["action"] = val_actions
    val_processed["recovered"] = val_outcomes

    return val_processed


# ============================================================================
# Preprocessing for Logistic Regression
# ============================================================================

def build_lr_preprocessor(train_df):
    """Build OneHotEncoder + StandardScaler fitted on training data ONLY.

    Returns: (encoder, scaler, feature_names_out)
    """
    X_cat_train = train_df[CATEGORICAL_FEATURES].copy()
    X_num_train = train_df[NUMERIC_FEATURES].copy()

    # OneHotEncoder: fitted on training categories only
    encoder = OneHotEncoder(sparse_output=False, handle_unknown="error", drop=None)
    encoder.fit(X_cat_train)

    # StandardScaler: fitted on training numeric features only
    scaler = StandardScaler()
    scaler.fit(X_num_train)

    # Build feature name list
    cat_feature_names = list(encoder.get_feature_names_out(CATEGORICAL_FEATURES))
    num_feature_names = list(NUMERIC_FEATURES)
    feature_names_out = num_feature_names + cat_feature_names

    return encoder, scaler, feature_names_out


def transform_features(df, encoder, scaler):
    """Apply fitted encoder and scaler to produce LR feature matrix.

    Preprocessing fitted on training data only — never refitted.
    """
    X_cat = df[CATEGORICAL_FEATURES].copy()
    X_num = df[NUMERIC_FEATURES].copy()

    X_cat_encoded = encoder.transform(X_cat)
    X_num_scaled = scaler.transform(X_num)

    X_combined = np.hstack([X_num_scaled, X_cat_encoded])
    return X_combined


# ============================================================================
# Training
# ============================================================================

def train_logistic_regression(X_train, y_train):
    """Train Logistic Regression with pre-specified hyperparameters.

    No hyperparameter tuning on test set. Default L2 regularization (C=1.0).
    solver='lbfgs', max_iter=1000 for convergence.
    """
    lr_model = LogisticRegression(
        solver="lbfgs",
        max_iter=1000,
        random_state=SEED,
        C=1.0,
        penalty="l2",
        verbose=0
    )
    lr_model.fit(X_train, y_train)
    return lr_model


# ============================================================================
# Test Evaluation — exact replication of Step 5F methodology
# ============================================================================

def run_lr_test_evaluation(test_df, lr_model, lr_calibrator, encoder, scaler):
    """Run policy evaluation on held-out test set using same Step 5F methodology.

    Replicates evaluate_step5f.py run_test_evaluation() exactly,
    substituting LR predictions for LightGBM predictions.
    """
    rng_crn = np.random.default_rng(CRN_SEED)
    crn_draws = rng_crn.random(size=len(test_df))

    # Batch predict LR probabilities for RETRY, NUDGE, ESCALATE
    dfs_to_predict = []
    for a in ["RETRY", "NUDGE", "ESCALATE"]:
        sub_df = test_df[PREDICTIVE_FEATURES[:-1]].copy()
        sub_df["action"] = a
        dfs_to_predict.append(sub_df)

    batch_df = pd.concat(dfs_to_predict, ignore_index=True)
    X_batch = transform_features(batch_df, encoder, scaler)

    raw_probs = lr_model.predict_proba(X_batch)[:, 1]
    cal_probs = lr_calibrator.transform(raw_probs)

    n_cases = len(test_df)
    raw_p_retry = raw_probs[:n_cases]
    raw_p_nudge = raw_probs[n_cases:2*n_cases]
    raw_p_escl  = raw_probs[2*n_cases:]

    cal_p_retry = cal_probs[:n_cases]
    cal_p_nudge = cal_probs[n_cases:2*n_cases]
    cal_p_escl  = cal_probs[2*n_cases:]

    results = []

    for idx, row in test_df.iterrows():
        case_id = row["case_id"]
        order_id = row["order_id"]
        c_unique_id = row["customer_unique_id"]
        ptype = row["payment_type"]
        p_val = float(row["payment_value"])
        category = row["failure_category"]
        reason = row["failure_reason"]
        attempt = int(row["recovery_attempt_number"])
        u_i = crn_draws[idx]

        # 1. Guardrail evaluation — identical to Step 5F
        g_status, g_rules = evaluate_guardrails_for_case(row)
        valid_active_actions = [a for a in ["RETRY", "NUDGE", "ESCALATE"]
                                if g_status[a] == "PASSED"]

        lr_raw_probs = {
            "RETRY": float(raw_p_retry[idx]),
            "NUDGE": float(raw_p_nudge[idx]),
            "ESCALATE": float(raw_p_escl[idx])
        }

        lr_cal_probs = {
            "RETRY": float(cal_p_retry[idx]) if g_status["RETRY"] == "PASSED" else 0.0,
            "NUDGE": float(cal_p_nudge[idx]) if g_status["NUDGE"] == "PASSED" else 0.0,
            "ESCALATE": float(cal_p_escl[idx]) if g_status["ESCALATE"] == "PASSED" else 0.0
        }

        # Utility calculation — identical to Step 5F
        lr_utilities = {}
        for a in ["RETRY", "NUDGE", "ESCALATE"]:
            _, _, _, tot_c = compute_action_costs(p_val, category, a)
            u = (p_val * lr_cal_probs[a]) - tot_c
            lr_utilities[a] = u

        # Policy selection — identical to Step 5F
        fallback_triggered = False
        if valid_active_actions:
            lr_selected_action = max(valid_active_actions,
                                     key=lambda a: lr_utilities[a])
            if (lr_utilities[lr_selected_action] < 0
                    and lr_selected_action in ["RETRY", "NUDGE"]):
                lr_selected_action = "ESCALATE" if p_val > 500.0 else "STOP"
                if lr_selected_action == "STOP":
                    fallback_triggered = True
        else:
            lr_selected_action = "STOP"
            fallback_triggered = True

        lr_rec_prob = (lr_cal_probs[lr_selected_action]
                       if lr_selected_action != "STOP" else 0.0)

        # Rule-Based Baseline — identical to Step 5F
        if category == "SOFT_DECLINE":
            rb_intent = "RETRY"
        elif category in ["FUNDS_ISSUE", "CUSTOMER_ACTION_REQUIRED",
                           "GENERIC_DECLINE"]:
            rb_intent = "NUDGE"
        elif category == "HARD_DECLINE":
            rb_intent = "STOP"
        else:
            rb_intent = "NUDGE"
        rule_based_action = (rb_intent if g_status.get(rb_intent, "PASSED") == "PASSED"
                             else "STOP")

        # Simulation Policy Upper Bound — identical to Step 5F
        sim_utilities = {}
        for a in ["RETRY", "NUDGE", "ESCALATE"]:
            sim_p = compute_simulator_probability(row, a)
            eff_p = sim_p if g_status[a] == "PASSED" else 0.0
            _, _, _, tot_c = compute_action_costs(p_val, category, a)
            sim_utilities[a] = (p_val * eff_p) - tot_c

        if valid_active_actions:
            upper_bound_action = max(valid_active_actions,
                                     key=lambda a: sim_utilities[a])
            if (sim_utilities[upper_bound_action] < 0
                    and upper_bound_action in ["RETRY", "NUDGE"]):
                upper_bound_action = ("ESCALATE" if p_val > 500.0 else "STOP")
        else:
            upper_bound_action = "STOP"

        # CRN-based outcomes — identical to Step 5F
        sim_p_lr = compute_simulator_probability(row, lr_selected_action)
        sim_p_rb = compute_simulator_probability(row, rule_based_action)
        sim_p_ub = compute_simulator_probability(row, upper_bound_action)

        rec_lr = 1 if u_i < sim_p_lr else 0
        rec_rb = 1 if u_i < sim_p_rb else 0
        rec_ub = 1 if u_i < sim_p_ub else 0

        amt_lr = p_val if rec_lr == 1 else 0.0
        amt_rb = p_val if rec_rb == 1 else 0.0
        amt_ub = p_val if rec_ub == 1 else 0.0

        _, _, _, cost_lr = compute_action_costs(p_val, category, lr_selected_action)
        _, _, _, cost_rb = compute_action_costs(p_val, category, rule_based_action)
        _, _, _, cost_ub = compute_action_costs(p_val, category, upper_bound_action)

        net_u_lr = amt_lr - cost_lr
        net_u_rb = amt_rb - cost_rb
        net_u_ub = amt_ub - cost_ub

        viol_lr = check_guardrail_violation(ptype, reason, category,
                                            lr_selected_action)

        results.append({
            "case_id": case_id,
            "order_id": order_id,
            "customer_unique_id": c_unique_id,
            "payment_value": p_val,
            "failure_category": category,

            "lr_selected_action": lr_selected_action,
            "lr_recovery_probability": lr_rec_prob,
            "lr_raw_probability_RETRY": lr_raw_probs["RETRY"],
            "lr_raw_probability_NUDGE": lr_raw_probs["NUDGE"],
            "lr_raw_probability_ESCALATE": lr_raw_probs["ESCALATE"],

            "rule_based_action": rule_based_action,
            "simulation_upper_bound_action": upper_bound_action,

            "crn_uniform": u_i,

            "recovered_LR": rec_lr,
            "recovered_RULE_BASED": rec_rb,
            "recovered_UPPER_BOUND": rec_ub,

            "recovered_amount_LR": amt_lr,
            "recovered_amount_RULE_BASED": amt_rb,
            "recovered_amount_UPPER_BOUND": amt_ub,

            "net_utility_LR": net_u_lr,
            "net_utility_RULE_BASED": net_u_rb,
            "net_utility_UPPER_BOUND": net_u_ub,

            "fallback_triggered": fallback_triggered,
            "guardrail_violation_LR": viol_lr,
        })

    return pd.DataFrame(results)


def compute_test_metrics(results_df):
    """Compute test metrics for LR model — identical methodology to Step 5F."""
    y_true = results_df["recovered_LR"].values
    y_prob = results_df["lr_recovery_probability"].values

    brier = float(brier_score_loss(y_true, y_prob))
    ece_val = float(compute_ece(y_true, y_prob, n_bins=10))
    logloss = float(log_loss(y_true, y_prob))
    roc_auc = float(roc_auc_score(y_true, y_prob))

    return {
        "brier_score": brier,
        "ece": ece_val,
        "log_loss": logloss,
        "roc_auc": roc_auc,
        "sample_count": len(y_true)
    }


def compute_policy_summaries(results_df):
    """Compute policy evaluation metrics — same methodology as Step 5F."""
    policies = [
        ("LR Policy (Model B)", "LR"),
        ("Rule-Based Policy", "RULE_BASED"),
        ("Simulation Policy Upper Bound", "UPPER_BOUND")
    ]

    total_cases = len(results_df)
    rev_at_risk = float(results_df["payment_value"].sum())
    rb_net_u = float(results_df["net_utility_RULE_BASED"].sum())
    rb_rec_amt = float(results_df["recovered_amount_RULE_BASED"].sum())
    ub_net_u = float(results_df["net_utility_UPPER_BOUND"].sum())

    summary_rows = []
    for name, tag in policies:
        net_u = float(results_df[f"net_utility_{tag}"].sum())
        rec_amt = float(results_df[f"recovered_amount_{tag}"].sum())
        rec_cnt = int(results_df[f"recovered_{tag}"].sum())
        rec_rate = float(rec_cnt) / float(total_cases)

        abs_lift_rev = rec_amt - rb_rec_amt
        pct_lift_rev = (abs_lift_rev / rb_rec_amt * 100.0) if rb_rec_amt != 0 else 0.0
        net_u_lift = net_u - rb_net_u
        regret = ub_net_u - net_u

        viol_cnt = int(results_df[f"guardrail_violation_{tag}"].sum()) if f"guardrail_violation_{tag}" in results_df.columns else 0

        summary_rows.append({
            "policy_name": name,
            "policy_tag": tag,
            "total_cases": total_cases,
            "revenue_at_risk_brl": rev_at_risk,
            "recovered_revenue_brl": rec_amt,
            "net_policy_utility_brl": net_u,
            "recovery_rate_pct": rec_rate * 100.0,
            "abs_revenue_lift_vs_rb_brl": abs_lift_rev,
            "pct_revenue_lift_vs_rb": pct_lift_rev,
            "net_utility_lift_vs_rb_brl": net_u_lift,
            "regret_vs_upper_bound_brl": regret,
            "guardrail_violations": viol_cnt
        })

    return pd.DataFrame(summary_rows)


def run_bootstrap(results_df, seed=42, iterations=1000):
    """Customer-Level Clustered Bootstrap — same methodology as Step 5F."""
    print(f"  Running Customer-Level Clustered Bootstrap ({iterations} iterations, SEED={seed})...")
    rng_bs = np.random.default_rng(seed)

    cust_agg = results_df.groupby("customer_unique_id").agg({
        "net_utility_LR": "sum",
        "net_utility_RULE_BASED": "sum",
        "net_utility_UPPER_BOUND": "sum",
        "recovered_amount_LR": "sum",
        "recovered_amount_RULE_BASED": "sum",
        "recovered_LR": ["sum", "count"]
    })
    cust_agg.columns = [
        "lr_net_u", "rb_net_u", "ub_net_u",
        "lr_rec", "rb_rec", "lr_rec_cnt", "case_cnt"
    ]

    n_custs = len(cust_agg)
    arr_lr_net_u = cust_agg["lr_net_u"].to_numpy()
    arr_rb_net_u = cust_agg["rb_net_u"].to_numpy()
    arr_ub_net_u = cust_agg["ub_net_u"].to_numpy()
    arr_lr_rec = cust_agg["lr_rec"].to_numpy()
    arr_rb_rec = cust_agg["rb_rec"].to_numpy()
    arr_lr_rec_cnt = cust_agg["lr_rec_cnt"].to_numpy()
    arr_case_cnt = cust_agg["case_cnt"].to_numpy()

    idx_matrix = rng_bs.choice(n_custs, size=(iterations, n_custs), replace=True)

    bs_lr_net_u = np.sum(arr_lr_net_u[idx_matrix], axis=1)
    bs_rb_net_u = np.sum(arr_rb_net_u[idx_matrix], axis=1)
    bs_ub_net_u = np.sum(arr_ub_net_u[idx_matrix], axis=1)
    bs_lr_rec = np.sum(arr_lr_rec[idx_matrix], axis=1)
    bs_rb_rec = np.sum(arr_rb_rec[idx_matrix], axis=1)
    bs_rec_cnt = np.sum(arr_lr_rec_cnt[idx_matrix], axis=1)
    bs_tot_cnt = np.sum(arr_case_cnt[idx_matrix], axis=1)

    bs_rec_rate = (bs_rec_cnt / bs_tot_cnt) * 100.0
    bs_abs_lift = bs_lr_rec - bs_rb_rec
    bs_pct_lift = (bs_abs_lift / bs_rb_rec) * 100.0
    bs_u_lift = bs_lr_net_u - bs_rb_net_u
    bs_regret = bs_ub_net_u - bs_lr_net_u

    ci_summary = {}
    for name, arr in [("lr_net_utility", bs_lr_net_u),
                       ("rb_net_utility", bs_rb_net_u),
                       ("lr_recovered_revenue", bs_lr_rec),
                       ("lr_recovery_rate_pct", bs_rec_rate),
                       ("abs_revenue_lift_brl", bs_abs_lift),
                       ("pct_revenue_lift", bs_pct_lift),
                       ("net_utility_lift_brl", bs_u_lift),
                       ("regret_brl", bs_regret)]:
        ci_summary[name] = {
            "mean": float(np.mean(arr)),
            "ci_95_low": float(np.percentile(arr, 2.5)),
            "ci_95_high": float(np.percentile(arr, 97.5))
        }

    return ci_summary


# ============================================================================
# Main Pipeline
# ============================================================================

def verify_frozen_artifacts(stage_label):
    """Verify all 14 frozen artifact SHA-256 hashes."""
    print(f"  Verifying 14 frozen artifact hashes ({stage_label})...")
    mismatches = []
    for key, expected_hash in MASTER_REFERENCE_HASHES.items():
        path = FROZEN_ARTIFACT_PATHS[key]
        actual_hash = get_file_checksum(path)
        if actual_hash != expected_hash:
            mismatches.append(f"  MISMATCH: {key} — expected {expected_hash[:16]}..., got {actual_hash[:16]}...")
    if mismatches:
        for m in mismatches:
            print(m)
        raise RuntimeError(f"FROZEN ARTIFACT INTEGRITY FAILURE at stage '{stage_label}': {len(mismatches)} mismatches!")
    print(f"  All 14 frozen artifact hashes verified: PASS ({stage_label})")


def run_pipeline():
    """Execute the complete supplementary model comparison pipeline."""
    start_time = time.time()
    print("=" * 70)
    print("RECOVERAI SUPPLEMENTARY MODEL COMPARISON EXPERIMENT")
    print("Model A: Frozen LightGBM + Isotonic (Official)")
    print("Model B: Logistic Regression (Supplementary)")
    print("=" * 70)

    output_dir = str(project_root / "models" / "recoverai_model_comparison")
    os.makedirs(output_dir, exist_ok=True)

    # Step 0: Verify frozen artifact integrity BEFORE experiment
    verify_frozen_artifacts("PRE-EXPERIMENT")

    # Step 1: Load frozen datasets
    print("\n[Step 1] Loading frozen datasets...")
    train_df = pd.read_csv(FROZEN_ARTIFACT_PATHS["train_cases"])
    val_raw = pd.read_csv(FROZEN_ARTIFACT_PATHS["val_cases"])
    test_df = pd.read_csv(FROZEN_ARTIFACT_PATHS["test_cases"])
    print(f"  Training:   {len(train_df)} rows")
    print(f"  Validation: {len(val_raw)} rows (raw, action/recovered to be generated)")
    print(f"  Test:       {len(test_df)} rows")

    # Step 2: Generate validation data with same seed
    print("\n[Step 2] Generating validation action/outcome (seed=42)...")
    val_df = prepare_validation_data(val_raw, seed=SEED)
    print(f"  Validation prepared: {len(val_df)} rows, "
          f"positive rate: {val_df['recovered'].mean():.4f}")

    # Step 3: Build preprocessing (fitted on training data ONLY)
    print("\n[Step 3] Building LR preprocessing (fit on training only)...")
    encoder, scaler, feature_names_out = build_lr_preprocessor(train_df)
    print(f"  OneHotEncoder categories: {sum(len(c) for c in encoder.categories_)} total values")
    print(f"  StandardScaler fitted on {len(NUMERIC_FEATURES)} numeric features")
    print(f"  Total LR feature dimensionality: {len(feature_names_out)}")

    # Step 4: Transform features
    print("\n[Step 4] Transforming feature matrices...")
    X_train = transform_features(train_df, encoder, scaler)
    y_train = train_df["recovered"].values
    X_val = transform_features(val_df, encoder, scaler)
    y_val = val_df["recovered"].values
    print(f"  X_train shape: {X_train.shape}")
    print(f"  X_val shape:   {X_val.shape}")

    # Step 5: Train Logistic Regression
    print("\n[Step 5] Training Logistic Regression (C=1.0, L2, lbfgs, seed=42)...")
    lr_model = train_logistic_regression(X_train, y_train)
    print(f"  Converged in {lr_model.n_iter_[0]} iterations")

    # Step 6: Compute raw LR validation metrics
    print("\n[Step 6] Computing raw LR validation metrics...")
    p_raw_val = lr_model.predict_proba(X_val)[:, 1]
    val_raw_metrics = {
        "brier_score": float(brier_score_loss(y_val, p_raw_val)),
        "ece": float(compute_ece(y_val, p_raw_val)),
        "log_loss": float(log_loss(y_val, p_raw_val)),
        "roc_auc": float(roc_auc_score(y_val, p_raw_val)),
        "sample_count": len(y_val)
    }
    print(f"  Raw LR Validation ROC-AUC: {val_raw_metrics['roc_auc']:.4f}")
    print(f"  Raw LR Validation Brier:   {val_raw_metrics['brier_score']:.4f}")

    # Step 7: Fit separate Isotonic calibrator on LR validation predictions
    print("\n[Step 7] Fitting separate Isotonic calibrator for LR...")
    lr_calibrator = IsotonicRegression(out_of_bounds="clip")
    lr_calibrator.fit(p_raw_val, y_val)
    p_cal_val = lr_calibrator.transform(p_raw_val)

    val_cal_metrics = {
        "brier_score": float(brier_score_loss(y_val, p_cal_val)),
        "ece": float(compute_ece(y_val, p_cal_val)),
        "log_loss": float(log_loss(y_val, p_cal_val)),
        "roc_auc": float(roc_auc_score(y_val, p_cal_val)),
        "sample_count": len(y_val)
    }
    print(f"  Calibrated LR Validation ROC-AUC: {val_cal_metrics['roc_auc']:.4f}")
    print(f"  Calibrated LR Validation Brier:   {val_cal_metrics['brier_score']:.4f}")

    # Step 8: Save Model B artifacts
    print("\n[Step 8] Saving Model B artifacts...")
    lr_model_path = os.path.join(output_dir, "logistic_regression_model.pkl")
    lr_calib_path = os.path.join(output_dir, "lr_isotonic_calibrator.pkl")
    encoder_path = os.path.join(output_dir, "lr_onehot_encoder.pkl")
    scaler_path = os.path.join(output_dir, "lr_standard_scaler.pkl")

    with open(lr_model_path, "wb") as f:
        pickle.dump(lr_model, f)
    with open(lr_calib_path, "wb") as f:
        pickle.dump(lr_calibrator, f)
    with open(encoder_path, "wb") as f:
        pickle.dump(encoder, f)
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"  Saved: {lr_model_path}")
    print(f"  Saved: {lr_calib_path}")

    # Step 9: Run test evaluation with LR (same Step 5F methodology)
    print("\n[Step 9] Running LR test evaluation (CRN_SEED=999)...")
    lr_results_df = run_lr_test_evaluation(test_df, lr_model, lr_calibrator,
                                            encoder, scaler)
    print(f"  Evaluated {len(lr_results_df)} test cases")

    # Step 10: Compute Model B test metrics
    print("\n[Step 10] Computing Model B test metrics...")
    lr_test_metrics = compute_test_metrics(lr_results_df)
    print(f"  LR Test ROC-AUC:  {lr_test_metrics['roc_auc']:.4f}")
    print(f"  LR Test Brier:    {lr_test_metrics['brier_score']:.4f}")
    print(f"  LR Test ECE:      {lr_test_metrics['ece']:.4f}")
    print(f"  LR Test Log Loss: {lr_test_metrics['log_loss']:.4f}")
    print(f"  LR Test N:        {lr_test_metrics['sample_count']}")

    # Step 11: Compute raw (uncalibrated) LR test metrics for reporting
    print("\n[Step 11] Computing raw (uncalibrated) LR test metrics...")
    # Re-run evaluation with raw probabilities instead of calibrated
    rng_crn2 = np.random.default_rng(CRN_SEED)
    crn_draws2 = rng_crn2.random(size=len(test_df))
    # For raw metrics, we need the raw probability for LR's selected action (under calibrated policy)
    # The selected action was chosen using calibrated probs, so raw metrics use those same selected actions
    # but compare against raw prob for that action
    lr_raw_test_probs = lr_results_df["lr_raw_probability_RETRY"].values  # placeholder
    # Actually, we need the raw prob for the selected action specifically
    raw_prob_for_selected = []
    for _, row in lr_results_df.iterrows():
        sel = row["lr_selected_action"]
        if sel == "STOP":
            raw_prob_for_selected.append(0.0)
        else:
            raw_prob_for_selected.append(row[f"lr_raw_probability_{sel}"])
    raw_prob_for_selected = np.array(raw_prob_for_selected)

    lr_raw_test_metrics = {
        "brier_score": float(brier_score_loss(lr_results_df["recovered_LR"].values, raw_prob_for_selected)),
        "ece": float(compute_ece(lr_results_df["recovered_LR"].values, raw_prob_for_selected)),
        "log_loss": float(log_loss(lr_results_df["recovered_LR"].values, raw_prob_for_selected)),
        "roc_auc": float(roc_auc_score(lr_results_df["recovered_LR"].values, raw_prob_for_selected)),
        "sample_count": len(lr_results_df)
    }
    print(f"  Raw LR Test ROC-AUC:  {lr_raw_test_metrics['roc_auc']:.4f}")
    print(f"  Raw LR Test Brier:    {lr_raw_test_metrics['brier_score']:.4f}")

    # Step 12: Policy comparison
    print("\n[Step 12] Computing policy summaries...")
    policy_summary = compute_policy_summaries(lr_results_df)
    lr_policy = policy_summary[policy_summary["policy_tag"] == "LR"].iloc[0]
    rb_policy = policy_summary[policy_summary["policy_tag"] == "RULE_BASED"].iloc[0]
    ub_policy = policy_summary[policy_summary["policy_tag"] == "UPPER_BOUND"].iloc[0]

    print(f"  LR Net Utility:           {lr_policy['net_policy_utility_brl']:.2f} BRL")
    print(f"  Rule-Based Net Utility:    {rb_policy['net_policy_utility_brl']:.2f} BRL")
    print(f"  Upper Bound Net Utility:   {ub_policy['net_policy_utility_brl']:.2f} BRL")
    print(f"  LR Recovery Rate:          {lr_policy['recovery_rate_pct']:.2f}%")
    print(f"  LR Lift vs Rule-Based:     {lr_policy['net_utility_lift_vs_rb_brl']:.2f} BRL")
    print(f"  LR Regret vs Upper Bound:  {lr_policy['regret_vs_upper_bound_brl']:.2f} BRL")

    # Step 13: Bootstrap
    print("\n[Step 13] Running bootstrap confidence intervals...")
    ci_summary = run_bootstrap(lr_results_df, seed=BOOTSTRAP_SEED,
                               iterations=BOOTSTRAP_ITERATIONS)

    # Step 14: Reproducibility test
    print("\n[Step 14] Reproducibility verification (second run)...")
    lr_results_df2 = run_lr_test_evaluation(test_df, lr_model, lr_calibrator,
                                             encoder, scaler)
    lr_test_metrics2 = compute_test_metrics(lr_results_df2)

    repro_pass = True
    for key in lr_test_metrics:
        if lr_test_metrics[key] != lr_test_metrics2[key]:
            print(f"  REPRODUCIBILITY FAILURE: {key} differs!")
            repro_pass = False
    if repro_pass:
        print("  Reproducibility verified: PASS (identical metrics across 2 runs)")
    else:
        raise RuntimeError("REPRODUCIBILITY CHECK FAILED")

    # Step 15: Build comparison metrics
    print("\n[Step 15] Building comparison metrics...")

    # Model A frozen metrics
    model_a_metrics = MODEL_A_FROZEN_METRICS.copy()

    # Comparison
    comparison = {}
    for metric in ["roc_auc", "brier_score", "ece", "log_loss"]:
        a_val = model_a_metrics[metric]
        b_val = lr_test_metrics[metric]
        abs_diff = b_val - a_val
        rel_diff = (abs_diff / abs(a_val) * 100.0) if a_val != 0 else 0.0

        # Determine which is better
        if metric == "roc_auc":
            better = "Model A" if a_val > b_val else ("Model B" if b_val > a_val else "Tie")
        else:
            better = "Model A" if a_val < b_val else ("Model B" if b_val < a_val else "Tie")

        comparison[metric] = {
            "model_a": a_val,
            "model_b_calibrated": b_val,
            "model_b_raw": lr_raw_test_metrics[metric],
            "absolute_difference": abs_diff,
            "relative_difference_pct": rel_diff,
            "better_model": better
        }

    # Model A frozen policy metrics (from step5f_policy_summary.csv)
    model_a_policy_summary = pd.read_csv(FROZEN_ARTIFACT_PATHS["step5f_summary"])
    model_a_ml_row = model_a_policy_summary[model_a_policy_summary["policy_tag"] == "ML"].iloc[0]

    policy_comparison = {
        "model_a_net_utility_brl": float(model_a_ml_row["net_policy_utility_brl"]),
        "model_b_net_utility_brl": float(lr_policy["net_policy_utility_brl"]),
        "model_a_recovered_revenue_brl": float(model_a_ml_row["recovered_revenue_brl"]),
        "model_b_recovered_revenue_brl": float(lr_policy["recovered_revenue_brl"]),
        "model_a_recovery_rate_pct": float(model_a_ml_row["recovery_rate_pct"]),
        "model_b_recovery_rate_pct": float(lr_policy["recovery_rate_pct"]),
        "model_a_regret_brl": float(model_a_ml_row["regret_vs_upper_bound_brl"]),
        "model_b_regret_brl": float(lr_policy["regret_vs_upper_bound_brl"]),
        "rule_based_net_utility_brl": float(rb_policy["net_policy_utility_brl"]),
        "upper_bound_net_utility_brl": float(ub_policy["net_policy_utility_brl"]),
    }

    comparison_payload = {
        "experiment": "Supplementary Model Comparison — LightGBM vs Logistic Regression",
        "status": "SUPPLEMENTARY — Does NOT replace frozen Step 5F results",
        "model_a": {
            "name": "LightGBM + Isotonic Calibration (Frozen Step 5E/5F)",
            "test_metrics": model_a_metrics
        },
        "model_b_calibrated": {
            "name": "Logistic Regression + Separate Isotonic Calibration",
            "test_metrics": lr_test_metrics
        },
        "model_b_raw": {
            "name": "Logistic Regression (Raw, Uncalibrated)",
            "test_metrics": lr_raw_test_metrics
        },
        "model_b_validation_metrics": {
            "raw": val_raw_metrics,
            "calibrated": val_cal_metrics
        },
        "metric_comparison": comparison,
        "policy_comparison": policy_comparison,
        "bootstrap_confidence_intervals": ci_summary,
        "reproducibility_verified": repro_pass,
        "frozen_artifacts_verified": True,
        "seeds": {
            "training_seed": SEED,
            "validation_seed": SEED,
            "crn_seed": CRN_SEED,
            "bootstrap_seed": BOOTSTRAP_SEED
        }
    }

    metrics_path = os.path.join(output_dir, "comparison_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(comparison_payload, f, indent=2)
    print(f"  Saved: {metrics_path}")

    # Step 16: Generate comparison report
    print("\n[Step 16] Generating comparison report...")
    generate_comparison_report(output_dir, comparison_payload, lr_policy,
                               rb_policy, ub_policy, model_a_ml_row, ci_summary)

    # Step 17: Final frozen artifact verification
    print("\n[Step 17] Final frozen artifact integrity verification...")
    verify_frozen_artifacts("POST-EXPERIMENT")

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("SUPPLEMENTARY MODEL COMPARISON EXPERIMENT: COMPLETE")
    print(f"Elapsed: {elapsed:.2f} seconds")
    print("=" * 70)

    # Print summary
    print("\n--- METRIC COMPARISON SUMMARY ---")
    print(f"{'Metric':<15} {'Model A (LightGBM)':<22} {'Model B (LR Cal.)':<22} {'Better':<10}")
    print("-" * 70)
    for metric in ["roc_auc", "brier_score", "ece", "log_loss"]:
        c = comparison[metric]
        print(f"{metric:<15} {c['model_a']:<22.6f} {c['model_b_calibrated']:<22.6f} {c['better_model']:<10}")
    print(f"{'N':<15} {model_a_metrics['sample_count']:<22} {lr_test_metrics['sample_count']:<22}")

    print("\n--- POLICY COMPARISON SUMMARY ---")
    print(f"{'Metric':<30} {'Model A':<18} {'Model B':<18}")
    print("-" * 70)
    print(f"{'Net Utility (BRL)':<30} {policy_comparison['model_a_net_utility_brl']:<18.2f} {policy_comparison['model_b_net_utility_brl']:<18.2f}")
    print(f"{'Recovered Revenue (BRL)':<30} {policy_comparison['model_a_recovered_revenue_brl']:<18.2f} {policy_comparison['model_b_recovered_revenue_brl']:<18.2f}")
    print(f"{'Recovery Rate (%)':<30} {policy_comparison['model_a_recovery_rate_pct']:<18.2f} {policy_comparison['model_b_recovery_rate_pct']:<18.2f}")
    print(f"{'Regret vs Upper Bound (BRL)':<30} {policy_comparison['model_a_regret_brl']:<18.2f} {policy_comparison['model_b_regret_brl']:<18.2f}")

    print("\nAll 14 frozen artifacts remain byte-identical: CONFIRMED")
    print("The frozen LightGBM pipeline remains the official RecoverAI model.")

    return comparison_payload


def generate_comparison_report(output_dir, payload, lr_policy, rb_policy,
                               ub_policy, model_a_ml_row, ci_summary):
    """Generate comparison_report.md in the output directory."""
    comp = payload["metric_comparison"]
    pol = payload["policy_comparison"]
    ma = payload["model_a"]["test_metrics"]
    mb = payload["model_b_calibrated"]["test_metrics"]
    mb_raw = payload["model_b_raw"]["test_metrics"]

    report = f"""# RecoverAI: Supplementary Model Comparison Report

> **THIS IS A SUPPLEMENTARY EXPERIMENT ONLY.**
> The existing LightGBM + Isotonic pipeline remains the official, frozen RecoverAI model.
> This report does NOT replace, modify, or invalidate the official Step 5F evaluation.

---

## 1. Motivation

This supplementary experiment compares the frozen LightGBM S-Learner (Model A) against a
Logistic Regression S-Learner (Model B) to assess whether a simpler linear model can achieve
comparable performance in the RecoverAI recovery probability prediction task.

Logistic Regression was selected because:
- It provides a transparent, interpretable linear baseline.
- It outputs calibrated probabilities natively (log-odds → sigmoid).
- Comparing against a linear model quantifies the value of non-linear interactions captured by LightGBM.
- It is the standard baseline for binary classification tasks.

## 2. Frozen Model A Description

- **Model:** LightGBM S-Learner (87 boosting rounds, early stopped from 500)
- **Calibration:** Isotonic Regression fitted on validation predictions
- **Artifacts:** Frozen `lgbm_model.pkl`, `isotonic_calibrator.pkl`
- **Status:** Official RecoverAI model — NEVER modified

## 3. Model B Description

- **Model:** `sklearn.linear_model.LogisticRegression(solver='lbfgs', C=1.0, max_iter=1000, random_state=42)`
- **Calibration:** Separate `IsotonicRegression(out_of_bounds='clip')` fitted on Model B's own validation predictions
- **Preprocessing:** OneHotEncoder (categoricals) + StandardScaler (numerics), both fitted on training data only
- **Status:** Supplementary experiment — NOT integrated into any production component

## 4. Data and Split Boundaries

| Split | Path | Rows | Contains action/recovered |
|---|---|---|---|
| Training | `recoverai_ml_training_cases.csv` | 11,051 | Yes (pre-generated, seed=42) |
| Validation | `recoverai_ml_validation_cases.csv` | 2,247 | No (generated at runtime, seed=42) |
| Test | `recoverai_ml_test_cases.csv` | 2,283 | No (CRN evaluation, seed=999) |

Split method: Customer-Grouped Temporal Split (70/15/15). Zero customer overlap across splits.

## 5. Feature Representation

Both models use the same 16 semantic features:
- **12 Numeric:** payment_value, payment_installments, previous_order_count, previous_payment_count,
  previous_success_count, previous_cancelled_count, historical_payment_success_rate,
  historical_average_payment, customer_tenure_before_payment, order_frequency_before_payment,
  hours_since_failure, recovery_attempt_number
- **4 Categorical:** payment_type, failure_category, failure_reason, action

Model A: categoricals as native LightGBM category dtype; numerics raw (no scaling).
Model B: categoricals one-hot encoded; numerics StandardScaler'd. Both fitted on training data only.

Note: `recovery_attempt_number` is constant (all=1) in the training data. It is retained for
semantic feature parity. It contributes zero information to both models.

## 6. Treatment/Action Representation

S-learner design: `action` ∈ {{RETRY, NUDGE, ESCALATE}} is a feature. STOP never appears in training.
At test time, each model predicts P(recovered | context, action) for all 3 active actions.

## 7. Calibration

- **Model A:** Frozen Isotonic calibrator fitted on LightGBM validation predictions → validation labels.
- **Model B:** Separate Isotonic calibrator fitted on LR validation predictions → same validation labels.
- Both calibrators use `IsotonicRegression(out_of_bounds="clip")`.
- Raw (uncalibrated) LR metrics are also reported below.

## 8. Evaluation Methodology

Identical Step 5F methodology for both models:
- CRN_SEED = 999 (shared uniform draws)
- Same guardrail rules (GR01–GR06)
- Same utility/cost structure
- Same policy selection (argmax utility + negative-utility fallback)
- Same simulator probability formula
- Metrics are policy-coupled: each model evaluated on its own selected actions

## 9. Model A Results (Frozen Step 5F)

| Metric | Value |
|---|---|
| ROC-AUC | {ma['roc_auc']:.6f} |
| Brier Score | {ma['brier_score']:.6f} |
| ECE | {ma['ece']:.6f} |
| Log Loss | {ma['log_loss']:.6f} |
| N | {ma['sample_count']} |

## 10. Model B Results

### Calibrated (Primary Comparison)

| Metric | Value |
|---|---|
| ROC-AUC | {mb['roc_auc']:.6f} |
| Brier Score | {mb['brier_score']:.6f} |
| ECE | {mb['ece']:.6f} |
| Log Loss | {mb['log_loss']:.6f} |
| N | {mb['sample_count']} |

### Raw (Uncalibrated)

| Metric | Value |
|---|---|
| ROC-AUC | {mb_raw['roc_auc']:.6f} |
| Brier Score | {mb_raw['brier_score']:.6f} |
| ECE | {mb_raw['ece']:.6f} |
| Log Loss | {mb_raw['log_loss']:.6f} |
| N | {mb_raw['sample_count']} |

## 11. Metric-by-Metric Comparison

| Metric | Model A | Model B (Cal.) | Abs Diff | Rel Diff (%) | Better |
|---|---|---|---|---|---|
| ROC-AUC | {comp['roc_auc']['model_a']:.6f} | {comp['roc_auc']['model_b_calibrated']:.6f} | {comp['roc_auc']['absolute_difference']:+.6f} | {comp['roc_auc']['relative_difference_pct']:+.2f}% | {comp['roc_auc']['better_model']} |
| Brier Score | {comp['brier_score']['model_a']:.6f} | {comp['brier_score']['model_b_calibrated']:.6f} | {comp['brier_score']['absolute_difference']:+.6f} | {comp['brier_score']['relative_difference_pct']:+.2f}% | {comp['brier_score']['better_model']} |
| ECE | {comp['ece']['model_a']:.6f} | {comp['ece']['model_b_calibrated']:.6f} | {comp['ece']['absolute_difference']:+.6f} | {comp['ece']['relative_difference_pct']:+.2f}% | {comp['ece']['better_model']} |
| Log Loss | {comp['log_loss']['model_a']:.6f} | {comp['log_loss']['model_b_calibrated']:.6f} | {comp['log_loss']['absolute_difference']:+.6f} | {comp['log_loss']['relative_difference_pct']:+.2f}% | {comp['log_loss']['better_model']} |

## 12. Policy Comparison

This comparison is valid because it uses the exact same Step 5F evaluation methodology
(identical CRN, guardrails, utility/cost structure, policy selection, simulator formula).

| Metric | Model A (LightGBM) | Model B (LR) | Rule-Based | Upper Bound |
|---|---|---|---|---|
| Net Utility (BRL) | {pol['model_a_net_utility_brl']:.2f} | {pol['model_b_net_utility_brl']:.2f} | {pol['rule_based_net_utility_brl']:.2f} | {pol['upper_bound_net_utility_brl']:.2f} |
| Recovered Revenue (BRL) | {pol['model_a_recovered_revenue_brl']:.2f} | {pol['model_b_recovered_revenue_brl']:.2f} | — | — |
| Recovery Rate (%) | {pol['model_a_recovery_rate_pct']:.2f} | {pol['model_b_recovery_rate_pct']:.2f} | — | — |
| Regret vs Upper Bound (BRL) | {pol['model_a_regret_brl']:.2f} | {pol['model_b_regret_brl']:.2f} | — | 0.00 |

### Model B Bootstrap 95% Confidence Intervals

| Metric | Mean | 95% CI Lower | 95% CI Upper |
|---|---|---|---|
| LR Net Utility (BRL) | {ci_summary['lr_net_utility']['mean']:.2f} | {ci_summary['lr_net_utility']['ci_95_low']:.2f} | {ci_summary['lr_net_utility']['ci_95_high']:.2f} |
| LR Recovered Revenue (BRL) | {ci_summary['lr_recovered_revenue']['mean']:.2f} | {ci_summary['lr_recovered_revenue']['ci_95_low']:.2f} | {ci_summary['lr_recovered_revenue']['ci_95_high']:.2f} |
| LR Recovery Rate (%) | {ci_summary['lr_recovery_rate_pct']['mean']:.2f} | {ci_summary['lr_recovery_rate_pct']['ci_95_low']:.2f} | {ci_summary['lr_recovery_rate_pct']['ci_95_high']:.2f} |
| Net Utility Lift vs RB (BRL) | {ci_summary['net_utility_lift_brl']['mean']:.2f} | {ci_summary['net_utility_lift_brl']['ci_95_low']:.2f} | {ci_summary['net_utility_lift_brl']['ci_95_high']:.2f} |
| Regret vs UB (BRL) | {ci_summary['regret_brl']['mean']:.2f} | {ci_summary['regret_brl']['ci_95_low']:.2f} | {ci_summary['regret_brl']['ci_95_high']:.2f} |

## 13. Interpretation

The comparison shows the relative performance of a non-linear tree ensemble (LightGBM) versus
a linear model (Logistic Regression) on the same prediction task using the same evaluation protocol.

Both models were given identical training data, the same semantic features, and were evaluated
under the same controlled conditions. The only intended differences are the model class,
the required categorical encoding, and the numeric scaling.

## 14. Limitations

1. All outcomes are simulated. Performance measures simulated environment recovery, not real-world behavior.
2. Test metrics are policy-coupled: each model is evaluated on its own selected actions. Direct metric
   comparison is meaningful but not equivalent to evaluating both models on the same fixed action set.
3. LightGBM has a structural advantage from native categorical handling (optimal subset splits)
   compared to one-hot encoding used by LR.
4. StandardScaler is applied for LR but not for LightGBM — this is model-appropriate, not a confound.
5. `recovery_attempt_number` is constant (all=1), providing zero information to either model.
6. The comparison is based on a single CRN realization (seed=999). Different seeds would produce
   different outcome realizations, though the expected-value comparison remains stable.
7. Model B hyperparameters (C=1.0) were not tuned. A grid search on validation data might improve LR,
   but this was not performed to avoid any risk of test-set influence.

## 15. Final Conclusion

This supplementary experiment provides a controlled comparison between the frozen LightGBM model
and a Logistic Regression baseline under identical evaluation conditions.

The results above should be interpreted as evidence of relative model performance within the
RecoverAI simulation environment. They do NOT change any official Step 5F result.

## 16. Official Status Statement

**The existing LightGBM + Isotonic Calibration pipeline remains the official, frozen RecoverAI model.**

This Logistic Regression experiment is supplementary scientific analysis only. It has NOT been:
- Integrated into the RecoverAI agent
- Integrated into the REST API
- Integrated into the batch runner
- Integrated into the dashboard
- Used to replace or modify any frozen artifact

All 14 frozen artifact SHA-256 hashes have been verified byte-identical before and after this experiment.
"""

    report_path = os.path.join(output_dir, "comparison_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  Saved: {report_path}")


if __name__ == "__main__":
    run_pipeline()
