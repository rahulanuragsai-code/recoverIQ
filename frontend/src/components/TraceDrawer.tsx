import React, { useState } from 'react';
import type { Transaction } from '../types';
import { PolicyBadge } from './PolicyBadge';
import {
  X,
  Cpu,
  Calculator,
  Compass,
  ShieldCheck,
  ShieldAlert,
  PlayCircle,
  RefreshCw,
} from 'lucide-react';
import { analyzeTransaction } from '../api/client';

interface TraceDrawerProps {
  transaction: Transaction | null;
  onClose: () => void;
  onUpdateTransaction: (updated: Transaction) => void;
}

export const TraceDrawer: React.FC<TraceDrawerProps> = ({
  transaction,
  onClose,
  onUpdateTransaction,
}) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  if (!transaction) return null;

  const handleReanalyze = async () => {
    try {
      setIsAnalyzing(true);
      const updated = await analyzeTransaction(transaction.transaction_id);
      onUpdateTransaction(updated);
    } catch (err) {
      console.error('Failed to re-analyze transaction', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/70 backdrop-blur-sm flex justify-end transition-opacity">
      <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-sm font-bold text-blue-400">
                {transaction.transaction_id}
              </span>
              <PolicyBadge type="segment" value={transaction.customer_segment} />
              {transaction.edge_case_tag && (
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  ⚡ Edge Case: {transaction.edge_case_tag}
                </span>
              )}
            </div>
            <div className="text-xs text-slate-400">
              Customer: <span className="font-mono text-slate-300">{transaction.customer_id}</span> • Gateway: <span className="text-slate-300">{transaction.gateway}</span> • Amount: <strong className="text-white font-mono">{formatINR(transaction.amount)}</strong>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleReanalyze}
              disabled={isAnalyzing}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzing ? 'animate-spin' : ''}`} />
              <span>{isAnalyzing ? 'Analyzing...' : 'Re-run Pipeline'}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Scrollable Content: 5-Step Pipeline Trace */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Raw Gateway Failure Context */}
          <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Raw Gateway Decline Event
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs mb-2">
              <div>
                <span className="text-slate-500">Decline Code:</span>{' '}
                <span className="font-mono font-semibold text-rose-300">{transaction.decline_code}</span>
              </div>
              <div>
                <span className="text-slate-500">Previous Retries:</span>{' '}
                <span className="font-mono font-semibold text-white">{transaction.previous_retry_count} / 3</span>
              </div>
              <div>
                <span className="text-slate-500">Subscription:</span>{' '}
                <span className="text-white">{transaction.is_subscription ? 'Yes (Recurring)' : 'No (One-off)'}</span>
              </div>
              <div>
                <span className="text-slate-500">Fraud Flag:</span>{' '}
                <span className={`font-mono font-bold ${transaction.fraud_flag ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {transaction.fraud_flag ? 'TRUE (Critical)' : 'False'}
                </span>
              </div>
            </div>
            <div className="mt-2 text-xs bg-slate-900 p-2.5 rounded border border-slate-800 text-slate-300 font-mono">
              "{transaction.decline_message}"
            </div>
          </div>

          {/* STEP 1: CLASSIFIER */}
          <div className="rounded-xl border border-blue-500/20 bg-slate-900/60 p-5 relative overflow-hidden">
            <div className="flex items-center gap-2 text-blue-400 text-xs font-bold uppercase tracking-wider mb-2">
              <Cpu className="w-4 h-4" />
              <span>Step 1: Root Cause Classifier</span>
            </div>
            <div className="flex items-center gap-3 my-2">
              <span className="text-xs text-slate-400">Classified Root Cause:</span>
              <PolicyBadge type="root_cause" value={transaction.root_cause || 'UNCLASSIFIED'} />
            </div>
            <p className="text-xs text-slate-300 italic mt-2 bg-slate-950/50 p-2.5 rounded border border-slate-800/80">
              "{transaction.root_cause_rationale || 'Pending analysis'}"
            </p>
          </div>

          {/* STEP 2: RECOVERABILITY SCORER */}
          <div className="rounded-xl border border-indigo-500/20 bg-slate-900/60 p-5">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-indigo-400 text-xs font-bold uppercase tracking-wider">
                <Calculator className="w-4 h-4" />
                <span>Step 2: Recoverability Scorer (Deterministic)</span>
              </div>
              <span className="text-lg font-mono font-bold text-white">
                {transaction.recoverability_score !== null ? `${Math.round((transaction.recoverability_score || 0) * 100)}%` : '--'}
              </span>
            </div>

            {/* Score Bar */}
            <div className="h-2.5 w-full bg-slate-800 rounded-full overflow-hidden my-2">
              <div
                className={`h-full transition-all duration-500 ${
                  (transaction.recoverability_score || 0) >= 0.6
                    ? 'bg-emerald-500'
                    : (transaction.recoverability_score || 0) >= 0.3
                    ? 'bg-amber-500'
                    : 'bg-rose-500'
                }`}
                style={{ width: `${Math.round((transaction.recoverability_score || 0) * 100)}%` }}
              />
            </div>

            {/* Factors list */}
            {transaction.score_factors && transaction.score_factors.length > 0 && (
              <div className="mt-3 space-y-1.5">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Key Driving Factors</div>
                {transaction.score_factors.map((f, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between text-xs bg-slate-950/40 px-2.5 py-1.5 rounded border border-slate-800/60"
                  >
                    <span className="text-slate-300">{f.description}</span>
                    <span
                      className={`font-mono font-bold text-xs ${
                        f.impact >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {f.impact >= 0 ? `+${f.impact}` : f.impact}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* STEP 3: STRATEGY GENERATOR (AGENTIC LLM PROPOSAL) */}
          <div className="rounded-xl border border-purple-500/20 bg-slate-900/60 p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 text-purple-400 text-xs font-bold uppercase tracking-wider">
                <Compass className="w-4 h-4" />
                <span>Step 3: Strategy Generator (LLM Proposal)</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                Agentic Playbook
              </span>
            </div>

            {transaction.proposed_playbook ? (
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="bg-slate-950/50 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Proposed Action</span>
                    <PolicyBadge type="action" value={transaction.proposed_playbook.action} />
                  </div>
                  <div className="bg-slate-950/50 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Channel</span>
                    <span className="font-semibold text-white capitalize">{transaction.proposed_playbook.channel}</span>
                  </div>
                  <div className="bg-slate-950/50 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Retry Delay</span>
                    <span className="font-semibold text-white font-mono">{transaction.proposed_playbook.retry_delay_hours}h</span>
                  </div>
                </div>
                <p className="text-xs text-slate-300 italic bg-slate-950/50 p-2.5 rounded border border-slate-800/80">
                  "{transaction.proposed_playbook.rationale}"
                </p>
              </div>
            ) : (
              <p className="text-xs text-slate-500">Not yet generated</p>
            )}
          </div>

          {/* STEP 4: POLICY GATE (SAFETY OVERRIDER) */}
          <div
            className={`rounded-xl border p-5 ${
              transaction.policy_gate_verdict === 'OVERRIDDEN'
                ? 'border-amber-500/40 bg-amber-950/15'
                : 'border-emerald-500/30 bg-emerald-950/15'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider">
                {transaction.policy_gate_verdict === 'OVERRIDDEN' ? (
                  <>
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    <span className="text-amber-400">Step 4: Policy Gate (INTERCEPTED & OVERRIDDEN)</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span className="text-emerald-400">Step 4: Policy Gate (VALIDATED & PASSED)</span>
                  </>
                )}
              </div>
              <PolicyBadge type="verdict" value={transaction.policy_gate_verdict || 'PASSED'} />
            </div>

            {/* If Overridden, display rules fired */}
            {transaction.policy_overrides && transaction.policy_overrides.length > 0 && (
              <div className="mb-4 space-y-2">
                <div className="text-[11px] font-bold text-amber-300 uppercase tracking-wider">
                  Deterministic Rules Enforced:
                </div>
                {transaction.policy_overrides.map((ov, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/25 text-xs text-amber-200"
                  >
                    <div className="font-mono font-bold text-amber-400 mb-0.5">{ov.rule}</div>
                    <div className="text-slate-300">{ov.reason}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Final Approved Playbook */}
            {transaction.final_playbook && (
              <div>
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Final Approved Playbook Executed
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="bg-slate-950/60 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Approved Action</span>
                    <PolicyBadge type="action" value={transaction.final_playbook.action} />
                  </div>
                  <div className="bg-slate-950/60 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Channel</span>
                    <span className="font-semibold text-white capitalize">{transaction.final_playbook.channel}</span>
                  </div>
                  <div className="bg-slate-950/60 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Cooldown Delay</span>
                    <span className="font-semibold text-white font-mono">{transaction.final_playbook.retry_delay_hours}h</span>
                  </div>
                </div>
                <p className="text-xs text-slate-300 italic mt-2 bg-slate-950/60 p-2.5 rounded border border-slate-800/80">
                  "{transaction.final_playbook.rationale}"
                </p>
              </div>
            )}
          </div>

          {/* STEP 5: SIMULATOR & COMPARATOR */}
          <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-5">
            <div className="flex items-center gap-2 text-slate-300 text-xs font-bold uppercase tracking-wider mb-3">
              <PlayCircle className="w-4 h-4 text-blue-400" />
              <span>Step 5: Recovery Simulator (Seed 42) vs Baseline</span>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs">
              {/* AI Outcome */}
              <div className="p-3.5 rounded-lg bg-slate-950/50 border border-slate-800">
                <div className="text-slate-400 text-[10px] uppercase font-semibold mb-1">
                  RecoverIQ Copilot Outcome
                </div>
                <div className="flex items-center justify-between my-1">
                  <PolicyBadge type="outcome" value={transaction.simulated_outcome_ai || 'SKIPPED'} />
                  <span className="font-mono text-slate-400">
                    {transaction.simulated_retries_ai || 0} retries used
                  </span>
                </div>
                {transaction.false_retry_avoided && (
                  <div className="mt-2 text-[11px] font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    ✓ False Retries Avoided
                  </div>
                )}
              </div>

              {/* Baseline Outcome */}
              <div className="p-3.5 rounded-lg bg-slate-950/50 border border-slate-800">
                <div className="text-slate-400 text-[10px] uppercase font-semibold mb-1">
                  Naive 3x Baseline Outcome
                </div>
                <div className="flex items-center justify-between my-1">
                  <PolicyBadge type="outcome" value={transaction.simulated_outcome_baseline || 'FAILED'} />
                  <span className="font-mono text-slate-400">
                    {transaction.simulated_retries_baseline || 0} retries used
                  </span>
                </div>
                <div className="mt-2 text-[11px] text-slate-500">
                  Fixed immediate re-attempts
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
