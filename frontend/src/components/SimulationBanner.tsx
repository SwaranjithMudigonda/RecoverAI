import React from 'react';
import { Info } from 'lucide-react';

export const SimulationBanner: React.FC = () => {
  return (
    <div className="w-full bg-[#18140C] border-b border-amber-500/20 px-4 py-2 text-xs">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-2 text-amber-200/90">
        <div className="flex items-center gap-2 font-medium">
          <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] uppercase tracking-wider font-semibold border border-amber-500/30">
            SIMULATION
          </span>
          <span className="font-semibold text-amber-300">
            Prototype environment • Outcomes are simulated • No real transactions executed
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-amber-400/70">
          <Info className="w-3.5 h-3.5 shrink-0" />
          <span>Olist real transaction context • Simulated failure reasons & recovery actions • Zero live gateway calls</span>
        </div>
      </div>
    </div>
  );
};
