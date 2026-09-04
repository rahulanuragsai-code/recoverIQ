import React from 'react';
import { ShieldCheck, ShieldAlert, Zap, Clock, Bell, UserCheck, Ban } from 'lucide-react';

interface BadgeProps {
  type: 'verdict' | 'segment' | 'action' | 'root_cause' | 'outcome';
  value: string;
}

export const PolicyBadge: React.FC<BadgeProps> = ({ type, value }) => {
  if (type === 'verdict') {
    if (value === 'PASSED') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          <ShieldCheck className="w-3 h-3" />
          PASSED
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
        <ShieldAlert className="w-3 h-3" />
        OVERRIDDEN
      </span>
    );
  }

  if (type === 'segment') {
    switch (value) {
      case 'high_value':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-400/10 text-amber-300 border border-amber-400/20">
            ★ High Value
          </span>
        );
      case 'regular':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-400/10 text-blue-300 border border-blue-400/20">
            Regular
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-400/10 text-slate-300 border border-slate-400/20">
            New
          </span>
        );
    }
  }

  if (type === 'action') {
    switch (value) {
      case 'retry_now':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-emerald-500/15 text-emerald-300 border border-emerald-500/20">
            <Zap className="w-3 h-3 text-emerald-400" />
            Retry Now
          </span>
        );
      case 'retry_scheduled':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-500/15 text-blue-300 border border-blue-500/20">
            <Clock className="w-3 h-3 text-blue-400" />
            Scheduled
          </span>
        );
      case 'notify_customer':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-purple-500/15 text-purple-300 border border-purple-500/20">
            <Bell className="w-3 h-3 text-purple-400" />
            Notify
          </span>
        );
      case 'escalate_human':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-rose-500/15 text-rose-300 border border-rose-500/20">
            <UserCheck className="w-3 h-3 text-rose-400" />
            Escalate
          </span>
        );
      case 'do_not_retry':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-500/20 text-slate-300 border border-slate-500/20">
            <Ban className="w-3 h-3 text-slate-400" />
            Do Not Retry
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-700 text-slate-300">
            {value}
          </span>
        );
    }
  }

  if (type === 'outcome') {
    if (value === 'RECOVERED') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
          ● Recovered
        </span>
      );
    }
    if (value === 'SKIPPED') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-500/20 text-slate-300 border border-slate-500/30">
          ○ Skipped
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-rose-500/20 text-rose-300 border border-rose-500/30">
        ✕ Failed
      </span>
    );
  }

  // root_cause
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded font-mono text-xs font-medium bg-slate-800 text-slate-200 border border-slate-700">
      {value.replace('_', ' ')}
    </span>
  );
};
