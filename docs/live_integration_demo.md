# Live Razorpay Test Mode Integration — Setup & Demo Script

**New capability, additive to the existing system.** Everything in the
original README (Steps 4E-7E, frozen Step 5F evaluation, the FastAPI
`/api/v1/recommend` service, the batch runner) is unchanged and still frozen.
This adds a third, live entry point sitting *alongside* those.

## Why this exists

The project already had strong **offline** evidence that RecoverAI understands
Razorpay's real error schema (`docs/razorpay_schema_mapping.md`,
`tests/test_razorpay_schema.py`). What it didn't have was proof that the
agent can sit behind a **real, running Razorpay Test Mode webhook** and make
(and optionally act on) a live decision — not a canned demo payload. That's
what `src/integrations/razorpay_live.py` adds.

```
Razorpay Test Mode sandbox (rzp_test_... keys)
        │  real payment.failed webhook
        ▼
POST /webhook/razorpay   (src/integrations/razorpay_live.py)
        │  HMAC-verified → sanitized → mapped to RecoverAI taxonomy
        ▼
RecoverAI.recommend()    (the SAME frozen Step 6D agent — src/recoverai_agent.py)
        │
        ├─ RETRY     → creates a real Test Mode Payment Link (execution, not just a label)
        ├─ NUDGE     → simulated reminder text, clearly logged as not sent
        └─ ESCALATE/STOP → logged only
        │
        ▼
data/processed/live_decisions_audit_log.csv   (separate from the frozen audit log)
```

## 1. One-time setup (~15 min)

1. **Get Test Mode API keys.** Razorpay Dashboard → toggle to **Test Mode** →
   Settings → API Keys → Generate Test Key. You'll get a `rzp_test_...` key
   ID and secret. These are sandbox-only; no real money ever moves.

2. **Install deps** (if not already present):
   ```bash
   pip install fastapi uvicorn requests --break-system-packages
   ```

3. **Set environment variables:**
   ```bash
   export RAZORPAY_TEST_KEY_ID="rzp_test_xxxxxxxxxxxx"
   export RAZORPAY_TEST_KEY_SECRET="your_test_secret"
   export RAZORPAY_WEBHOOK_SECRET="pick-any-string-you-also-put-in-the-dashboard"
   ```

4. **Start the live bridge:**
   ```bash
   uvicorn src.integrations.razorpay_live:app --port 8010 --reload
   ```
   Check `curl http://localhost:8010/health` returns `LIVE_RAZORPAY_TEST_MODE_BRIDGE`
   with the same `model_hash` your frozen `/api/v1/health` reports.

5. **Expose it to Razorpay's servers.** Razorpay's sandbox needs to reach your
   machine over the internet to deliver the webhook — use a tunnel:
   ```bash
   ngrok http 8010
   ```
   Copy the `https://<random>.ngrok-free.app` URL it prints.

6. **Register the webhook in Razorpay.** Dashboard (Test Mode) → Settings →
   Webhooks → Add New Webhook:
   - URL: `https://<your-ngrok-url>/webhook/razorpay`
   - Secret: the same string as `RAZORPAY_WEBHOOK_SECRET`
   - Active events: check **`payment.failed`**

## 2. Trigger a real failure and watch it decide

```bash
python tools/trigger_test_failure.py --scenario insufficient_funds --amount 499
```
This prints a real sandbox Payment Link and a matching Razorpay test card.
Open the link, enter the card, and click **Failure** on the mock bank screen.
Within a few seconds your `uvicorn` terminal shows the webhook arrive, get
mapped, and get a decision — check `data/processed/live_decisions_audit_log.csv`
for the row.

**No internet during the actual pitch, or want a guaranteed take?** Use the
offline replay fallback, which exercises the identical code path without
depending on Razorpay's sandbox or your internet connection:
```bash
python tools/trigger_test_failure.py --offline-replay --scenario authentication_failed --amount 499
```
If you use this in front of judges, say so explicitly — it's a rehearsal
replay of a real webhook shape, not a live sandbox call. Keep the live path
as your primary demo and this as insurance.

## 3. What to say to judges

- "Everyone in this track will show an ML model and a metrics table. Here's
  what's different: this is wired to Razorpay's actual Test Mode sandbox.
  I'm going to fail a real payment right now." *(trigger it live)*
- "That's not a mock — Razorpay just sent a real webhook, RecoverAI mapped its
  real error schema to our taxonomy, and it decided RETRY / NUDGE / ESCALATE
  in real time." *(point at the terminal + audit CSV)*
- If RETRY: "It didn't just recommend — it went and created a real recovery
  Payment Link in Razorpay's sandbox." *(open the short_url from the response)*
- Be upfront about the honest limits (this is also a strength, not a
  weakness, if you say it plainly): "Two things are still approximated here
  and I want to be transparent about them: Razorpay's Indian payment methods
  (UPI, netbanking) don't map 1:1 onto our Olist-trained payment types, and a
  fresh sandbox customer has no real order history, so we use documented
  neutral defaults instead of inventing realistic-looking numbers. Both are
  disclosed in every API response under `context_provenance`."

## 4. Scope boundary (keep saying this — it's the project's biggest strength)

This live bridge does **not** change, retrain, or re-evaluate anything in
Tier A (the frozen Step 5E/5F ML pipeline and its R$179,015.96 net-utility
benchmark) or Tier B (the offline schema fixtures). It's a new, additive input
path that calls the exact same `RecoverAI.recommend()` used by the existing
REST API — so every safety guardrail (GR01-GR06), the leakage/credential
rejection, and the calibrated probability model apply identically here. What's
new is that the *input* now comes from a real gateway sandbox instead of a
hand-typed JSON body.
