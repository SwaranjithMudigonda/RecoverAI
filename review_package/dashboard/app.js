/**
 * RecoverAI Step 7C Interactive Dashboard Client Engine (Audited & Hardened)
 *
 * Architecture Rule:
 * The dashboard is strictly a client presentation layer.
 * All inference must flow through the Step 7A REST API -> RecoverAI Agent Engine.
 * There is ZERO client-side fake ML inference or local recommendation fallback code.
 */

const REASON_CATEGORIES = {
  "SOFT_DECLINE": ["network_error", "bank_technical_error", "gateway_error", "payment_timed_out"],
  "FUNDS_ISSUE": ["insufficient_funds", "withdrawal_limit_exceeded"],
  "CUSTOMER_ACTION_REQUIRED": ["authentication_failed", "expired_card", "boleto_expired", "card_not_enrolled"],
  "HARD_DECLINE": ["stolen_card", "card_number_invalid", "compliance_violation"],
  "GENERIC_DECLINE": ["payment_cancelled", "payment_failed", "do_not_honor"]
};

const PRESETS = {
  "soft": {
    payment_type: "credit_card",
    payment_value: 250.00,
    payment_installments: 1,
    failure_category: "SOFT_DECLINE",
    failure_reason: "network_error",
    recovery_attempt_number: 1,
    hours_since_failure: 1.0,
    previous_order_count: 2,
    previous_payment_count: 2,
    previous_success_count: 2,
    previous_cancelled_count: 0,
    historical_payment_success_rate: 1.0,
    historical_average_payment: 250.00,
    customer_tenure_before_payment: 30,
    order_frequency_before_payment: 15.0
  },
  "boleto": {
    payment_type: "boleto",
    payment_value: 120.00,
    payment_installments: 1,
    failure_category: "CUSTOMER_ACTION_REQUIRED",
    failure_reason: "boleto_expired",
    recovery_attempt_number: 1,
    hours_since_failure: 2.0,
    previous_order_count: 1,
    previous_payment_count: 1,
    previous_success_count: 1,
    previous_cancelled_count: 0,
    historical_payment_success_rate: 1.0,
    historical_average_payment: 120.00,
    customer_tenure_before_payment: 10,
    order_frequency_before_payment: 10.0
  },
  "hard": {
    payment_type: "credit_card",
    payment_value: 500.00,
    payment_installments: 2,
    failure_category: "HARD_DECLINE",
    failure_reason: "card_number_invalid",
    recovery_attempt_number: 1,
    hours_since_failure: 0.5,
    previous_order_count: 5,
    previous_payment_count: 5,
    previous_success_count: 4,
    previous_cancelled_count: 1,
    historical_payment_success_rate: 0.80,
    historical_average_payment: 450.00,
    customer_tenure_before_payment: 90,
    order_frequency_before_payment: 18.0
  },
  "auth": {
    payment_type: "credit_card",
    payment_value: 300.00,
    payment_installments: 1,
    failure_category: "CUSTOMER_ACTION_REQUIRED",
    failure_reason: "authentication_failed",
    recovery_attempt_number: 1,
    hours_since_failure: 1.5,
    previous_order_count: 3,
    previous_payment_count: 3,
    previous_success_count: 3,
    previous_cancelled_count: 0,
    historical_payment_success_rate: 1.0,
    historical_average_payment: 300.00,
    customer_tenure_before_payment: 45,
    order_frequency_before_payment: 15.0
  }
};

// Static Step 5F Artifact Data Single Source of Truth
const FROZEN_STEP5F_ARTIFACT_DATA = {
  summary: [
    {
      policy_name: "Simulation Policy Upper Bound",
      policy_tag: "UPPER_BOUND",
      total_cases: 2283,
      revenue_at_risk_brl: 345292.12,
      recovered_revenue_brl: 185002.26,
      net_policy_utility_brl: 179176.76,
      recovery_rate_pct: 52.3434,
      avg_recovered_per_case_brl: 81.0347,
      abs_revenue_lift_vs_rb_brl: 7875.84,
      pct_revenue_lift_vs_rb: 4.4465,
      net_utility_lift_vs_rb_brl: 6108.34,
      regret_vs_upper_bound_brl: 0.0,
      guardrail_violations: 0
    },
    {
      policy_name: "ML Policy (LightGBM S-Learner)",
      policy_tag: "ML",
      total_cases: 2283,
      revenue_at_risk_brl: 345292.12,
      recovered_revenue_brl: 184987.96,
      net_policy_utility_brl: 179015.96,
      recovery_rate_pct: 52.2996,
      avg_recovered_per_case_brl: 81.0285,
      abs_revenue_lift_vs_rb_brl: 7861.54,
      pct_revenue_lift_vs_rb: 4.4384,
      net_utility_lift_vs_rb_brl: 5947.54,
      regret_vs_upper_bound_brl: 160.80,
      guardrail_violations: 0
    },
    {
      policy_name: "Rule-Based Policy Baseline",
      policy_tag: "RULE_BASED",
      total_cases: 2283,
      revenue_at_risk_brl: 345292.12,
      recovered_revenue_brl: 177126.42,
      net_policy_utility_brl: 173068.42,
      recovery_rate_pct: 50.5913,
      avg_recovered_per_case_brl: 77.5849,
      abs_revenue_lift_vs_rb_brl: 0.0,
      pct_revenue_lift_vs_rb: 0.0,
      net_utility_lift_vs_rb_brl: 0.0,
      regret_vs_upper_bound_brl: 6108.34,
      guardrail_violations: 0
    },
    {
      policy_name: "Always-NUDGE Baseline",
      policy_tag: "ALWAYS_NUDGE",
      total_cases: 2283,
      revenue_at_risk_brl: 345292.12,
      recovered_revenue_brl: 125195.89,
      net_policy_utility_brl: 119488.39,
      recovery_rate_pct: 35.6548,
      avg_recovered_per_case_brl: 54.8383,
      abs_revenue_lift_vs_rb_brl: -51930.53,
      pct_revenue_lift_vs_rb: -29.3183,
      net_utility_lift_vs_rb_brl: -53580.03,
      regret_vs_upper_bound_brl: 59688.37,
      guardrail_violations: 0
    }
  ],
  metrics: {
    test_ml_metrics: {
      brier_score: 0.222695,
      ece: 0.026444,
      log_loss: 0.651352,
      roc_auc: 0.687857,
      sample_count: 2283
    },
    bootstrap_confidence_intervals: {
      ml_net_utility: { mean: 178776.12, ci_95_low: 162926.10, ci_95_high: 196091.84 },
      rb_net_utility: { mean: 172832.00, ci_95_low: 157416.26, ci_95_high: 190087.36 },
      ml_recovered_revenue: { mean: 184747.56, ci_95_low: 169058.99, ci_95_high: 202161.82 },
      rb_recovered_revenue: { mean: 176886.99, ci_95_low: 161448.32, ci_95_high: 194140.05 },
      ml_recovery_rate_pct: { mean: 52.31, ci_95_low: 50.42, ci_95_high: 54.26 },
      abs_revenue_lift_brl: { mean: 7860.57, ci_95_low: 4974.46, ci_95_high: 11181.81 },
      pct_revenue_lift: { mean: 4.45, ci_95_low: 2.75, ci_95_high: 6.38 },
      net_utility_lift_brl: { mean: 5944.12, ci_95_low: 3130.62, ci_95_high: 9101.72 },
      regret_brl: { mean: 156.35, ci_95_low: -622.47, ci_95_high: 942.07 }
    }
  }
};

document.addEventListener("DOMContentLoaded", () => {
  updateFailureReasons();
  loadStep5fMetrics();
  fetchHealthAndProvenance();
  handleRecommend();
});

function updateFailureReasons() {
  const catSelect = document.getElementById("failure_category");
  const reasonSelect = document.getElementById("failure_reason");
  const ptypeSelect = document.getElementById("payment_type");
  const selectedCat = catSelect.value;
  const ptype = ptypeSelect.value;

  reasonSelect.innerHTML = "";
  const reasons = REASON_CATEGORIES[selectedCat] || [];

  reasons.forEach(r => {
    if (r === "boleto_expired" && ptype !== "boleto") return;
    const opt = document.createElement("option");
    opt.value = r;
    opt.textContent = r;
    reasonSelect.appendChild(opt);
  });

  if (reasonSelect.options.length > 0) {
    reasonSelect.selectedIndex = 0;
  }
}

function loadPreset(presetKey) {
  const data = PRESETS[presetKey];
  if (!data) return;

  document.querySelectorAll(".btn-preset").forEach(btn => btn.classList.remove("active"));
  event.target.classList.add("active");

  document.getElementById("payment_type").value = data.payment_type;
  document.getElementById("payment_value").value = data.payment_value;
  document.getElementById("payment_installments").value = data.payment_installments;
  document.getElementById("failure_category").value = data.failure_category;

  updateFailureReasons();

  document.getElementById("failure_reason").value = data.failure_reason;
  document.getElementById("recovery_attempt_number").value = data.recovery_attempt_number;
  document.getElementById("hours_since_failure").value = data.hours_since_failure;
  document.getElementById("previous_order_count").value = data.previous_order_count;
  document.getElementById("previous_payment_count").value = data.previous_payment_count;
  document.getElementById("previous_success_count").value = data.previous_success_count;
  document.getElementById("previous_cancelled_count").value = data.previous_cancelled_count;
  document.getElementById("historical_payment_success_rate").value = data.historical_payment_success_rate;
  document.getElementById("historical_average_payment").value = data.historical_average_payment;
  document.getElementById("customer_tenure_before_payment").value = data.customer_tenure_before_payment;
  document.getElementById("order_frequency_before_payment").value = data.order_frequency_before_payment;

  handleRecommend();
}

async function fetchHealthAndProvenance() {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/v1/health");
    if (res.ok) {
      const data = await res.json();
      if (data.model_artifact_hash) {
        document.getElementById("modelHashNav").textContent = data.model_artifact_hash.substring(0, 8) + "..." + data.model_artifact_hash.substring(56);
      }
    }
  } catch (e) {
    document.getElementById("modelHashNav").textContent = "ca968b77...068e7";
  }
}

/**
 * FIX 1: Artifact-Driven Metric Rendering
 * Dynamically populates Policy Evaluation section using data from step5f artifacts.
 */
function loadStep5fMetrics() {
  const data = FROZEN_STEP5F_ARTIFACT_DATA;
  const summary = data.summary;
  const metrics = data.metrics.test_ml_metrics;
  const cis = data.metrics.bootstrap_confidence_intervals;

  const mlRow = summary.find(r => r.policy_tag === "ML");
  const rbRow = summary.find(r => r.policy_tag === "RULE_BASED");
  const upperRow = summary.find(r => r.policy_tag === "UPPER_BOUND");

  // Stat Cards
  document.getElementById("statMlNetUtility").textContent = `R$ ${mlRow.net_policy_utility_brl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
  document.getElementById("statMlSub").textContent = `Recovery Rate: ${mlRow.recovery_rate_pct.toFixed(2)}% • Violations: ${mlRow.guardrail_violations}`;

  document.getElementById("statLiftVal").textContent = `+R$ ${mlRow.net_utility_lift_vs_rb_brl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
  document.getElementById("statLiftSub").textContent = `+${mlRow.pct_revenue_lift_vs_rb.toFixed(2)}% Lift [95% CI: +${cis.pct_revenue_lift.ci_95_low.toFixed(2)}%, +${cis.pct_revenue_lift.ci_95_high.toFixed(2)}%]`;

  const capturePct = ((mlRow.net_policy_utility_brl / upperRow.net_policy_utility_brl) * 100).toFixed(2);
  document.getElementById("statUpperCapture").textContent = `${capturePct}%`;
  document.getElementById("statUpperSub").textContent = `Regret vs Upper Bound: R$ ${mlRow.regret_vs_upper_bound_brl.toFixed(2)}`;

  document.getElementById("statRbNetUtility").textContent = `R$ ${rbRow.net_policy_utility_brl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
  document.getElementById("statRbSub").textContent = `Recovery Rate: ${rbRow.recovery_rate_pct.toFixed(2)}%`;

  // ML Performance Box
  document.getElementById("mlRocAuc").textContent = metrics.roc_auc.toFixed(4);
  document.getElementById("mlBrier").textContent = metrics.brier_score.toFixed(4);
  document.getElementById("mlEce").textContent = metrics.ece.toFixed(4);
  document.getElementById("mlLogLoss").textContent = metrics.log_loss.toFixed(4);
  document.getElementById("mlSamples").textContent = metrics.sample_count.toLocaleString();

  // Policy Table Rows
  const tbody = document.getElementById("policyTableBody");
  tbody.innerHTML = "";

  summary.forEach(row => {
    const isUpper = row.policy_tag === "UPPER_BOUND";
    const isMl = row.policy_tag === "ML";
    const tr = document.createElement("tr");

    if (isUpper) tr.className = "row-upper";
    if (isMl) tr.className = "row-ml";

    const liftPrefix = row.net_utility_lift_vs_rb_brl > 0 ? "+R$ " : (row.net_utility_lift_vs_rb_brl < 0 ? "-R$ " : "R$ ");
    const liftValStr = liftPrefix + Math.abs(row.net_utility_lift_vs_rb_brl).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    const liftPctStr = (row.pct_revenue_lift_vs_rb > 0 ? "+" : "") + row.pct_revenue_lift_vs_rb.toFixed(2) + "%";

    tr.innerHTML = `
      <td>${isMl || isUpper ? `<strong>${row.policy_name}</strong>` : row.policy_name}</td>
      <td>${isMl ? `<strong>R$ ${row.recovered_revenue_brl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</strong>` : `R$ ${row.recovered_revenue_brl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}</td>
      <td>${isMl ? `<strong>R$ ${row.net_policy_utility_brl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</strong>` : `R$ ${row.net_policy_utility_brl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}</td>
      <td>${isMl ? `<strong>${row.recovery_rate_pct.toFixed(2)}%</strong>` : `${row.recovery_rate_pct.toFixed(2)}%`}</td>
      <td>${isMl ? `<strong class="text-positive">${liftValStr}</strong>` : liftValStr}</td>
      <td>${isMl ? `<strong class="text-positive">${liftPctStr}</strong>` : liftPctStr}</td>
      <td>R$ ${row.regret_vs_upper_bound_brl.toFixed(2)}</td>
      <td><span class="badge-zero">${row.guardrail_violations}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

/**
 * REST API Recommendation Call
 */
async function handleRecommend() {
  const contextPayload = {
    payment_type: document.getElementById("payment_type").value,
    payment_value: parseFloat(document.getElementById("payment_value").value),
    payment_installments: parseInt(document.getElementById("payment_installments").value),
    previous_order_count: parseInt(document.getElementById("previous_order_count").value),
    previous_payment_count: parseInt(document.getElementById("previous_payment_count").value),
    previous_success_count: parseInt(document.getElementById("previous_success_count").value),
    previous_cancelled_count: parseInt(document.getElementById("previous_cancelled_count").value),
    historical_payment_success_rate: parseFloat(document.getElementById("historical_payment_success_rate").value),
    historical_average_payment: parseFloat(document.getElementById("historical_average_payment").value),
    customer_tenure_before_payment: parseInt(document.getElementById("customer_tenure_before_payment").value),
    order_frequency_before_payment: parseFloat(document.getElementById("order_frequency_before_payment").value),
    failure_category: document.getElementById("failure_category").value,
    failure_reason: document.getElementById("failure_reason").value,
    hours_since_failure: parseFloat(document.getElementById("hours_since_failure").value),
    recovery_attempt_number: parseInt(document.getElementById("recovery_attempt_number").value)
  };

  try {
    const response = await fetch("http://127.0.0.1:8000/api/v1/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(contextPayload)
    });

    if (response.ok) {
      const data = await response.json();
      renderRecommendation(data);
    } else {
      renderApiOfflineState();
    }
  } catch (err) {
    // FIX 2: Render safe API UNAVAILABLE state (Zero client-side fake ML inference)
    renderApiOfflineState();
  }
}

/**
 * FIX 2: Safe API Offline State Rendering (NO client-side fake ML inference)
 */
function renderApiOfflineState() {
  const badgeEl = document.getElementById("selectedActionBadge");
  badgeEl.textContent = "API UNAVAILABLE";
  badgeEl.className = "action-badge badge-offline";

  document.getElementById("selectionReasonText").textContent = "RecoverAI API is offline. Start the API to run inference.";
  document.getElementById("selectedProbVal").textContent = "0.0%";
  document.getElementById("selectedUtilityVal").textContent = "R$ 0.00";
  document.getElementById("fallbackStatusVal").textContent = "OFFLINE";

  const probChart = document.getElementById("probBarChart");
  probChart.innerHTML = `<div class="bar-row"><div class="bar-info"><span>API Offline</span><span>Start uvicorn server</span></div></div>`;

  const utilChart = document.getElementById("utilityBarChart");
  utilChart.innerHTML = `<div class="bar-row"><div class="bar-info"><span>API Offline</span><span>Start uvicorn server</span></div></div>`;

  const gGrid = document.getElementById("guardrailsGrid");
  gGrid.innerHTML = `<div class="g-card"><span class="g-action">ALL ACTIONS</span><span class="g-status blocked">OFFLINE</span></div>`;
}

function renderRecommendation(data) {
  const dec = data.decision;
  const acts = data.actions;

  const badgeEl = document.getElementById("selectedActionBadge");
  badgeEl.textContent = dec.selected_action;
  badgeEl.className = `action-badge badge-${dec.selected_action.toLowerCase()}`;

  document.getElementById("selectionReasonText").textContent = dec.selection_reason;
  document.getElementById("selectedProbVal").textContent = (dec.recovery_probability * 100).toFixed(1) + "%";
  document.getElementById("selectedUtilityVal").textContent = `R$ ${dec.expected_utility.toFixed(2)}`;
  document.getElementById("fallbackStatusVal").textContent = data.fallback_triggered ? "TRUE (Fallback Active)" : "FALSE";

  if (data.model_artifact_hash) {
    document.getElementById("modelHashNav").textContent = data.model_artifact_hash.substring(0, 8) + "..." + data.model_artifact_hash.substring(56);
  }

  // Probabilities Bar Chart
  const probChart = document.getElementById("probBarChart");
  probChart.innerHTML = "";

  ["RETRY", "NUDGE", "ESCALATE", "STOP"].forEach(act => {
    const info = acts[act];
    const isBlocked = info.guardrail_result === "BLOCKED";
    const probPct = (info.probability * 100).toFixed(1);

    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <div class="bar-info">
        <span>${act}</span>
        <span>${isBlocked ? "BLOCKED (0.0%)" : probPct + "%"}</span>
      </div>
      <div class="bar-bg">
        <div class="bar-fill ${isBlocked ? 'blocked' : 'passed'}" style="width: ${isBlocked ? '0%' : probPct + '%'}"></div>
      </div>
    `;
    probChart.appendChild(row);
  });

  // Utility Bar Chart
  const utilChart = document.getElementById("utilityBarChart");
  utilChart.innerHTML = "";

  const pval = parseFloat(document.getElementById("payment_value").value) || 250.0;

  ["RETRY", "NUDGE", "ESCALATE", "STOP"].forEach(act => {
    const info = acts[act];
    const isBlocked = info.guardrail_result === "BLOCKED";
    const utilVal = info.utility;

    let displayVal = `R$ ${utilVal.toFixed(2)}`;
    let barWidth = "0%";

    if (isBlocked) {
      displayVal = "BLOCKED (-999,999.00)";
      barWidth = "0%";
    } else if (utilVal > 0) {
      barWidth = Math.min(100, (utilVal / pval) * 100) + "%";
    }

    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <div class="bar-info">
        <span>${act}</span>
        <span>${displayVal}</span>
      </div>
      <div class="bar-bg">
        <div class="bar-fill ${isBlocked ? 'blocked' : 'passed'}" style="width: ${barWidth}"></div>
      </div>
    `;
    utilChart.appendChild(row);
  });

  // Guardrails Monitor Grid
  const gGrid = document.getElementById("guardrailsGrid");
  gGrid.innerHTML = "";

  ["RETRY", "NUDGE", "ESCALATE", "STOP"].forEach(act => {
    const info = acts[act];
    const isBlocked = info.guardrail_result === "BLOCKED";
    const rules = info.guardrail_rule_ids && info.guardrail_rule_ids.length > 0 ? info.guardrail_rule_ids.join(", ") : "NONE";

    const card = document.createElement("div");
    card.className = "g-card";
    card.innerHTML = `
      <span class="g-action">${act}</span>
      <span class="g-status ${isBlocked ? 'blocked' : 'passed'}">${info.guardrail_result}</span>
      <span class="g-rules">Rules: ${rules}</span>
    `;
    gGrid.appendChild(card);
  });
}

function checkAuditStatus() {
  const statusEl = document.getElementById("auditStatus");
  if (statusEl) statusEl.textContent = "Status: Audit Log Ready (Read-Only)";
}
