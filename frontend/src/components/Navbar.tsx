import React from 'react';
import {
  Activity,
  Layers,
  FileText,
  Play,
  Database,
  Cpu,
  RefreshCw,
} from 'lucide-react';

interface NavbarProps {
  currentTab: 'overview' | 'transactions' | 'audit';
  onSelectTab: (tab: 'overview' | 'transactions' | 'audit') => void;
  onRunSimulation: () => void;
  onSeedData: () => void;
  isSimulating: boolean;
  isSeeding: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onSelectTab,
  onRunSimulation,
  onSeedData,
  isSimulating,
  isSeeding,
}) => {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Hackathon Tag */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold tracking-tight text-white">RecoverIQ</span>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                    Track 03
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 font-medium">
                  Razorpay AI Buildathon 2026
                </p>
              </div>
            </div>

            {/* Navigation Tabs */}
            <nav className="hidden md:flex items-center space-x-1 ml-6 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
              <button
                onClick={() => onSelectTab('overview')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                  currentTab === 'overview'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Activity className="w-3.5 h-3.5" />
                Overview & KPIs
              </button>

              <button
                onClick={() => onSelectTab('transactions')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                  currentTab === 'transactions'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                Transactions (600)
              </button>

              <button
                onClick={() => onSelectTab('audit')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                  currentTab === 'audit'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                Policy Audit Log
              </button>
            </nav>
          </div>

          {/* Actions & Status */}
          <div className="flex items-center gap-3">
            <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-[11px] text-slate-400 font-mono">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              <span>Pluggable LLM: <strong className="text-slate-200">Mock / Live</strong></span>
            </div>

            <button
              onClick={onSeedData}
              disabled={isSeeding || isSimulating}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition disabled:opacity-50"
              title="Re-seed synthetic dataset (Seed 42)"
            >
              <Database className={`w-3.5 h-3.5 text-slate-400 ${isSeeding ? 'animate-spin' : ''}`} />
              <span>{isSeeding ? 'Seeding...' : 'Seed Data'}</span>
            </button>

            <button
              onClick={onRunSimulation}
              disabled={isSimulating || isSeeding}
              className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/25 transition disabled:opacity-50"
            >
              {isSimulating ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Simulating...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run Batch Simulation</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="flex md:hidden items-center justify-around py-2 border-t border-slate-800/80 text-xs">
          <button
            onClick={() => onSelectTab('overview')}
            className={`px-3 py-1 rounded ${currentTab === 'overview' ? 'text-blue-400 font-bold' : 'text-slate-400'}`}
          >
            Overview
          </button>
          <button
            onClick={() => onSelectTab('transactions')}
            className={`px-3 py-1 rounded ${currentTab === 'transactions' ? 'text-blue-400 font-bold' : 'text-slate-400'}`}
          >
            Transactions
          </button>
          <button
            onClick={() => onSelectTab('audit')}
            className={`px-3 py-1 rounded ${currentTab === 'audit' ? 'text-blue-400 font-bold' : 'text-slate-400'}`}
          >
            Audit Log
          </button>
        </div>
      </div>
    </header>
  );
};
