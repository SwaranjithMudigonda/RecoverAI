"""
RecoverAI: Track 03 AI Revenue Recovery
Step 7B: Batch Recommendation Runner (Audited & Hardened)

This CLI module ingests a user-specified input payment CSV, strips all forbidden post-decision
and sensitive credential fields, delegates context evaluation to the frozen Step 6D RecoverAI agent
(`src.recoverai_agent.RecoverAI`), and streams audited decision traces incrementally to a new output CSV.

Hardening Fixes Included:
1. Incremental streaming output using csv.DictWriter (Zero memory accumulation)
2. Safe context initialization before row-level try-except (Prevents UnboundLocalError)
3. Sanitized error reporting (Safe error codes, stack traces to stderr ONLY, zero credential leaks)
"""

import os
import sys
import json
import csv
import argparse
import logging
import pandas as pd
from typing import Dict, Any

# Import frozen Step 6D RecoverAI Agent
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.recoverai_agent import RecoverAI, PROHIBITED_SENSITIVE_CREDENTIALS, FORBIDDEN_FIELDS, get_file_checksum

# Configure logger for stderr diagnostics
logger = logging.getLogger("recoverai_batch")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    logger.addHandler(handler)

# Context fields allowed to be passed into RecoverAI.recommend()
ALLOWED_CONTEXT_FIELDS = [
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
    "recovery_attempt_number"
]

OUTPUT_FIELDNAMES = [
    "request_id", "timestamp", "case_id", "order_id", "customer_unique_id",
    "status", "error_code", "error_message",
    "payment_type", "payment_value", "failure_category", "failure_reason",
    "selected_action", "selected_probability", "selected_expected_utility",
    "selection_reason", "fallback_triggered",
    "guardrail_RETRY", "guardrail_NUDGE", "guardrail_ESCALATE", "guardrail_STOP",
    "guardrail_rules_RETRY", "guardrail_rules_NUDGE", "guardrail_rules_ESCALATE", "guardrail_rules_STOP",
    "model_probability_RETRY", "model_probability_NUDGE", "model_probability_ESCALATE",
    "calibrated_probability_RETRY", "calibrated_probability_NUDGE", "calibrated_probability_ESCALATE",
    "effective_probability_RETRY", "effective_probability_NUDGE", "effective_probability_ESCALATE",
    "utility_RETRY", "utility_NUDGE", "utility_ESCALATE", "utility_STOP",
    "model_artifact_hash", "calibrator_artifact_hash"
]


def extract_clean_context(row_dict: Dict[str, Any]) -> tuple:
    """
    Extract pre-decision context dictionary, stripping all forbidden post-decision fields
    and sensitive payment credentials. Retains source identifiers as metadata.
    """
    metadata = {
        "case_id": str(row_dict.get("case_id", "N/A")),
        "order_id": str(row_dict.get("order_id", "N/A")),
        "customer_unique_id": str(row_dict.get("customer_unique_id", "N/A")),
        "customer_id": str(row_dict.get("customer_id", "N/A"))
    }

    clean_context = {}
    for key, value in row_dict.items():
        # Exclude metadata, forbidden fields, and sensitive credentials
        if key in metadata or key in FORBIDDEN_FIELDS or key in PROHIBITED_SENSITIVE_CREDENTIALS:
            continue

        # Type conversion for allowed fields
        if key in ALLOWED_CONTEXT_FIELDS:
            if pd.isna(value):
                continue
            if key in ["payment_value", "historical_payment_success_rate", "historical_average_payment", "order_frequency_before_payment", "hours_since_failure"]:
                try:
                    clean_context[key] = float(value)
                except (ValueError, TypeError):
                    clean_context[key] = value
            elif key in ["payment_installments", "previous_order_count", "previous_payment_count", "previous_success_count", "previous_cancelled_count", "customer_tenure_before_payment", "recovery_attempt_number"]:
                try:
                    clean_context[key] = int(value)
                except (ValueError, TypeError):
                    clean_context[key] = value
            else:
                clean_context[key] = str(value)

    return clean_context, metadata


def process_batch(input_csv_path: str, output_csv_path: str, agent: RecoverAI = None) -> int:
    """
    FIX 1: Process input CSV synchronously and stream output records incrementally using csv.DictWriter.
    Zero memory accumulation of all result rows in a Python list.
    """
    if not os.path.exists(input_csv_path):
        raise FileNotFoundError(f"Input CSV file not found at {input_csv_path}")

    if agent is None:
        agent = RecoverAI()

    input_df = pd.read_csv(input_csv_path)
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)

    processed_count = 0

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as out_file:
        writer = csv.DictWriter(out_file, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()

        for idx, row in input_df.iterrows():
            processed_count += 1
            req_id = f"batch-req-{processed_count:06d}"

            # FIX 2: Pre-initialize variables before try/except block to prevent UnboundLocalError
            clean_context: Dict[str, Any] = {}
            metadata: Dict[str, str] = {
                "case_id": "N/A", "order_id": "N/A", "customer_unique_id": "N/A"
            }

            try:
                row_dict = row.to_dict()
                clean_context, metadata = extract_clean_context(row_dict)

                # Delegate decision to frozen Step 6D Agent Engine
                response = agent.recommend(clean_context, request_id=req_id)

                if response.get("status") == "SUCCESS":
                    dec = response["decision"]
                    ctx = response["context"]
                    acts = response["actions"]

                    output_record = {
                        "request_id": response["request_id"],
                        "timestamp": response["timestamp"],
                        "case_id": metadata["case_id"],
                        "order_id": metadata["order_id"],
                        "customer_unique_id": metadata["customer_unique_id"],
                        "status": response["status"],
                        "error_code": "NONE",
                        "error_message": "NONE",

                        "payment_type": ctx["payment_type"],
                        "payment_value": ctx["payment_value"],
                        "failure_category": ctx["failure_category"],
                        "failure_reason": ctx["failure_reason"],

                        "selected_action": dec["selected_action"],
                        "selected_probability": dec["recovery_probability"],
                        "selected_expected_utility": dec["expected_utility"],
                        "selection_reason": dec["selection_reason"],
                        "fallback_triggered": response["fallback_triggered"],

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

                        "model_artifact_hash": agent.model_artifact_hash,
                        "calibrator_artifact_hash": agent.calibrator_artifact_hash
                    }
                else:
                    # FIX 3: Rejection audit record (Safe error codes, zero credential leak)
                    output_record = {
                        "request_id": response.get("request_id", req_id),
                        "timestamp": response.get("timestamp", "N/A"),
                        "case_id": metadata["case_id"],
                        "order_id": metadata["order_id"],
                        "customer_unique_id": metadata["customer_unique_id"],
                        "status": response.get("status", "INVALID_INPUT"),
                        "error_code": response.get("error_code", "VALIDATION_ERROR"),
                        "error_message": response.get("message", "Validation error."),

                        "payment_type": clean_context.get("payment_type", "N/A"),
                        "payment_value": clean_context.get("payment_value", 0.0),
                        "failure_category": clean_context.get("failure_category", "N/A"),
                        "failure_reason": clean_context.get("failure_reason", "N/A"),

                        "selected_action": "NONE",
                        "selected_probability": 0.0,
                        "selected_expected_utility": 0.0,
                        "selection_reason": "REJECTED",
                        "fallback_triggered": False,

                        "guardrail_RETRY": "N/A", "guardrail_NUDGE": "N/A", "guardrail_ESCALATE": "N/A", "guardrail_STOP": "N/A",
                        "guardrail_rules_RETRY": "N/A", "guardrail_rules_NUDGE": "N/A", "guardrail_rules_ESCALATE": "N/A", "guardrail_rules_STOP": "N/A",
                        "model_probability_RETRY": 0.0, "model_probability_NUDGE": 0.0, "model_probability_ESCALATE": 0.0,
                        "calibrated_probability_RETRY": 0.0, "calibrated_probability_NUDGE": 0.0, "calibrated_probability_ESCALATE": 0.0,
                        "effective_probability_RETRY": 0.0, "effective_probability_NUDGE": 0.0, "effective_probability_ESCALATE": 0.0,
                        "utility_RETRY": 0.0, "utility_NUDGE": 0.0, "utility_ESCALATE": 0.0, "utility_STOP": 0.0,

                        "model_artifact_hash": agent.model_artifact_hash,
                        "calibrator_artifact_hash": agent.calibrator_artifact_hash
                    }

            except Exception as e:
                # FIX 3: Safe error reporting (Log raw stack trace to stderr ONLY, write sanitized CSV row)
                logger.exception(f"Sanitized row processing error for request {req_id}")
                output_record = {
                    "request_id": req_id,
                    "timestamp": "N/A",
                    "case_id": metadata["case_id"],
                    "order_id": metadata["order_id"],
                    "customer_unique_id": metadata["customer_unique_id"],
                    "status": "SYSTEM_ERROR",
                    "error_code": "ROW_PROCESSING_ERROR",
                    "error_message": "Row processing error.",

                    "payment_type": clean_context.get("payment_type", "N/A"),
                    "payment_value": clean_context.get("payment_value", 0.0),
                    "failure_category": clean_context.get("failure_category", "N/A"),
                    "failure_reason": clean_context.get("failure_reason", "N/A"),

                    "selected_action": "NONE",
                    "selected_probability": 0.0,
                    "selected_expected_utility": 0.0,
                    "selection_reason": "ERROR",
                    "fallback_triggered": False,

                    "guardrail_RETRY": "N/A", "guardrail_NUDGE": "N/A", "guardrail_ESCALATE": "N/A", "guardrail_STOP": "N/A",
                    "guardrail_rules_RETRY": "N/A", "guardrail_rules_NUDGE": "N/A", "guardrail_rules_ESCALATE": "N/A", "guardrail_rules_STOP": "N/A",
                    "model_probability_RETRY": 0.0, "model_probability_NUDGE": 0.0, "model_probability_ESCALATE": 0.0,
                    "calibrated_probability_RETRY": 0.0, "calibrated_probability_NUDGE": 0.0, "calibrated_probability_ESCALATE": 0.0,
                    "effective_probability_RETRY": 0.0, "effective_probability_NUDGE": 0.0, "effective_probability_ESCALATE": 0.0,
                    "utility_RETRY": 0.0, "utility_NUDGE": 0.0, "utility_ESCALATE": 0.0, "utility_STOP": 0.0,

                    "model_artifact_hash": agent.model_artifact_hash,
                    "calibrator_artifact_hash": agent.calibrator_artifact_hash
                }

            # FIX 1: Stream record immediately to CSV file via csv.DictWriter
            writer.writerow(output_record)

    print(f"Batch Processing Complete: Streamed {processed_count} rows incrementally to {output_csv_path}")
    return processed_count


def main():
    parser = argparse.ArgumentParser(description="RecoverAI Step 7B Batch Recommendation Runner")
    parser.add_argument("--input", required=True, help="Path to input payment CSV file")
    parser.add_argument("--output", required=True, help="Path to destination output CSV file")
    args = parser.parse_args()

    process_batch(args.input, args.output)


if __name__ == "__main__":
    main()
