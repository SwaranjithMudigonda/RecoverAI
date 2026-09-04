import React, { useState } from 'react';
import { LIGHTGBM_MODEL_HASH, ISOTONIC_CALIBRATOR_HASH } from '../data/frozenEvaluation';
import { Copy, Check } from 'lucide-react';

export const ModelSignatures: React.FC = () => {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copyHash = (hash: string, key: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <section className="bg-[#111820] border border-[#26313D] rounded-xl p-5 sm:p-6">
      <div className="pb-4 mb-4 border-b border-[#26313D]">
        <h2 className="text-base font-semibold text-[#F3F5F7]">
          Frozen Model Provenance Signatures
        </h2>
        <span className="text-xs text-[#9AA6B2]">
          Cryptographic SHA-256 checksums verifying frozen model and calibrator integrity
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-[#141B23] border border-[#26313D] rounded-lg p-3.5">
          <div className="flex items-center justify-between gap-2 mb-2">
            <span className="text-xs font-medium text-[#9AA6B2]">
              LightGBM S-Learner (lgbm_model.pkl)
            </span>
            <button
              type="button"
              onClick={() => copyHash(LIGHTGBM_MODEL_HASH, 'model')}
              className="text-xs text-[#9AA6B2] hover:text-[#F3F5F7] flex items-center gap-1"
            >
              {copiedKey === 'model' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copiedKey === 'model' ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <code className="text-xs font-mono text-blue-400 bg-[#0B0F14] p-2.5 rounded block border border-[#26313D] break-all select-all">
            {LIGHTGBM_MODEL_HASH}
          </code>
        </div>

        <div className="bg-[#141B23] border border-[#26313D] rounded-lg p-3.5">
          <div className="flex items-center justify-between gap-2 mb-2">
            <span className="text-xs font-medium text-[#9AA6B2]">
              Isotonic Calibrator (isotonic_calibrator.pkl)
            </span>
            <button
              type="button"
              onClick={() => copyHash(ISOTONIC_CALIBRATOR_HASH, 'calib')}
              className="text-xs text-[#9AA6B2] hover:text-[#F3F5F7] flex items-center gap-1"
            >
              {copiedKey === 'calib' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copiedKey === 'calib' ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <code className="text-xs font-mono text-blue-400 bg-[#0B0F14] p-2.5 rounded block border border-[#26313D] break-all select-all">
            {ISOTONIC_CALIBRATOR_HASH}
          </code>
        </div>
      </div>
    </section>
  );
};
