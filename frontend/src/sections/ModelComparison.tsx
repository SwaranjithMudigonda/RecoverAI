import React from 'react';
import { FROZEN_MODEL_COMPARISON_DATA } from '../data/frozenEvaluation';

export const ModelComparison: React.FC = () => {
  const comp = FROZEN_MODEL_COMPARISON_DATA;

  const rows = [
    { metric: 'Test ROC-AUC', a: comp.aucA.toFixed(4), b: comp.aucB.toFixed(4), rb: '—' },
    { metric: 'Test Brier Score', a: comp.brierA.toFixed(4), b: comp.brierB.toFixed(4), rb: '—' },
    { metric: 'Expected Calibration Error (ECE)', a: comp.eceA.toFixed(4), b: comp.eceB.toFixed(4), rb: '—' },
    { metric: 'Test Log Loss', a: comp.lossA.toFixed(4), b: comp.lossB.toFixed(4), rb: '—' },
    { metric: 'Recovery Rate', a: comp.rateA, b: comp.rateB, rb: '50.59%' },
    { metric: 'Net Policy Utility', a: comp.utilA, b: comp.utilB, rb: 'R$ 173,068.42' },
    { metric: 'Regret vs Upper Bound', a: comp.regretA, b: comp.regretB, rb: 'R$ 6,108.34' },
  ];

  return (
    <section id="benchmarks" className="bg-[#111820] border border-[#26313D] rounded-xl p-5 sm:p-6">
      <div className="pb-4 mb-4 border-b border-[#26313D]">
        <h2 className="text-base font-semibold text-[#F3F5F7]">
          Supplementary Model Benchmark Comparison
        </h2>
        <span className="text-xs text-[#9AA6B2]">
          Comparative analysis on held-out test dataset (N = 2,283 cases)
        </span>
      </div>

      <div className="overflow-x-auto mb-4">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-[#26313D] text-[#9AA6B2] text-[11px] font-medium">
              <th className="py-2.5 px-3">Metric</th>
              <th className="py-2.5 px-3 text-blue-400">
                Model A: LightGBM + Isotonic (Primary)
              </th>
              <th className="py-2.5 px-3">
                Model B: Logistic Regression + Isotonic (Baseline)
              </th>
              <th className="py-2.5 px-3">
                Rule-Based Policy Baseline
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#26313D]/60 font-mono">
            {rows.map(r => (
              <tr key={r.metric} className="hover:bg-[#141B23] transition-colors">
                <td className="py-2.5 px-3 font-sans font-medium text-[#F3F5F7]">
                  {r.metric}
                </td>
                <td className="py-2.5 px-3 text-blue-400 font-semibold bg-blue-950/10">
                  {r.a}
                </td>
                <td className="py-2.5 px-3 text-[#9AA6B2]">
                  {r.b}
                </td>
                <td className="py-2.5 px-3 text-[#667380]">
                  {r.rb}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Methodological Insight */}
      <div className="bg-[#141B23] border border-[#26313D] rounded-lg p-3.5 text-xs text-[#9AA6B2] leading-relaxed">
        <span className="font-semibold text-[#F3F5F7]">Methodological Insight: </span>
        Comparable probability metrics do not necessarily imply comparable policy performance. In this S-learner setting, action-context interactions materially affect downstream utility optimization. Model B (Logistic Regression) is highly competitive on basic probability distance metrics (achieving a slightly better Brier Score and Log Loss). However, Model A (LightGBM) delivers substantially stronger policy-level performance, capturing more utility and reducing regret by 152× because tree ensembles learn action-context interactions natively.
      </div>
    </section>
  );
};
