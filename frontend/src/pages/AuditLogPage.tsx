import React, { useState, useEffect } from 'react';
import type { AuditLog } from '../types';
import { getAuditLogs } from '../api/client';
import { PolicyBadge } from '../components/PolicyBadge';
import {
  FileText,
  Search,
  Filter,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  ArrowRight,
} from 'lucide-react';

export const AuditLogPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [isLoading, setIsLoading] = useState(false);

  // Filters
  const [verdict, setVerdict] = useState('');
  const [action, setAction] = useState('');
  const [search, setSearch] = useState('');

  const fetchLogs = async () => {
    try {
      setIsLoading(true);
      const res = await getAuditLogs({
        verdict: verdict || undefined,
        action: action || undefined,
        search: search || undefined,
        page,
        page_size: pageSize,
      });
      setLogs(res.logs);
      setTotal(res.total);
    } catch (err) {
      console.error('Failed to load audit logs', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, verdict, action]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchLogs();
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" />
            <span>Deterministic Policy Audit Trail</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Immutable log of all AI proposals evaluated against deterministic safety rules and override decisions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setVerdict(verdict === 'OVERRIDDEN' ? '' : 'OVERRIDDEN');
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition flex items-center gap-1.5 ${
              verdict === 'OVERRIDDEN'
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
            <span>Show Policy Overrides Only</span>
          </button>

          <button
            onClick={fetchLogs}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3 backdrop-blur">
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by Transaction ID, Customer ID, Rule name, or Override Reason..."
              className="w-full bg-slate-950/80 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition"
          >
            Search
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-800/80 text-xs">
          <div className="flex items-center gap-1.5 text-slate-400 mr-2">
            <Filter className="w-3.5 h-3.5" />
            <span>Filters:</span>
          </div>

          <select
            value={verdict}
            onChange={(e) => {
              setVerdict(e.target.value);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-300 text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="">All Policy Verdicts</option>
            <option value="OVERRIDDEN">OVERRIDDEN (Rule Intervened)</option>
            <option value="PASSED">PASSED (Rule Compliant)</option>
          </select>

          <select
            value={action}
            onChange={(e) => {
              setAction(e.target.value);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-300 text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="">All Final Actions</option>
            <option value="retry_now">Retry Now</option>
            <option value="retry_scheduled">Retry Scheduled</option>
            <option value="notify_customer">Notify Customer</option>
            <option value="escalate_human">Escalate Human</option>
            <option value="do_not_retry">Do Not Retry</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-lg backdrop-blur">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Transaction & Customer</th>
                <th className="py-3 px-4">Proposed by LLM</th>
                <th className="py-3 px-4">Verdict</th>
                <th className="py-3 px-4">Enforced Final Action</th>
                <th className="py-3 px-4">Rules Fired & Override Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    {isLoading ? 'Loading audit records...' : 'No audit entries found. Run batch simulation first.'}
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                      {log.created_at ? new Date(log.created_at).toLocaleTimeString() : '--'}
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap font-mono">
                      <div className="text-white font-semibold">{log.transaction_id}</div>
                      <div className="text-[10px] text-slate-500">{log.customer_id}</div>
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      <PolicyBadge type="action" value={log.proposed_action} />
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      <PolicyBadge type="verdict" value={log.policy_verdict} />
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        {log.policy_verdict === 'OVERRIDDEN' && (
                          <ArrowRight className="w-3.5 h-3.5 text-amber-400" />
                        )}
                        <PolicyBadge type="action" value={log.final_action} />
                      </div>
                    </td>

                    <td className="py-3 px-4">
                      {log.rules_fired && log.rules_fired.length > 0 ? (
                        <div className="space-y-1">
                          <div className="flex flex-wrap gap-1">
                            {log.rules_fired.map((rule, idx) => (
                              <span
                                key={idx}
                                className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/15 text-amber-300 border border-amber-500/25"
                              >
                                {rule}
                              </span>
                            ))}
                          </div>
                          {log.override_reasons && log.override_reasons[0] && (
                            <p className="text-[11px] text-slate-400 line-clamp-2">
                              {log.override_reasons[0]}
                            </p>
                          )}
                        </div>
                      ) : (
                        <span className="text-[11px] text-slate-500 italic">
                          Clean pass • No safety rules violated
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3 bg-slate-950/60 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing <strong className="text-white">{logs.length}</strong> of{' '}
            <strong className="text-white">{total}</strong> audit entries
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1 || isLoading}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span>
              Page <strong className="text-white">{page}</strong> of{' '}
              <strong className="text-white">{totalPages}</strong>
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages || isLoading}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
