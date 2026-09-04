"""
src/integrations/razorpay_live.py
==================================

Tier C: LIVE Razorpay Test Mode bridge.

Unlike tools/collect_razorpay_samples.py (Tier B: offline, static fixture
collection) and the Step 5F simulation (Tier A: frozen, Olist-derived
training/eval — never touched by this file), this module is a genuinely
LIVE integration:

  Razorpay Test Mode sandbox
        │  real payment.failed webhook (rzp_test_... environment only)
        ▼
  POST /webhook/razorpay  (this file)
        │  signature-verified, sanitized, mapped to RecoverAI schema
        ▼
  src.recoverai_agent.RecoverAI.recommend()   <-- the SAME frozen Step 6D agent
        │
        ▼
  optional execution: RETRY -> create a new Test Mode Payment Link
                       NUDGE -> simulated reminder message (logged, not sent)
                       ESCALATE / STOP -> logged only

IMPORTANT — what this file is and is NOT:
- It calls the real Razorpay Test Mode sandbox API. No real money ever moves;
  rzp_test_ keys are sandboxed by Razorpay itself.
- It does NOT modify, retrain, or re-evaluate the frozen Step 5E/5F ML
  artifacts or benchmarks. It is a new, additive input path into the same
  agent.recommend() call already exercised by src/api/server.py.
- It writes to its own audit log (data/processed/live_decisions_audit_log.csv),
  separate from the frozen recoverai_agent_audit_log.csv, so live-demo traffic
  never mixes with or overwrites existing audit history.
- Customer history features (previous_order_count, historical_payment_success_rate,
  etc.) have NO real basis for a fresh Razorpay Test Mode customer — they are
  filled with explicit, documented neutral defaults (see DEFAULT_HISTORY_CONTEXT
  below) rather than invented realistic-looking numbers. This is disclosed in
  every response under "context_provenance".

Run with:
    uvicorn src.integrations.razorpay_live:app --port 8010 --reload

Required environment variables:
    RAZORPAY_TEST_KEY_ID       rzp_test_... (from Razorpay Dashboard, Test Mode)
    RAZORPAY_TEST_KEY_SECRET   matching secret
    RAZORPAY_WEBHOOK_SECRET    the secret you set when creating the webhook

Optional:
    RECOVERAI_LIVE_EXECUTE     "true" (default) to actually call the Razorpay
                                API for RETRY execution; "false" to only
                                recommend, never execute.
"""

import os
import sys
import csv
import json
import hmac
import hashlib
import threading
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from src.recoverai_agent import RecoverAI, SUPPORTED_PAYMENT_TYPES  # noqa: E402
from collect_razorpay_samples import sanitize_payment_payload, map_to_recoverai_taxonomy  # noqa: E402

app = FastAPI(
    title="RecoverAI Live Razorpay Test Mode Bridge",
    description="Tier C: live sandbox integration, additive to the frozen Step 6D agent",
    version="1.0.0",
)

LIVE_AUDIT_LOG_PATH = REPO_ROOT / "data" / "processed" / "live_decisions_audit_log.csv"
_log_lock = threading.Lock()

# Single shared agent instance, pointed at ITS OWN audit log so live-demo
# traffic never touches the frozen recoverai_agent_audit_log.csv used by
# src/api/server.py or the Step 5F evaluation artifacts.
agent = RecoverAI(audit_log_path=str(REPO_ROOT / "data" / "processed" / "live_agent_internal_audit_log.csv"))

RECOVERAI_LIVE_EXECUTE = os.environ.get("RECOVERAI_LIVE_EXECUTE", "true").lower() == "true"

# Razorpay "method" -> RecoverAI SUPPORTED_PAYMENT_TYPES. RecoverAI's supported
# types (credit_card/debit_card/boleto/voucher) come from the Olist (Brazil)
# training distribution, so Razorpay's India-centric methods (upi, netbanking,
# wallet, emi) have no exact analog. We map explicitly and flag the
# approximation rather than silently guessing.
METHOD_MAP = {
    "card": "credit_card",          # refined to debit_card below if card.type == 'debit'
    "emi": "credit_card",
    "upi": "debit_card",            # nearest analog: instant, account-linked debit
    "netbanking": "debit_card",
    "wallet": "debit_card",
}

# Explicit, documented neutral defaults for a Razorpay Test Mode customer with
# no real order history in RecoverAI's Olist-derived training distribution.
# These are NOT fabricated to look realistic — they are round, clearly-neutral
# values, and every response discloses that they were defaulted.
DEFAULT_HISTORY_CONTEXT = {
    "previous_order_count": 1,
    "previous_payment_count": 1,
    "previous_success_count": 0,
    "previous_cancelled_count": 0,
    "historical_payment_success_rate": 0.5,
    "customer_tenure_before_payment": 0,
    "order_frequency_before_payment": 0,
    "recovery_attempt_number": 1,
}


def _verify_webhook_signature(raw_body: bytes, signature_header: str, secret: str) -> bool:
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header or "")


def _map_method(payment: dict) -> dict:
    method = payment.get("method", "card")
    card_obj = payment.get("card")
    if not isinstance(card_obj, dict):
        card_obj = {}
    if method == "card" and card_obj.get("type") == "debit":
        return {"payment_type": "debit_card", "approximated": False}
    mapped = METHOD_MAP.get(method, "credit_card")
    return {"payment_type": mapped, "approximated": method not in ("card",)}


def _build_context(payment: dict, mapping: dict) -> dict:
    method_info = _map_method(payment)
    raw_amount = payment.get("amount")
    try:
        amount_rupees = float(raw_amount) / 100.0 if raw_amount is not None else 1.0
    except (ValueError, TypeError):
        amount_rupees = 1.0
    if amount_rupees <= 0:
        amount_rupees = 1.0

    context = {
        "payment_type": method_info["payment_type"],
        "payment_value": amount_rupees,
        "payment_installments": 1,
        "failure_category": mapping["failure_category"],
        "failure_reason": mapping["failure_reason"],
        "hours_since_failure": 0.0,
        "historical_average_payment": amount_rupees,
        **DEFAULT_HISTORY_CONTEXT,
    }
    return context, method_info


def _append_live_audit(record: dict):
    try:
        LIVE_AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _log_lock:
            has_content = LIVE_AUDIT_LOG_PATH.exists() and LIVE_AUDIT_LOG_PATH.stat().st_size > 0
            with open(LIVE_AUDIT_LOG_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(record.keys()))
                if not has_content:
                    writer.writeheader()
                writer.writerow(record)
    except Exception as e:
        print(f"[WARN] Failed to write live audit log: {e}", file=sys.stderr)


def _execute_retry(payment: dict, amount_rupees: float) -> dict:
    """Create a new Razorpay Test Mode Payment Link for the same amount.
    This is a REAL sandbox API call (no real money), demonstrating that
    RecoverAI's RETRY recommendation can drive a real action, not just a label."""
    if not RECOVERAI_LIVE_EXECUTE:
        return {"executed": False, "reason": "RECOVERAI_LIVE_EXECUTE=false"}

    key_id = os.environ.get("RAZORPAY_TEST_KEY_ID") or os.environ.get("RAZORPAY_KEY_ID")
    key_secret = os.environ.get("RAZORPAY_TEST_KEY_SECRET") or os.environ.get("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        return {"executed": False, "reason": "missing RAZORPAY_TEST_KEY_ID/SECRET or RAZORPAY_KEY_ID/SECRET"}
    if not key_id.startswith("rzp_test_"):
        return {"executed": False, "reason": "refused: key is not a rzp_test_ key"}

    try:
        import requests
        resp = requests.post(
            "https://api.razorpay.com/v1/payment_links",
            auth=(key_id, key_secret),
            json={
                "amount": int(round(amount_rupees * 100)),
                "currency": "INR",
                "description": f"RecoverAI RETRY recovery link for {payment.get('id', 'unknown')}",
                "notes": {"recoverai_source_payment_id": payment.get("id", "unknown"), "recoverai_action": "RETRY"},
            },
            timeout=10,
        )
        if resp.status_code >= 400:
            return {"executed": False, "reason": f"razorpay_api_error ({resp.status_code}): {resp.text}"}
        data = resp.json()
        return {"executed": True, "payment_link_id": data.get("id"), "short_url": data.get("short_url")}
    except requests.exceptions.Timeout:
        return {"executed": False, "reason": "razorpay_api_timeout (10s exceeded)"}
    except Exception as e:
        return {"executed": False, "reason": f"razorpay_api_error: {e}"}


@app.get("/health")
async def health():
    return {
        "status": "OK",
        "mode": "LIVE_RAZORPAY_TEST_MODE_BRIDGE",
        "model_hash": agent.model_artifact_hash,
        "calibrator_hash": agent.calibrator_artifact_hash,
        "live_execution_enabled": RECOVERAI_LIVE_EXECUTE,
    }


@app.post("/webhook/razorpay")
async def razorpay_webhook(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET")
    if not webhook_secret and os.environ.get("RECOVERAI_DEMO_MODE") == "true":
        webhook_secret = "recoverai_test_webhook_secret_2026"

    if not webhook_secret:
        raise HTTPException(status_code=500, detail="RAZORPAY_WEBHOOK_SECRET not configured on server")
    if not _verify_webhook_signature(raw_body, signature, webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Malformed JSON body")

    if body.get("event") != "payment.failed":
        return JSONResponse({"status": "IGNORED", "reason": f"event={body.get('event')} not handled"})

    try:
        raw_payment = body["payload"]["payment"]["entity"]
    except (KeyError, TypeError):
        raise HTTPException(status_code=400, detail="Malformed payment.failed payload")

    sanitized_payment = sanitize_payment_payload(raw_payment)
    mapping = map_to_recoverai_taxonomy(
        sanitized_payment.get("error_source", "unknown"),
        sanitized_payment.get("error_step", "unknown"),
        sanitized_payment.get("error_reason", "unknown"),
    )
    context, method_info = _build_context(sanitized_payment, mapping)

    try:
        decision = agent.recommend(context, request_id=sanitized_payment.get("id"))
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "SYSTEM_ERROR",
                "error_code": "RECOMMENDATION_ENGINE_ERROR",
                "message": "Internal error evaluating recovery recommendation",
                "detail": str(e),
            }
        )

    execution_result = {"executed": False, "reason": "not applicable for this action"}
    nudge_message = None
    if decision.get("status") == "SUCCESS":
        selected = decision.get("decision", {}).get("selected_action")
        if selected == "RETRY":
            execution_result = _execute_retry(sanitized_payment, context["payment_value"])
        elif selected == "NUDGE":
            nudge_message = (
                f"[SIMULATED — NOT SENT] Hi, your payment of Rs.{context['payment_value']:.2f} "
                f"didn't go through ({mapping['failure_reason'].replace('_', ' ')}). "
                f"Tap to retry: <payment_link_placeholder>"
            )
            execution_result = {"executed": False, "reason": "NUDGE has no SMS/WhatsApp gateway configured; message logged only"}

    response_payload = {
        "status": decision.get("status"),
        "request_id": decision.get("request_id"),
        "timestamp": decision.get("timestamp"),
        "razorpay_source": {
            "payment_id": sanitized_payment.get("id"),
            "error_code": sanitized_payment.get("error_code"),
            "error_source": sanitized_payment.get("error_source"),
            "error_step": sanitized_payment.get("error_step"),
            "error_reason": sanitized_payment.get("error_reason"),
        },
        "mapped_taxonomy": mapping,
        "context_provenance": {
            "payment_type_approximated": method_info["approximated"],
            "customer_history_defaulted": True,
            "note": "previous_order_count/historical_payment_success_rate/etc. use documented "
                    "neutral defaults (DEFAULT_HISTORY_CONTEXT) — this sandbox customer has no "
                    "real history in the Olist-derived training distribution.",
        },
        "decision": decision.get("decision"),
        "execution": execution_result,
        "nudge_message": nudge_message,
    }

    _append_live_audit({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "razorpay_payment_id": sanitized_payment.get("id"),
        "error_reason": sanitized_payment.get("error_reason"),
        "mapped_failure_category": mapping["failure_category"],
        "mapped_failure_reason": mapping["failure_reason"],
        "selected_action": decision.get("decision", {}).get("selected_action"),
        "recovery_probability": decision.get("decision", {}).get("recovery_probability"),
        "expected_utility": decision.get("decision", {}).get("expected_utility"),
        "executed": execution_result.get("executed"),
        "execution_detail": json.dumps(execution_result),
    })

    return JSONResponse(response_payload)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
