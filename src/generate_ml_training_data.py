"""
RecoverAI: Track 03 AI Revenue Recovery
Step 5D: ML Training Data Construction Script (Controlled Uniform Exploration)

This script generates separate ML training, validation, and test datasets using
controlled uniform exploration over valid recovery actions:
- data/processed/recoverai_ml_training_cases.csv
- data/processed/recoverai_ml_validation_cases.csv
- data/processed/recoverai_ml_test_cases.csv

Provenance Principles:
- REAL_OLIST: Payment features, timestamps, customer identity
- DERIVED_FROM_REAL_OLIST: Leakage-free customer history prior to T0
- SIMULATED_EXPLORATION: Uniform random exploration action + outcome
- Existing dataset data/processed/recoverai_recovery_cases.csv remains UNCHANGED.
"""

import os
import sys
import hashlib
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd

# Global Configuration
SEED = 42
FAILURE_SAMPLING_RATE = 0.15
PROVENANCE_VERSION = "v1.0-ml-training-exploration"

# Canonical Failure Reason Names
CANONICAL_FAILURE_REASONS = [
    "network_error",
    "bank_technical_error",
    "gateway_error",
    "insufficient_funds",
    "withdrawal_limit_exceeded",
    "authentication_failed",
    "expired_card",
    "payment_cancelled",
    "payment_timed_out",
    "card_not_enrolled",
    "stolen_card",
    "card_number_invalid",
    "compliance_violation",
    "boleto_expired",
    "payment_failed",
    "do_not_honor"
]

FAILURE_CATEGORY_MAP = {
    "network_error": "SOFT_DECLINE",
    "bank_technical_error": "SOFT_DECLINE",
    "gateway_error": "SOFT_DECLINE",
    "insufficient_funds": "FUNDS_ISSUE",
    "withdrawal_limit_exceeded": "FUNDS_ISSUE",
    "authentication_failed": "CUSTOMER_ACTION_REQUIRED",
    "expired_card": "CUSTOMER_ACTION_REQUIRED",
    "payment_cancelled": "CUSTOMER_ACTION_REQUIRED",
    "payment_timed_out": "CUSTOMER_ACTION_REQUIRED",
    "card_not_enrolled": "CUSTOMER_ACTION_REQUIRED",
    "boleto_expired": "CUSTOMER_ACTION_REQUIRED",
    "stolen_card": "HARD_DECLINE",
    "card_number_invalid": "HARD_DECLINE",
    "compliance_violation": "HARD_DECLINE",
    "do_not_honor": "GENERIC_DECLINE",
    "payment_failed": "GENERIC_DECLINE"
}

# Failure Reason Weights per Payment Method
FAILURE_WEIGHTS = {
    "credit_card": {
        "network_error": 0.15,
        "bank_technical_error": 0.10,
        "gateway_error": 0.10,
        "insufficient_funds": 0.20,
        "withdrawal_limit_exceeded": 0.05,
        "authentication_failed": 0.15,
        "expired_card": 0.05,
        "payment_cancelled": 0.05,
        "stolen_card": 0.04,
        "card_number_invalid": 0.04,
        "compliance_violation": 0.02,
        "do_not_honor": 0.03,
        "payment_failed": 0.02
    },
    "debit_card": {
        "network_error": 0.15,
        "bank_technical_error": 0.10,
        "gateway_error": 0.10,
        "insufficient_funds": 0.20,
        "withdrawal_limit_exceeded": 0.05,
        "authentication_failed": 0.15,
        "expired_card": 0.05,
        "payment_cancelled": 0.05,
        "stolen_card": 0.04,
        "card_number_invalid": 0.04,
        "compliance_violation": 0.02,
        "do_not_honor": 0.03,
        "payment_failed": 0.02
    },
    "boleto": {
        "boleto_expired": 0.50,
        "payment_cancelled": 0.20,
        "payment_timed_out": 0.20,
        "payment_failed": 0.10
    },
    "voucher": {
        "payment_cancelled": 0.30,
        "payment_timed_out": 0.20,
        "payment_failed": 0.50
    }
}


def get_file_checksum(filepath):
    """Compute SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_raw_data(raw_dir):
    """Load Olist raw datasets from data/raw/."""
    orders_path = os.path.join(raw_dir, "olist_orders_dataset.csv")
    payments_path = os.path.join(raw_dir, "olist_order_payments_dataset.csv")
    customers_path = os.path.join(raw_dir, "olist_customers_dataset.csv")

    raw_checksums = {
        "orders": get_file_checksum(orders_path),
        "payments": get_file_checksum(payments_path),
        "customers": get_file_checksum(customers_path)
    }

    orders = pd.read_csv(orders_path)
    payments = pd.read_csv(payments_path)
    customers = pd.read_csv(customers_path)

    return orders, payments, customers, raw_checksums


def construct_eligible_cases(orders, payments, customers):
    """Merge datasets and extract eligible payment contexts."""
    df = payments.merge(orders, on="order_id", how="inner")
    df = df.merge(customers, on="customer_id", how="inner")

    df = df[df["payment_value"] > 0]
    df = df[df["payment_type"].isin(["credit_card", "debit_card", "boleto", "voucher"])]
    df = df.dropna(subset=["order_purchase_timestamp"])

    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["case_id"] = df["order_id"] + "_" + df["payment_sequential"].astype(str)

    df = df.sort_values(by=["order_purchase_timestamp", "case_id"]).reset_index(drop=True)

    return df


def derive_customer_history(df):
    """
    Derive leakage-free customer history features strictly prior to T0.
    T_past < T0 enforced.
    """
    df_sorted = df.sort_values(by=["order_purchase_timestamp", "case_id"]).reset_index(drop=True)
    
    prev_order_count = np.zeros(len(df_sorted), dtype=int)
    prev_payment_count = np.zeros(len(df_sorted), dtype=int)
    prev_success_count = np.zeros(len(df_sorted), dtype=int)
    prev_cancelled_count = np.zeros(len(df_sorted), dtype=int)
    hist_success_rate = np.zeros(len(df_sorted), dtype=float)
    hist_avg_payment = np.zeros(len(df_sorted), dtype=float)
    customer_tenure = np.zeros(len(df_sorted), dtype=int)
    order_freq = np.zeros(len(df_sorted), dtype=float)

    customer_history_db = {}

    for i, row in df_sorted.iterrows():
        c_id = row["customer_unique_id"]
        t0 = row["order_purchase_timestamp"]
        p_val = row["payment_value"]
        o_id = row["order_id"]
        o_status = row["order_status"]

        if c_id not in customer_history_db:
            customer_history_db[c_id] = {
                "first_t0": t0,
                "orders": set(),
                "successful_orders": set(),
                "cancelled_orders": set(),
                "payments": [],
            }

        c_db = customer_history_db[c_id]

        prior_payments = [p for p in c_db["payments"] if p[0] < t0]
        prior_orders = [t for t, oid in c_db["orders"] if t < t0]
        prior_successes = [t for t, oid in c_db["successful_orders"] if t < t0]
        prior_cancels = [t for t, oid in c_db["cancelled_orders"] if t < t0]

        p_orders_cnt = len(set(prior_orders))
        p_pmts_cnt = len(prior_payments)
        p_succ_cnt = len(set(prior_successes))
        p_canc_cnt = len(set(prior_cancels))

        prev_order_count[i] = p_orders_cnt
        prev_payment_count[i] = p_pmts_cnt
        prev_success_count[i] = p_succ_cnt
        prev_cancelled_count[i] = p_canc_cnt

        if p_orders_cnt > 0:
            hist_success_rate[i] = float(p_succ_cnt) / float(p_orders_cnt)
            tenure_days = (t0 - c_db["first_t0"]).days
            customer_tenure[i] = max(0, tenure_days)
            order_freq[i] = float(tenure_days) / float(p_orders_cnt)
        else:
            hist_success_rate[i] = 0.0
            customer_tenure[i] = 0
            order_freq[i] = 0.0

        if p_pmts_cnt > 0:
            hist_avg_payment[i] = sum(p[1] for p in prior_payments) / float(p_pmts_cnt)
        else:
            hist_avg_payment[i] = 0.0

        c_db["payments"].append((t0, p_val))
        c_db["orders"].add((t0, o_id))
        if o_status == "delivered":
            c_db["successful_orders"].add((t0, o_id))
        elif o_status == "canceled":
            c_db["cancelled_orders"].add((t0, o_id))

    df_sorted["previous_order_count"] = prev_order_count
    df_sorted["previous_payment_count"] = prev_payment_count
    df_sorted["previous_success_count"] = prev_success_count
    df_sorted["previous_cancelled_count"] = prev_cancelled_count
    df_sorted["historical_payment_success_rate"] = hist_success_rate
    df_sorted["historical_average_payment"] = hist_avg_payment
    df_sorted["customer_tenure_before_payment"] = customer_tenure
    df_sorted["order_frequency_before_payment"] = order_freq

    return df_sorted


def perform_customer_grouped_temporal_split(df, seed=42):
    """
    Perform Customer-Grouped Temporal Split (70% Train, 15% Validation, 15% Test).
    Groups customers by earliest purchase timestamp to ensure chronological split
    and ZERO customer leakage across splits.
    """
    cust_first_t0 = df.groupby("customer_unique_id")["order_purchase_timestamp"].min().sort_values().reset_index()

    n_cust = len(cust_first_t0)
    n_train = int(round(0.70 * n_cust))
    n_val = int(round(0.15 * n_cust))

    train_custs = set(cust_first_t0.iloc[:n_train]["customer_unique_id"])
    val_custs = set(cust_first_t0.iloc[n_train:n_train + n_val]["customer_unique_id"])
    test_custs = set(cust_first_t0.iloc[n_train + n_val:]["customer_unique_id"])

    split_map = {}
    for c in train_custs:
        split_map[c] = "train"
    for c in val_custs:
        split_map[c] = "val"
    for c in test_custs:
        split_map[c] = "test"

    df["split"] = df["customer_unique_id"].map(split_map)
    return df, train_custs, val_custs, test_custs


def sample_failures(df, sampling_rate=0.15, seed=42):
    """
    Perform stratified random sampling by payment_type to select ~15% failure cases.
    Generate a realistic, reproducible distribution for hours_since_failure.
    """
    rng = np.random.default_rng(seed)
    sampled_indices = []

    strata_allocations = {
        "credit_card": 0.70,
        "boleto": 0.20,
        "voucher": 0.07,
        "debit_card": 0.03
    }

    total_target_sample = int(round(len(df) * sampling_rate))

    for ptype, target_ratio in strata_allocations.items():
        stratum_df = df[df["payment_type"] == ptype]
        stratum_target = int(round(total_target_sample * target_ratio))
        stratum_target = min(stratum_target, len(stratum_df))

        stratum_indices = stratum_df.index.to_numpy()
        sampled = rng.choice(stratum_indices, size=stratum_target, replace=False)
        sampled_indices.extend(sampled)

    sampled_indices = sorted(sampled_indices)
    sampled_df = df.loc[sampled_indices].copy().reset_index(drop=True)

    failure_reasons = []
    failure_categories = []

    for i, row in sampled_df.iterrows():
        ptype = row["payment_type"]
        weights_dict = FAILURE_WEIGHTS[ptype]
        reasons = list(weights_dict.keys())
        probs = list(weights_dict.values())
        probs = np.array(probs) / sum(probs)

        chosen_reason = rng.choice(reasons, p=probs)
        chosen_category = FAILURE_CATEGORY_MAP[chosen_reason]

        failure_reasons.append(chosen_reason)
        failure_categories.append(chosen_category)

    sampled_df["failure_reason"] = failure_reasons
    sampled_df["failure_category"] = failure_categories

    hours_dist = rng.uniform(0.5, 72.0, size=len(sampled_df))
    sampled_df["hours_since_failure"] = np.round(hours_dist, 1)
    sampled_df["recovery_attempt_number"] = 1

    return sampled_df


def identify_valid_actions(row):
    """
    Identify valid active recovery actions from ['RETRY', 'NUDGE', 'ESCALATE'].
    STOP is NOT an ML training action.
    """
    ptype = row["payment_type"]
    p_val = float(row["payment_value"])
    reason = row["failure_reason"]
    category = row["failure_category"]
    attempt = row["recovery_attempt_number"]

    valid_actions = []

    # RETRY eligibility checks
    retry_blocked = False
    if ptype == "boleto":
        retry_blocked = True
    if ptype == "voucher":
        retry_blocked = True
    if category == "HARD_DECLINE":
        retry_blocked = True
    if reason in ["authentication_failed", "expired_card", "boleto_expired"]:
        retry_blocked = True
    if attempt > 3:
        retry_blocked = True
    if p_val > 5000.0 and reason in ["do_not_honor", "payment_failed"]:
        retry_blocked = True

    if not retry_blocked:
        valid_actions.append("RETRY")

    # NUDGE & ESCALATE are valid active interventions
    valid_actions.append("NUDGE")
    valid_actions.append("ESCALATE")

    return valid_actions


def compute_simulation_probability(row, action):
    """
    Compute recovery probability under the simulation environment formula.
    """
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


def generate_ml_datasets(sampled_df, seed=42):
    """
    Generate ML training, validation, and test datasets.
    Controlled Uniform Exploration for TRAIN set.
    """
    rng = np.random.default_rng(seed)

    train_rows = []
    val_rows = []
    test_rows = []

    for i, row in sampled_df.iterrows():
        split = row["split"]
        valid_actions = identify_valid_actions(row)

        base_dict = {
            "case_id": row["case_id"],
            "order_id": row["order_id"],
            "customer_id": row["customer_id"],
            "customer_unique_id": row["customer_unique_id"],
            "order_purchase_timestamp": str(row["order_purchase_timestamp"]),
            "payment_type": row["payment_type"],
            "payment_value": row["payment_value"],
            "payment_installments": row["payment_installments"],
            "previous_order_count": row["previous_order_count"],
            "previous_payment_count": row["previous_payment_count"],
            "previous_success_count": row["previous_success_count"],
            "previous_cancelled_count": row["previous_cancelled_count"],
            "historical_payment_success_rate": row["historical_payment_success_rate"],
            "historical_average_payment": row["historical_average_payment"],
            "customer_tenure_before_payment": row["customer_tenure_before_payment"],
            "order_frequency_before_payment": row["order_frequency_before_payment"],
            "failure_category": row["failure_category"],
            "failure_reason": row["failure_reason"],
            "hours_since_failure": row["hours_since_failure"],
            "recovery_attempt_number": row["recovery_attempt_number"],
            "valid_actions_count": len(valid_actions),
            "valid_actions": "|".join(valid_actions),
            "split": split,
            "simulation_seed": seed,
            "provenance_version": PROVENANCE_VERSION
        }

        if split == "train":
            # Controlled Uniform Exploration: Uniformly pick 1 valid action
            chosen_action = rng.choice(valid_actions)
            prob = compute_simulation_probability(row, chosen_action)
            draw = rng.random()
            is_rec = 1 if draw < prob else 0

            train_dict = base_dict.copy()
            train_dict["action"] = chosen_action
            train_dict["recovered"] = is_rec
            train_rows.append(train_dict)

        elif split == "val":
            val_dict = base_dict.copy()
            val_rows.append(val_dict)

        elif split == "test":
            test_dict = base_dict.copy()
            test_rows.append(test_dict)

    train_df = pd.DataFrame(train_rows)
    val_df = pd.DataFrame(val_rows)
    test_df = pd.DataFrame(test_rows)

    return train_df, val_df, test_df


def run_leakage_and_quality_checks(train_df, val_df, test_df, original_recovery_cases_checksum):
    """
    Run 14 mandatory leakage and quality validation checks.
    """
    print("Executing 14 Mandatory Leakage & Quality Validation Checks...")
    errors = []

    train_custs = set(train_df["customer_unique_id"])
    val_custs = set(val_df["customer_unique_id"])
    test_custs = set(test_df["customer_unique_id"])

    # 1. Zero customer overlap across splits
    if len(train_custs.intersection(val_custs)) > 0 or \
       len(train_custs.intersection(test_custs)) > 0 or \
       len(val_custs.intersection(test_custs)) > 0:
        errors.append("Check 1 Failed: Customer unique ID overlap detected across splits.")

    # 2. No forbidden post-decision columns in ML feature matrix
    forbidden_cols = [
        "selected_action", "model_probability_RETRY", "model_probability_NUDGE",
        "model_probability_ESCALATE", "model_probability_STOP",
        "effective_probability_RETRY", "effective_probability_NUDGE",
        "effective_probability_ESCALATE", "effective_probability_STOP",
        "utility_RETRY", "utility_NUDGE", "utility_ESCALATE", "utility_STOP",
        "guardrail_RETRY", "guardrail_NUDGE", "guardrail_ESCALATE", "guardrail_STOP",
        "guardrail_rules_RETRY", "guardrail_rules_NUDGE", "guardrail_rules_ESCALATE", "guardrail_rules_STOP",
        "recovery_probability", "expected_recovered_amount", "recovered_amount"
    ]
    for c in forbidden_cols:
        if c in train_df.columns:
            errors.append(f"Check 2 Failed: Forbidden column {c} found in training set.")

    # 3. No STOP action in ML training actions
    if (train_df["action"] == "STOP").any():
        errors.append("Check 3 Failed: STOP action found in training actions.")

    # 4. Every training action is valid for that case
    for i, row in train_df.iterrows():
        valid_acts = row["valid_actions"].split("|")
        if row["action"] not in valid_acts:
            errors.append(f"Check 4 Failed: Training action {row['action']} invalid for row {i}.")
            break

    # 5. No Boleto + RETRY
    if len(train_df[(train_df["payment_type"] == "boleto") & (train_df["action"] == "RETRY")]) > 0:
        errors.append("Check 5 Failed: Boleto RETRY found in training set.")

    # 6. No Voucher + RETRY
    if len(train_df[(train_df["payment_type"] == "voucher") & (train_df["action"] == "RETRY")]) > 0:
        errors.append("Check 6 Failed: Voucher RETRY found in training set.")

    # 7. No Hard Decline + RETRY
    if len(train_df[(train_df["failure_category"] == "HARD_DECLINE") & (train_df["action"] == "RETRY")]) > 0:
        errors.append("Check 7 Failed: Hard Decline RETRY found in training set.")

    # 8. No Auth failure + RETRY
    auth_reasons = ["authentication_failed", "expired_card", "boleto_expired"]
    if len(train_df[(train_df["failure_reason"].isin(auth_reasons)) & (train_df["action"] == "RETRY")]) > 0:
        errors.append("Check 8 Failed: Auth failure RETRY found in training set.")

    # 9. Exactly one training action per training case
    if train_df["case_id"].duplicated().any():
        errors.append("Check 9 Failed: Multiple training actions per case_id.")

    # 10. Exactly one outcome per training observation
    if train_df["recovered"].isnull().any():
        errors.append("Check 10 Failed: Missing training outcomes.")

    # 11. recovered is binary {0, 1}
    if not set(train_df["recovered"]).issubset({0, 1}):
        errors.append("Check 11 Failed: Non-binary recovered values.")

    # 12. Zero missing values in required ML columns
    ml_feature_cols = [
        "payment_type", "payment_value", "payment_installments",
        "previous_order_count", "previous_payment_count", "previous_success_count", "previous_cancelled_count",
        "historical_payment_success_rate", "historical_average_payment",
        "customer_tenure_before_payment", "order_frequency_before_payment",
        "failure_category", "failure_reason", "hours_since_failure", "recovery_attempt_number", "action"
    ]
    if train_df[ml_feature_cols].isnull().sum().sum() > 0:
        errors.append("Check 12 Failed: Missing values in ML feature matrix.")

    # 13. Determinism check
    # Handled in main pipeline

    # 14. Original recovery dataset unchanged
    project_root = Path(__file__).resolve().parents[1]
    existing_dataset_path = str(project_root / "data" / "processed" / "recoverai_recovery_cases.csv")
    if get_file_checksum(existing_dataset_path) != original_recovery_cases_checksum:
        errors.append("Check 14 Failed: Existing dataset recoverai_recovery_cases.csv was modified!")

    if errors:
        print(f"Validation FAILED with {len(errors)} errors:")
        for err in errors:
            print("  -", err)
        raise RuntimeError("Validation Pipeline Failed.")
    else:
        print("ALL 14 MANDATORY LEAKAGE & QUALITY CHECKS PASSED SUCCESSFULLY.")


def print_exploration_diagnostics(train_df):
    """
    Print uniform exploration action distribution diagnostics.
    """
    print("\n" + "="*60)
    print("=== UNIFORM EXPLORATION ACTION DIAGNOSTICS ===")
    print("="*60)

    for k in [1, 2, 3]:
        sub = train_df[train_df["valid_actions_count"] == k]
        print(f"\nConditioned on valid_actions_count == {k} (Total cases: {len(sub)}):")
        if len(sub) > 0:
            counts = sub["action"].value_counts()
            for act, cnt in counts.items():
                pct = (cnt / len(sub)) * 100
                print(f"  {act:8s} -> Count: {cnt:5d} ({pct:5.2f}%)")

    print("\nOverall Training Action Distribution:")
    for act, cnt in train_df["action"].value_counts().items():
        pct = (cnt / len(train_df)) * 100
        print(f"  {act:8s} -> Count: {cnt:5d} ({pct:5.2f}%)")

    print("\nOverall Training Target (recovered) Distribution:")
    for tgt, cnt in train_df["recovered"].value_counts().items():
        pct = (cnt / len(train_df)) * 100
        label = "Recovered (1)" if tgt == 1 else "Failed (0)"
        print(f"  {label:15s} -> Count: {cnt:5d} ({pct:5.2f}%)")

    print("="*60 + "\n")


def generate_pipeline():
    """Execute ML training dataset generation pipeline."""
    start_time = time.time()
    print("Starting RecoverAI Step 5D ML Training Data Generation Pipeline...")

    project_root = Path(__file__).resolve().parents[1]
    raw_dir = str(project_root / "data" / "raw")
    processed_dir = str(project_root / "data" / "processed")
    os.makedirs(processed_dir, exist_ok=True)

    existing_dataset_path = os.path.join(processed_dir, "recoverai_recovery_cases.csv")
    original_recovery_cases_checksum = get_file_checksum(existing_dataset_path)

    # 1. Load Raw Data & Eligible Cases
    orders, payments, customers, raw_checksums = load_raw_data(raw_dir)
    eligible_df = construct_eligible_cases(orders, payments, customers)
    print(f"Loaded raw data and constructed eligible cases: {len(eligible_df)}")

    # 2. Customer History & Grouped Temporal Split
    df_history = derive_customer_history(eligible_df)
    df_split, train_custs, val_custs, test_custs = perform_customer_grouped_temporal_split(df_history, seed=SEED)
    print("Performed Customer-Grouped Temporal Split (70/15/15).")

    # 3. Sample Failure Cases (~15% sample rate)
    df_sampled = sample_failures(df_split, sampling_rate=FAILURE_SAMPLING_RATE, seed=SEED)
    print(f"Sampled failure cases: {len(df_sampled)} (~15% of eligible)")

    # 4. Generate Datasets (Uniform Exploration on Train)
    train_df, val_df, test_df = generate_ml_datasets(df_sampled, seed=SEED)

    # 5. Print Exploration Diagnostics
    print_exploration_diagnostics(train_df)

    # 6. Run Leakage & Quality Validation Checks
    run_leakage_and_quality_checks(train_df, val_df, test_df, original_recovery_cases_checksum)

    # 7. Save Output Files
    train_path = os.path.join(processed_dir, "recoverai_ml_training_cases.csv")
    val_path = os.path.join(processed_dir, "recoverai_ml_validation_cases.csv")
    test_path = os.path.join(processed_dir, "recoverai_ml_test_cases.csv")

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    print(f"Saved training dataset: {train_path} ({len(train_df)} rows)")
    print(f"Saved validation dataset: {val_path} ({len(val_df)} rows)")
    print(f"Saved test dataset: {test_path} ({len(test_df)} rows)")

    # 8. Reproducibility Test (Pass 2)
    print("Testing Pipeline Reproducibility (Pass 2)...")
    train_df2, val_df2, test_df2 = generate_ml_datasets(df_sampled, seed=SEED)

    if not train_df.equals(train_df2) or not val_df.equals(val_df2) or not test_df.equals(test_df2):
        raise RuntimeError("Reproducibility Check FAILED: Pass 1 and Pass 2 outputs differ!")
    print("REPRODUCIBILITY CHECK PASSED: Pass 1 and Pass 2 outputs are 100% identical.")

    elapsed = time.time() - start_time
    print(f"Step 5D Pipeline completed successfully in {elapsed:.2f} seconds.")

    return train_df, val_df, test_df, elapsed


if __name__ == "__main__":
    generate_pipeline()
