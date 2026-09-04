import React from 'react';
import { ShieldCheck, Activity, Layers } from 'lucide-react';
import { useCurrency } from '../lib/utils';

interface HeaderProps {
  activeTab: 'decide' | 'batch' | 'trust';
  onTabChange: (tab: 'decide' | 'batch' | 'trust') => void;
  isOnline: boolean | null;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, onTabChange, isOnline }) => {
  const { currency, toggleCurrency } = useCurrency();

  return (
    <header className="sticky top-0 z-50 w-full bg-[#0B0E14]/95 backdrop-blur border-b border-[#232D38]">
      {/* SIMULATED ENVIRONMENT — PROTOTYPE ONLY — NO REAL TRANSACTIONS EXECUTED */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
        {/* Left: Brand Identity */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold tracking-tight text-[#F3F5F7]">
              RecoverAI
            </span>
            <span className="text-[10px] font-mono font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-[#16202C] text-[#8C9BAE] border border-[#263545]">
              PROTOTYPE ONLY
            </span>
          </div>
          <span className="text-[#2D3A4B] hidden sm:inline">|</span>
          <span className="text-xs text-[#8C9BAE] hidden sm:inline font-normal">
            AI Revenue Recovery Orchestrator
          </span>
        </div>

        {/* Center: Primary Navigation */}
        <nav className="flex items-center gap-1.5 p-1 rounded-lg bg-[#121820] border border-[#232D38]">
          <button
            type="button"
            onClick={() => onTabChange('decide')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activeTab === 'decide'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-[#8C9BAE] hover:text-[#F3F5F7] hover:bg-[#1A2330]'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Decide</span>
          </button>
          <button
            type="button"
            onClick={() => onTabChange('batch')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activeTab === 'batch'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-[#8C9BAE] hover:text-[#F3F5F7] hover:bg-[#1A2330]'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Batch Stream</span>
          </button>
          <button
            type="button"
            onClick={() => onTabChange('trust')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activeTab === 'trust'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-[#8C9BAE] hover:text-[#F3F5F7] hover:bg-[#1A2330]'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Trust & Evidence</span>
          </button>
        </nav>

        {/* Right: Currency Mode & API Gateway Status Indicator */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Market & Currency Toggle */}
          <button
            type="button"
            onClick={toggleCurrency}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#121820] hover:bg-[#16202C] border border-[#232D38] text-xs font-mono font-semibold transition-all shadow-sm"
            title="Toggle Market Currency: Razorpay INR (₹) vs Olist BRL (R$)"
          >
            <span className={currency === 'INR' ? 'text-emerald-400 font-bold' : 'text-[#667380]'}>
              🇮🇳 INR (₹)
            </span>
            <span className="text-[#384452]">|</span>
            <span className={currency === 'BRL' ? 'text-blue-400 font-bold' : 'text-[#667380]'}>
              🇧🇷 BRL
            </span>
          </button>

          <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-[#121820] border border-[#232D38] text-xs font-mono">
            {isOnline === null ? (
              <>
                <span className="w-2 h-2 rounded-full bg-slate-500 animate-pulse" />
                <span className="text-[#8C9BAE]">API Connecting...</span>
              </>
            ) : isOnline ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-[#F3F5F7] font-semibold">API Online</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-rose-500" />
                <span className="text-rose-400 font-semibold">API Offline</span>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
