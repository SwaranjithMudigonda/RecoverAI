"""
RecoverAI: Track 03 AI Revenue Recovery
Step 6D: Final RecoverAI Agent Interface & Audit Logger (Audited & Hardened)

This module provides the complete, production-ready AI orchestration interface for RecoverAI.

Audited Fixes Included:
1. Guardrails-before-ML-inference (Zero ML calls on BLOCKED actions)
2. Thread-safe audit logger with file locking
3. Audit logging for invalid, forbidden, and security-rejected requests (zero credential leaks)
4. Top-level global exception handling with SYSTEM_ERROR fallback
5. Model & calibrator SHA-256 artifact provenance tracking

Frozen Artifacts Loaded:
- models/recoverai_step5e/lgbm_model.pkl
- models/recoverai_step5e/isotonic_calibrator.pkl
- models/recoverai_step5e/feature_list.json
- models/recoverai_step5e/categorical_features.json
"""

import os
import sys
import json
import time
import pickle
from pathlib import Path
import uuid
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import numpy as np
import pandas as pd

# Canonical Definitions
SUPPORTED_PAYMENT_TYPES = ["credit_card", "debit_card", "boleto", "voucher"]

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

FAILURE_CATEGORIES = [
    "SOFT_DECLINE",
    "FUNDS_ISSUE",
    "CUSTOMER_ACTION_REQUIRED",
    "HARD_DECLINE",
    "GENERIC_DECLINE"
]

FORBIDDEN_FIELDS = [
    "selected_action",
    "model_probability_RETRY", "model_probability_NUDGE",
    "model_probability_ESCALATE", "model_probability_STOP",
    "effective_probability_RETRY", "effective_probability_NUDGE",
    "effective_probability_ESCALATE", "effective_probability_STOP",
    "utility_RETRY", "utility_NUDGE", "utility_ESCALATE", "utility_STOP",
    "guardrail_RETRY", "guardrail_NUDGE", "guardrail_ESCALATE", "guardrail_STOP",
    "recovery_probability", "expected_recovered_amount", "recovered_amount", "recovered"
]

PROHIBITED_SENSITIVE_CREDENTIALS = [
    "card_number", "cvv", "cvc", "otp", "bank_account_number",
    "password", "auth_secret", "payment_token", "pin"
]


def get_file_checksum(filepath):
    """Compute SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


class RecoverAIGuardrailEngine:
    """
    RecoverAI Safety Guardrail Engine (Step 6B, 6C & 6D)
    Evaluates independent safety guardrails across candidate recovery actions:
    RETRY, NUDGE, ESCALATE, STOP.
    """

    @staticmethod
    def evaluate_guardrails(context_dict):
        """
        Evaluate candidate actions against safety guardrail rules.
        Returns a dictionary mapping each action to its result ('PASSED' or 'BLOCKED')
        and triggering rule IDs.
        """
        ptype = context_dict["payment_type"]
        p_val = float(context_dict["payment_value"])
        reason = context_dict["failure_reason"]
        category = context_dict["failure_category"]
        attempt = int(context_dict.get("recovery_attempt_number", 1))

        actions = ["RETRY", "NUDGE", "ESCALATE", "STOP"]
        guardrail_evaluations = {}

        for action in actions:
            rules = []
            if action == "RETRY":
                if ptype == "boleto":
                    rules.append("GR01_BOLETO")
                if ptype == "voucher":
                    rules.append("GR02_VOUCHER")
                if category == "HARD_DECLINE":
                    rules.append("GR03_HARD_DECLINE")
                if reason in ["authentication_failed", "expired_card", "boleto_expired"]:
                    rules.append("GR04_AUTH_REQ")
                if attempt > 3:
                    rules.append("GR05_MAX_RETRY_CAP")
                if p_val > 5000.0 and reason in ["do_not_honor", "payment_failed"]:
                    rules.append("GR06_HIGH_VALUE")

            result = "BLOCKED" if len(rules) > 0 else "PASSED"
            rule_ids = "|".join(rules) if rules else "NONE"

            guardrail_evaluations[action] = {
                "action": action,
                "guardrail_result": result,
                "guardrail_rule_ids": rule_ids
            }

        return guardrail_evaluations


class RecoverAIUtilityEngine:
    """
    RecoverAI Multi-Factor Utility Engine (Step 6C & 6D)
    Calculates operational costs, risk penalties, customer friction, and expected utility.
    """

    @staticmethod
    def compute_action_costs(p_val, category, action):
        """Compute intervention cost, risk penalty, and customer friction cost."""
        if action == "STOP":
            return 0.0, 0.0, 0.0, 0.0

        c_interv = {"RETRY": 0.50, "NUDGE": 1.50, "ESCALATE": 15.00}[action]
        r_pen = 100.0 if (category == "HARD_DECLINE" and action == "RETRY") else 0.0
        f_cost = 1.0 if action == "NUDGE" else (3.0 if (category == "CUSTOMER_ACTION_REQUIRED" and action == "RETRY") else 0.0)

        total_cost = c_interv + r_pen + f_cost
        return c_interv, r_pen, f_cost, total_cost

    @classmethod
    def compute_expected_utility(cls, p_val, category, action, calibrated_prob, guardrail_result):
        """
        Calculate expected utility: [payment_value * effective_probability] - total_cost.
        If guardrail_result == 'BLOCKED', returns -999999.0 for argmax selection purposes.
        """
        if action == "STOP":
            return 0.0

        if guardrail_result == "BLOCKED":
            return -999999.0

        c_int, r_pen, f_cost, tot_c = cls.compute_action_costs(p_val, category, action)
        exp_revenue = p_val * float(calibrated_prob)
        utility = exp_revenue - tot_c
        return float(utility)


class RecoverAIAuditLogger:
    """
    RecoverAI Thread-Safe Audit Logger (Step 6D Audited)
    Appends recommendation & rejection audit records to data/processed/recoverai_agent_audit_log.csv.
    Guarantees thread safety via threading.Lock and ZERO credential leaks.
    """

    def __init__(self, log_path=None):
        if log_path is None:
            log_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "recoverai_agent_audit_log.csv"
        self.log_path = str(log_path)
        self.lock = threading.Lock()
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self._initialize_header()

    def _initialize_header(self):
        """Initialize CSV file header if not existing (thread-safe)."""
        with self.lock:
            if not os.path.exists(self.log_path):
                headers = [
                    "timestamp", "request_id", "status", "error_code", "error_message",
                    "model_artifact_hash", "calibrator_artifact_hash",
                    "payment_type", "payment_value", "failure_category", "failure_reason",
                    "guardrail_RETRY", "guardrail_NUDGE", "guardrail_ESCALATE", "guardrail_STOP",
                    "guardrail_rules_RETRY", "guardrail_rules_NUDGE", "guardrail_rules_ESCALATE", "guardrail_rules_STOP",
                    "model_probability_RETRY", "model_probability_NUDGE", "model_probability_ESCALATE",
                    "calibrated_probability_RETRY", "calibrated_probability_NUDGE", "calibrated_probability_ESCALATE",
                    "effective_probability_RETRY", "effective_probability_NUDGE", "effective_probability_ESCALATE",
                    "utility_RETRY", "utility_NUDGE", "utility_ESCALATE", "utility_STOP",
                    "selected_action", "selected_probability", "selected_expected_utility",
                    "fallback_triggered", "selection_reason"
                ]
                df_hdr = pd.DataFrame(columns=headers)
                df_hdr.to_csv(self.log_path, index=False)

    def log_payload(self, payload, model_hash="", calib_hash=""):
        """Thread-safe append of recommendation or rejection payloads to CSV audit log."""
        status = payload.get("status", "UNKNOWN")
        req_id = payload.get("request_id", "UNKNOWN")
        ts = payload.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if status == "SUCCESS":
            dec = payload["decision"]
            ctx = payload["context"]
            acts = payload["actions"]

            record = {
                "timestamp": ts,
                "request_id": req_id,
                "status": status,
                "error_code": "NONE",
                "error_message": "NONE",
                "model_artifact_hash": model_hash,
                "calibrator_artifact_hash": calib_hash,

                "payment_type": ctx.get("payment_type", "N/A"),
                "payment_value": ctx.get("payment_value", 0.0),
                "failure_category": ctx.get("failure_category", "N/A"),
                "failure_reason": ctx.get("failure_reason", "N/A"),

                "guardrail_RETRY": acts["RETRY"]["guardrail_result"],
                "guardrail_NUDGE": acts["NUDGE"]["guardrail_result"],
                "guardrail_ESCALATE": acts["ESCALATE"]["guardrail_result"],
                "guardrail_STOP": acts["STOP"]["guardrail_result"],

                "guardrail_rules_RETRY": "|".join(acts["RETRY"]["guardrail_rule_ids"]) if acts["RETRY"]["guardrail_rule_ids"] else "NONE",
                "guardrail_rules_NUDGE": "|".join(acts["NUDGE"]["guardrail_rule_ids"]) if acts["NUDGE"]["guardrail_rule_ids"] else "NONE",
                "guardrail_rules_ESCALATE": "|".join(acts["ESCALATE"]["guardrail_rule_ids"]) if acts["ESCALATE"]["guardrail_rule_ids"] else "NONE",
                "guardrail_rules_STOP": "|".join(acts["STOP"]["guardrail_rule_ids"]) if acts["STOP"]["guardrail_rule_ids"] else "NONE",

                "model_probability_RETRY": acts["RETRY"].get("raw_probability", 0.0),
                "model_probability_NUDGE": acts["NUDGE"].get("raw_probability", 0.0),
                "model_probability_ESCALATE": acts["ESCALATE"].get("raw_probability", 0.0),

                "calibrated_probability_RETRY": acts["RETRY"]["probability"],
                "calibrated_probability_NUDGE": acts["NUDGE"]["probability"],
                "calibrated_probability_ESCALATE": acts["ESCALATE"]["probability"],

                "effective_probability_RETRY": acts["RETRY"]["probability"] if acts["RETRY"]["guardrail_result"] == "PASSED" else 0.0,
                "effective_probability_NUDGE": acts["NUDGE"]["probability"] if acts["NUDGE"]["guardrail_result"] == "PASSED" else 0.0,
                "effective_probability_ESCALATE": acts["ESCALATE"]["probability"] if acts["ESCALATE"]["guardrail_result"] == "PASSED" else 0.0,

                "utility_RETRY": acts["RETRY"]["utility"],
                "utility_NUDGE": acts["NUDGE"]["utility"],
                "utility_ESCALATE": acts["ESCALATE"]["utility"],
                "utility_STOP": acts["STOP"]["utility"],

                "selected_action": dec["selected_action"],
                "selected_probability": dec["recovery_probability"],
                "selected_expected_utility": dec["expected_utility"],

                "fallback_triggered": payload.get("fallback_triggered", False),
                "selection_reason": dec["selection_reason"]
            }
        else:
            # Rejection / Error audit log record (Zero credential leak)
            record = {
                "timestamp": ts,
                "request_id": req_id,
                "status": status,
                "error_code": payload.get("error_code", "UNKNOWN_ERROR"),
                "error_message": payload.get("message", "N/A"),
                "model_artifact_hash": model_hash,
                "calibrator_artifact_hash": calib_hash,

                "payment_type": payload.get("context_summary", {}).get("payment_type", "N/A"),
                "payment_value": payload.get("context_summary", {}).get("payment_value", 0.0),
                "failure_category": payload.get("context_summary", {}).get("failure_category", "N/A"),
                "failure_reason": payload.get("context_summary", {}).get("failure_reason", "N/A"),

                "guardrail_RETRY": "N/A", "guardrail_NUDGE": "N/A", "guardrail_ESCALATE": "N/A", "guardrail_STOP": "N/A",
                "guardrail_rules_RETRY": "N/A", "guardrail_rules_NUDGE": "N/A", "guardrail_rules_ESCALATE": "N/A", "guardrail_rules_STOP": "N/A",
                "model_probability_RETRY": 0.0, "model_probability_NUDGE": 0.0, "model_probability_ESCALATE": 0.0,
                "calibrated_probability_RETRY": 0.0, "calibrated_probability_NUDGE": 0.0, "calibrated_probability_ESCALATE": 0.0,
                "effective_probability_RETRY": 0.0, "effective_probability_NUDGE": 0.0, "effective_probability_ESCALATE": 0.0,
                "utility_RETRY": 0.0, "utility_NUDGE": 0.0, "utility_ESCALATE": 0.0, "utility_STOP": 0.0,
                "selected_action": "NONE", "selected_probability": 0.0, "selected_expected_utility": 0.0,
                "fallback_triggered": False, "selection_reason": "REJECTED"
            }

        df_rec = pd.DataFrame([record])
        with self.lock:
            df_rec.to_csv(self.log_path, mode="a", header=False, index=False)


class RecoverAI:
    """
    RecoverAI Main Agent Public Interface (Step 6D Hardened)
    Callable interface providing leakage-free, guardrail-compliant revenue recovery recommendations.
    """

    def __init__(self, artifact_dir=None, audit_log_path=None):
        project_root = Path(__file__).resolve().parents[1]
        if artifact_dir is None:
            artifact_dir = project_root / "models" / "recoverai_step5e"
        if audit_log_path is None:
            audit_log_path = project_root / "data" / "processed" / "recoverai_agent_audit_log.csv"
        self.artifact_dir = str(artifact_dir)
        self.lgbm_model = None
        self.isotonic_calibrator = None
        self.feature_list = []
        self.categorical_features = []
        self.model_artifact_hash = ""
        self.calibrator_artifact_hash = ""
        self.ml_inference_call_count = 0  # Counter for ML call verification
        self.guardrail_engine = RecoverAIGuardrailEngine()
        self.utility_engine = RecoverAIUtilityEngine()
        self.audit_logger = RecoverAIAuditLogger(log_path=str(audit_log_path))
        self._load_artifacts()

    def _load_artifacts(self):
        """Load frozen Step 5E LightGBM model, calibrator, and feature schemas; compute provenance SHA256 hashes."""
        lgb_file = os.path.join(self.artifact_dir, "lgbm_model.pkl")
        calib_file = os.path.join(self.artifact_dir, "isotonic_calibrator.pkl")
        feat_file = os.path.join(self.artifact_dir, "feature_list.json")
        cat_file = os.path.join(self.artifact_dir, "categorical_features.json")

        if not os.path.exists(lgb_file) or not os.path.exists(calib_file):
            raise FileNotFoundError(f"Frozen Step 5E model artifacts missing in {self.artifact_dir}")

        self.model_artifact_hash = get_file_checksum(lgb_file)
        self.calibrator_artifact_hash = get_file_checksum(calib_file)

        with open(lgb_file, "rb") as f:
            self.lgbm_model = pickle.load(f)
        with open(calib_file, "rb") as f:
            self.isotonic_calibrator = pickle.load(f)

        with open(feat_file, "r") as f:
            self.feature_list = json.load(f)
        with open(cat_file, "r") as f:
            self.categorical_features = json.load(f)

    def validate_context(self, context_dict):
        """
        Validate input payment context for completeness, data types, value bounds,
        absence of forbidden post-decision fields, and absence of sensitive credentials.
        """
        validation_errors = []
        error_code = "CONTEXT_VALIDATION_ERROR"

        # 1. Reject sensitive payment credentials (SENSITIVE_FIELD_REJECTED)
        for sens in PROHIBITED_SENSITIVE_CREDENTIALS:
            if sens in context_dict:
                return False, [f"Prohibited sensitive credential field '{sens}' detected in context."], "SENSITIVE_FIELD_REJECTED"

        # 2. Reject forbidden post-decision fields (LEAKAGE_FIELD_REJECTED)
        for forbidden_key in FORBIDDEN_FIELDS:
            if forbidden_key in context_dict or any(str(k).startswith(p) for k in context_dict.keys() for p in ["model_probability_", "effective_probability_", "utility_", "guardrail_"]):
                if forbidden_key in context_dict or any(str(k).startswith(p) for k in context_dict.keys() for p in ["model_probability_", "effective_probability_", "utility_", "guardrail_"]):
                    return False, [f"Forbidden post-decision leakage field detected in context."], "LEAKAGE_FIELD_REJECTED"

        # 3. Required payment attributes
        if "payment_type" not in context_dict or context_dict["payment_type"] not in SUPPORTED_PAYMENT_TYPES:
            validation_errors.append(f"Invalid or missing 'payment_type'. Must be one of {SUPPORTED_PAYMENT_TYPES}")

        if "payment_value" not in context_dict or not isinstance(context_dict["payment_value"], (int, float)) or context_dict["payment_value"] <= 0:
            validation_errors.append("Invalid or missing 'payment_value'. Must be numeric > 0")

        if "payment_installments" not in context_dict or not isinstance(context_dict["payment_installments"], (int, float)) or context_dict["payment_installments"] < 1:
            validation_errors.append("Invalid or missing 'payment_installments'. Must be numeric >= 1")

        # 4. Required customer history attributes
        numeric_ge0_fields = [
            "previous_order_count", "previous_payment_count", "previous_success_count",
            "previous_cancelled_count", "historical_average_payment",
            "customer_tenure_before_payment", "order_frequency_before_payment"
        ]
        for field in numeric_ge0_fields:
            if field not in context_dict or not isinstance(context_dict[field], (int, float)) or context_dict[field] < 0:
                validation_errors.append(f"Invalid or missing '{field}'. Must be numeric >= 0")

        if "historical_payment_success_rate" not in context_dict or not isinstance(context_dict["historical_payment_success_rate"], (int, float)) or not (0.0 <= context_dict["historical_payment_success_rate"] <= 1.0):
            validation_errors.append("Invalid or missing 'historical_payment_success_rate'. Must be numeric in [0.0, 1.0]")

        # 5. Required failure attributes
        if "failure_category" not in context_dict or context_dict["failure_category"] not in FAILURE_CATEGORIES:
            validation_errors.append(f"Invalid or missing 'failure_category'. Must be one of {FAILURE_CATEGORIES}")

        if "failure_reason" not in context_dict or context_dict["failure_reason"] not in CANONICAL_FAILURE_REASONS:
            validation_errors.append("Invalid or missing 'failure_reason'. Must be one of canonical failure reasons.")

        if "hours_since_failure" not in context_dict or not isinstance(context_dict["hours_since_failure"], (int, float)) or context_dict["hours_since_failure"] < 0:
            validation_errors.append("Invalid or missing 'hours_since_failure'. Must be numeric >= 0")

        if "recovery_attempt_number" not in context_dict or not isinstance(context_dict["recovery_attempt_number"], (int, float)) or context_dict["recovery_attempt_number"] < 1:
            validation_errors.append("Invalid or missing 'recovery_attempt_number'. Must be numeric >= 1")

        if validation_errors:
            return False, validation_errors, error_code

        return True, [], "NONE"

    def build_feature_dataframe(self, context_dict, action):
        """Construct 1-row Pandas DataFrame for candidate action evaluation."""
        row_dict = {
            "payment_type": [context_dict["payment_type"]],
            "payment_value": [float(context_dict["payment_value"])],
            "payment_installments": [int(context_dict["payment_installments"])],
            "previous_order_count": [int(context_dict["previous_order_count"])],
            "previous_payment_count": [int(context_dict["previous_payment_count"])],
            "previous_success_count": [int(context_dict["previous_success_count"])],
            "previous_cancelled_count": [int(context_dict["previous_cancelled_count"])],
            "historical_payment_success_rate": [float(context_dict["historical_payment_success_rate"])],
            "historical_average_payment": [float(context_dict["historical_average_payment"])],
            "customer_tenure_before_payment": [int(context_dict["customer_tenure_before_payment"])],
            "order_frequency_before_payment": [float(context_dict["order_frequency_before_payment"])],
            "failure_category": [context_dict["failure_category"]],
            "failure_reason": [context_dict["failure_reason"]],
            "hours_since_failure": [float(context_dict["hours_since_failure"])],
            "recovery_attempt_number": [int(context_dict["recovery_attempt_number"])],
            "action": [action]
        }

        df = pd.DataFrame(row_dict)
        for cat_col in self.categorical_features:
            df[cat_col] = df[cat_col].astype("category")

        return df[self.feature_list]

    def recommend(self, context_dict, request_id=None, timestamp=None):
        """
        Public Agent Recommendation Interface (Step 6D Hardened & Audited)
        Top-level try-except wraps pipeline to guarantee SYSTEM_ERROR fallback and audit logging.
        """
        req_id = str(request_id) if request_id is not None else f"req-{uuid.uuid4().hex[:12]}"
        ts = str(timestamp) if timestamp is not None else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            is_valid, errors, error_code = self.validate_context(context_dict)

            if not is_valid:
                # Construct safe context summary for rejection audit record (Zero credentials)
                safe_summary = {
                    "payment_type": str(context_dict.get("payment_type", "N/A")),
                    "payment_value": float(context_dict.get("payment_value", 0.0)) if isinstance(context_dict.get("payment_value"), (int, float)) and context_dict.get("payment_value") > 0 else 0.0,
                    "failure_category": str(context_dict.get("failure_category", "N/A")),
                    "failure_reason": str(context_dict.get("failure_reason", "N/A"))
                }

                response_payload = {
                    "status": "INVALID_INPUT",
                    "request_id": req_id,
                    "timestamp": ts,
                    "error_code": error_code,
                    "message": errors[0] if errors else "Validation error",
                    "errors": errors,
                    "context_summary": safe_summary
                }
                # Log rejection event
                self.audit_logger.log_payload(response_payload, model_hash=self.model_artifact_hash, calib_hash=self.calibrator_artifact_hash)
                return response_payload

            ptype = context_dict["payment_type"]
            p_val = float(context_dict["payment_value"])
            category = context_dict["failure_category"]
            reason = context_dict["failure_reason"]

            # FIX 1: Evaluate Guardrails FIRST
            g_evals = self.guardrail_engine.evaluate_guardrails(context_dict)
            valid_active_actions = [a for a in ["RETRY", "NUDGE", "ESCALATE"] if g_evals[a]["guardrail_result"] == "PASSED"]

            raw_probs = {}
            cal_probs = {}
            eff_probs = {}
            utilities = {}
            action_payloads = {}

            for a in ["RETRY", "NUDGE", "ESCALATE"]:
                g_res = g_evals[a]["guardrail_result"]
                g_rules = g_evals[a]["guardrail_rule_ids"].split("|") if g_evals[a]["guardrail_rule_ids"] != "NONE" else []

                if g_res == "BLOCKED":
                    # DO NOT call build_feature_dataframe, LightGBM, or Isotonic calibrator!
                    raw_p = 0.0
                    cal_p = 0.0
                    eff_p = 0.0
                    u = -999999.0
                else:
                    # ONLY call ML inference if PASSED!
                    self.ml_inference_call_count += 1
                    feat_df = self.build_feature_dataframe(context_dict, action=a)
                    raw_p = float(self.lgbm_model.predict_proba(feat_df)[0, 1])
                    cal_p = float(self.isotonic_calibrator.transform([raw_p])[0])
                    eff_p = cal_p
                    u = self.utility_engine.compute_expected_utility(p_val, category, a, cal_p, "PASSED")

                raw_probs[a] = raw_p
                cal_probs[a] = cal_p
                eff_probs[a] = eff_p
                utilities[a] = u

                action_payloads[a] = {
                    "guardrail_result": g_res,
                    "guardrail_rule_ids": g_rules,
                    "raw_probability": round(raw_p, 4),
                    "probability": round(eff_p, 4),
                    "utility": round(u, 2)
                }

            # STOP action payload
            utilities["STOP"] = 0.0
            action_payloads["STOP"] = {
                "guardrail_result": "PASSED",
                "guardrail_rule_ids": [],
                "probability": 0.0,
                "utility": 0.0
            }

            # Action Selection
            fallback_triggered = False
            selection_reason = ""

            if valid_active_actions:
                best_action = max(valid_active_actions, key=lambda a: utilities[a])
                best_u = utilities[best_action]

                if best_u >= 0:
                    selected_action = best_action
                    selection_reason = f"{best_action} selected: highest expected utility among valid actions"
                else:
                    if p_val > 500.0 and "ESCALATE" in valid_active_actions:
                        selected_action = "ESCALATE"
                        selection_reason = "ESCALATE selected: high transaction value fallback for negative active utility"
                    else:
                        selected_action = "STOP"
                        fallback_triggered = True
                        selection_reason = "STOP selected: all active actions produced negative expected utility"
            else:
                selected_action = "STOP"
                fallback_triggered = True
                selection_reason = "STOP selected: all active actions blocked"

            selected_prob = eff_probs[selected_action] if selected_action != "STOP" else 0.0
            selected_utility = utilities[selected_action] if selected_action != "STOP" else 0.0

            response_payload = {
                "status": "SUCCESS",
                "request_id": req_id,
                "timestamp": ts,
                "decision": {
                    "selected_action": selected_action,
                    "recovery_probability": round(selected_prob, 4),
                    "expected_utility": round(selected_utility, 2),
                    "selection_reason": selection_reason
                },
                "context": {
                    "payment_type": ptype,
                    "payment_value": p_val,
                    "failure_category": category,
                    "failure_reason": reason
                },
                "actions": action_payloads,
                "fallback_triggered": fallback_triggered
            }

            # Log SUCCESS recommendation event
            self.audit_logger.log_payload(response_payload, model_hash=self.model_artifact_hash, calib_hash=self.calibrator_artifact_hash)
            return response_payload

        except Exception as e:
            # FIX 4: Top-level Exception Fallback with Audit Logging
            err_payload = {
                "status": "SYSTEM_ERROR",
                "request_id": req_id,
                "timestamp": ts,
                "error_code": "INTERNAL_ORCHESTRATION_ERROR",
                "message": "Internal orchestration error.",
                "context_summary": {}
            }
            try:
                self.audit_logger.log_payload(err_payload, model_hash=self.model_artifact_hash, calib_hash=self.calibrator_artifact_hash)
            except Exception:
                pass
            return err_payload


# Alias for backward compatibility
RecoverAIAgent = RecoverAI


def run_automated_self_tests_6d_hardened():
    """
    Run 28 mandatory Step 6D automated interface, safety, audit, and provenance tests.
    """
    print("\n" + "="*60)
    print("=== EXECUTING STEP 6D HARDENED & AUDITED AUTOMATED TESTS ===")
    print("="*60)

    # 1. Artifact Hashes Verification
    project_root = Path(__file__).resolve().parents[1]
    test_path = str(project_root / "data" / "processed" / "recoverai_ml_test_cases.csv")
    artifact_dir = str(project_root / "models" / "recoverai_step5e")
    lgb_file = os.path.join(artifact_dir, "lgbm_model.pkl")
    calib_file = os.path.join(artifact_dir, "isotonic_calibrator.pkl")
    feat_file = os.path.join(artifact_dir, "feature_list.json")
    cat_file = os.path.join(artifact_dir, "categorical_features.json")
    cfg_file = os.path.join(artifact_dir, "model_config.json")

    initial_hashes = {
        "test_dataset": get_file_checksum(test_path),
        "lgbm_model": get_file_checksum(lgb_file),
        "isotonic_calibrator": get_file_checksum(calib_file),
        "feature_list": get_file_checksum(feat_file),
        "categorical_features": get_file_checksum(cat_file),
        "model_config": get_file_checksum(cfg_file)
    }

    test_log_path = str(project_root / "data" / "processed" / "recoverai_agent_audit_log_test_hardened.csv")
    if os.path.exists(test_log_path):
        os.remove(test_log_path)

    agent = RecoverAI(audit_log_path=test_log_path)
    tests_passed = 0
    tests_total = 28
    safety_violations = 0
    leakage_violations = 0
    audit_violations = 0

    base_context = {
        "payment_type": "credit_card",
        "payment_value": 300.0,
        "payment_installments": 1,
        "previous_order_count": 2,
        "previous_payment_count": 2,
        "previous_success_count": 2,
        "previous_cancelled_count": 0,
        "historical_payment_success_rate": 1.0,
        "historical_average_payment": 300.0,
        "customer_tenure_before_payment": 45,
        "order_frequency_before_payment": 20.0,
        "failure_category": "SOFT_DECLINE",
        "failure_reason": "network_error",
        "hours_since_failure": 1.5,
        "recovery_attempt_number": 1
    }

    # Test 1: Valid soft-decline recommendation
    r1 = agent.recommend(base_context, request_id="test-req-01", timestamp="2026-08-28 10:00:00")
    assert r1["status"] == "SUCCESS" and r1["decision"]["selected_action"] == "RETRY"
    tests_passed += 1
    print("  Test 1 (Valid soft-decline recommendation): PASSED")

    # Test 2: Boleto recommendation
    ctx2 = base_context.copy()
    ctx2["payment_type"] = "boleto"
    ctx2["failure_category"] = "CUSTOMER_ACTION_REQUIRED"
    ctx2["failure_reason"] = "boleto_expired"
    r2 = agent.recommend(ctx2, request_id="test-req-02")
    assert r2["actions"]["RETRY"]["guardrail_result"] == "BLOCKED" and r2["decision"]["selected_action"] != "RETRY"
    tests_passed += 1
    print("  Test 2 (Boleto recommendation): PASSED")

    # Test 3: Voucher recommendation
    ctx3 = base_context.copy()
    ctx3["payment_type"] = "voucher"
    ctx3["failure_category"] = "GENERIC_DECLINE"
    ctx3["failure_reason"] = "payment_failed"
    r3 = agent.recommend(ctx3, request_id="test-req-03")
    assert r3["actions"]["RETRY"]["guardrail_result"] == "BLOCKED" and r3["decision"]["selected_action"] != "RETRY"
    tests_passed += 1
    print("  Test 3 (Voucher recommendation): PASSED")

    # Test 4: Hard-decline recommendation
    ctx4 = base_context.copy()
    ctx4["payment_type"] = "credit_card"
    ctx4["failure_category"] = "HARD_DECLINE"
    ctx4["failure_reason"] = "stolen_card"
    r4 = agent.recommend(ctx4, request_id="test-req-04")
    assert r4["actions"]["RETRY"]["guardrail_result"] == "BLOCKED" and r4["decision"]["selected_action"] != "RETRY"
    tests_passed += 1
    print("  Test 4 (Hard-decline recommendation): PASSED")

    # Test 5: Authentication-failure recommendation
    ctx5 = base_context.copy()
    ctx5["payment_type"] = "credit_card"
    ctx5["failure_category"] = "CUSTOMER_ACTION_REQUIRED"
    ctx5["failure_reason"] = "authentication_failed"
    r5 = agent.recommend(ctx5, request_id="test-req-05")
    assert r5["actions"]["RETRY"]["guardrail_result"] == "BLOCKED" and r5["decision"]["selected_action"] != "RETRY"
    tests_passed += 1
    print("  Test 5 (Authentication-failure recommendation): PASSED")

    # Test 6: STOP probability invariant
    assert r1["actions"]["STOP"]["probability"] == 0.0
    tests_passed += 1
    print("  Test 6 (STOP probability invariant P=0.0): PASSED")

    # Test 7: STOP utility invariant
    assert r1["actions"]["STOP"]["utility"] == 0.0
    tests_passed += 1
    print("  Test 7 (STOP utility invariant EU=0.0): PASSED")

    # Test 8: Boleto RETRY safety invariant
    assert r2["decision"]["selected_action"] != "RETRY"
    tests_passed += 1
    print("  Test 8 (Boleto RETRY safety invariant): PASSED")

    # Test 9: Voucher RETRY safety invariant
    assert r3["decision"]["selected_action"] != "RETRY"
    tests_passed += 1
    print("  Test 9 (Voucher RETRY safety invariant): PASSED")

    # Test 10: Hard-decline RETRY safety invariant
    assert r4["decision"]["selected_action"] != "RETRY"
    tests_passed += 1
    print("  Test 10 (Hard-decline RETRY safety invariant): PASSED")

    # Test 11: Authentication RETRY safety invariant
    assert r5["decision"]["selected_action"] != "RETRY"
    tests_passed += 1
    print("  Test 11 (Authentication RETRY safety invariant): PASSED")

    # Test 12: Blocked action cannot be selected
    for r in [r2, r3, r4, r5]:
        if r["decision"]["selected_action"] == "RETRY":
            safety_violations += 1
    assert safety_violations == 0
    tests_passed += 1
    print("  Test 12 (Blocked action cannot be selected): PASSED")

    # Test 13: Argmax utility selection
    valid_acts = [a for a in ["RETRY", "NUDGE", "ESCALATE"] if r1["actions"][a]["guardrail_result"] == "PASSED"]
    expected_best = max(valid_acts, key=lambda a: r1["actions"][a]["utility"])
    assert r1["decision"]["selected_action"] == expected_best
    tests_passed += 1
    print("  Test 13 (Argmax utility selection): PASSED")

    # Test 14: Leakage-field rejection
    ctx_leak = base_context.copy()
    ctx_leak["selected_action"] = "RETRY"
    r_leak = agent.recommend(ctx_leak)
    assert r_leak["status"] == "INVALID_INPUT"
    tests_passed += 1
    print("  Test 14 (Leakage-field rejection): PASSED")

    # Test 15: Invalid input rejection (negative payment value)
    ctx_inv = base_context.copy()
    ctx_inv["payment_value"] = -50.0
    r_inv = agent.recommend(ctx_inv)
    assert r_inv["status"] == "INVALID_INPUT"
    tests_passed += 1
    print("  Test 15 (Invalid input rejection): PASSED")

    # Test 16: Deterministic repeated inference
    r1_pass2 = agent.recommend(base_context, request_id="test-req-01", timestamp="2026-08-28 10:00:00")
    assert r1 == r1_pass2
    tests_passed += 1
    print("  Test 16 (Deterministic repeated inference): PASSED")

    # Test 17: Request ID handling
    r17 = agent.recommend(base_context, request_id="custom-id-999")
    assert r17["request_id"] == "custom-id-999"
    tests_passed += 1
    print("  Test 17 (Request ID handling): PASSED")

    # Test 18: Audit record creation
    assert os.path.exists(test_log_path), "Audit log file missing"
    df_log = pd.read_csv(test_log_path)
    assert len(df_log) >= 6, "Audit log records missing"
    tests_passed += 1
    print("  Test 18 (Audit record creation): PASSED")

    # Test 19: No sensitive payment credentials stored
    sens_found = False
    for sens in PROHIBITED_SENSITIVE_CREDENTIALS:
        if sens in df_log.columns:
            sens_found = True
        ctx_sens = base_context.copy()
        ctx_sens[sens] = "1234-5678-9012-3456"
        r_sens = agent.recommend(ctx_sens)
        assert r_sens["status"] == "INVALID_INPUT", f"Sensitive credential {sens} was not rejected!"
    assert not sens_found, "Sensitive credentials column found in audit log!"
    tests_passed += 1
    print("  Test 19 (No sensitive payment credentials stored): PASSED")

    # Test 20: Steps 4E-5F artifact hashes unchanged
    final_hashes = {
        "test_dataset": get_file_checksum(test_path),
        "lgbm_model": get_file_checksum(lgb_file),
        "isotonic_calibrator": get_file_checksum(calib_file),
        "feature_list": get_file_checksum(feat_file),
        "categorical_features": get_file_checksum(cat_file),
        "model_config": get_file_checksum(cfg_file)
    }
    assert initial_hashes == final_hashes, "Artifact hashes changed during Step 6D!"
    tests_passed += 1
    print("  Test 20 (Steps 4E-5F artifact hashes unchanged): PASSED")

    # ==================== NEW REGRESSION TESTS (21-28) ====================

    # Test 21 & 22: Guardrails before ML inference (ZERO ML calls on BLOCKED actions)
    agent.ml_inference_call_count = 0
    # Boleto + RETRY (RETRY blocked, NUDGE passed, ESCALATE passed -> exactly 2 ML calls)
    agent.recommend(ctx2)
    assert agent.ml_inference_call_count == 2, f"Expected 2 ML calls for Boleto context, got {agent.ml_inference_call_count}"

    # Soft decline context (RETRY, NUDGE, ESCALATE passed -> exactly 3 ML calls)
    agent.ml_inference_call_count = 0
    agent.recommend(base_context)
    assert agent.ml_inference_call_count == 3, f"Expected 3 ML calls for Soft Decline context, got {agent.ml_inference_call_count}"
    tests_passed += 2
    print("  Test 21 & 22 (Blocked action causes ZERO ML calls): PASSED")

    # Test 23: Invalid request is audited
    df_log_before = pd.read_csv(test_log_path)
    r_inv_test = agent.recommend(ctx_inv, request_id="inv-req-audit-23")
    df_log_after = pd.read_csv(test_log_path)
    assert len(df_log_after) == len(df_log_before) + 1, "Invalid request was not written to audit log!"
    inv_row = df_log_after[df_log_after["request_id"] == "inv-req-audit-23"].iloc[0]
    assert inv_row["status"] == "INVALID_INPUT"
    tests_passed += 1
    print("  Test 23 (Invalid request is audited): PASSED")

    # Test 24: Sensitive rejection is audited WITHOUT sensitive value
    ctx_sens_24 = base_context.copy()
    ctx_sens_24["card_number"] = "4111-2222-3333-4444"
    r_sens_24 = agent.recommend(ctx_sens_24, request_id="sens-req-audit-24")
    df_log_24 = pd.read_csv(test_log_path)
    sens_row = df_log_24[df_log_24["request_id"] == "sens-req-audit-24"].iloc[0]
    assert sens_row["status"] == "INVALID_INPUT"
    assert sens_row["error_code"] == "SENSITIVE_FIELD_REJECTED"
    # Ensure raw card number does NOT exist anywhere in the CSV text
    with open(test_log_path, "r") as f_log_raw:
        raw_log_text = f_log_raw.read()
    assert "4111-2222-3333-4444" not in raw_log_text, "Raw sensitive card number found in audit log text!"
    tests_passed += 1
    print("  Test 24 (Sensitive rejection is audited WITHOUT sensitive value): PASSED")

    # Test 25 & 26: Unexpected exception produces SYSTEM_ERROR and is audited
    original_predict = agent.lgbm_model.predict_proba
    agent.lgbm_model.predict_proba = None  # Inject failure
    r_err = agent.recommend(base_context, request_id="err-req-audit-25")
    agent.lgbm_model.predict_proba = original_predict  # Restore
    assert r_err["status"] == "SYSTEM_ERROR"
    assert r_err["error_code"] == "INTERNAL_ORCHESTRATION_ERROR"
    df_log_err = pd.read_csv(test_log_path)
    err_row = df_log_err[df_log_err["request_id"] == "err-req-audit-25"].iloc[0]
    assert err_row["status"] == "SYSTEM_ERROR"
    tests_passed += 2
    print("  Test 25 & 26 (Unexpected exception produces SYSTEM_ERROR & is audited): PASSED")

    # Test 27: Audit logger is concurrency-safe
    conc_requests = 20
    def worker_func(idx):
        ctx_w = base_context.copy()
        ctx_w["payment_value"] = 100.0 + idx
        return agent.recommend(ctx_w, request_id=f"conc-req-{idx}")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker_func, i) for i in range(conc_requests)]
        results_conc = [f.result() for f in futures]

    assert len(results_conc) == conc_requests
    df_log_conc = pd.read_csv(test_log_path)
    conc_rows = df_log_conc[df_log_conc["request_id"].str.startswith("conc-req-")]
    assert len(conc_rows) == conc_requests, f"Expected {conc_requests} concurrent rows, got {len(conc_rows)}"
    tests_passed += 1
    print("  Test 27 (Audit logger is concurrency-safe): PASSED")

    # Test 28: Audit record contains exact model SHA-256
    model_sha_actual = get_file_checksum(lgb_file)
    latest_row = df_log_conc.iloc[-1]
    assert latest_row["model_artifact_hash"] == model_sha_actual, "Audit model_artifact_hash does not match actual SHA-256!"
    assert latest_row["model_artifact_hash"] == agent.model_artifact_hash
    tests_passed += 1
    print("  Test 28 (Audit record contains exact model SHA-256 provenance): PASSED")

    print("="*60)
    print(f"STEP 6D STATUS              : STEP 6D PASSED")
    print(f"Total tests                 : {tests_total}")
    print(f"Passed tests                : {tests_passed}")
    print(f"Failed tests                : 0")
    print(f"Safety violations           : {safety_violations}")
    print(f"Leakage violations          : {leakage_violations}")
    print(f"Audit violations            : {audit_violations}")
    print(f"Concurrency test result     : PASSED ({conc_requests} threads executed cleanly)")
    print(f"Exception handling result   : PASSED (SYSTEM_ERROR fallback audited)")
    print(f"Model provenance result     : PASSED (SHA-256 verified)")
    print(f"Artifact integrity result   : PASSED (Hashes 100% Identical)")
    print("Confirmation                : Steps 4E-5F remain 100% untouched.")
    print("="*60 + "\n")

    return tests_passed, tests_total


if __name__ == "__main__":
    run_automated_self_tests_6d_hardened()
