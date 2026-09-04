import React from 'react';
import type { SimulationMetrics, Transaction } from '../types';
import { MetricCard } from '../components/MetricCard';
import { ComparisonChart } from '../components/ComparisonChart';
import {
  IndianRupee,
  TrendingUp,
  ShieldAlert,
  CheckCircle2,
  RefreshCw,
  Sparkles,
  Zap,
  ArrowRight,
} from 'lucide-react';

interface OverviewPageProps {
  metrics: SimulationMetrics | null;
  onRunSimulation: () => void;
  onSelectTransaction: (tx: Transaction) => void;
  onNavigateToTransactions: () => void;
  isSimulating: boolean;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  metrics,
  onRunSimulation,
  onNavigateToTransactions,
  isSimulating,
}) => {
  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="space-y-8">
      {/* Hero / Headline */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-400 mb-1">
            <Sparkles className="w-4 h-4" />
            <span>Autonomous AI Recovery vs Naive 3x Retries</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Revenue Recovery Performance Copilot
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl">
            RecoverIQ replaces blind, generic payment retries with root-cause diagnostics,
            risk-adjusted scoring, and deterministic safety policy guardrails.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRunSimulation}
            disabled={isSimulating}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-xl shadow-blue-500/20 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isSimulating ? 'animate-spin' : ''}`} />
            <span>{isSimulating ? 'Simulating 600 Records...' : 'Run Batch Simulation'}</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Total Amount at Risk"
          value={metrics ? formatINR(metrics.amount_at_risk) : '₹0'}
          subtitle="Across 600 failed transactions"
          icon={<IndianRupee className="w-5 h-5 text-blue-400" />}
          highlightColor="blue"
        />

        <MetricCard
          title="Amount Recovered (AI)"
          value={metrics ? formatINR(metrics.amount_recovered_ai) : '₹0'}
          subtitle={`Baseline: ${metrics ? formatINR(metrics.amount_recovered_baseline) : '₹0'}`}
          icon={<CheckCircle2 className="w-5 h-5 text-emerald-400" />}
          highlightColor="emerald"
          trend={
            metrics
              ? {
                  value: `+${formatINR(metrics.amount_recovered_ai - metrics.amount_recovered_baseline)}`,
                  isPositive: true,
                }
              : undefined
          }
        />

        <MetricCard
          title="Recovery Rate Uplift"
          value={metrics ? `+${metrics.recovery_rate_uplift_pct}%` : '0%'}
          subtitle={`AI: ${metrics?.recovery_rate_ai || 0}% vs Baseline: ${metrics?.recovery_rate_baseline || 0}%`}
          icon={<TrendingUp className="w-5 h-5 text-indigo-400" />}
          highlightColor="purple"
          trend={metrics ? { value: `Uplift`, isPositive: true } : undefined}
        />

        <MetricCard
          title="False Retries Avoided"
          value={metrics ? metrics.false_retries_avoided : 0}
          subtitle="Wasted retries on fraud & expired cards prevented"
          icon={<ShieldAlert className="w-5 h-5 text-amber-400" />}
          highlightColor="amber"
        />
      </div>

      {/* Benchmark Visualizations */}
      <ComparisonChart metrics={metrics} />

      {/* Edge Cases Showcase Spotlight */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              <span>Seeded Stress Cases: "What Broke & How RecoverIQ Handled It"</span>
            </h2>
            <p className="text-xs text-slate-400">
              Two tricky failure scenarios deliberately injected into the dataset to test agentic resilience and safety.
            </p>
          </div>
          <button
            onClick={onNavigateToTransactions}
            className="flex items-center gap-1.5 text-xs font-semibold text-blue-400 hover:text-blue-300"
          >
            <span>Explore all 600 in Table</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Edge Case 1 */}
          <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-amber-500/40 transition">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold font-mono text-amber-300">
                tx_edge_fraud_001
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                FRAUD CAMOUFLAGE
              </span>
            </div>
            <p className="text-xs text-slate-300 mb-2 font-mono">
              "Transaction cannot be processed: balance check failed (code 51)"
            </p>
            <div className="text-xs text-slate-400 space-y-1">
              <div>
                <strong className="text-slate-300">The Trap: </strong>
                Decline message mimics insufficient funds. An unconstrained LLM or naive retry would attempt retrying.
              </div>
              <div>
                <strong className="text-emerald-400">Policy Gate Intervention: </strong>
                Zero-Tolerance rule overrides LLM proposal, clamping retries to 0 and routing to human risk operations.
              </div>
            </div>
          </div>

          {/* Edge Case 2 */}
          <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-blue-500/40 transition">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold font-mono text-blue-300">
                tx_edge_exp_backup_002
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                EXPIRED CARD + BACKUP MANDATE
              </span>
            </div>
            <p className="text-xs text-slate-300 mb-2 font-mono">
              "Primary card lapsed. Secondary mandate on UPI Autopay is linked in customer wallet."
            </p>
            <div className="text-xs text-slate-400 space-y-1">
              <div>
                <strong className="text-slate-300">The Problem: </strong>
                Naive baseline retries the dead card 3 times and loses a ₹48,000 high-value recurring subscription.
              </div>
              <div>
                <strong className="text-emerald-400">RecoverIQ Recovery: </strong>
                Detects linked mandate, sends WhatsApp 1-click fallback notification, recovering funds with 0 blind retries.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
