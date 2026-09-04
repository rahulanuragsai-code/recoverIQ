import React, { useState, useEffect } from 'react';
import type { Transaction } from '../types';
import { getTransactions } from '../api/client';
import { PolicyBadge } from '../components/PolicyBadge';
import {
  Search,
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Sparkles,
  Layers,
} from 'lucide-react';

interface TransactionsPageProps {
  onSelectTransaction: (tx: Transaction) => void;
}

export const TransactionsPage: React.FC<TransactionsPageProps> = ({
  onSelectTransaction,
}) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [isLoading, setIsLoading] = useState(false);

  // Filters
  const [search, setSearch] = useState('');
  const [rootCause, setRootCause] = useState('');
  const [segment, setSegment] = useState('');
  const [action, setAction] = useState('');
  const [fraudOnly, setFraudOnly] = useState(false);
  const [edgeOnly, setEdgeOnly] = useState(false);

  const fetchTxList = async () => {
    try {
      setIsLoading(true);
      const res = await getTransactions({
        search: search || undefined,
        root_cause: rootCause || undefined,
        segment: segment || undefined,
        action: action || undefined,
        fraud_flag: fraudOnly ? true : undefined,
        edge_case_only: edgeOnly ? true : undefined,
        page,
        page_size: pageSize,
      });
      setTransactions(res.transactions);
      setTotal(res.total);
    } catch (err) {
      console.error('Failed to load transactions', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTxList();
  }, [page, rootCause, segment, action, fraudOnly, edgeOnly]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchTxList();
  };

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-400" />
            <span>Failed Transactions Explorer</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Click any row to open the complete 5-step AI reasoning trace and policy verdict.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setEdgeOnly(!edgeOnly);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition flex items-center gap-1.5 ${
              edgeOnly
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Seeded Edge Cases Only</span>
          </button>

          <button
            onClick={fetchTxList}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Refresh List"
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
              placeholder="Search by Transaction ID, Customer ID, Gateway, or Decline Message..."
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

          {/* Root Cause Filter */}
          <select
            value={rootCause}
            onChange={(e) => {
              setRootCause(e.target.value);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-300 text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="">All Root Causes</option>
            <option value="INSUFFICIENT_FUNDS">Insufficient Funds</option>
            <option value="CARD_EXPIRED">Card Expired</option>
            <option value="ISSUER_DECLINE">Issuer Decline</option>
            <option value="INVALID_CVV">Invalid CVV</option>
            <option value="NETWORK_TIMEOUT">Network Timeout</option>
            <option value="SUSPECTED_FRAUD">Suspected Fraud</option>
            <option value="PROCESSING_ERROR">Processing Error</option>
          </select>

          {/* Segment Filter */}
          <select
            value={segment}
            onChange={(e) => {
              setSegment(e.target.value);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-300 text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="">All Segments</option>
            <option value="high_value">★ High Value</option>
            <option value="regular">Regular</option>
            <option value="new">New</option>
          </select>

          {/* Action Filter */}
          <select
            value={action}
            onChange={(e) => {
              setAction(e.target.value);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-300 text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="">All Actions</option>
            <option value="retry_now">Retry Now</option>
            <option value="retry_scheduled">Retry Scheduled</option>
            <option value="notify_customer">Notify Customer</option>
            <option value="escalate_human">Escalate Human</option>
            <option value="do_not_retry">Do Not Retry</option>
          </select>

          {/* Fraud Flag Toggle */}
          <label className="flex items-center gap-1.5 text-xs text-slate-300 cursor-pointer ml-auto bg-slate-950 px-2.5 py-1 rounded border border-slate-800">
            <input
              type="checkbox"
              checked={fraudOnly}
              onChange={(e) => {
                setFraudOnly(e.target.checked);
                setPage(1);
              }}
              className="rounded border-slate-700 text-rose-600 focus:ring-rose-500 bg-slate-900"
            />
            <span className="flex items-center gap-1 text-rose-300">
              <ShieldAlert className="w-3.5 h-3.5" />
              Suspected Fraud Only
            </span>
          </label>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-lg backdrop-blur">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Transaction ID</th>
                <th className="py-3 px-4">Customer & Segment</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Gateway & Decline</th>
                <th className="py-3 px-4">Root Cause</th>
                <th className="py-3 px-4">Recoverability</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Policy Gate</th>
                <th className="py-3 px-4">AI Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {transactions.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    {isLoading ? 'Loading transactions...' : 'No transactions found matching criteria.'}
                  </td>
                </tr>
              ) : (
                transactions.map((tx) => (
                  <tr
                    key={tx.transaction_id}
                    onClick={() => onSelectTransaction(tx)}
                    className="hover:bg-slate-800/50 cursor-pointer transition"
                  >
                    <td className="py-3 px-4 font-mono font-medium text-white whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span className="text-blue-400 font-bold">{tx.transaction_id}</span>
                        {tx.edge_case_tag && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                            EDGE
                          </span>
                        )}
                        {tx.fraud_flag && (
                          <span className="px-1 py-0.2 rounded text-[9px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                            FRAUD
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="font-mono text-slate-300">{tx.customer_id}</div>
                      <PolicyBadge type="segment" value={tx.customer_segment} />
                    </td>

                    <td className="py-3 px-4 font-mono font-bold text-white whitespace-nowrap">
                      {formatINR(tx.amount)}
                    </td>

                    <td className="py-3 px-4">
                      <div className="text-slate-300 font-medium">{tx.gateway}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{tx.decline_code}</div>
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      <PolicyBadge type="root_cause" value={tx.root_cause || tx.decline_code} />
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      {tx.recoverability_score !== null && tx.recoverability_score !== undefined ? (
                        <div className="w-24">
                          <div className="flex justify-between text-[10px] font-mono mb-1">
                            <span className="text-slate-400">Score</span>
                            <span className="font-bold text-white">
                              {Math.round(tx.recoverability_score * 100)}%
                            </span>
                          </div>
                          <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                tx.recoverability_score >= 0.6
                                  ? 'bg-emerald-500'
                                  : tx.recoverability_score >= 0.3
                                  ? 'bg-amber-500'
                                  : 'bg-rose-500'
                              }`}
                              style={{ width: `${Math.round(tx.recoverability_score * 100)}%` }}
                            />
                          </div>
                        </div>
                      ) : (
                        <span className="text-slate-600 font-mono">--</span>
                      )}
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      {tx.final_action ? (
                        <PolicyBadge type="action" value={tx.final_action} />
                      ) : (
                        <span className="text-slate-500 text-xs">Pending</span>
                      )}
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      <PolicyBadge type="verdict" value={tx.policy_gate_verdict || 'PASSED'} />
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      {tx.simulated_outcome_ai ? (
                        <PolicyBadge type="outcome" value={tx.simulated_outcome_ai} />
                      ) : (
                        <span className="text-slate-600 text-xs">Unsimulated</span>
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
            Showing <strong className="text-white">{transactions.length}</strong> of{' '}
            <strong className="text-white">{total}</strong> transactions
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
