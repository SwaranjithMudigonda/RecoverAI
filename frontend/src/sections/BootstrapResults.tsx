import React from 'react';
import { FROZEN_STEP5F_ARTIFACT_DATA } from '../data/frozenEvaluation';
import { formatBRL } from '../lib/utils';

export const BootstrapResults: React.FC = () => {
  const cis = FROZEN_STEP5F_ARTIFACT_DATA.metrics.bootstrap_confidence_intervals;

  const rows = [
    {
      metric: 'ML Policy Net Utility',
      mean: formatBRL(cis.ml_net_utility.mean),
      low: formatBRL(cis.ml_net_utility.ci_95_low),
      high: formatBRL(cis.ml_net_utility.ci_95_high),
      ci: `[${formatBRL(cis.ml_net_utility.ci_95_low)}, ${formatBRL(cis.ml_net_utility.ci_95_high)}]`,
      type: 'currency',
    },
    {
      metric: 'Rule-Based Net Utility',
      mean: formatBRL(cis.rb_net_utility.mean),
      low: formatBRL(cis.rb_net_utility.ci_95_low),
      high: formatBRL(cis.rb_net_utility.ci_95_high),
      ci: `[${formatBRL(cis.rb_net_utility.ci_95_low)}, ${formatBRL(cis.rb_net_utility.ci_95_high)}]`,
      type: 'currency',
    },
    {
      metric: 'Net Utility Lift (vs Rule-Based)',
      mean: `+${formatBRL(cis.net_utility_lift_brl.mean)}`,
      low: `+${formatBRL(cis.net_utility_lift_brl.ci_95_low)}`,
      high: `+${formatBRL(cis.net_utility_lift_brl.ci_95_high)}`,
      ci: `[+${formatBRL(cis.net_utility_lift_brl.ci_95_low)}, +${formatBRL(cis.net_utility_lift_brl.ci_95_high)}]`,
      type: 'lift',
    },
    {
      metric: 'Gross Revenue Lift %',
      mean: `+${cis.pct_revenue_lift.mean.toFixed(2)}%`,
      low: `+${cis.pct_revenue_lift.ci_95_low.toFixed(2)}%`,
      high: `+${cis.pct_revenue_lift.ci_95_high.toFixed(2)}%`,
      ci: `[+${cis.pct_revenue_lift.ci_95_low.toFixed(2)}%, +${cis.pct_revenue_lift.ci_95_high.toFixed(2)}%]`,
      type: 'lift',
    },
    {
      metric: 'ML Recovery Rate',
      mean: `${cis.ml_recovery_rate_pct.mean.toFixed(2)}%`,
      low: `${cis.ml_recovery_rate_pct.ci_95_low.toFixed(2)}%`,
      high: `${cis.ml_recovery_rate_pct.ci_95_high.toFixed(2)}%`,
      ci: `[${cis.ml_recovery_rate_pct.ci_95_low.toFixed(2)}%, ${cis.ml_recovery_rate_pct.ci_95_high.toFixed(2)}%]`,
      type: 'percent',
    },
    {
      metric: 'Policy Regret vs Upper Bound',
      mean: formatBRL(cis.regret_brl.mean),
      low: formatBRL(cis.regret_brl.ci_95_low),
      high: formatBRL(cis.regret_brl.ci_95_high),
      ci: `[${formatBRL(cis.regret_brl.ci_95_low)}, ${formatBRL(cis.regret_brl.ci_95_high)}]`,
      type: 'currency',
    },
  ];

  return (
    <section className="bg-[#111820] border border-[#26313D] rounded-xl p-5 sm:p-6 space-y-4">
      <div className="pb-4 border-b border-[#26313D] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-[#F3F5F7]">
            Bootstrap Statistical Inference (Simulated 95% CIs)
          </h2>
          <span className="text-xs text-[#9AA6B2]">
            Non-parametric bootstrap estimation (B = 1,000 resamples on held-out test distribution). Delineates point estimates from inferential uncertainty bounds.
          </span>
        </div>
        <span className="px-2.5 py-1 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-mono font-semibold shrink-0">
          p &lt; 0.05 (Significant)
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-[#26313D] text-[#9AA6B2] text-[11px] font-medium">
              <th className="py-2.5 px-3">Evaluation Metric</th>
              <th className="py-2.5 px-3">Bootstrap Mean</th>
              <th className="py-2.5 px-3">Visual CI Range (95%)</th>
              <th className="py-2.5 px-3 text-right">Confidence Interval</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#26313D]/60 font-mono">
            {rows.map(r => (
              <tr key={r.metric} className="hover:bg-[#141B23] transition-colors">
                <td className="py-3 px-3 font-sans font-medium text-[#F3F5F7]">
                  {r.metric}
                </td>
                <td className={`py-3 px-3 font-bold ${r.type === 'lift' ? 'text-emerald-400' : 'text-[#F3F5F7]'}`}>
                  {r.mean}
                </td>
                {/* Visual CI range bar */}
                <td className="py-3 px-3 min-w-[140px]">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-[#667380] font-mono">{r.low}</span>
                    <div className="relative flex-1 h-1.5 bg-[#16202C] rounded-full overflow-hidden">
                      <div
                        className={`absolute inset-y-0 rounded-full ${
                          r.type === 'lift' ? 'bg-emerald-500' : 'bg-blue-500'
                        }`}
                        style={{ left: '20%', right: '20%' }}
                      />
                      <div
                        className="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-white ring-2 ring-blue-400"
                        style={{ left: '50%' }}
                      />
                    </div>
                    <span className="text-[10px] text-[#667380] font-mono">{r.high}</span>
                  </div>
                </td>
                <td className="py-3 px-3 text-right text-[#9AA6B2]">
                  {r.ci}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};
