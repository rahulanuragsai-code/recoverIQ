import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

export const SyntheticBanner: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-amber-500/20 via-blue-500/20 to-purple-500/20 border-b border-amber-500/30 px-4 py-2 text-xs text-amber-200 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-2 font-medium">
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
        <span>
          <strong className="text-amber-300 font-bold uppercase tracking-wide">Synthetic Demo Data:</strong> All 600 records and outcomes are simulated for Razorpay AI Buildathon 2026. Zero real payment transactions or financial debits occur.
        </span>
      </div>
      <div className="hidden md:flex items-center gap-2 text-slate-300 font-mono text-[11px] bg-slate-900/60 px-2 py-0.5 rounded border border-slate-700">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
        <span>Deterministic Seed 42 • Hard-Coded Policy Gate Active</span>
      </div>
    </div>
  );
};
