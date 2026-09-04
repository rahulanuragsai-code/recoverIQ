import React from 'react';
import type { SimulationMetrics } from '../types';
import { TrendingUp, ShieldAlert, CheckCircle2, Zap } from 'lucide-react';

interface ComparisonChartProps {
  metrics: SimulationMetrics | null;
}

export const ComparisonChart: React.FC<ComparisonChartProps> = ({ metrics }) => {
  if (!metrics) {
    return (
      <div className="p-8 text-center text-slate-500 rounded-xl border border-slate-800 bg-slate-900/40">
        Run batch simulation to view head-to-head performance benchmarks.
      </div>
    );
  }

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const aiRate = metrics.recovery_rate_ai;
  const baseRate = metrics.recovery_rate_baseline;
  const uplift = metrics.recovery_rate_uplift_pct;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 1. Recovery Rate Head-to-Head */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 shadow-md backdrop-blur">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white">Recovery Rate: AI vs Naive Baseline</h3>
            <p className="text-xs text-slate-400">Head-to-head on identical 600 transaction test set</p>
          </div>
          <div className="flex items-center gap-1 text-xs font-bold text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-2.5 py-1 rounded-full">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>+{uplift}% Uplift</span>
          </div>
        </div>

        <div className="space-y-5 pt-2">
          {/* AI Copilot Bar */}
          <div>
            <div className="flex justify-between text-xs font-semibold mb-1.5">
              <span className="flex items-center gap-1.5 text-blue-400">
                <Zap className="w-3.5 h-3.5" />
                RecoverIQ (AI + Policy Gate)
              </span>
              <span className="font-mono text-white text-sm font-bold">{aiRate}%</span>
            </div>
            <div className="h-4 w-full bg-slate-800 rounded-full overflow-hidden p-0.5">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-700 shadow-sm"
                style={{ width: `${Math.min(100, Math.max(0, aiRate))}%` }}
              />
            </div>
            <div className="flex justify-between text-[11px] text-slate-400 mt-1">
              <span>Recovered: {formatINR(metrics.amount_recovered_ai)}</span>
              <span className="text-emerald-400 font-medium">Personalized Playbooks</span>
            </div>
          </div>

          {/* Baseline Bar */}
          <div>
            <div className="flex justify-between text-xs font-semibold mb-1.5">
              <span className="text-slate-400">Naive Baseline (Immediate 3x Retry)</span>
              <span className="font-mono text-slate-300 text-sm font-bold">{baseRate}%</span>
            </div>
            <div className="h-4 w-full bg-slate-800 rounded-full overflow-hidden p-0.5">
              <div
                className="h-full bg-slate-600 rounded-full transition-all duration-700"
                style={{ width: `${Math.min(100, Math.max(0, baseRate))}%` }}
              />
            </div>
            <div className="flex justify-between text-[11px] text-slate-400 mt-1">
              <span>Recovered: {formatINR(metrics.amount_recovered_baseline)}</span>
              <span className="text-slate-500">Unstratified Retries</span>
            </div>
          </div>
        </div>

        {/* Value Callout Box */}
        <div className="mt-6 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300 flex items-start gap-2.5">
          <CheckCircle2 className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-white font-semibold">Net Incremental Revenue: </strong>
            RecoverIQ recovered{' '}
            <span className="font-bold font-mono text-emerald-300">
              {formatINR(metrics.amount_recovered_ai - metrics.amount_recovered_baseline)}
            </span>{' '}
            more revenue while completely eliminating blind retries on fraud and exhausted cards.
          </div>
        </div>
      </div>

      {/* 2. Policy Governance & Avoided Retries */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 shadow-md backdrop-blur">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white">Policy Gate & Governance Impact</h3>
            <p className="text-xs text-slate-400">Deterministic guardrails intercepting harmful retries</p>
          </div>
          <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
            Seed {metrics.seed}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4 my-3">
          <div className="p-4 rounded-lg bg-slate-800/60 border border-slate-700/60">
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <span>Policy Overrides</span>
            </div>
            <div className="text-2xl font-bold font-mono text-amber-300">
              {metrics.policy_overrides_count}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              LLM proposals overridden by safety rules
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-800/60 border border-slate-700/60">
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>False Retries Avoided</span>
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-300">
              {metrics.false_retries_avoided}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Useless gateway charges & churn prevented
            </p>
          </div>
        </div>

        {/* Action Breakdown distribution */}
        {metrics.action_breakdown && (
          <div className="mt-4 pt-4 border-t border-slate-800">
            <div className="text-xs font-semibold text-slate-400 mb-2">Approved Action Distribution</div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(metrics.action_breakdown).map(([action, count]) => (
                <div
                  key={action}
                  className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-xs flex items-center gap-1.5"
                >
                  <span className="text-slate-300 capitalize">{action.replace('_', ' ')}</span>
                  <span className="font-mono font-bold text-blue-400">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
