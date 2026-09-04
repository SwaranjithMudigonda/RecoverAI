import React from 'react';

export const IntegrationVerification: React.FC = () => {
  const tests = [
    { label: 'Step 7D Integration Suite', score: '18/18', status: 'Passed', desc: 'End-to-end API, agent, batch, and negative validation tests' },
    { label: 'Step 7E Release Verification', score: '10/10', status: 'Passed', desc: 'Master checksum verification, determinism, and categorical audits' },
    { label: 'Model Benchmark Test Suite', score: '14/14', status: 'Passed', desc: 'S-learner comparative tests and evaluation metric parity' },
    { label: 'Preceding Artifact Integrity', score: '14/14', status: 'Identical', desc: 'Byte-identical SHA-256 matches vs master reference' },
    { label: 'Concurrent API Stress Load', score: '50/50', status: 'Successful', desc: 'Simultaneous workers executed with zero race conditions' },
  ];

  return (
    <section className="bg-[#111820] border border-[#26313D] rounded-xl p-5 sm:p-6">
      <div className="pb-4 mb-4 border-b border-[#26313D]">
        <h2 className="text-base font-semibold text-[#F3F5F7]">
          Automated Verification Evidence
        </h2>
        <span className="text-xs text-[#9AA6B2]">
          Pre-release testing evidence and system regression passes
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {tests.map(t => (
          <div key={t.label} className="bg-[#141B23] border border-[#26313D] rounded-lg p-3.5 flex flex-col justify-between">
            <div>
              <div className="text-xs font-medium text-[#9AA6B2] mb-1">
                {t.label}
              </div>
              <div className="text-xl font-bold text-[#F3F5F7] font-mono">
                {t.score}
              </div>
            </div>
            <div className="mt-2 pt-2 border-t border-[#26313D]">
              <span className="inline-flex items-center text-[10px] font-medium text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                {t.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
