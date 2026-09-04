# Track 03 Alignment & Roadmap

**Track brief:** "Build an agent that detects revenue at risk, determines the
right intervention, and executes a bounded recovery workflow: from payment
failures and checkout abandonment to overdue receivables."

RecoverAI's current scope — post-decline payment recovery — is the track's
own first example direction ("Payment degradation → root cause → recovery
action"), built end-to-end and evaluated against **The Bar**:

| The Bar | RecoverAI |
|---|---|
| Measured money recovered across a batch | Step 5F: R$184,987.96 recovered / 2,283 held-out cases, +4.44% lift vs. rule-based baseline, 1,000-sample bootstrap CIs |
| Compliant escalation | Guardrail engine (GR01–GR06) + `ESCALATE` as a first-class action with its own cost and expected utility |
| Stopping rules | `STOP` is a modeled action, not an error fallback — selected whenever every active action has negative expected utility |
| Audit trail | Thread-safe CSV audit logger (frozen decisions) + a separate live audit log for the Razorpay Test Mode bridge |

## Why the same architecture generalizes to the brief's other directions

The core decision loop — **candidate actions → guardrails → calibrated
P(recovery) → net expected utility → argmax, with a hard STOP floor** — is not
payment-failure-specific. Each other example direction slots into the same
four-part interface (context schema in, guardrail rules, an action set with
costs, a probability model) rather than needing a new architecture:

- **Checkout drop-off recovery** — same `NUDGE`/`STOP` action pair, new
  context schema (cart contents, time-since-abandon instead of
  failure_category/failure_reason).
- **Failed-subscription recovery** — `RETRY` becomes "retry the mandate
  charge," with the exact same GR05 (attempt cap) and GR06 (value cap)
  guardrail shapes.
- **B2B receivables / promise-to-pay tracker** — `ESCALATE` becomes "route to
  a collections rep," and a new `PROMISE_LOGGED` action would sit at the same
  utility-comparison layer, with the audit logger already built to record it.
- **Mandate retry sequencer** — is literally the existing `recovery_attempt_number`
  + GR05 guardrail, generalized from card retries to UPI/NACH mandate retries.
- **Hinglish voice recovery** — a channel decision downstream of the existing
  `NUDGE`/`ESCALATE` choice, not a new decision layer; the agent already
  outputs an action + reason, independent of which channel delivers it.

None of this is built — it's explicitly scoped as roadmap, not claimed as
done. The point for judges: the one direction that's fully built (payment
recovery) is a real instance of a general architecture, not a one-off script,
which is why extending it to the other four is a schema-and-cost-table change
rather than a rewrite.
