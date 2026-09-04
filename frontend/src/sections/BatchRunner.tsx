import React, { useState } from 'react';
import {
  Play,
  RotateCcw,
  Download,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Layers,
  Sparkles,
  TrendingUp,
  FileText
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { fetchRecommendation } from '../lib/api';
import { formatBRL, formatPercent } from '../lib/utils';
import type { PaymentContext, RecommendationResponse, ActionType } from '../types/recovery';

interface BatchItem {
  id: string;
  context: PaymentContext;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'ERROR';
  recommendation?: RecommendationResponse;
  latencyMs?: number;
  error?: string;
}

const SAMPLE_OLIST_BATCH: Array<{ id: string; name: string; context: PaymentContext }> = [
  {
    id: 'TXN-9021',
    name: 'Soft Decline - Credit Card (Loyal Customer)',
    context: {
      payment_type: 'credit_card',
      payment_value: 285.50,
      payment_installments: 3,
      previous_order_count: 5,
      previous_payment_count: 7,
      previous_success_count: 6,
      previous_cancelled_count: 1,
      historical_payment_success_rate: 0.857,
      historical_average_payment: 240.00,
      customer_tenure_before_payment: 180,
      order_frequency_before_payment: 0.028,
      failure_category: 'SOFT_DECLINE',
      failure_reason: 'network_error',
      hours_since_failure: 1.5,
      recovery_attempt_number: 1,
    },
  },
  {
    id: 'TXN-9022',
    name: 'Hard Decline - Stolen/Invalid Card',
    context: {
      payment_type: 'credit_card',
      payment_value: 412.00,
      payment_installments: 1,
      previous_order_count: 1,
      previous_payment_count: 1,
      previous_success_count: 1,
      previous_cancelled_count: 0,
      historical_payment_success_rate: 1.0,
      historical_average_payment: 412.00,
      customer_tenure_before_payment: 30,
      order_frequency_before_payment: 0.033,
      failure_category: 'HARD_DECLINE',
      failure_reason: 'stolen_card',
      hours_since_failure: 0.5,
      recovery_attempt_number: 1,
    },
  },
  {
    id: 'TXN-9023',
    name: 'Boleto Bancario - Pending Cash Slip',
    context: {
      payment_type: 'boleto',
      payment_value: 154.20,
      payment_installments: 1,
      previous_order_count: 2,
      previous_payment_count: 2,
      previous_success_count: 2,
      previous_cancelled_count: 0,
      historical_payment_success_rate: 1.0,
      historical_average_payment: 130.00,
      customer_tenure_before_payment: 60,
      order_frequency_before_payment: 0.033,
      failure_category: 'CUSTOMER_ACTION_REQUIRED',
      failure_reason: 'boleto_expired',
      hours_since_failure: 24.0,
      recovery_attempt_number: 1,
    },
  },
  {
    id: 'TXN-9024',
    name: 'Insufficient Funds - Debit Card High Value',
    context: {
      payment_type: 'debit_card',
      payment_value: 890.00,
      payment_installments: 1,
      previous_order_count: 4,
      previous_payment_count: 4,
      previous_success_count: 4,
      previous_cancelled_count: 0,
      historical_payment_success_rate: 1.0,
      historical_average_payment: 650.00,
      customer_tenure_before_payment: 220,
      order_frequency_before_payment: 0.018,
      failure_category: 'FUNDS_ISSUE',
      failure_reason: 'insufficient_funds',
      hours_since_failure: 3.0,
      recovery_attempt_number: 2,
    },
  },
  {
    id: 'TXN-9025',
    name: 'Micro-Transaction - Generic Gateway Glitch',
    context: {
      payment_type: 'credit_card',
      payment_value: 38.90,
      payment_installments: 1,
      previous_order_count: 0,
      previous_payment_count: 0,
      previous_success_count: 0,
      previous_cancelled_count: 0,
      historical_payment_success_rate: 0.0,
      historical_average_payment: 0.0,
      customer_tenure_before_payment: 0,
      order_frequency_before_payment: 0.0,
      failure_category: 'GENERIC_DECLINE',
      failure_reason: 'gateway_error',
      hours_since_failure: 0.8,
      recovery_attempt_number: 1,
    },
  },
  {
    id: 'TXN-9026',
    name: 'Exhausted Retry Limit - High Velocity',
    context: {
      payment_type: 'credit_card',
      payment_value: 340.00,
      payment_installments: 2,
      previous_order_count: 2,
      previous_payment_count: 5,
      previous_success_count: 2,
      previous_cancelled_count: 3,
      historical_payment_success_rate: 0.40,
      historical_average_payment: 210.00,
      customer_tenure_before_payment: 95,
      order_frequency_before_payment: 0.021,
      failure_category: 'SOFT_DECLINE',
      failure_reason: 'bank_technical_error',
      hours_since_failure: 14.0,
      recovery_attempt_number: 3,
    },
  },
  {
    id: 'TXN-9027',
    name: 'VIP Customer High Ticket Luxury Item',
    context: {
      payment_type: 'credit_card',
      payment_value: 1750.00,
      payment_installments: 6,
      previous_order_count: 12,
      previous_payment_count: 15,
      previous_success_count: 15,
      previous_cancelled_count: 0,
      historical_payment_success_rate: 1.0,
      historical_average_payment: 1200.00,
      customer_tenure_before_payment: 480,
      order_frequency_before_payment: 0.031,
      failure_category: 'CUSTOMER_ACTION_REQUIRED',
      failure_reason: 'authentication_failed',
      hours_since_failure: 2.0,
      recovery_attempt_number: 1,
    },
  },
  {
    id: 'TXN-9028',
    name: 'Voucher Payment Split Failure',
    context: {
      payment_type: 'voucher',
      payment_value: 95.00,
      payment_installments: 1,
      previous_order_count: 3,
      previous_payment_count: 3,
      previous_success_count: 3,
      previous_cancelled_count: 0,
      historical_payment_success_rate: 1.0,
      historical_average_payment: 85.00,
      customer_tenure_before_payment: 110,
      order_frequency_before_payment: 0.027,
      failure_category: 'GENERIC_DECLINE',
      failure_reason: 'payment_failed',
      hours_since_failure: 4.5,
      recovery_attempt_number: 1,
    },
  },
];

export const BatchRunner: React.FC = () => {
  const [items, setItems] = useState<BatchItem[]>(
    SAMPLE_OLIST_BATCH.map(s => ({
      id: s.id,
      context: s.context,
      status: 'PENDING',
    }))
  );
  const [isRunning, setIsRunning] = useState(false);
  const [currentIdx, setCurrentIdx] = useState<number>(-1);

  // Run live batch execution against the real API
  const handleRunBatch = async () => {
    if (isRunning) return;
    setIsRunning(true);

    const updated = [...items];

    for (let i = 0; i < updated.length; i++) {
      setCurrentIdx(i);
      updated[i] = { ...updated[i], status: 'RUNNING' };
      setItems([...updated]);

      const t0 = performance.now();
      try {
        const res = await fetchRecommendation(updated[i].context);
        const t1 = performance.now();
        updated[i] = {
          ...updated[i],
          status: 'COMPLETED',
          recommendation: res,
          latencyMs: Math.round(t1 - t0),
        };
      } catch (err: any) {
        const t1 = performance.now();
        updated[i] = {
          ...updated[i],
          status: 'ERROR',
          error: err?.message || 'Inference call failed',
          latencyMs: Math.round(t1 - t0),
        };
      }
      setItems([...updated]);
    }

    setIsRunning(false);
    setCurrentIdx(-1);
  };

  const handleReset = () => {
    if (isRunning) return;
    setItems(
      SAMPLE_OLIST_BATCH.map(s => ({
        id: s.id,
        context: s.context,
        status: 'PENDING',
      }))
    );
    setCurrentIdx(-1);
  };

  // Export Results as CSV
  const handleExportCSV = () => {
    const headers = [
      'Transaction_ID',
      'Payment_Type',
      'Payment_Value_BRL',
      'Failure_Category',
      'Selected_Action',
      'Calibrated_Recovery_Prob',
      'Expected_Net_Utility_BRL',
      'Guardrail_Check',
      'Inference_Latency_MS',
    ];

    const rows = items.map(item => {
      const rec = item.recommendation;
      const dec = rec?.decision;
      return [
        item.id,
        item.context.payment_type,
        item.context.payment_value.toFixed(2),
        item.context.failure_category,
        dec?.selected_action || 'N/A',
        dec ? (dec.recovery_probability * 100).toFixed(2) + '%' : 'N/A',
        dec ? dec.expected_utility.toFixed(2) : 'N/A',
        rec?.actions?.RETRY?.guardrail_result === 'BLOCKED' ? 'RETRY_BLOCKED' : 'CLEARED',
        item.latencyMs ?? 'N/A',
      ].join(',');
    });

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `recoverai_batch_decisions_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Aggregate Metrics calculation
  const completedItems = items.filter(i => i.status === 'COMPLETED' && i.recommendation);
  const totalValue = items.reduce((acc, i) => acc + i.context.payment_value, 0);
  const totalExpectedUtility = completedItems.reduce(
    (acc, i) => acc + (i.recommendation?.decision.expected_utility ?? 0),
    0
  );
  const avgProbability = completedItems.length
    ? completedItems.reduce((acc, i) => acc + (i.recommendation?.decision.recovery_probability ?? 0), 0) /
      completedItems.length
    : 0;
  const avgLatency = completedItems.length
    ? completedItems.reduce((acc, i) => acc + (i.latencyMs ?? 0), 0) / completedItems.length
    : 0;

  // Action breakdown counts
  const actionCounts: Record<ActionType, number> = {
    RETRY: 0,
    NUDGE: 0,
    ESCALATE: 0,
    STOP: 0,
  };
  completedItems.forEach(i => {
    const act = i.recommendation?.decision.selected_action;
    if (act && actionCounts[act] !== undefined) {
      actionCounts[act]++;
    }
  });

  const chartData = [
    { name: 'RETRY', count: actionCounts.RETRY, color: '#3B82F6' },
    { name: 'NUDGE', count: actionCounts.NUDGE, color: '#10B981' },
    { name: 'ESCALATE', count: actionCounts.ESCALATE, color: '#F59E0B' },
    { name: 'STOP', count: actionCounts.STOP, color: '#64748B' },
  ];

  const progressPercent = Math.round(
    (items.filter(i => i.status === 'COMPLETED' || i.status === 'ERROR').length / items.length) * 100
  );

  return (
    <div className="space-y-8">
      {/* Batch Hero Header */}
      <div className="bg-[#121820] border border-[#232D38] rounded-xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
              LIVE BATCH STREAMING
            </span>
            <span className="text-xs text-[#8C9BAE] font-mono">• Production REST API Bridge</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[#F3F5F7]">
            Batch Revenue Recovery Engine
          </h1>
          <p className="text-xs text-[#8C9BAE] max-w-2xl leading-relaxed">
            Execute high-throughput batch decisioning across failed transaction cohorts. Each row streams live through the LightGBM S-Learner, Isotonic Calibrator, and GR01–GR06 safety guardrails.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5 shrink-0">
          <button
            type="button"
            onClick={handleRunBatch}
            disabled={isRunning}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all shadow-md ${
              isRunning
                ? 'bg-blue-600/50 text-white cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-500 text-white active:scale-95'
            }`}
          >
            <Play className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Processing Batch...' : 'Run Batch Inference'}</span>
          </button>

          <button
            type="button"
            onClick={handleReset}
            disabled={isRunning}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-[#16202C] hover:bg-[#1E2B3B] text-[#8C9BAE] hover:text-[#F3F5F7] border border-[#263545] transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>

          <button
            type="button"
            onClick={handleExportCSV}
            disabled={completedItems.length === 0}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold border transition-all ${
              completedItems.length > 0
                ? 'bg-[#16202C] hover:bg-[#1E2B3B] text-emerald-400 border-emerald-500/30 hover:text-emerald-300'
                : 'bg-[#121820] text-[#667380] border-[#232D38] cursor-not-allowed'
            }`}
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Progress Bar & Status */}
      {isRunning && (
        <div className="bg-[#121820] border border-blue-500/40 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-blue-400 font-mono font-semibold flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 animate-spin" />
              Streaming Row {currentIdx + 1} of {items.length} to /api/v1/recommend...
            </span>
            <span className="text-white font-mono font-bold">{progressPercent}%</span>
          </div>
          <div className="h-2 w-full bg-[#16202C] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-emerald-400 transition-all duration-200"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Real-Time Aggregate KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#121820] border border-[#232D38] rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-[#8C9BAE]">
            <span>Total Ingested Value</span>
            <Layers className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#F3F5F7] mt-1">
            {formatBRL(totalValue)}
          </div>
          <div className="text-[11px] text-[#8C9BAE] mt-0.5 font-mono">
            {items.length} Failed Transactions
          </div>
        </div>

        <div className="bg-[#121820] border border-[#232D38] rounded-xl p-4 border-l-2 border-l-emerald-500">
          <div className="flex items-center justify-between text-xs text-[#8C9BAE]">
            <span>Expected Recovered Utility</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
            {completedItems.length > 0 ? formatBRL(totalExpectedUtility) : 'R$ 0.00'}
          </div>
          <div className="text-[11px] text-emerald-300/80 mt-0.5 font-mono">
            {completedItems.length > 0 ? `${((totalExpectedUtility / totalValue) * 100).toFixed(1)}% Value Yield` : 'Awaiting execution'}
          </div>
        </div>

        <div className="bg-[#121820] border border-[#232D38] rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-[#8C9BAE]">
            <span>Batch Calibrated Probability</span>
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#F3F5F7] mt-1">
            {completedItems.length > 0 ? formatPercent(avgProbability) : '0.0%'}
          </div>
          <div className="text-[11px] text-[#8C9BAE] mt-0.5 font-mono">
            ECE Calibrated Average
          </div>
        </div>

        <div className="bg-[#121820] border border-[#232D38] rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-[#8C9BAE]">
            <span>Avg Pipeline Latency</span>
            <Clock className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#F3F5F7] mt-1">
            {completedItems.length > 0 ? `${avgLatency.toFixed(1)} ms` : '—'}
          </div>
          <div className="text-[11px] text-[#8C9BAE] mt-0.5 font-mono">
            In-Memory Python REST
          </div>
        </div>
      </div>

      {/* Action Distribution Breakdown & Chart */}
      {completedItems.length > 0 && (
        <div className="bg-[#121820] border border-[#232D38] rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#F3F5F7]">
              Action Allocation Distribution
            </h3>
            <span className="text-xs text-[#8C9BAE] font-mono">
              {completedItems.length} Decided
            </span>
          </div>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#667380" fontSize={11} tickLine={false} />
                <YAxis stroke="#667380" fontSize={11} allowDecimals={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#16202C',
                    borderColor: '#263545',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#F3F5F7',
                  }}
                  formatter={(val: any) => [`${val} Transactions`, 'Allocated']}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Batch Transactions Table */}
      <div className="bg-[#121820] border border-[#232D38] rounded-xl overflow-hidden">
        <div className="p-4 border-b border-[#232D38] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-semibold text-[#F3F5F7]">
              Batch Transaction Manifest
            </h3>
          </div>
          <span className="text-xs text-[#8C9BAE] font-mono">
            {completedItems.length}/{items.length} Processed
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#232D38] text-[#8C9BAE] text-[11px] font-mono bg-[#16202C]/40">
                <th className="py-2.5 px-3">TXN ID</th>
                <th className="py-2.5 px-3">Method</th>
                <th className="py-2.5 px-3">Amount (BRL)</th>
                <th className="py-2.5 px-3">Failure Reason</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Selected Action</th>
                <th className="py-2.5 px-3">Calibrated Prob</th>
                <th className="py-2.5 px-3">Expected Utility</th>
                <th className="py-2.5 px-3 text-right">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#232D38]/60 font-mono">
              {items.map(item => {
                const dec = item.recommendation?.decision;
                const retryBlocked = item.recommendation?.actions?.RETRY?.guardrail_result === 'BLOCKED';

                return (
                  <tr
                    key={item.id}
                    className={`hover:bg-[#16202C]/40 transition-colors ${
                      item.status === 'RUNNING' ? 'bg-blue-500/10 animate-pulse' : ''
                    }`}
                  >
                    <td className="py-3 px-3 font-semibold text-blue-400">
                      {item.id}
                    </td>
                    <td className="py-3 px-3 uppercase text-[#F3F5F7]">
                      {item.context.payment_type}
                    </td>
                    <td className="py-3 px-3 font-bold text-[#F3F5F7]">
                      {formatBRL(item.context.payment_value)}
                    </td>
                    <td className="py-3 px-3 text-[#8C9BAE] font-sans truncate max-w-[160px]">
                      {item.context.failure_reason.replace(/_/g, ' ')}
                    </td>
                    <td className="py-3 px-3">
                      {item.status === 'COMPLETED' ? (
                        <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>DONE</span>
                        </span>
                      ) : item.status === 'RUNNING' ? (
                        <span className="inline-flex items-center gap-1 text-[10px] text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded border border-blue-500/20">
                          <Sparkles className="w-3 h-3 animate-spin" />
                          <span>EVAL</span>
                        </span>
                      ) : item.status === 'ERROR' ? (
                        <span className="inline-flex items-center gap-1 text-[10px] text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20">
                          <AlertTriangle className="w-3 h-3" />
                          <span>ERR</span>
                        </span>
                      ) : (
                        <span className="text-[10px] text-[#667380] bg-[#16202C] px-1.5 py-0.5 rounded">
                          QUEUED
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      {dec ? (
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                              dec.selected_action === 'RETRY'
                                ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                                : dec.selected_action === 'NUDGE'
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                : dec.selected_action === 'ESCALATE'
                                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                : 'bg-slate-700/40 text-slate-300 border border-slate-600'
                            }`}
                          >
                            {dec.selected_action}
                          </span>
                          {retryBlocked && (
                            <span className="text-[9px] text-rose-400 font-sans border border-rose-500/30 px-1 rounded bg-rose-500/10">
                              GR BLOCKED
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-[#667380]">—</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-[#F3F5F7]">
                      {dec ? formatPercent(dec.recovery_probability) : '—'}
                    </td>
                    <td className="py-3 px-3 font-bold text-emerald-400">
                      {dec ? formatBRL(dec.expected_utility) : '—'}
                    </td>
                    <td className="py-3 px-3 text-right text-[#8C9BAE]">
                      {item.latencyMs ? `${item.latencyMs}ms` : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
