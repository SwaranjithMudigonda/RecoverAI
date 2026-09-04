"""
tests/test_razorpay_live_bridge.py
==================================

Unit and contract test suite for the live Razorpay bridge (src/integrations/razorpay_live.py).
Tests the HMAC signature verification, payload sanitization, taxonomy mapping,
agent recommendation invocation, audit logging, and error handling.
"""

import os
import sys
import json
import hmac
import hashlib
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.integrations.razorpay_live import app, agent, _verify_webhook_signature, _map_method, _build_context

client = TestClient(app)
TEST_SECRET = "recoverai_test_webhook_secret_2026"


def _make_signed_request(payload: dict, secret: str = TEST_SECRET):
    raw_body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return client.post(
        "/webhook/razorpay",
        data=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )


class TestRazorpayLiveBridge:
    """Test suite for live Razorpay bridge endpoints and logic."""

    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "OK"
        assert data["mode"] == "LIVE_RAZORPAY_TEST_MODE_BRIDGE"
        assert data["model_hash"] == agent.model_artifact_hash
        assert data["calibrator_hash"] == agent.calibrator_artifact_hash

    def test_signature_verification_success_and_failure(self):
        body = b'{"test": "data"}'
        sig = hmac.new(TEST_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
        assert _verify_webhook_signature(body, sig, TEST_SECRET) is True
        assert _verify_webhook_signature(body, "wrong_sig", TEST_SECRET) is False
        assert _verify_webhook_signature(body, "", TEST_SECRET) is False

    def test_webhook_rejects_invalid_signature(self):
        resp = client.post(
            "/webhook/razorpay",
            json={"event": "payment.failed"},
            headers={"X-Razorpay-Signature": "invalid_sig"},
        )
        assert resp.status_code == 401
        assert "Invalid webhook signature" in resp.json()["detail"]

    def test_webhook_ignores_non_failed_events(self):
        payload = {"event": "payment.authorized", "payload": {}}
        resp = _make_signed_request(payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "IGNORED"

    def test_webhook_rejects_malformed_payload(self):
        payload = {"event": "payment.failed", "payload": {"not_payment": {}}}
        resp = _make_signed_request(payload)
        assert resp.status_code == 400

    def test_webhook_insufficient_funds_end_to_end(self):
        payload = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_if_12345",
                        "entity": "payment",
                        "amount": 49900,
                        "currency": "INR",
                        "status": "failed",
                        "method": "card",
                        "card": {"type": "credit"},
                        "error_code": "BAD_REQUEST_ERROR",
                        "error_description": "Payment failed due to insufficient funds",
                        "error_source": "bank",
                        "error_step": "payment_authorization",
                        "error_reason": "insufficient_funds",
                        "contact": "+919988776655",
                        "email": "customer@example.com",
                    }
                }
            },
        }
        resp = _make_signed_request(payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUCCESS"
        assert "decision" in data
        assert data["mapped_taxonomy"]["failure_category"] == "FUNDS_ISSUE"
        assert data["mapped_taxonomy"]["failure_reason"] == "insufficient_funds"
        assert data["decision"]["selected_action"] in ("NUDGE", "RETRY", "STOP", "ESCALATE")
        assert "context_provenance" in data
        assert data["context_provenance"]["customer_history_defaulted"] is True

    def test_method_mapping_card_and_upi(self):
        card_pay = {"method": "card", "card": {"type": "credit"}}
        assert _map_method(card_pay)["payment_type"] == "credit_card"

        debit_pay = {"method": "card", "card": {"type": "debit"}}
        assert _map_method(debit_pay)["payment_type"] == "debit_card"

        upi_pay = {"method": "upi"}
        assert _map_method(upi_pay)["payment_type"] == "debit_card"

        # Safe against None card
        null_card_pay = {"method": "card", "card": None}
        assert _map_method(null_card_pay)["payment_type"] == "credit_card"
