import React, { useState, useEffect } from 'react';
import type { SimulationMetrics, Transaction } from './types';
import { getMetrics, runBatchSimulation, seedDataset } from './api/client';
import { SyntheticBanner } from './components/SyntheticBanner';
import { Navbar } from './components/Navbar';
import { TraceDrawer } from './components/TraceDrawer';
import { OverviewPage } from './pages/OverviewPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { AuditLogPage } from './pages/AuditLogPage';
import { CheckCircle2, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'overview' | 'transactions' | 'audit'>('overview');
  const [metrics, setMetrics] = useState<SimulationMetrics | null>(null);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const showToast = (text: string, type: 'success' | 'error' = 'success') => {
    setToastMessage({ text, type });
    setTimeout(() => {
      setToastMessage(null);
    }, 4000);
  };

  const loadInitialMetrics = async () => {
    try {
      const res = await getMetrics();
      setMetrics(res);
    } catch (err) {
      console.warn('Initial metrics fetch deferred (database might be unseeded)', err);
    }
  };

  useEffect(() => {
    loadInitialMetrics();
  }, []);

  const handleRunSimulation = async () => {
    try {
      setIsSimulating(true);
      const res = await runBatchSimulation();
      setMetrics(res);
      showToast(`Batch simulation completed! Recovery uplift: +${res.recovery_rate_uplift_pct}%, False retries avoided: ${res.false_retries_avoided}`);
    } catch (err: any) {
      console.error('Simulation failed', err);
      showToast('Failed to run batch simulation', 'error');
    } finally {
      setIsSimulating(false);
    }
  };

  const handleSeedData = async () => {
    try {
      setIsSeeding(true);
      const res = await seedDataset();
      await loadInitialMetrics();
      showToast(`Dataset re-seeded successfully with ${res.count} records (Seed ${res.seed}).`);
    } catch (err: any) {
      console.error('Seeding failed', err);
      showToast('Failed to seed synthetic dataset', 'error');
    } finally {
      setIsSeeding(false);
    }
  };

  const handleUpdateTransaction = (updated: Transaction) => {
    setSelectedTransaction(updated);
    // Reload metrics after single transaction update
    loadInitialMetrics();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* 1. Global Synthetic Banner */}
      <SyntheticBanner />

      {/* 2. Sticky Header Navbar */}
      <Navbar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        onRunSimulation={handleRunSimulation}
        onSeedData={handleSeedData}
        isSimulating={isSimulating}
        isSeeding={isSeeding}
      />

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-2xl bg-slate-900 border border-slate-700 text-xs font-medium animate-in fade-in slide-in-from-bottom-2 duration-200">
          {toastMessage.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          )}
          <span className="text-white">{toastMessage.text}</span>
        </div>
      )}

      {/* 3. Main Page Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentTab === 'overview' && (
          <OverviewPage
            metrics={metrics}
            onRunSimulation={handleRunSimulation}
            onSelectTransaction={setSelectedTransaction}
            onNavigateToTransactions={() => setCurrentTab('transactions')}
            isSimulating={isSimulating}
          />
        )}

        {currentTab === 'transactions' && (
          <TransactionsPage onSelectTransaction={setSelectedTransaction} />
        )}

        {currentTab === 'audit' && <AuditLogPage />}
      </main>

      {/* 4. Slide-Over Detail Drawer (5-Step Trace) */}
      <TraceDrawer
        transaction={selectedTransaction}
        onClose={() => setSelectedTransaction(null)}
        onUpdateTransaction={handleUpdateTransaction}
      />

      {/* 5. Minimal Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-6 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <strong className="text-slate-200">RecoverIQ</strong> — Built for Razorpay AI Buildathon 2026 (Track 03: AI Revenue Recovery)
          </div>
          <div className="font-mono text-[11px] text-slate-400">
            Seed 42 • Fully Deterministic • Zero External Keys Required
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
