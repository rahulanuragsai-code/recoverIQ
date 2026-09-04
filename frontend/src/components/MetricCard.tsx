import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  highlightColor?: 'blue' | 'emerald' | 'amber' | 'purple' | 'rose';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  highlightColor = 'blue',
}) => {
  const borderColors = {
    blue: 'border-blue-500/30 hover:border-blue-500/50',
    emerald: 'border-emerald-500/30 hover:border-emerald-500/50',
    amber: 'border-amber-500/30 hover:border-amber-500/50',
    purple: 'border-purple-500/30 hover:border-purple-500/50',
    rose: 'border-rose-500/30 hover:border-rose-500/50',
  };

  const bgGradients = {
    blue: 'from-blue-950/40 to-slate-900/40',
    emerald: 'from-emerald-950/40 to-slate-900/40',
    amber: 'from-amber-950/40 to-slate-900/40',
    purple: 'from-purple-950/40 to-slate-900/40',
    rose: 'from-rose-950/40 to-slate-900/40',
  };

  return (
    <div
      className={`relative rounded-xl border bg-gradient-to-b ${bgGradients[highlightColor]} ${borderColors[highlightColor]} p-5 backdrop-blur transition-all duration-200 shadow-lg`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {title}
        </span>
        <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300">
          {icon}
        </div>
      </div>

      <div className="flex items-baseline gap-2">
        <div className="text-2xl font-bold tracking-tight text-white font-mono">
          {value}
        </div>
        {trend && (
          <span
            className={`text-xs font-semibold px-1.5 py-0.5 rounded ${
              trend.isPositive
                ? 'bg-emerald-500/20 text-emerald-400'
                : 'bg-rose-500/20 text-rose-400'
            }`}
          >
            {trend.value}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="mt-2 text-xs text-slate-400 font-medium">
          {subtitle}
        </p>
      )}
    </div>
  );
};
